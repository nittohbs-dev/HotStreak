"""カード素材の共通入口。画像はatlasから読み、IDで切り出してキャッシュする。"""
import json
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/cards/catalog.json"
COLOR_LABELS = {"blue": "青", "orange": "オレンジ", "salmon": "サーモン", "yellow": "黄", "green": "緑"}
ALIASES = {label: key for key, label in COLOR_LABELS.items()}


class CardAssets:
    def __init__(self):
        self.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.sheet = pygame.image.load(str(ROOT / self.catalog["image"]))
        self.icons = pygame.image.load(str(ROOT / self.catalog["icons_image"]))
        self.cards = {card["id"]: card for card in self.catalog["cards"]}
        self.cache = {}

    def card(self, card_id, size):
        key = (card_id, tuple(size))
        if key not in self.cache:
            entry = self.cards[card_id]
            self.cache[key] = pygame.transform.smoothscale(self.sheet.subsurface(entry["rect"]), size)
        return self.cache[key]

    def icon(self, color, size):
        color = ALIASES.get(color, color)
        key = ("icon", color, tuple(size))
        if key not in self.cache:
            rect = self.catalog["icons"].get(color)
            if rect is None:
                return None
            self.cache[key] = pygame.transform.scale(self.icons.subsurface(rect), size)
        return self.cache[key]

    def race_cards(self):
        return [card for card in self.cards.values() if card["kind"] == "race"]
