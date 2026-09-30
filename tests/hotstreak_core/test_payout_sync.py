import asyncio
from random import Random
import pytest
from fastapi.testclient import TestClient
from hotstreak_core.cards import catalog
from hotstreak_core.state import GameSession, Player, RuleError
from hotstreak_core.setup_cards import SetupCardsService
from hotstreak_core.race_service import RaceService
from hotstreak_core.payout_service import PayoutService
from hotstreak_sync.runtime import create_app


def seed(s):
    # betting/card-seed は別Issue。サービス間の受渡し状態を用意する。
    s.phase = 'card-seed'
    for p in s.players:
        p.seed = p.hand.pop()
        p.tickets = [dict(ticketInstanceId=p.player_id+str(i), ticketId=key,
                          ticketKind='side', tier='top', face='safe', label=key,
                          double=s.race_index == 3 and i == 0) for i, key in enumerate(('yes', 'no'))]


def fixture(n=3, random_seed=0):
    s = GameSession('game', [Player(str(i)) for i in range(n)], rng=Random(random_seed))
    s.prompts = [c for c in catalog() if c['kind'] == 'event']
    app = create_app([SetupCardsService(), RaceService(), PayoutService()])
    app.state.runtime.add_session(s)
    asyncio.run(app.state.runtime.enter('game', 'setup-cards'))
    return s, app


@pytest.mark.parametrize('n', range(3, 9))
def test_three_races_card_conservation_once_only_and_co_winners(n):
    for random_seed in range(10):
        s, app = fixture(n, random_seed)
        SetupCardsService().advance(s)
        for race in range(1, 4):
            assert all(len(p.hand) == 3 for p in s.players)
            seed(s)
            RaceService().enter(s)
            all_cards = s.engine.cards + sum((p.hand for p in s.players), []) + s.unused
            assert len(all_cards) == len({c.instance_id for c in all_cards}) == 53
            for _ in range(60):
                RaceService().advance(s)
                if s.phase == 'payout':
                    break
            assert s.phase == 'payout'
            PayoutService().enter(s)
            balances = [p.balance for p in s.players]
            PayoutService().enter(s)
            assert [p.balance for p in s.players] == balances
            if race == 3:
                assert PayoutService().snapshot(s)['winners'] == [p.player_id for p in s.players]
            PayoutService().advance(s)
            if race < 3:
                assert s.phase == 'betting' and s.draft_start == race % n
                assert not any(p.tickets or p.seed for p in s.players)
                assert s.engine is None and s.prompt_index == race
        assert s.phase == 'lobby' and s.players == [] and s.race_index == 1


def test_api_ws_settlement_is_atomic_and_private():
    s, app = fixture()
    seed(s)
    RaceService().enter(s)
    # 次のカードで第3体がゴールする盤面。
    e = s.engine
    for i, m in enumerate(e.mascots[:2]):
        m.status, m.rank = 'goal', i+1
        e.slots[i] = m.color
    e.mascots[2].position = 11
    from hotstreak_core.cards import CardSupply
    e.deck = [next(c for c in CardSupply(Random(1)).cards if c.card_id == 'yellow_move_2')]
    with TestClient(app) as c:
        c.cookies.set('hs_game', s.players[0].token)
        with c.websocket_connect('/ws/sessions/game') as ws:
            ws.receive_json()
            body = dict(phase=s.phase, revision=s.revision)
            hdr = {'X-Display-Token': s.display_token, 'Idempotency-Key': 'finish'}
            r = c.post('/api/sessions/game/advance', json=body, headers=hdr)
            assert r.status_code == 200, r.text
            assert ws.receive_json()['type'] == 'race.finished'
            event = ws.receive_json()
            assert event['type'] == 'payout.state'
            assert event['payload']['myBreakdown']['playerId'] == '0'
            balances = [p.balance for p in s.players]
            assert c.post('/api/sessions/game/advance', json=body, headers=hdr).json() == r.json()
            assert [p.balance for p in s.players] == balances
            personal = c.get('/api/sessions/game/payout?playerId=1').json()
            assert personal['myBreakdown']['playerId'] == '0'
            c.cookies.clear()
            assert c.get('/api/sessions/game/payout?playerId=0').json()['myBreakdown'] is None


def test_failed_settlement_does_not_partially_pay():
    s, app = fixture()
    seed(s)
    RaceService().enter(s)
    s.engine.shorten()
    s.phase = 'payout'
    s.players[-1].tickets[0]['tier'] = 'invalid'
    with pytest.raises(RuleError):
        PayoutService().enter(s)
    assert [p.balance for p in s.players] == [10, 10, 10]
    assert not s.settled


def test_failed_settlement_rolls_back_reveal_and_can_retry():
    s, app = fixture()
    seed(s)
    RaceService().enter(s)
    from hotstreak_core.cards import CardSupply
    # 3体が開始位置に残っているため、最後の1枚の後の短縮で終了する。
    s.engine.deck = [next(c for c in CardSupply(Random(1)).cards if c.card_id == 'blue_move_3')]
    s.players[-1].tickets[0]['tier'] = 'invalid'
    with TestClient(app) as c:
        body = dict(phase=s.phase, revision=s.revision)
        hdr = {'X-Display-Token': s.display_token, 'Idempotency-Key': 'retry'}
        failed = c.post('/api/sessions/game/advance', json=body, headers=hdr)
        assert failed.status_code == 409
        assert s.phase == 'race' and s.revision == body['revision']
        assert s.engine.revealed == 0 and s.engine.removed == 0 and len(s.engine.deck) == 1
        assert not s.settled and [p.balance for p in s.players] == [10]*3
        s.players[-1].tickets[0]['tier'] = 'top'
        result = c.post('/api/sessions/game/advance', json=body, headers=hdr)
        assert result.status_code == 200 and s.phase == 'payout'
        assert s.engine.revealed == 1 and s.settled == {1}
