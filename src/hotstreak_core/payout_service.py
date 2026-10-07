"""REQ-payout-001〜006: 確定結果の一度だけの精算とレース間リセット。"""
from .payout import calculate
from .state import RuleError


class PayoutService:
    phase = 'payout'
    section = 'payout'
    event = 'payout'

    def enter(self, session):
        if session.phase not in ('race', self.phase):
            raise RuleError('配当を開始できるフェーズではありません')
        if not session.engine or not session.engine.finished:
            raise RuleError('レースが終了していません')
        if session.race_index in session.settled:
            return
        if not 0 <= session.prompt_index < len(session.prompts):
            raise RuleError('サイドベットのお題がありません')
        ranks = {m.color: m.rank for m in session.engine.mascots}
        outcome = session.engine.outcome(session.prompts[session.prompt_index]['effect'])
        try:
            computed = {p.player_id: calculate(p.balance, p.tickets, ranks, outcome, session.race_index)
                        for p in session.players}
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise RuleError('精算する札または着順が不正です') from exc
        # 全員分の検証を済ませてから反映する。
        for p in session.players:
            p.balance = computed[p.player_id]['balance']
        session.breakdowns = computed
        session.settled.add(session.race_index)
        session.phase = self.phase

    def advance(self, session):
        session.require(self.phase)
        if session.race_index not in session.settled:
            raise RuleError('精算が完了していません')
        if session.race_index == 3:
            session.players = []
            session.public_cards = []
            session.unused = []
            session.dealt = False
            session.engine = None
            session.race_index = 1
            session.settled = set()
            session.breakdowns = {}
            session.rng.shuffle(session.prompts)
            session.prompt_index = 0
            session.draft_first = session.draft_start = 0
            session.phase = 'lobby'
        else:
            if session.prompt_index + 1 >= len(session.prompts):
                raise RuleError('次のサイドベットのお題がありません')
            deck = list(session.engine.cards)
            if len(deck) != 18 or any(len(p.hand) != 2 for p in session.players):
                raise RuleError('補充前の山または手札の枚数が不正です')
            session.rng.shuffle(deck)
            for p in session.players:
                p.hand.append(deck.pop())
                p.tickets = []
                p.seed = None
            session.public_cards = deck
            session.race_index += 1
            session.prompt_index += 1
            session.engine = None
            session.breakdowns = {}
            session.draft_start = (session.draft_first+session.race_index-1) % len(session.players)
            session.phase = 'betting'
        session.transition_state = {}

    def snapshot(self, session, viewer=None):
        session.require(self.phase)
        if session.race_index not in session.settled:
            raise RuleError('精算が完了していません')
        if viewer:
            session.player(viewer)
        prompt = session.prompts[session.prompt_index]
        return dict(session.public(), **dict(
            standings=sorted([m.public() for m in session.engine.mascots], key=lambda m: m['rank']),
            sideBetOutcome=session.engine.outcome(prompt['effect']),
            prompt=dict(cardId=prompt['id'], text=prompt['label']),
            balances=[dict(p.public(), rank=1+sum(o.balance > p.balance for o in session.players),
                           delta=session.breakdowns[p.player_id]['delta']) for p in session.players],
            myBreakdown=dict(session.breakdowns[viewer], playerId=viewer) if viewer else None,
            winners=[p.player_id for p in session.players if p.balance == max(o.balance for o in session.players)]
                    if session.race_index == 3 else []))
