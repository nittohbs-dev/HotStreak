"""REQ-setup-001〜007: ロビー完了時に一度だけ配布する。"""
from .cards import CardSupply
from .state import RuleError


class SetupCardsService:
    phase = 'setup-cards'
    section = 'setup'
    event = 'setup'

    def enter(self, session):
        if session.phase == self.phase and session.dealt:
            return  # 遷移通知の重複では再配布しない。
        session.require('lobby')
        if not 3 <= len(session.players) <= 8:
            raise RuleError('3〜8人の参加が必要です')
        try:
            public, hands, unused = CardSupply(session.rng).deal([p.player_id for p in session.players])
        except (ValueError, StopIteration) as exc:
            raise RuleError('カードの準備に失敗しました', 500) from exc
        for p in session.players:
            p.hand = hands[p.player_id]
        session.public_cards, session.unused = public, unused
        session.dealt, session.phase = True, self.phase

    def advance(self, session):
        session.require(self.phase)
        if not session.dealt:
            raise RuleError('カードの準備中です')
        session.phase = 'betting'

    def snapshot(self, session, viewer=None):
        session.require(self.phase)
        return dict(session.public(), dealt=session.dealt,
                    faceUpCards=[c.public() for c in session.public_cards],
                    handsReady=[dict(playerId=p.player_id, count=len(p.hand)) for p in session.players])
