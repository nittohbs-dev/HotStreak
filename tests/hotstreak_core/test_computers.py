from random import Random
import pytest
from hotstreak_core.session import GameSession, RuleError


@pytest.mark.parametrize('humans', [1, 2, 3, 8])
def test_computers_complete_three_races_without_human_input(humans):
    s = GameSession(rng=Random(13))
    for _ in range(humans):
        s.join()
    s.advance()
    assert len(s.players) == max(3, humans)
    assert sum(p.is_computer for p in s.players) == max(0, 3-humans)
    assert all(len(p.hand) == 3 for p in s.players)
    s.advance()
    for race in range(1, 4):
        assert s.phase == 'betting'
        while s.turn < len(s.order):
            p = s.player(s.order[s.turn])
            assert not p.is_computer
            key = next(k for k, count in s.stock.items() if count < 3)
            s.pick(p.player_id, dict(ticketId=key, ticketKind='side' if key in ('yes','no') else 'mascot', face='safe'))
        assert all(len(p.tickets) == 2 for p in s.players)
        if race == 3:
            for p in s.players:
                if p.is_computer:
                    assert sum(t['double'] for t in p.tickets) == 1
                else:
                    s.double(p.player_id, p.tickets[0]['ticketInstanceId'])
        s.advance()
        for p in s.players:
            if p.is_computer:
                assert p.seed is not None and len(p.hand) == 2
            else:
                s.seed(p.player_id, p.hand[0].instance_id)
        s.advance()
        assert len(s.engine.cards) == 18
        for _ in range(60):
            s.advance()
            if s.phase == 'payout':
                break
        assert s.phase == 'payout'
        s.advance()
    assert s.phase == 'lobby' and not s.players


def test_empty_room_cannot_start_or_add_computers():
    s = GameSession()
    with pytest.raises(RuleError):
        s.advance()
    assert not s.players and s.phase == 'lobby'
