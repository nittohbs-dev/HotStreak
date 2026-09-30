"""REQ-race-001〜007: 仕込み完了から確定結果までを同期する。"""
from .race import RaceEngine
from .state import RuleError


class RaceService:
    phase = 'race'
    section = 'race'
    event = 'race'

    def enter(self, session):
        if session.phase == self.phase and session.engine is not None:
            return
        session.require('card-seed')
        if not session.players or any(p.seed is None for p in session.players):
            raise RuleError('全員の仕込みを待っています')
        if not 0 <= session.prompt_index < len(session.prompts):
            raise RuleError('サイドベットのお題がありません')
        try:
            engine = RaceEngine(session.public_cards + [p.seed for p in session.players], session.rng)
        except ValueError as exc:
            raise RuleError(str(exc)) from exc
        session.engine = engine
        session.transition_state = {}
        session.phase = self.phase

    def advance(self, session):
        session.require(self.phase)
        if session.engine is None or session.engine.finished:
            raise RuleError('進行できるレースがありません')
        session.engine.reveal()
        if session.engine.finished:
            session.transition_state = dict(
                standings=sorted([m.public() for m in session.engine.mascots], key=lambda m: m['rank']),
                sideBetOutcome=session.engine.outcome(session.prompts[session.prompt_index]['effect']))
            session.phase = 'payout'

    def snapshot(self, session, viewer=None):
        session.require(self.phase)
        state = dict(session.public(), **session.engine.public())
        for entry, player in zip(state['players'], session.players):
            entry.update(rank=1+sum(p.balance > player.balance for p in session.players), bets=player.tickets)
        live = [m for m in session.engine.mascots if m.rank is None]
        for mascot in state['mascots']:
            if mascot['rank'] is None:
                mascot['rank'] = (1 + sum(m.status == 'goal' for m in session.engine.mascots)
                                  + sum(m.position > mascot['position'] for m in live))
        prompt = session.prompts[session.prompt_index]
        state['prompt'] = dict(cardId=prompt['id'], text=prompt['label'])
        state['myBets'] = session.player(viewer).tickets if viewer else []
        return state
