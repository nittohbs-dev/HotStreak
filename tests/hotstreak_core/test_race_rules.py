from random import Random
from hotstreak_core.cards import CardSupply
from hotstreak_core.race import RaceEngine
CARDS = {c.card_id: c for c in CardSupply(Random(1)).cards}


def engine():
    e = RaceEngine(list(CARDS.values())[:18], Random(1))
    for lane, mascot in enumerate(e.mascots):
        mascot.lane = lane
    return e

def play(e, key):
    e.resolve(CARDS[key])

def test_collision_knockout_and_rank_from_bottom():
    e = engine()
    e.mascots[1].lane = 0
    e.mascots[1].position = 4
    play(e, 'blue_move_3')
    assert e.mascots[1].fallen
    assert 'same_space' not in e.facts  # 通過しただけでは同じマスに停止していない。
    e.mascots[0].position = 2
    play(e, 'blue_move_3')
    assert e.mascots[1].status == 'dq'
    assert e.mascots[1].rank == 4
    play(e, 'yellow_fall')
    play(e, 'yellow_fall')
    assert e.mascots[2].rank == 3

def test_star_fallen_reverse_recover_and_swerve():
    e = engine()
    play(e, 'blue_star')
    assert e.mascots[0].position == 7
    play(e, 'blue_turn')
    play(e, 'blue_star')
    assert e.mascots[0].position == 2
    play(e, 'blue_recover_2')
    assert e.mascots[0].position == 4 and e.mascots[0].facing == 1
    play(e, 'blue_fall')
    play(e, 'blue_star')
    assert e.mascots[0].position == 5
    play(e, 'blue_swerve_3')
    assert e.mascots[0].position == 6
    assert e.mascots[0].rank == 4


def test_goal_precedes_swerve_offside():
    e = engine()
    e.mascots[0].position = 12
    play(e, 'blue_swerve_1')
    assert e.mascots[0].status == 'goal' and e.mascots[0].rank == 1

def test_green_cannot_finish_or_collide():
    e = engine()
    for m in e.mascots:
        m.position = 11
        m.lane = 1
    e.mascots[1].fallen = True
    play(e, 'green_move_3')
    assert all(m.position == 12 and m.status == 'racing' for m in e.mascots)
    assert sum(m.fallen for m in e.mascots) == 1
    assert 'finish_two' in e.facts
    play(e, 'green_recover_2')
    assert not any(m.fallen for m in e.mascots)

def test_simultaneous_dq_ties_and_remaining_rank():
    e = engine()
    e.mascots[3].position = 5
    e.shorten()
    assert [m.rank for m in e.mascots] == [4, 4, 4, 1]
    assert e.finished
    assert e.outcome('out_of_bounds')

def test_sequential_collisions_are_not_simultaneous_dq():
    e = engine()
    for m, pos in zip(e.mascots[1:3], (3, 4)):
        m.position, m.lane, m.fallen = pos, 0, True
    play(e, 'blue_move_3')
    assert [e.mascots[i].rank for i in (1, 2)] == [4, 3]
    e = engine()
    for m in e.mascots[1:3]:
        m.position, m.lane, m.fallen = 3, 0, True
    play(e, 'blue_move_3')
    assert [e.mascots[i].rank for i in (1, 2)] == [4, 4]

def test_empty_final_only_at_first_finish():
    e = engine()
    play(e, 'blue_move_2')
    assert 'empty_final' not in e.facts
    e.mascots[0].position = 12
    e.mascots[1].position = 11
    play(e, 'blue_move_2')
    assert 'empty_final' not in e.facts
    other = engine()
    other.mascots[0].position = 12
    play(other, 'blue_move_2')
    assert 'empty_final' in other.facts

def test_all_catalog_effects_resolve():
    for card in CARDS.values():
        e = engine()
        e.resolve(card)
        assert all(m.facing in (-1, 1) for m in e.mascots)

def test_side_bet_final_positions_and_crawling():
    e = engine()
    e.mascots[0].position = 9
    e.mascots[0].fallen = True
    play(e, 'blue_star')
    assert 'crawl_final' in e.facts
    e.mascots[1].position = 10
    e.mascots[1].lane = 0
    play(e, 'orange_move_minus_2')
    assert 'same_space' not in e.facts
    e.mascots[1].position = 10
    play(e, 'orange_turn')
    assert 'same_space' in e.facts
    play(e, 'orange_fall')
    assert 'fallen_two' in e.facts
    e.mascots[0].position = 12
    e.mascots[0].status = 'goal'
    e.mascots[1].status = 'goal'
    e.mascots[2].status = 'dq'
    e.assign_ranks()
    assert e.outcome('dangle_bottom') is False
    assert e.outcome('gobbler_bottom') is False
    assert e.outcome('mum_bottom') is True
    assert e.outcome('hurley_bottom') is True
