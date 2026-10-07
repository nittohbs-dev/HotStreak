import pytest
from hotstreak_core.payout import calculate, ticket_amount


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
