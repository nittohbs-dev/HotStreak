"""セッションの状態遷移。呼出側はセッション単位で排他する。"""
from dataclasses import dataclass, field
from random import Random
from secrets import token_urlsafe
from .cards import CardSupply, COLORS, NAMES, catalog
from .race import RaceEngine
from .payout import calculate, TIERS


class RuleError(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


@dataclass
class Player:
    player_id: str
    token: str
    name: str = ''
    balance: int = 10
    hand: list = field(default_factory=list)
    tickets: list = field(default_factory=list)
    seed: object = None
    is_computer: bool = False

    def public(self):
        return dict(playerId=self.player_id, displayName=self.name,
                    nameReady=bool(self.name), balance=self.balance, isComputer=self.is_computer)


class GameSession:
    def __init__(self, session_id=None, rng=None):
        self.session_id = session_id or token_urlsafe(9)
        self.display_token = token_urlsafe(32)
        self.rng = rng or Random()
        self.phase = 'lobby'
        self.revision = 0
        self.race_index = 1
        self.players = []
        self.public_cards = []
        self.unused = []
        self.dealt = False
        self.engine = None
        self.turn = 0
        self.stock = {}
        self.order = []
        self.breakdowns = {}
        self.settled = set()
        self.prompts = [c for c in catalog() if c['kind'] == 'event']
        self.rng.shuffle(self.prompts)
        self.prompt_index = 0

    def require(self, phase):
        if self.phase != phase:
            raise RuleError('このフェーズでは操作できません')

    def player(self, pid):
        p = next((p for p in self.players if p.player_id == pid), None)
        if p is None:
            raise RuleError('参加者が見つかりません', 404)
        return p

    def join(self):
        self.require('lobby')
        if len(self.players) >= 8:
            raise RuleError('定員に達しました')
        p = Player(token_urlsafe(9), token_urlsafe(32))
        self.players.append(p)
        return p

    def name(self, pid, name):
        self.require('lobby')
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 40:
            raise RuleError('名前を1〜40文字で入力してください', 400)
        self.player(pid).name = name.strip()

    def setup(self):
        self.require('lobby')
        if not 1 <= len(self.players) <= 8:
            raise RuleError('1人以上の参加が必要です')
        while len(self.players) < 3:
            number = 1 + sum(p.is_computer for p in self.players)
            self.players.append(Player(token_urlsafe(9), token_urlsafe(32),
                                       name=f'コンピュータ{number}', is_computer=True))
        public, hands, unused = CardSupply(self.rng).deal([p.player_id for p in self.players])
        for i, p in enumerate(self.players):
            p.name = p.name or f'プレイヤー{i+1}'
            p.hand = hands[p.player_id]
        self.public_cards, self.unused = public, unused
        self.dealt, self.phase = True, 'setup-cards'

    def start_betting(self):
        self.phase = 'betting'
        self.stock = {key: 0 for key in (*COLORS, 'yes', 'no')}
        offset = (self.race_index-1) % len(self.players)
        ids = [p.player_id for p in self.players]
        clockwise = ids[offset:]+ids[:offset]
        self.order = clockwise + list(reversed(clockwise))
        self.turn = 0
        for p in self.players:
            p.tickets = []
            p.seed = None
        self.play_computers()

    def pick(self, pid, body):
        self._pick(pid, body)
        self.play_computers()

    def _pick(self, pid, body):
        self.require('betting')
        if self.turn >= len(self.order) or self.order[self.turn] != pid:
            raise RuleError('あなたの番ではありません', 403)
        key, face = body.get('ticketId'), body.get('face')
        if not isinstance(key, str) or key not in self.stock or face not in ('safe', 'risky'):
            raise RuleError('札と表裏を選んでください', 400)
        kind = 'mascot' if key in COLORS else 'side'
        if body.get('ticketKind') != kind:
            raise RuleError('札の種類が一致しません', 400)
        tier = self.stock[key]
        if tier >= 3:
            raise RuleError('この札は残っていません')
        self.player(pid).tickets.append(dict(ticketInstanceId=f'{self.race_index}:{key}:{tier}',
            ticketId=key, ticketKind=kind, tier=TIERS[tier], face=face,
            label=NAMES.get(key, key.upper()), double=False))
        self.stock[key] += 1
        self.turn += 1

    def play_computers(self):
        """公開情報だけで選択。人間の番で止まり、フェーズは自動で進めない。"""
        if self.phase == 'betting':
            while self.turn < len(self.order):
                player = self.player(self.order[self.turn])
                if not player.is_computer:
                    break
                key = self.rng.choice([key for key, used in self.stock.items() if used < 3])
                self._pick(player.player_id, dict(ticketId=key,
                    ticketKind='mascot' if key in COLORS else 'side',
                    face=self.rng.choice(('safe', 'risky'))))
            if self.race_index == 3:
                for player in self.players:
                    if player.is_computer and len(player.tickets) == 2 and not any(t['double'] for t in player.tickets):
                        self.double(player.player_id, self.rng.choice(player.tickets)['ticketInstanceId'])
        elif self.phase == 'card-seed':
            for player in self.players:
                if player.is_computer and player.seed is None:
                    self.seed(player.player_id, self.rng.choice(player.hand).instance_id)

    def double(self, pid, ticket_id):
        self.require('betting')
        tickets = self.player(pid).tickets
        if self.race_index != 3 or len(tickets) != 2:
            raise RuleError('第3レースの札を2枚取得してから選択してください')
        if not any(t['ticketInstanceId'] == ticket_id for t in tickets):
            raise RuleError('所持していない札です', 400)
        for t in tickets:
            t['double'] = t['ticketInstanceId'] == ticket_id

    def seed(self, pid, instance_id):
        self.require('card-seed')
        p = self.player(pid)
        if p.seed is not None:
            raise RuleError('仕込みは確定済みです')
        card = next((c for c in p.hand if c.instance_id == instance_id), None)
        if card is None:
            raise RuleError('手札にないカードです', 400)
        p.seed = card
        p.hand.remove(card)

    def settle(self):
        if not self.engine or not self.engine.finished:
            raise RuleError('レースが終了していません')
        if self.race_index in self.settled:
            return
        ranks = {m.color: m.rank for m in self.engine.mascots}
        outcome = self.engine.outcome(self.prompts[self.prompt_index]['effect'])
        # 全員分を計算してから反映し、途中失敗で部分精算しない。
        computed = {p.player_id: calculate(p.balance, p.tickets, ranks, outcome, self.race_index)
                    for p in self.players}
        for p in self.players:
            p.balance = computed[p.player_id]['balance']
        self.breakdowns = computed
        self.settled.add(self.race_index)
        self.phase = 'payout'

    def advance(self):
        if self.phase == 'lobby':
            self.setup()
        elif self.phase == 'setup-cards':
            if not self.dealt:
                raise RuleError('カード準備中です')
            self.start_betting()
        elif self.phase == 'betting':
            if self.turn != len(self.order):
                raise RuleError('全員の札選びを待っています')
            if self.race_index == 3 and any(sum(t['double'] for t in p.tickets) != 1 for p in self.players):
                raise RuleError('全員のダブル選択を待っています')
            self.phase = 'card-seed'
            self.play_computers()
        elif self.phase == 'card-seed':
            if any(p.seed is None for p in self.players):
                raise RuleError('全員の仕込みを待っています')
            deck = self.public_cards + [p.seed for p in self.players]
            self.engine = RaceEngine(deck, self.rng)
            self.phase = 'race'
        elif self.phase == 'race':
            self.engine.reveal()
            if self.engine.finished:
                self.settle()
        elif self.phase == 'payout':
            if self.race_index == 3:
                self.phase = 'champion'
            else:
                deck = list(self.engine.cards)
                self.rng.shuffle(deck)
                for p in self.players:
                    p.hand.append(deck.pop())
                self.public_cards = deck
                self.race_index += 1
                self.prompt_index += 1
                self.engine = None
                self.start_betting()
        elif self.phase == 'champion':
            self.phase = 'lobby'
            self.players = []
            self.public_cards = []
            self.dealt = False
            self.engine = None
            self.race_index = 1
            self.settled = set()
            self.breakdowns = {}
            self.rng.shuffle(self.prompts)
            self.prompt_index = 0

    @property
    def host_player_id(self):
        return next((p.player_id for p in self.players if not p.is_computer), None)

    def advance_reason(self):
        if self.phase == 'lobby' and not self.players:
            return '参加者を待っています'
        if self.phase == 'setup-cards' and not self.dealt:
            return 'カード準備中です'
        if self.phase == 'betting':
            if self.turn != len(self.order):
                return '全員の札選びを待っています'
            if self.race_index == 3 and any(sum(t['double'] for t in p.tickets) != 1 for p in self.players):
                return '全員のダブル選択を待っています'
        if self.phase == 'card-seed' and any(p.seed is None for p in self.players):
            return '全員の仕込みを待っています'
        if self.phase == 'race':
            return 'レースは会場のEnterで進行します'
        return ''

    def snapshot(self, pid=None):
        state = dict(sessionId=self.session_id, phase=self.phase, revision=self.revision,
                     raceIndex=self.race_index, playerCount=len(self.players),
                     players=[p.public() for p in self.players])
        labels = {'lobby': '公開カードへ', 'setup-cards': 'マ券選びへ',
                  'betting': 'カード仕込みへ', 'card-seed': 'レースへ',
                  'payout': '総合優勝へ' if self.race_index == 3 else '次のレースへ',
                  'champion': '参加受付へ'}
        reason = self.advance_reason()
        state.update(hostPlayerId=self.host_player_id,
                     canAdvance=bool(pid and pid == self.host_player_id and not reason),
                     advanceLabel=labels.get(self.phase, ''), advanceReason=reason)
        if pid:
            state['viewerPlayerId'] = self.player(pid).player_id
        if self.phase == 'setup-cards':
            state.update(dealt=self.dealt, faceUpCards=[c.public() for c in self.public_cards],
                         handsReady=[dict(playerId=p.player_id, count=len(p.hand)) for p in self.players])
        if self.phase in ('betting', 'card-seed', 'race', 'payout', 'champion'):
            prompt = self.prompts[self.prompt_index]
            state['prompt'] = dict(cardId=prompt['id'], text=prompt['label'])
        if self.phase in ('betting', 'card-seed'):
            # 場に公開済みのカードだけを共有する。各プレイヤーの手札・仕込み札は含めない。
            state['faceUpCards'] = [c.public() for c in self.public_cards]
        if self.phase == 'betting':
            state.update(stock=[dict(ticketId=k, ticketKind='mascot' if k in COLORS else 'side',
                label=NAMES.get(k, k.upper()), tier=TIERS[min(v, 2)], remaining=3-v) for k, v in self.stock.items()],
                currentPlayerId=self.order[self.turn] if self.turn < len(self.order) else None,
                round=min(2, self.turn//len(self.players)+1), turnIndex=self.turn, turnTotal=len(self.order),
                picksByPlayer={p.player_id: p.tickets for p in self.players},
                doubleByPlayer={p.player_id: next((t['ticketInstanceId'] for t in p.tickets if t['double']), None)
                                for p in self.players})
        if self.phase == 'card-seed':
            state.update(progress=[dict(playerId=p.player_id, displayName=p.name, seeded=p.seed is not None)
                                   for p in self.players], deckCountExpected=18)
            if pid:
                p = self.player(pid)
                # 既存Phoneの cardId は選択用識別子。描画はrectを使う。
                state['hand'] = [dict(c.public(), cardId=c.instance_id, catalogId=c.card_id) for c in p.hand]
                state['seededCard'] = dict(p.seed.public(), cardId=p.seed.instance_id) if p.seed else None
        if self.phase in ('race', 'payout', 'champion'):
            for entry, p in zip(state['players'], self.players):
                entry.update(rank=1+sum(o.balance > p.balance for o in self.players), bets=p.tickets)
            state.update(self.engine.public())
            live = sorted((m for m in self.engine.mascots if m.rank is None), key=lambda m: -m.position)
            for m in state['mascots']:
                if m['rank'] is None:
                    m['rank'] = 1+sum(o.status == 'goal' for o in self.engine.mascots)+sum(o.position > m['position'] for o in live)
            state['myBets'] = self.player(pid).tickets if pid else []
        if self.phase in ('payout', 'champion'):
            state.update(standings=sorted([m.public() for m in self.engine.mascots], key=lambda m: m['rank']),
                sideBetOutcome=self.engine.outcome(self.prompts[self.prompt_index]['effect']),
                balances=[dict(p.public(), rank=1+sum(o.balance > p.balance for o in self.players),
                               delta=self.breakdowns[p.player_id]['delta']) for p in self.players],
                myBreakdown=dict(self.breakdowns[pid], playerId=pid) if pid else None,
                winners=[p.player_id for p in self.players if p.balance == max(o.balance for o in self.players)]
                        if self.race_index == 3 else [])
        return state
