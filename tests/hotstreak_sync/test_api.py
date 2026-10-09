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
        assert state['phase'] == 'champion'
        assert state['winners']
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


def test_first_phone_authority_readiness_and_display_race_are_enforced():
    app = create_app()
    with TestClient(app) as display:
        initial = display.post('/api/sessions').json()
        base = '/api/sessions/' + initial['sessionId']
        first = TestClient(app, client=('192.0.2.10', 5000))
        other = TestClient(app, client=('192.0.2.11', 5001))
        joined = first.post(base+'/join').json()
        other.post(base+'/join')
        state = first.get(base).json()
        assert state['hostPlayerId'] == joined['playerId']
        assert state['canAdvance']
        assert not other.get(base).json()['canAdvance']
        assert 'displayToken' not in state
        body = dict(phase=state['phase'], revision=state['revision'])
        assert command(other, 'POST', base+'/advance', body).status_code == 403
        response = command(first, 'POST', base+'/advance', body)
        assert response.status_code == 200
        assert response.json()['phase'] == 'setup-cards'
        assert command(first, 'POST', base+'/advance', body).status_code == 409
        state = response.json()
        body = dict(phase=state['phase'], revision=state['revision'])
        headers = {'Idempotency-Key': 'one-phone-command'}
        response = first.post(base+'/advance', json=body, headers=headers)
        assert response.status_code == 200
        assert first.post(base+'/advance', json=body, headers=headers).json() == response.json()
        state = response.json()
        assert not state['canAdvance'] and state['advanceReason']
        assert command(first, 'POST', base+'/advance', dict(phase=state['phase'], revision=state['revision'])).status_code == 409
        with first.websocket_connect('/ws/sessions/'+initial['sessionId']) as ws:
            assert ws.receive_json()['payload']['hostPlayerId'] == joined['playerId']
        s = app.state.rooms[initial['sessionId']].session
        s.phase = 'race'
        assert command(first, 'POST', base+'/advance', dict(phase='race', revision=s.revision)).status_code == 403


def test_phone_and_display_simultaneous_transition_only_once():
    app = create_app()
    with TestClient(app) as display:
        initial = display.post('/api/sessions').json()
        base = '/api/sessions/' + initial['sessionId']
        first = display
        first.post(base+'/join')
        state = first.get(base).json()
        body = dict(phase=state['phase'], revision=state['revision'])
        def submit(phone):
            return command(first if phone else display, 'POST', base+'/advance', body,
                           **({} if phone else {'X-Display-Token': initial['displayToken']})).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(submit, [False, True])) == [200, 409]


def test_champion_keeps_all_tied_winners_and_reset_revokes_old_phone():
    from hotstreak_core.race import RaceEngine
    app = create_app()
    with TestClient(app) as display:
        initial = display.post('/api/sessions').json()
        base = '/api/sessions/' + initial['sessionId']
        first = TestClient(app)
        first.post(base+'/join')
        s = app.state.rooms[initial['sessionId']].session
        for _ in range(7):
            s.join()
        s.setup()
        s.engine = RaceEngine(s.public_cards + [p.hand[0] for p in s.players], Random(2))
        for _ in range(100):
            s.engine.reveal()
            if s.engine.finished:
                break
        s.settle()
        # 同点の最終配当スナップショットを用意（精算規則自体は別テスト）。
        s.race_index = 3
        before = [p.balance for p in s.players]
        def advance():
            state = first.get(base).json()
            return command(first, 'POST', base+'/advance', dict(phase=state['phase'], revision=state['revision']))
        response = advance()
        assert response.status_code == 200
        champion = response.json()
        assert champion['phase'] == 'champion'
        assert len(champion['winners']) == 8
        assert [p.balance for p in s.players] == before
        assert first.get(base).json()['phase'] == 'champion'
        response = advance()
        assert response.status_code == 200
        assert response.json()['phase'] == 'lobby'
        assert response.json()['hostPlayerId'] is None
        assert response.json()['canAdvance'] is False
        assert advance().status_code == 403
        newcomer = TestClient(app)
        assert newcomer.post(base+'/join').json()['canAdvance']
        assert not first.get(base).json()['canAdvance']
