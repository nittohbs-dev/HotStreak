"""同期機能間で受け渡す状態。画面・参加受付の処理は持たない。"""
from dataclasses import dataclass, field
from random import Random
from secrets import token_urlsafe


class RuleError(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


@dataclass
class Player:
    player_id: str
    name: str = ''
    token: str = field(default_factory=lambda: token_urlsafe(32))
    balance: int = 10
    hand: list = field(default_factory=list)
    tickets: list = field(default_factory=list)
    seed: object = None

    def public(self):
        return dict(playerId=self.player_id, displayName=self.name,
                    nameReady=bool(self.name), balance=self.balance)


@dataclass
class GameSession:
    session_id: str
    players: list[Player]
    phase: str = 'lobby'
    revision: int = 0
    display_token: str = field(default_factory=lambda: token_urlsafe(32))
    rng: Random = field(default_factory=Random)
    race_index: int = 1
    dealt: bool = False
    public_cards: list = field(default_factory=list)
    unused: list = field(default_factory=list)
    engine: object = None
    prompt_index: int = 0
    prompts: list = field(default_factory=list)
    breakdowns: dict = field(default_factory=dict)
    settled: set = field(default_factory=set)
    draft_start: int = 0
    transition_state: dict = field(default_factory=dict)

    def require(self, phase):
        if self.phase != phase:
            raise RuleError('このフェーズでは操作できません')

    def player(self, pid):
        p = next((p for p in self.players if p.player_id == pid), None)
        if p is None:
            raise RuleError('参加者が見つかりません', 404)
        return p

    def public(self):
        return dict(self.transition_state, sessionId=self.session_id, phase=self.phase, revision=self.revision,
                    raceIndex=self.race_index, playerCount=len(self.players),
                    players=[p.public() for p in self.players])
