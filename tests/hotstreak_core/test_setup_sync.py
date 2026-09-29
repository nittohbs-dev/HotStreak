import asyncio
from concurrent.futures import ThreadPoolExecutor
from random import Random
import pytest
from fastapi.testclient import TestClient
from hotstreak_core.state import GameSession, Player, RuleError
from hotstreak_core.setup_cards import SetupCardsService
from hotstreak_sync.runtime import create_app


def fixture(deal=True):
    session = GameSession('test', [Player(str(i), name=f'P{i}') for i in range(3)], rng=Random(1))
    app = create_app()
    app.state.runtime.add_session(session)
    if deal:
        asyncio.run(app.state.runtime.enter('test', 'setup-cards'))
    return session, app


def headers(s, key='key'):
    return {'X-Display-Token': s.display_token, 'Idempotency-Key': key}


def test_setup_is_once_and_private():
    s, app = fixture()
    cards = list(s.public_cards)
    hands = [list(p.hand) for p in s.players]
    asyncio.run(app.state.runtime.enter('test', 'setup-cards'))
    assert s.public_cards == cards and [p.hand for p in s.players] == hands
    with TestClient(app) as client, client.websocket_connect('/ws/sessions/test') as ws:
        event = ws.receive_json()
        assert event['type'] == 'setup.state'
        state = client.get('/api/sessions/test/setup').json()
        assert state == event['payload']
        assert len(state['faceUpCards']) == 15
        assert all(p['count'] == 3 for p in state['handsReady'])
        assert all(c.instance_id not in str(state) for p in s.players for c in p.hand)
        assert all(p.token not in str(state) for p in s.players)
        body = dict(phase=s.phase, revision=s.revision)
        first = client.post('/api/sessions/test/advance', json=body, headers=headers(s))
        assert first.status_code == 200 and first.json()['phase'] == 'betting'
        assert ws.receive_json()['type'] == 'setup.advanced'
        assert client.post('/api/sessions/test/advance', json=body, headers=headers(s)).json() == first.json()
        assert client.post('/api/sessions/test/advance', json=body, headers=headers(s, 'stale')).status_code == 409
        assert client.get('/api/sessions/test/setup').status_code == 409


def test_guard_unprepared_unknown_unauthorized_and_bad_request():
    s, app = fixture(False)
    s.phase = 'setup-cards'
    with TestClient(app) as c:
        body = dict(phase=s.phase, revision=s.revision)
        assert c.post('/api/sessions/test/advance', json=body, headers=headers(s)).status_code == 409
        assert c.post('/api/sessions/test/advance', json=body).status_code == 403
        assert c.post('/api/sessions/test/advance', json=[], headers=headers(s)).status_code == 400
        assert c.get('/api/sessions/absent/setup').status_code == 404
    assert s.revision == 0 and not s.dealt


def test_concurrent_duplicate_and_stale_inputs():
    s, app = fixture()
    with TestClient(app) as c:
        body = dict(phase=s.phase, revision=s.revision)
        with ThreadPoolExecutor(2) as pool:
            responses = list(pool.map(lambda _: c.post('/api/sessions/test/advance', json=body, headers=headers(s)), range(2)))
        assert [r.status_code for r in responses] == [200, 200]
        assert responses[0].json() == responses[1].json()
        assert s.revision == 2
        changed = dict(body, revision=2)
        assert c.post('/api/sessions/test/advance', json=changed, headers=headers(s)).status_code == 409


def test_failed_deal_rolls_back():
    s, app = fixture(False)
    s.players = s.players[:2]
    with pytest.raises(RuleError):
        asyncio.run(app.state.runtime.enter('test', 'setup-cards'))
    assert s.phase == 'lobby' and s.revision == 0 and s.public_cards == []
