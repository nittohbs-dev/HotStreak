"""機能サービスを登録する共通REST/WS。参加受付・画面は別Issueで接続する。"""
import asyncio
from copy import deepcopy
from secrets import compare_digest, token_urlsafe
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from hotstreak_core.state import GameSession
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

    def complete_transition(self, session, old_phase):
        target = session.phase
        if target != old_phase and target in self.services:
            session.phase = old_phase
            self.services[target].enter(session)

    def publish(self, session, events):
        for viewer, queue in self.listeners[session.session_id].values():
            viewer = viewer if any(p.player_id == viewer for p in session.players) else None
            payload = self.snapshot(session, None if session.phase == "card-seed" else viewer)
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
                if session.phase == "setup-cards" and body.get("firstPlayerId") is not None:
                    first = session.player(body["firstPlayerId"])
                    session.draft_first = session.draft_start = session.players.index(first)
                service.advance(session)
                self.complete_transition(session, old_phase)
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


def create_app(services=None, public_base=None):
    if services is None:
        from hotstreak_core.setup_cards import SetupCardsService
        services = [SetupCardsService()]
    runtime = SyncRuntime(services)
    app = FastAPI(title='HotStreak sync features')
    app.state.runtime = runtime

    def viewer(session, connection):
        token = connection.cookies.get(f'hs_{session.session_id}', '')
        return next((p.player_id for p in session.players if compare_digest(p.token, token)), None)

    def local_display(request):
        if not request.client or request.client.host not in ('127.0.0.1', '::1', 'testclient'):
            raise RuleError('会場Displayから操作してください', 403)

    def actor(session, request, claimed=None):
        pid = viewer(session, request)
        if not pid or (claimed is not None and pid != claimed):
            raise RuleError('操作できません', 403)
        return pid

    @app.middleware('http')
    async def same_origin(request, call_next):
        origin = request.headers.get('origin')
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin and origin.split('://', 1)[-1] != request.headers.get('host'):
            return JSONResponse(status_code=403, content=dict(message='操作できません'))
        return await call_next(request)

    async def read_body(request):
        try:
            body = await request.json()
        except ValueError:
            raise RuleError('JSONを指定してください', 400)
        if not isinstance(body, dict):
            raise RuleError('JSONオブジェクトを指定してください', 400)
        return body

    @app.post('/api/sessions')
    async def create_session(request: Request):
        local_display(request)
        if 'lobby' not in runtime.services:
            raise RuleError('参加受付が登録されていません', 404)
        session = GameSession('sess_' + token_urlsafe(12), [])
        runtime.add_session(session)
        base = (public_base or str(request.base_url)).rstrip('/')
        return dict(session.public(), joinUrl=f'{base}/join/{session.session_id}', displayToken=session.display_token)

    @app.get('/api/sessions/{sid}')
    async def current(sid: str, request: Request):
        session = runtime.get(sid)
        async with runtime.locks[sid]:
            return dict(runtime.snapshot(session, viewer(session, request)), playerId=viewer(session, request))

    @app.post('/api/sessions/{sid}/join')
    async def join(sid: str):
        session = runtime.get(sid)
        service = runtime.services.get('lobby')
        if not service:
            raise RuleError('参加受付が登録されていません', 404)
        async with runtime.locks[sid]:
            player = service.join(session)
            session.revision += 1
            runtime.publish(session, ['lobby.state'])
            response = JSONResponse(dict(session.public(), playerId=player.player_id))
            response.set_cookie(f'hs_{sid}', player.token, httponly=True, samesite='strict')
            return response

    @app.put('/api/sessions/{sid}/players/{pid}/name')
    async def name(sid: str, pid: str, request: Request):
        session = runtime.get(sid)
        actor(session, request, pid)
        body = await read_body(request)
        async with runtime.locks[sid]:
            backup = deepcopy(session.__dict__)
            try:
                runtime.services['lobby'].name(session, pid, body.get('displayName'))
            except Exception:
                session.__dict__.clear()
                session.__dict__.update(backup)
                raise
            session.revision += 1
            runtime.publish(session, ['lobby.state'])
            return runtime.snapshot(session, pid)

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
        local_display(request)
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

    async def player_action(sid, section, action, request):
        session = runtime.get(sid)
        body = await read_body(request)
        pid = actor(session, request, body.get('playerId'))
        key = request.headers.get('Idempotency-Key', '')
        if not key or len(key) > 128:
            raise RuleError('操作IDを指定してください', 400)
        receipt_key = ('player', pid, key)
        fingerprint = (section, action, body)
        async with runtime.locks[sid]:
            receipts = runtime.receipts[sid]
            if receipt_key in receipts:
                previous, result = receipts[receipt_key]
                if previous != fingerprint:
                    raise RuleError('操作IDが異なる操作に使われています')
                return deepcopy(result)
            service = next((s for s in services if s.section == section), None)
            if service is None or not hasattr(service, 'act'):
                raise RuleError('機能が見つかりません', 404)
            backup = deepcopy(session.__dict__)
            try:
                service.act(session, action, body, pid)
            except Exception:
                session.__dict__.clear()
                session.__dict__.update(backup)
                raise
            session.revision += 1
            result = runtime.snapshot(session, pid)
            receipts[receipt_key] = (deepcopy(fingerprint), deepcopy(result))
            if len(receipts) > 1024:
                receipts.pop(next(iter(receipts)))
            runtime.publish(session, [service.event+'.state'])
            return result

    @app.post('/api/sessions/{sid}/betting/picks')
    async def pick(sid: str, request: Request):
        return await player_action(sid, 'betting', 'picks', request)

    @app.put('/api/sessions/{sid}/betting/double')
    async def double(sid: str, request: Request):
        return await player_action(sid, 'betting', 'double', request)

    @app.post('/api/sessions/{sid}/seed')
    async def seed(sid: str, request: Request):
        return await player_action(sid, 'seed', 'seed', request)

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
            queue.put_nowait(dict(type=event+'.state', payload=runtime.snapshot(session, None if session.phase == "card-seed" else pid)))
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
