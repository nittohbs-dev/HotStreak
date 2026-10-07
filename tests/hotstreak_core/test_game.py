from random import Random
import pytest
from hotstreak_core.cards import CardSupply
from hotstreak_core.race import RaceEngine
from hotstreak_core.session import GameSession, RuleError
from hotstreak_core.payout import calculate, ticket_amount

CARDS = {c.card_id: c for c in CardSupply(Random(1)).cards}


def engine():
    e = RaceEngine(list(CARDS.values())[:18], Random(1))
    # 効果テストの盤面は初期配置から独立させる。
    for lane, mascot in enumerate(e.mascots):
        mascot.lane = lane
    return e


def play(e, key):
    e.resolve(CARDS[key])


def test_course_has_13_numbered_spaces_including_starting_position():
    e = engine()
    course = e.public()['course']
    assert course == dict(lanes=4, columns=13, start=2,
                          stars=[2, 7, 12], removed=0)
    assert all(m.position == 2 for m in e.mascots)
    e.move(e.mascots[0], 10)
    assert e.mascots[0].position == 12 and e.mascots[0].status == 'racing'
    e.move(e.mascots[0], 1)
    assert e.mascots[0].position == 13 and e.mascots[0].status == 'goal'


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


def test_star_route_matches_numbered_track_in_both_directions():
    e = engine()
    for expected in (7, 12, 13):
        play(e, 'blue_star')
        assert e.mascots[0].position == expected
    assert e.mascots[0].status == 'goal'
    e = engine()
    e.mascots[0].position = 12
    e.mascots[0].facing = -1
    for expected in (7, 2, 2):
        play(e, 'blue_star')
        assert e.mascots[0].position == expected


def test_display_and_mock_use_the_server_course():
    from hotstreak_display.screens.race import COURSE_COLUMNS, STAR_COLUMNS
    from hotstreak_display.screens.race_effects import STAR_POSITIONS
    course = engine().public()['course']
    assert COURSE_COLUMNS == course['columns'] == 13
    assert list(STAR_COLUMNS) == course['stars'] == [2, 7, 12]
    assert STAR_POSITIONS == (2, 7, 12, 13)


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
    e.mascots[1].position = 12
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


def test_payout_table_double_negative_and_floor():
    ticket = dict(ticketInstanceId='t', ticketId='blue', ticketKind='mascot',
                  tier='top', face='safe', label='ダングル', double=False)
    assert [ticket_amount(ticket, {'blue': rank}, False, 1) for rank in range(1, 5)] == [10, 7, 5, 0]
    ticket.update(ticketId='yes', ticketKind='side', face='risky', double=True)
    result = calculate(3, [ticket], {}, False, 3)
    assert result['total'] == -10 and result['balance'] == 0 and result['delta'] == -3


@pytest.mark.parametrize('face,expected', [
    ('safe', [(10, 7, 5, 0), (7, 5, 3, 0), (5, 3, 2, 0)]),
    ('risky', [(15, 5, 2, 0), (11, 3, 1, 0), (8, 2, 0, 0)]),
])
def test_all_mascot_payout_faces(face, expected):
    for tier, amounts in zip(('top', 'mid', 'bot'), expected):
        t = dict(ticketId='blue', ticketKind='mascot', tier=tier, face=face, double=True)
        for rank, amount in enumerate(amounts, 1):
            assert ticket_amount(t, {'blue': rank}, False, 1) == amount
            assert ticket_amount(t, {'blue': rank}, False, 3) == amount*2


def test_all_side_bet_payout_faces_and_answers():
    for tier, safe, risky in zip(('top', 'mid', 'bot'), (10, 7, 5), (15, 12, 10)):
        for face, correct in (('safe', safe), ('risky', risky)):
            for answer in ('yes', 'no'):
                t = dict(ticketId=answer, ticketKind='side', tier=tier, face=face)
                assert ticket_amount(t, {}, answer == 'yes', 1) == correct
                assert ticket_amount(t, {}, answer != 'yes', 1) == (0 if face == 'safe' else -5)


