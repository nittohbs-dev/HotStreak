"""Issue #22 / REQ-lobby-001〜008: 参加受付と名前確定。"""
from secrets import token_urlsafe
from .state import Player, RuleError


class LobbyService:
    phase = section = event = 'lobby'

    def enter(self, session):
        session.phase = self.phase

    def join(self, session):
        if session.phase != self.phase:
            raise RuleError('受付は終了しました')
        if len(session.players) >= 8:
            raise RuleError('参加人数が上限です')
        player = Player('p_' + token_urlsafe(9))
        session.players.append(player)
        return player

    def name(self, session, pid, value):
        session.require(self.phase)
        if not isinstance(value, str) or not value.strip():
            raise RuleError('名前を入力してください', 400)
        if len(value.strip()) > 40:
            raise RuleError('名前は40文字以内にしてください', 400)
        player = session.player(pid)
        if player.name and player.name != value.strip():
            raise RuleError('名前はすでに確定しています')
        player.name = value.strip()

    def advance(self, session):
        session.require(self.phase)
        if len(session.players) < 3:
            raise RuleError('参加者が足りません（3人以上）')
        for index, player in enumerate(session.players, 1):
            if not player.name:
                player.name = f'プレイヤー{index}'
                player.balance = 10
        session.phase = 'setup-cards'

    def snapshot(self, session, viewer=None):
        return session.public()
