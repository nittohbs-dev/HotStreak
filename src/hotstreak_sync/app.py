"""FastAPI / WebSocket。セッション状態はメモリ内、ワーカーは1個で動かす。"""
import asyncio
from copy import deepcopy
from pathlib import Path
import secrets
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from hotstreak_core.session import GameSession, RuleError

ROOT = Path(__file__).resolve().parents[2]
PREFIX = {'lobby': 'lobby', 'setup-cards': 'setup', 'betting': 'betting',
          'card-seed': 'seed', 'race': 'race', 'payout': 'payout', 'champion': 'champion'}


class Room:
    def __init__(self, session):
        self.session = session
        self.lock = asyncio.Lock()
        self.listeners = {}  # socket -> (playerId, bounded queue)
        self.receipts = {}  # idempotency key -> (request fingerprint, response)

    def publish(self, old_phase):
        s = self.session
        transition = None
        if old_phase != s.phase:
            transition = f'{PREFIX[old_phase]}.finished' if old_phase == 'race' else f'{PREFIX[old_phase]}.advanced'
        for ws, (pid, queue) in list(self.listeners.items()):
            # 最終精算後のロビーは新規参加。旧プレイヤーの秘密状態は送らない。
            viewer = pid if any(p.player_id == pid for p in s.players) else None
            payload = deepcopy(s.snapshot(viewer))
            messages = []
            if transition:
                messages.append(dict(type=transition, payload=payload))
            messages.append(dict(type=f'{PREFIX[s.phase]}.state', payload=payload))
            for message in messages:
                if queue.full():
                    # 遅い購読者に最新スナップショットを残す。復帰時はphaseで追従。
                    queue.get_nowait()
                queue.put_nowait(message)


