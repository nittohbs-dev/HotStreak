"""Issue #30 / REQ-betting-001〜009: スネークドラフトと1枚ダブル。"""
from .cards import COLORS, NAMES, catalog
from .state import RuleError

TIERS = ('top', 'mid', 'bot')
LABELS = dict(NAMES, yes='サイド YES', no='サイド NO')


class BettingService:
    phase = section = event = 'betting'

    def enter(self, session):
        if session.phase not in ('setup-cards', 'payout'):
            raise RuleError('マ券選択を開始できません')
        if not session.prompts:
            session.prompts = [c for c in catalog() if c['kind'] == 'event']
            session.rng.shuffle(session.prompts)
            session.prompt_index = 0
        for player in session.players:
            player.tickets = []
        session.phase = self.phase

    def order(self, session):
        ids = [p.player_id for p in session.players]
        start = session.draft_start % len(ids)
        forward = ids[start:] + ids[:start]
        return forward + list(reversed(forward))

    def stock(self, session):
        used = [t['ticketId'] for p in session.players for t in p.tickets]
        return [dict(ticketId=key, ticketKind='mascot' if key in COLORS else 'side',
                     label=LABELS[key], remaining=3-used.count(key), tier=TIERS[min(used.count(key), 2)])
                for key in (*COLORS, 'yes', 'no')]

    def ready(self, session):
        return all(len(p.tickets) == 2 and (session.race_index != 3 or sum(bool(t.get('double')) for t in p.tickets) == 1)
                   for p in session.players)

    def act(self, session, action, body, pid):
        session.require(self.phase)
        player = session.player(pid)
        if action == 'picks':
            taken = sum(len(p.tickets) for p in session.players)
            order = self.order(session)
            if taken >= len(order) or order[taken] != pid:
                raise RuleError('あなたの番ではありません', 403)
            if body.get('face') not in ('safe', 'risky'):
                raise RuleError('セーフかリスキーを選んでください', 400)
            stock = next((t for t in self.stock(session) if t['ticketId'] == body.get('ticketId')), None)
            if stock is None or body.get('ticketKind') != stock['ticketKind']:
                raise RuleError('その札は選べません', 400)
            if not stock['remaining']:
                raise RuleError('この札は残りがありません')
            ticket = {k: v for k, v in stock.items() if k != 'remaining'}
            ticket.update(ticketInstanceId=f'r{session.race_index}-{stock["ticketId"]}-{stock["tier"]}',
                          face=body['face'], double=False)
            player.tickets.append(ticket)
        elif action == 'double':
            if session.race_index != 3 or len(player.tickets) != 2:
                raise RuleError('このレースでは使えません')
            if any(t.get('double') for t in player.tickets):
                raise RuleError('ダブルはすでに確定しています')
            ticket = next((t for t in player.tickets if t['ticketInstanceId'] == body.get('ticketInstanceId')), None)
            if ticket is None:
                raise RuleError('自分の札を指定してください', 400)
            ticket['double'] = True
        else:
            raise RuleError('操作が見つかりません', 404)

    def advance(self, session):
        session.require(self.phase)
        if not self.ready(session):
            raise RuleError('まだドラフト中です')
        session.phase = 'card-seed'

    def snapshot(self, session, viewer=None):
        taken = sum(len(p.tickets) for p in session.players)
        order = self.order(session)
        prompt = session.prompts[session.prompt_index]
        return dict(session.public(), prompt=dict(cardId=prompt['id'], text=prompt['label']),
                    stock=self.stock(session), currentPlayerId=order[taken] if taken < len(order) else None,
                    round=min(2, 1+taken//len(session.players)), turnIndex=min(len(order), taken+1),
                    turnTotal=len(order), ready=self.ready(session),
                    picksByPlayer={p.player_id: p.tickets for p in session.players},
                    doubleByPlayer={p.player_id: next((t['ticketInstanceId'] for t in p.tickets if t.get('double')), None)
                                    for p in session.players})
