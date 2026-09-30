from fastapi.testclient import TestClient
from hotstreak_sync.server import build_app


def test_lobby_names_wait_for_display_enter():
    app = build_app('http://192.168.1.10:8000')
    with TestClient(app) as display:
        created = display.post('/api/sessions', json={}).json()
        sid = created['sessionId']
        assert created['joinUrl'] == f'http://192.168.1.10:8000/join/{sid}'
        clients = [TestClient(app) for _ in range(3)]
        ids = [c.post(f'/api/sessions/{sid}/join', json={}).json()['playerId'] for c in clients]
        assert clients[0].put(f'/api/sessions/{sid}/players/{ids[1]}/name', json={'displayName': '盗用'}).status_code == 403
        with display.websocket_connect(f'/ws/sessions/{sid}') as ws:
            assert ws.receive_json()['type'] == 'lobby.state'
            for i, (c, pid) in enumerate(zip(clients, ids)):
                result = c.put(f'/api/sessions/{sid}/players/{pid}/name', json={'displayName': f'P{i}'})
                assert result.status_code == 200
                assert ws.receive_json()['type'] == 'lobby.state'
            current = display.get(f'/api/sessions/{sid}').json()
            assert current['phase'] == 'lobby'
            headers = {'X-Display-Token': created['displayToken'], 'Idempotency-Key': 'start'}
            result = display.post(f'/api/sessions/{sid}/advance',
                                  json={'phase': 'lobby', 'revision': current['revision']}, headers=headers)
            assert result.status_code == 200
            assert ws.receive_json()['type'] == 'lobby.advanced'
            assert ws.receive_json()['type'] == 'setup.state'
        state = display.get(f'/api/sessions/{sid}').json()
        assert state['phase'] == 'setup-cards' and len(state['faceUpCards']) == 15
        assert all(p['balance'] == 10 for p in state['players'])
        assert clients[0].post(f'/api/sessions/{sid}/join').status_code == 409
        assert 'displayToken' not in state


def test_lobby_limits_enter_placeholder_and_origin():
    app = build_app()
    with TestClient(app) as c:
        created = c.post('/api/sessions', json={}).json()
        sid = created['sessionId']
        headers = {'X-Display-Token': created['displayToken'], 'Idempotency-Key': 'advance'}
        for _ in range(2):
            c.post(f'/api/sessions/{sid}/join')
        current = c.get(f'/api/sessions/{sid}').json()
        assert c.post(f'/api/sessions/{sid}/advance', json={'phase': 'lobby', 'revision': current['revision']}, headers=headers).status_code == 409
        for _ in range(6):
            assert c.post(f'/api/sessions/{sid}/join').status_code == 200
        assert c.post(f'/api/sessions/{sid}/join').status_code == 409
        assert c.post('/api/sessions', json={}, headers={'Origin': 'https://elsewhere.example'}).status_code == 403
        current = c.get(f'/api/sessions/{sid}').json()
        result = c.post(f'/api/sessions/{sid}/advance', json={'phase': 'lobby', 'revision': current['revision']}, headers=headers)
        assert result.status_code == 200
        assert [p['displayName'] for p in result.json()['players']] == [f'プレイヤー{i}' for i in range(1, 9)]
        assert len(result.json()['faceUpCards']) == 10
