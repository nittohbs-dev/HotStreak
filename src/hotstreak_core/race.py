"""カード効果・コース短縮・順位を決定する純粋なレースエンジン。"""
from dataclasses import dataclass
from random import Random
from .cards import COLORS, NAMES

COURSE_COLUMNS = 14
START_POSITION = 2
STAR_POSITIONS = (0, 5, 8, COURSE_COLUMNS)
FINAL_STRETCH_START = COURSE_COLUMNS - 3
FINAL_SPACE = COURSE_COLUMNS - 1
SHORTEN_STEP = 3


@dataclass
class Mascot:
    color: str
    lane: int
    position: int = START_POSITION
    facing: int = 1
    fallen: bool = False
    status: str = 'racing'
    rank: int | None = None

    def public(self):
        return dict(mascotId=self.color, color=self.color, displayName=NAMES[self.color],
                    lane=self.lane, position=self.position, facing=self.facing,
                    fallen=self.fallen, status=self.status, rank=self.rank,
                    disqualified=self.status == 'dq', finished=self.status != 'racing')


class RaceEngine:
    def __init__(self, cards, rng=None):
        if len(cards) != 18 or len({c.instance_id for c in cards}) != 18:
            raise ValueError('レース山は異なる個体の18枚必要です')
        self.cards = list(cards)
        self.rng = rng or Random()
        self.mascots = [Mascot(c, (2, 0, 3, 1)[i]) for i, c in enumerate(COLORS)]
        self.removed = 0
        self.current = None
        self.revealed = 0
        self.history = []
        self.slots = [None] * 4
        self.facts = set()
        self.events = []
        self.finished = False
        self.before_shortening = None
        self.shuffle()

    def shuffle(self):
        deck = list(self.cards)
        self.rng.shuffle(deck)
        self.burned, self.deck = deck[:3], deck[3:]
        self.discard = []

    def dq(self, mascot, reason):
        if mascot.status != 'racing':
            return
        mascot.status = 'dq'
        self.facts.update(('disqualified', reason))
        self.events.append(dict(kind='dq', mascotId=mascot.color, reason=reason))

    def fall(self, mascot):
        if mascot.fallen:
            self.dq(mascot, 'knockout')
        else:
            mascot.fallen = True
            self.events.append(dict(kind='fall', mascotId=mascot.color))

    def observe(self):
        active = [m for m in self.mascots if m.status == 'racing']
        if len({(m.position, m.lane) for m in active}) < len(active):
            self.facts.add('same_space')
        if sum(m.fallen for m in active) >= 2:
            self.facts.add('fallen_two')
        if sum(m.position == FINAL_SPACE for m in active) >= 2:
            self.facts.add('finish_two')

    def move(self, mascot, delta, group=False):
        direction = 1 if delta > 0 else -1
        for _ in range(abs(delta)):
            if group and mascot.position + direction >= COURSE_COLUMNS:
                break
            previous = mascot.position
            mascot.position += direction
            if mascot.fallen and (FINAL_STRETCH_START <= previous <= FINAL_SPACE
                                  or FINAL_STRETCH_START <= mascot.position <= FINAL_SPACE):
                self.facts.add('crawl_final')
            if mascot.position >= COURSE_COLUMNS:
                mascot.status = 'goal'
                self.events.append(dict(kind='goal', mascotId=mascot.color))
                break
            if mascot.position < self.removed:
                self.dq(mascot, 'out_of_bounds')
                break
            if not group:
                self.collide(mascot)
                if sum(o.fallen and o.status == 'racing' for o in self.mascots) >= 2:
                    self.facts.add('fallen_two')

    def collide(self, moving):
        for other in self.mascots:
            if (other is not moving and other.status == 'racing'
                    and (other.position, other.lane) == (moving.position, moving.lane)):
                self.fall(other)
        # 同じマスへの衝突は同時。別のマスで順に衝突したDQは別順位。
        self.assign_ranks(finalize=False)

    def resolve(self, card):
        """効果を解決。テストはこの入口で実際の全カードを検証できる。"""
        if self.finished:
            raise ValueError('終了済みです')
        self.events = []
        self.current = card
        action = card.effect
        group = card.color == 'green'
        targets = [m for m in self.mascots if m.status == 'racing'
                   and (group or m.color == card.color)]
        for m in targets:
            if action == 'fall':
                self.fall(m)
            elif action == 'turn':
                m.facing *= -1
            else:
                if action.startswith('recover_'):
                    m.fallen, m.facing = False, 1
                if action == 'star':
                    ahead = [p for p in STAR_POSITIONS
                             if p >= self.removed and (p-m.position)*m.facing > 0]
                    dest = (min(ahead) if m.facing > 0 else max(ahead)) if ahead else m.position
                    delta = dest-m.position
                else:
                    amount = int(action.rsplit('_', 1)[1])
                    delta = amount * (-1 if '_minus_' in action else 1) * m.facing
                if m.fallen and delta:
                    delta = 1 if delta > 0 else -1
                self.move(m, delta, group)
                if action.startswith('swerve_') and m.status == 'racing':
                    m.lane += (-1 if m.color in ('blue', 'yellow') else 1)*m.facing
                    if not 0 <= m.lane < 4:
                        self.dq(m, 'out_of_bounds')
                    else:
                        self.collide(m)
        # 全員カードの途中状態は同時移動後の事実として数えない。
        self.observe()
        self.assign_ranks()

    def assign_ranks(self, finalize=True):
        pending = [m for m in self.mascots if m.status != 'racing' and m.rank is None]
        goals = [m for m in pending if m.status == 'goal']
        dqs = [m for m in pending if m.status == 'dq']
        for m in goals:
            slot = self.slots.index(None)
            self.slots[slot] = m.color
            m.rank = slot+1
            if slot == 0 and not any(o.status == 'racing' and o.position >= FINAL_STRETCH_START
                                     for o in self.mascots):
                self.facts.add('empty_final')
        if dqs:
            lowest = max(i for i, item in enumerate(self.slots) if item is None)+1
            for m in dqs:
                slot = max(i for i, item in enumerate(self.slots) if item is None)
                self.slots[slot] = m.color
                m.rank = lowest  # 同時DQは空いていた最下位の配当を共有。
        if finalize and sum(m.status != 'racing' for m in self.mascots) >= 3:
            for m in self.mascots:
                if m.status == 'racing':
                    slot = self.slots.index(None)
                    self.slots[slot] = m.color
                    m.rank, m.status = slot+1, 'remaining'
            self.finished = True

    def shorten(self):
        self.removed = min(COURSE_COLUMNS, self.removed+SHORTEN_STEP)
        self.events.append(dict(kind='shorten', removed=self.removed))
        for m in self.mascots:
            if m.position < self.removed:
                self.dq(m, 'out_of_bounds')
        self.observe()
        self.assign_ranks()
        if not self.finished:
            self.shuffle()

    def reveal(self):
        if self.finished:
            raise ValueError('終了済みです')
        self.before_shortening = None
        card = self.deck.pop(0)
        self.discard.append(card)
        self.revealed += 1
        self.history.append(card)
        self.resolve(card)
        if not self.deck and not self.finished:
            self.before_shortening = [m.public() for m in self.mascots]
            self.shorten()
        return card

    def outcome(self, effect):
        if not self.finished:
            raise ValueError('レース結果は未確定です')
        bottom = {'gobbler_bottom': 'orange', 'hurley_bottom': 'salmon',
                  'mum_bottom': 'yellow', 'dangle_bottom': 'blue'}
        if effect in bottom:
            return next(m.rank for m in self.mascots if m.color == bottom[effect]) >= 3
        if effect not in {'knockout', 'out_of_bounds', 'disqualified', 'same_space',
                          'fallen_two', 'crawl_final', 'finish_two', 'empty_final'}:
            raise ValueError('未対応のサイドベットです')
        return effect in self.facts

    def public(self):
        return dict(mascots=[m.public() for m in self.mascots],
                    course=dict(lanes=4, columns=COURSE_COLUMNS, start=START_POSITION,
                                stars=list(STAR_POSITIONS), removed=self.removed),
                    currentCard=self.current.public() if self.current else None,
                    remaining=len(self.deck), revealed=self.revealed, events=list(self.events),
                    revealedCards=[c.public() for c in self.history],
                    beforeShortening=self.before_shortening,
                    standingsPreview=[m.public() for m in self.mascots if m.rank is not None])
