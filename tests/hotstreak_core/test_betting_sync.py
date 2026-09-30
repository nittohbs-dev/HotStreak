from random import Random
import pytest
from hotstreak_core.betting import BettingService
from hotstreak_core.setup_cards import SetupCardsService
from hotstreak_core.state import GameSession, Player, RuleError


@pytest.mark.parametrize('count', range(3, 9))
def test_snake_supply_and_double(count):
    s = GameSession('game', [Player(str(i), name=f'P{i}') for i in range(count)], rng=Random(4))
    SetupCardsService().enter(s)
    service = BettingService()
    service.enter(s)
    assert len(s.prompts) == 12
    assert sum(t['remaining'] for t in service.stock(s)) == 18
    s.race_index = 3
    order = service.order(s)
    assert order == [str(i) for i in range(count)] + [str(i) for i in reversed(range(count))]
    for pid in order:
        stock = next(t for t in service.stock(s) if t['remaining'])
        service.act(s, 'picks', dict(stock, face='safe'), pid)
    with pytest.raises(RuleError):
        service.advance(s)
    assert all(len(p.tickets) == 2 for p in s.players)
    assert len({t['ticketInstanceId'] for p in s.players for t in p.tickets}) == count*2
    for p in s.players:
        service.act(s, 'double', {'ticketInstanceId': p.tickets[0]['ticketInstanceId']}, p.player_id)
    service.advance(s)
    assert s.phase == 'card-seed'


def test_out_of_turn_and_first_rotation():
    s = GameSession('g', [Player(str(i)) for i in range(3)], phase='setup-cards', draft_start=1)
    service = BettingService()
    service.enter(s)
    assert service.order(s) == ['1', '2', '0', '0', '2', '1']
    with pytest.raises(RuleError) as error:
        service.act(s, 'picks', {'ticketId': 'blue', 'ticketKind': 'mascot', 'face': 'safe'}, '0')
    assert error.value.status == 403
    with pytest.raises(RuleError):
        service.advance(s)
