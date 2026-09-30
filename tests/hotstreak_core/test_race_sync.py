import asyncio
from random import Random
from fastapi.testclient import TestClient
from hotstreak_core.cards import catalog
from hotstreak_core.state import GameSession, Player
from hotstreak_core.setup_cards import SetupCardsService
from hotstreak_core.race_service import RaceService
from hotstreak_sync.runtime import create_app


def fixture():
    s = GameSession('race', [Player(str(i)) for i in range(3)], rng=Random(2))
    s.prompts = [c for c in catalog() if c['kind'] == 'event']
    SetupCardsService().enter(s)
    s.phase = 'card-seed'
    for p in s.players:
        p.seed = p.hand.pop()
        p.tickets = [dict(ticketId='blue', ticketInstanceId=p.player_id)]
    app = create_app([RaceService()])
    app.state.runtime.add_session(s)
    asyncio.run(app.state.runtime.enter(s.session_id, 'race'))
    return s, app


def test_burn_retry_auth_and_finished_event():
    s, app = fixture()
    assert len(s.engine.burned) == 3 and len(s.engine.deck) == 15
    burned = list(s.engine.burned)
    asyncio.run(app.state.runtime.enter(s.session_id, 'race'))
    assert s.engine.burned == burned
    with TestClient(app) as c, c.websocket_connect('/ws/sessions/race') as ws:
        assert ws.receive_json()['type'] == 'race.state'
        assert c.get('/api/sessions/race/race?playerId=0').json()['myBets'] == []
        c.cookies.set('hs_race', s.players[0].token)
        assert c.get('/api/sessions/race/race').json()['myBets'] == s.players[0].tickets
        for turn in range(60):
            body = dict(phase=s.phase, revision=s.revision)
            hdr = {'X-Display-Token': s.display_token, 'Idempotency-Key': str(turn)}
            r = c.post('/api/sessions/race/advance', json=body, headers=hdr)
            assert r.status_code == 200, r.text
            assert c.post('/api/sessions/race/advance', json=body, headers=hdr).json() == r.json()
            event = ws.receive_json()
            if s.phase == 'payout':
                assert event['type'] == 'race.finished'
                assert len(event['payload']['standings']) == 4
                assert type(event['payload']['sideBetOutcome']) is bool
                break
            assert event['type'] == 'race.state'
            assert s.engine.revealed == turn+1
        else:
            raise AssertionError('レースが終了しない')
        assert c.get('/api/sessions/race/race').status_code == 409
        assert s.players[0].balance == 10  # 金額化は配当サービスが担当。