def create_app(session_factory=GameSession):
    app = FastAPI(title='HotStreak sync')
    app.state.rooms = {}

    def room(sid):
        if sid not in app.state.rooms:
            raise RuleError('セッションが見つかりません', 404)
        return app.state.rooms[sid]

    def player_id(s, connection, required=False):
        token = connection.cookies.get(f'hs_{s.session_id}', '')
        pid = next((p.player_id for p in s.players if secrets.compare_digest(p.token, token)), None)
        if required and pid is None:
            raise RuleError('参加し直してください', 403)
        return pid

    def local(request):
        if not request.client or request.client.host not in ('127.0.0.1', '::1', 'testclient'):
            raise RuleError('会場Displayから操作してください', 403)

    def display(s, request):
        local(request)
        if not secrets.compare_digest(request.headers.get('X-Display-Token', ''), s.display_token):
            raise RuleError('Display認証が必要です', 403)

    @app.exception_handler(RuleError)
    async def rule_error(request, exc):
        return JSONResponse(status_code=exc.status, content=dict(message=str(exc)))

    @app.post('/api/sessions')
    async def create(request: Request):
        local(request)
        s = session_factory()
        app.state.rooms[s.session_id] = Room(s)
        return dict(s.snapshot(), displayToken=s.display_token, joinUrl=f'/join/{s.session_id}')

    @app.get('/api/sessions/{sid}')
    async def snapshot(sid: str, request: Request):
        r = room(sid)
        async with r.lock:
            return deepcopy(r.session.snapshot(player_id(r.session, request)))

    @app.post('/api/sessions/{sid}/join')
    async def join(sid: str, request: Request):
        r = room(sid)
        async with r.lock:
            s = r.session
            existing = player_id(s, request)
            if existing:
                p = s.player(existing)
            else:
                p = s.join()
                s.revision += 1
                r.publish(s.phase)
            response = JSONResponse(dict(s.snapshot(p.player_id), playerId=p.player_id))
            response.set_cookie(f'hs_{sid}', p.token, httponly=True, samesite='strict',
                                secure=request.url.scheme == 'https', path='/')
            return response

    async def mutate(sid, request, operation, host=False):
        r = room(sid)
        async with r.lock:
            s = r.session
            pid = None
            if host:
                if request.headers.get('X-Display-Token'):
                    display(s, request)
                else:
                    pid = player_id(s, request, True)
                    if pid != s.host_player_id or s.phase == 'race':
                        raise RuleError('最初の参加者だけが画面を進められます（レースは会場操作）', 403)
            else:
                pid = player_id(s, request, True)
            try:
                body = await request.json()
            except ValueError:
                raise RuleError('JSONを指定してください', 400)
            if not isinstance(body, dict):
                raise RuleError('JSONオブジェクトを指定してください', 400)
            key = request.headers.get('Idempotency-Key', '')
            if not key or len(key) > 128:
                raise RuleError('操作IDが必要です', 400)
            fingerprint = (pid, request.method, request.url.path, body)
            receipt_key = (pid, key)
            if receipt_key in r.receipts:
                previous, result = r.receipts[receipt_key]
                if previous != fingerprint:
                    raise RuleError('操作IDが異なる操作に使われています')
                return result
            # 古い画面のEnterや二つのDisplayによる二重進行を拒否する。
            if host and (type(body.get('revision')) is not int or body.get('revision') != s.revision or body.get('phase') != s.phase):
                raise RuleError('状態が更新されました。再取得してください')
            old_phase = s.phase
            operation(s, pid, body)
            s.revision += 1
            viewer = pid if any(p.player_id == pid for p in s.players) else None
            result = deepcopy(s.snapshot(viewer))
            r.receipts[receipt_key] = (deepcopy(fingerprint), result)
            if len(r.receipts) > 1024:
                r.receipts.pop(next(iter(r.receipts)))
            r.publish(old_phase)
            return result

    @app.put('/api/sessions/{sid}/players/{pid}/name')
    async def name(sid: str, pid: str, request: Request):
        def change(s, caller, body):
            if caller != pid:
                raise RuleError('他の参加者の名前は変更できません', 403)
            s.name(pid, body.get('displayName'))
        return await mutate(sid, request, change)

    @app.post('/api/sessions/{sid}/advance')
    async def advance(sid: str, request: Request):
        return await mutate(sid, request, lambda s, pid, body: s.advance(), host=True)

    @app.post('/api/sessions/{sid}/betting/picks')
    async def pick(sid: str, request: Request):
        return await mutate(sid, request, lambda s, pid, body: s.pick(pid, body))

    @app.put('/api/sessions/{sid}/betting/double')
    async def double(sid: str, request: Request):
        return await mutate(sid, request, lambda s, pid, body: s.double(pid, body.get('ticketInstanceId')))

    @app.post('/api/sessions/{sid}/seed')
    async def seed(sid: str, request: Request):
        return await mutate(sid, request, lambda s, pid, body: s.seed(pid, body.get('handCardId')))

    @app.get('/api/sessions/{sid}/{section}')
    async def feature(sid: str, section: str, request: Request):
        expected = {'setup': 'setup-cards', 'betting': 'betting', 'seed': 'card-seed',
                    'race': 'race', 'payout': 'payout', 'champion': 'champion'}
        if section not in expected:
            raise RuleError('画面が見つかりません', 404)
        r = room(sid)
        async with r.lock:
            r.session.require(expected[section])
            return deepcopy(r.session.snapshot(player_id(r.session, request)))

    @app.websocket('/ws/sessions/{sid}')
    async def subscribe(ws: WebSocket, sid: str):
        # 同一オリジンのページだけを許可。ネイティブDisplayはOriginなし。
        origin = ws.headers.get('origin')
        if origin and origin.split('://', 1)[-1] != ws.headers.get('host'):
            await ws.close(code=1008)
            return
        if sid not in app.state.rooms:
            await ws.close(code=1008)
            return
        r = room(sid)
        await ws.accept()
        queue = asyncio.Queue(maxsize=8)
        async with r.lock:
            pid = player_id(r.session, ws)
            r.listeners[ws] = (pid, queue)
            queue.put_nowait(dict(type=f'{PREFIX[r.session.phase]}.state', payload=deepcopy(r.session.snapshot(pid))))
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
            async with r.lock:
                r.listeners.pop(ws, None)

    @app.get('/join/{sid}')
    async def join_page(sid: str):
        room(sid)
        return RedirectResponse(f'/phone/lobby.html?session={sid}&connection=session')

    app.mount('/assets', StaticFiles(directory=ROOT/'assets'), name='assets')
    app.mount('/phone', StaticFiles(directory=ROOT/'src/hotstreak_phone', html=True), name='phone')
    return app


app = create_app()
