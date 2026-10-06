"""53枚の物理カードを、種類と個体を区別して管理する。"""
from dataclasses import dataclass
import json
from pathlib import Path
from random import Random

CATALOG_PATH = Path(__file__).resolve().parents[2] / 'data/cards/catalog.json'
COLORS = ('blue', 'orange', 'yellow', 'salmon')
NAMES = dict(zip(COLORS, ('ダングル', 'ゴブラー', 'マム', 'ハーレー')))
# ルールブック SETUP 図の特別枠4枚。
STARTERS = tuple(f'{color}_recover_2' for color in COLORS)


@dataclass(frozen=True)
class RaceCard:
    instance_id: str
    card_id: str
    color: str
    effect: str
    label: str
    rect: tuple

    def public(self):
        return dict(cardInstanceId=self.instance_id, cardId=self.card_id,
                    mascot=self.color, color=self.color, effectKind=self.effect,
                    effectLabel=self.label, label=self.label, rect=list(self.rect),
                    lane=str(COLORS.index(self.color)) if self.color in COLORS else 'all')


def catalog():
    return json.loads(CATALOG_PATH.read_text(encoding='utf-8'))['cards']


class CardSupply:
    def __init__(self, rng: Random):
        self.rng = rng
        self.cards = [RaceCard(f"{c['id']}:{n}", c['id'], c['color'], c['effect'],
                               c['label'], tuple(c['rect']))
                      for c in catalog() if c['kind'] == 'race'
                      for n in range(c['quantity'])]
        if len(self.cards) != 53:
            raise ValueError('レースカード供給は53枚必要です')

    def deal(self, player_ids):
        if not 3 <= len(player_ids) <= 8 or len(set(player_ids)) != len(player_ids):
            raise ValueError('参加者は3〜8人必要です')
        starters = [next(c for c in self.cards if c.card_id == key) for key in STARTERS]
        remaining = [c for c in self.cards if c not in starters]
        self.rng.shuffle(remaining)
        public = starters + remaining[:14-len(player_ids)]
        offset = 14-len(player_ids)
        hands = {pid: remaining[offset+i*3:offset+(i+1)*3] for i, pid in enumerate(player_ids)}
        return public, hands, remaining[offset+len(player_ids)*3:]
