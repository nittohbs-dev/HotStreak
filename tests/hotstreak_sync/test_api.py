from concurrent.futures import ThreadPoolExecutor
from random import Random
from uuid import uuid4
from fastapi.testclient import TestClient
from hotstreak_core.session import GameSession
from hotstreak_sync.app import create_app


def command(client, method, path, body, **headers):
    return client.request(method, path, json=body, headers={'Idempotency-Key': str(uuid4()), **headers})


def test_http_ws_private_hands_idempotency_and_three_races():
    app = create_app(lambda: GameSession(rng=Random(4)))
    with TestClient(app) as host:
        created = host.post('/api/sessions').json()
        sid = created['sessionId']
        base = f'/api/sessions/{sid}'
        token = {'X-Display-Token': created['displayToken']}
        people = []
        for i in range(3):
            c = TestClient(app)
            joined = c.post(base+'/join').json()
            pid = joined['playerId']
            people.append((c, pid))
            assert command(c, 'PUT', base+f'/players/{pid}/name', {'displayName': f'P{i}'}).status_code == 200
            assert c.post(base+'/join').json()['playerId'] == pid
        assert host.get(base).json()['playerCount'] == 3
        assert command(people[0][0], 'PUT', base+f'/players/{people[1][1]}/name', {'displayName': 'wrong'}).status_code == 403

        def advance():
            state = host.get(base).json()
            body = {'revision': state['revision'], 'phase': state['phase']}
            response = command(host, 'POST', base+'/advance', body, **token)
            assert response.status_code == 200, response.text
            return response.json()

        assert command(host, 'POST', base+'/advance', {}).status_code == 403
        with host.websocket_connect(f'/ws/sessions/{sid}') as ws:
            assert ws.receive_json()['type'] == 'lobby.state'
            setup = advance()
            assert ws.receive_json()['type'] == 'lobby.advanced'
            public = ws.receive_json()
            assert public['type'] == 'setup.state'
            assert len(public['payload']['faceUpCards']) == 15
            assert 'hand' not in public['payload']
            assert all('hand' not in p for p in public['payload']['players'])
        # 同じ操作を二度送っても次のフェーズへ二重進行しない。
        request_headers = {**token, 'Idempotency-Key': 'fixed-setup'}
        body = {'revision': setup['revision'], 'phase': setup['phase']}
        a = host.post(base+'/advance', json=body, headers=request_headers)
        b = host.post(base+'/advance', json=body, headers=request_headers)
        assert a.json() == b.json() and a.json()['phase'] == 'betting'
        assert command(host, 'POST', base+'/advance', body, **token).status_code == 409

        for race in range(1, 4):
            while True:
                state = host.get(base).json()
                if state['currentPlayerId'] is None:
                    break
                client = next(c for c, pid in people if pid == state['currentPlayerId'])
                stock = next(t for t in state['stock'] if t['remaining'])
                assert command(client, 'POST', base+'/betting/picks',
                               dict(ticketId=stock['ticketId'], ticketKind=stock['ticketKind'], face='risky')).status_code == 200
            if race == 3:
                for c, pid in people:
                    picks = c.get(base).json()['picksByPlayer'][pid]
                    assert command(c, 'PUT', base+'/betting/double', {'ticketInstanceId': picks[0]['ticketInstanceId']}).status_code == 200
            advance()
            assert 'hand' not in host.get(base+'/seed').json()
            for c, pid in people:
                with c.websocket_connect(f'/ws/sessions/{sid}') as ws:
                    mine = ws.receive_json()['payload']
                    hand = mine['hand']
                    assert len(hand) == 3
                    assert mine['phase'] == 'card-seed'
                assert command(c, 'POST', base+'/seed', {'handCardId': hand[0]['cardId']}).status_code == 200
                assert command(c, 'POST', base+'/seed', {'handCardId': hand[1]['cardId']}).status_code == 409
            state = advance()
            assert state['phase'] == 'race'
            count = 0
            while state['phase'] == 'race':
                state = advance()
                count += 1
                assert count <= 60
            assert state['phase'] == 'payout'
            assert state['myBreakdown'] is None
            for c, pid in people:
                payout = c.get(base+'/payout').json()
                assert payout['myBreakdown']['playerId'] == pid
                assert len(payout['myBreakdown']['items']) == 2
            state = advance()
        assert state['phase'] == 'lobby'


def test_two_simultaneous_enter_requests_only_advance_once():
    app = create_app()
    with TestClient(app) as c:
        new = c.post('/api/sessions').json()
        sid = new['sessionId']
        s = app.state.rooms[sid].session
        for _ in range(3):
            s.join()
        s.setup()
        body = {'phase': s.phase, 'revision': s.revision}
        def submit(_):
            return command(c, 'POST', f'/api/sessions/{sid}/advance', body,
                           **{'X-Display-Token': s.display_token}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(submit, range(2))) == [200, 409]
        assert s.phase == 'betting'


def test_ws_rejects_cross_origin():
    from starlette.websockets import WebSocketDisconnect
    import pytest
    with TestClient(create_app()) as c:
        sid = c.post('/api/sessions').json()['sessionId']
        with pytest.raises(WebSocketDisconnect):
            with c.websocket_connect(f'/ws/sessions/{sid}', headers={'origin': 'https://elsewhere.invalid'}):
                pass
