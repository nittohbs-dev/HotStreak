"""Issue #34 / REQ-seed-001〜005: 本人の手札1枚を非公開で仕込む。"""
from .state import RuleError


def hand_card(card):
    # 同じ絵柄が複数枚あっても、操作対象は物理カードのIDで区別する。
    return dict(card.public(), cardId=card.instance_id, templateId=card.card_id)


class CardSeedService:
    phase = 'card-seed'
    section = event = 'seed'

    def enter(self, session):
        session.require('betting')
        if any(len(p.hand) != 3 for p in session.players):
            raise RuleError('手札の準備に失敗しました', 500)
        for player in session.players:
            player.seed = None
        session.phase = self.phase

    def act(self, session, action, body, pid):
        session.require(self.phase)
        player = session.player(pid)
        if player.seed is not None:
            raise RuleError('すでに仕込んでいます')
        card = next((c for c in player.hand if c.instance_id == body.get('handCardId')), None)
        if card is None:
            raise RuleError('そのカードは選べません', 400)
        player.hand.remove(card)
        player.seed = card
        if all(p.seed for p in session.players):
            self.validate_deck(session)

    def validate_deck(self, session):
        deck = session.public_cards + [p.seed for p in session.players]
        if len(deck) != 18 or len({c.instance_id for c in deck}) != 18:
            raise RuleError('デッキの準備に失敗しました', 500)

    def advance(self, session):
        session.require(self.phase)
        if not session.players or any(p.seed is None for p in session.players):
            raise RuleError('まだ仕込み中です')
        self.validate_deck(session)
        session.phase = 'race'

    def snapshot(self, session, viewer=None):
        state = dict(session.public(), progress=[dict(p.public(), seeded=p.seed is not None) for p in session.players],
                     deckCountExpected=len(session.public_cards)+len(session.players),
                     ready=all(p.seed is not None for p in session.players))
        if viewer:
            player = session.player(viewer)
            state.update(hand=[hand_card(c) for c in player.hand],
                         seededCard=hand_card(player.seed) if player.seed else None)
        return state