def test_side_bet_final_positions_and_crawling():
    e = engine()
    e.mascots[0].position = 10
    e.mascots[0].fallen = True
    play(e, 'blue_star')
    assert 'crawl_final' in e.facts
    e.mascots[1].position = 11
    e.mascots[1].lane = 0
    play(e, 'orange_move_minus_2')
    assert 'same_space' not in e.facts
    e.mascots[1].position = 11
    play(e, 'orange_turn')
    assert 'same_space' in e.facts
    play(e, 'orange_fall')
    assert 'fallen_two' in e.facts
    e.mascots[0].position = 13
    e.mascots[0].status = 'goal'
    e.mascots[1].status = 'goal'
    e.mascots[2].status = 'dq'
    e.assign_ranks()
    assert e.outcome('dangle_bottom') is False
    assert e.outcome('gobbler_bottom') is False
    assert e.outcome('mum_bottom') is True
    assert e.outcome('hurley_bottom') is True


def prepare(s, n=3):
    for i in range(n):
        p = s.join()
        s.name(p.player_id, f'P{i}')
    s.advance()
    s.advance()


def draft_and_seed(s):
    while s.turn < len(s.order):
        pid = s.order[s.turn]
        key = next(k for k, used in s.stock.items() if used < 3)
        s.pick(pid, dict(ticketId=key, ticketKind='mascot' if key in ('blue', 'orange', 'yellow', 'salmon') else 'side', face='safe'))
    if s.race_index == 3:
        for p in s.players:
            s.double(p.player_id, p.tickets[0]['ticketInstanceId'])
    s.advance()
    for p in s.players:
        s.seed(p.player_id, p.hand[0].instance_id)
    s.advance()


@pytest.mark.parametrize('n', range(3, 9))
def test_three_complete_races_conserve_cards_and_settle_once(n):
    for seed in range(10):
        s = GameSession(rng=Random(seed))
        prepare(s, n)
        for race in range(1, 4):
            assert all(len(p.hand) == 3 for p in s.players)
            draft_and_seed(s)
            assert len(s.engine.burned) == 3 and len(s.engine.deck) == 15
            all_cards = s.engine.cards + sum((p.hand for p in s.players), []) + s.unused
            assert len(all_cards) == len({c.instance_id for c in all_cards}) == 53
            turns = 0
            while s.phase == 'race':
                s.advance()
                turns += 1
                assert turns <= 60  # 4回短縮すれば必ず終了。
            assert s.phase == 'payout'
            before = [p.balance for p in s.players]
            s.settle()
            assert [p.balance for p in s.players] == before
            assert all(m.rank is not None for m in s.engine.mascots)
            s.advance()
        assert s.phase == 'lobby' and not s.players


def test_private_hand_and_illegal_actions():
    s = GameSession()
    prepare(s)
    with pytest.raises(RuleError):
        s.advance()
    assert 'hand' not in s.snapshot()
    draft_and_seed(s)
    with pytest.raises(RuleError):
        s.seed(s.players[0].player_id, 'unknown')


def test_betting_and_seed_snapshots_only_share_public_cards():
    s = GameSession(rng=Random(7))
    prepare(s)
    public_ids = {card.instance_id for card in s.public_cards}
    private_ids = {card.instance_id for player in s.players for card in player.hand}

    betting = s.snapshot(s.players[0].player_id)
    assert {card['cardInstanceId'] for card in betting['faceUpCards']} == public_ids
    assert not private_ids & {card['cardInstanceId'] for card in betting['faceUpCards']}

    while s.turn < len(s.order):
        pid = s.order[s.turn]
        key = next(k for k, used in s.stock.items() if used < 3)
        s.pick(pid, dict(ticketId=key,
                         ticketKind='mascot' if key in ('blue', 'orange', 'yellow', 'salmon') else 'side',
                         face='safe'))
    s.advance()
    seeded = s.players[0].hand[0]
    s.seed(s.players[0].player_id, seeded.instance_id)

    display = s.snapshot()
    assert {card['cardInstanceId'] for card in display['faceUpCards']} == public_ids
    assert seeded.instance_id not in {card['cardInstanceId'] for card in display['faceUpCards']}
    assert 'hand' not in display
    assert 'seededCard' not in display


def test_initial_lane_order_and_revealed_history():
    e = RaceEngine(list(CARDS.values())[:18], Random(1))
    assert [m.color for m in sorted(e.mascots, key=lambda m: m.lane)] == ['orange', 'salmon', 'blue', 'yellow']
    revealed = [e.reveal(), e.reveal()]
    assert e.public()['revealedCards'] == [c.public() for c in revealed]
    e.shuffle()
    assert e.public()['revealedCards'] == [c.public() for c in revealed]
