"""札1枚ごとの金額化。順位決定・通信・画面には依存しない。"""
MASCOT = {
    'safe': ((10, 7, 5, 0), (7, 5, 3, 0), (5, 3, 2, 0)),
    'risky': ((15, 5, 2, 0), (11, 3, 1, 0), (8, 2, 0, 0)),
}
SIDE = {'safe': (10, 7, 5), 'risky': (15, 12, 10)}
TIERS = ('top', 'mid', 'bot')


def ticket_amount(ticket, ranks, side_outcome, race_index):
    tier = TIERS.index(ticket['tier'])
    face = ticket['face']
    if ticket['ticketKind'] == 'mascot':
        amount = MASCOT[face][tier][ranks[ticket['ticketId']]-1]
    else:
        correct = (ticket['ticketId'] == 'yes') == side_outcome
        amount = SIDE[face][tier] if correct else (-5 if face == 'risky' else 0)
    return amount * (2 if race_index == 3 and ticket.get('double') else 1)


def calculate(balance, tickets, ranks, side_outcome, race_index):
    if race_index == 3 and sum(bool(t.get('double')) for t in tickets) != 1:
        raise ValueError('第3レースはダブル札を1枚選択してください')
    items = [dict(ticketInstanceId=t['ticketInstanceId'], label=t['label'],
                  kind=t['ticketKind'], face=t['face'], tier=t['tier'],
                  double=bool(t.get('double')), amount=ticket_amount(t, ranks, side_outcome, race_index))
             for t in tickets]
    total = sum(t['amount'] for t in items)
    after = max(0, balance+total)
    return dict(items=items, total=total, balance=after, delta=after-balance)
