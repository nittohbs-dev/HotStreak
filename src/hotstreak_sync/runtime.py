"""機能サービスを登録する共通REST/WS。参加受付・画面は別Issueで接続する。"""
import asyncio
from copy import deepcopy
from secrets import compare_digest
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from hotstreak_core.state import RuleError


class SyncRuntime:
    def __init__(self, services):
        self.services = {service.phase: service for service in services}
        self.sessions, self.locks, self.receipts, self.listeners = {}, {}, {}, {}

    def add_session(self, session):
        if session.session_id in self.sessions:
            raise RuleError('セッションは登録済みです')
        sid = session.session_id
        self.sessions[sid] = session
        self.locks[sid] = asyncio.Lock()
        self.receipts[sid] = {}
        self.listeners[sid] = {}

    def get(self, sid):
        if sid not in self.sessions:
            raise RuleError('セッションが見つかりません', 404)
        return self.sessions[sid]

    def snapshot(self, session, viewer=None):
        service = self.services.get(session.phase)
        return deepcopy(service.snapshot(session, viewer) if service else session.public())

    def publish(self, session, events):
        for viewer, queue in self.listeners[session.session_id].values():
            viewer = viewer if any(p.player_id == viewer for p in session.players) else None
            payload = self.snapshot(session, viewer)
            for kind in events:
                if queue.full():
                    queue.get_nowait()
                queue.put_nowait(dict(type=kind, payload=payload))

    async def enter(self, sid, phase):
        """ロビー完了・仕込み完了・race.finishedから呼ぶ内部入口。HTTP配布/精算APIは設けない。"""
        session = self.get(sid)
        if phase not in self.services:
            raise RuleError('同期機能が登録されていません')
        async with self.locks[sid]:
            backup = deepcopy(session.__dict__)
            try:
                self.services[phase].enter(session)
            except Exception:
                session.__dict__.clear()
                session.__dict__.update(backup)
                raise
            session.revision += 1
            self.publish(session, [self.services[phase].event+'.state'])
            return self.snapshot(session)

    async def advance(self, sid, body, key):
        session = self.get(sid)
        async with self.locks[sid]:
            receipts = self.receipts[sid]
            if key in receipts:
                previous, result = receipts[key]
                if previous != body:
                    raise RuleError('操作IDが異なる操作に使われています')
                return deepcopy(result)
            if type(body.get('revision')) is not int or body['revision'] != session.revision or body.get('phase') != session.phase:
                raise RuleError('状態が更新されました。再取得してください')
            service = self.services.get(session.phase)
            if not service:
                raise RuleError('このフェーズの進行は別の機能が担当します')
            backup = deepcopy(session.__dict__)
            old_phase = session.phase
            try:
                service.advance(session)
                # レース終了と精算は同一排他区間。精算失敗時はめくりもロールバック。
                if old_phase == 'race' and session.phase == 'payout' and 'payout' in self.services:
                    self.services['payout'].enter(session)
            except Exception:
                session.__dict__.clear()
                session.__dict__.update(backup)
                raise
            session.revision += 1
            result = self.snapshot(session)
            receipts[key] = (deepcopy(body), result)
            if len(receipts) > 1024:
                receipts.pop(next(iter(receipts)))
            events = [service.event+'.state']
            if session.phase != old_phase:
                events = [service.event+('.finished' if old_phase == 'race' else '.advanced')]
                next_service = self.services.get(session.phase)
                if next_service:
                    events.append(next_service.event+'.state')
            self.publish(session, events)
            return deepcopy(result)


def create_app(services=None):
    if services is None:
        from hotstreak_core.setup_cards import SetupCardsService
        services = [SetupCardsService()]
    runtime = SyncRuntime(services)
    app = FastAPI(title='HotStreak sync features')
    app.state.runtime = runtime

    def viewer(session, connection):
        token = connection.cookies.get(f'hs_{session.session_id}', '')
        return next((p.player_id for p in session.players if compare_digest(p.token, token)), None)

    @app.exception_handler(RuleError)
    async def rule_error(request, exc):
        return JSONResponse(status_code=exc.status, content=dict(message=str(exc)))

    @app.get('/api/sessions/{sid}/{section}')
    async def state(sid: str, section: str, request: Request):
        session = runtime.get(sid)
        service = next((s for s in services if s.section == section), None)
        if not service:
            raise RuleError('機能が見つかりません', 404)
        async with runtime.locks[sid]:
            session.require(service.phase)
            return runtime.snapshot(session, viewer(session, request))

    @app.post('/api/sessions/{sid}/advance')
    async def advance(sid: str, request: Request):
        session = runtime.get(sid)
        if not request.client or request.client.host not in ('127.0.0.1', '::1', 'testclient'):
            raise RuleError('会場Displayから操作してください', 403)
        if not compare_digest(request.headers.get('X-Display-Token', ''), session.display_token):
            raise RuleError('Display認証が必要です', 403)
        try:
            body = await request.json()
        except ValueError:
            raise RuleError('JSONを指定してください', 400)
        key = request.headers.get('Idempotency-Key', '')
        if not isinstance(body, dict) or not key or len(key) > 128:
            raise RuleError('操作IDとJSONオブジェクトが必要です', 400)
        return await runtime.advance(sid, body, key)

    @app.websocket('/ws/sessions/{sid}')
    async def subscribe(ws: WebSocket, sid: str):
        origin = ws.headers.get('origin')
        if sid not in runtime.sessions or (origin and origin.split('://', 1)[-1] != ws.headers.get('host')):
            await ws.close(code=1008)
            return
        await ws.accept()
        session = runtime.get(sid)
        queue = asyncio.Queue(maxsize=8)
        async with runtime.locks[sid]:
            pid = viewer(session, ws)
            runtime.listeners[sid][ws] = (pid, queue)
            service = runtime.services.get(session.phase)
            event = service.event if service else session.phase
            queue.put_nowait(dict(type=event+'.state', payload=runtime.snapshot(session, pid)))
        async def send():
            while True:
                await ws.send_json(await queue.get())
        sender = asyncio.create_task(send())
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)
            async with runtime.locks[sid]:
                runtime.listeners[sid].pop(ws, None)
    return app
