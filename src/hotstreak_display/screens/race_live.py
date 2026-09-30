"""REQ-race-004〜006: サーバが確定した位置だけを補間して描画する。"""
import pygame
from .race import View, COLORS


class LiveRaceModel:
    def __init__(self):
        self.key = None
        self.elapsed = 0
        self.progress = 1
        self.moving = False
        self.visual_positions = [2.] * 4
        self.visual_lanes = list(range(4))
        self.fallen = [False] * 4
        self.status = ['racing'] * 4
        self.removed = 0

    def apply(self, snapshot):
        key = (snapshot['raceIndex'], snapshot['revealed'])
        if key == self.key:
            return
        new_race = self.key is None or self.key[0] != key[0]
        self.key = key
        self.race_index = snapshot['raceIndex']
        mascots = {m['color']: m for m in snapshot['mascots']}
        ordered = [mascots[color] for color in COLORS]
        self.start_positions = list(self.visual_positions) if not new_race else [float(m['position']) for m in ordered]
        self.start_lanes = list(self.visual_lanes) if not new_race else [float(m['lane']) for m in ordered]
        self.target_positions = [m['position'] for m in ordered]
        self.target_lanes = [m['lane'] for m in ordered]
        self.old_fallen = list(self.fallen)
        self.fallen = [m['fallen'] for m in ordered]
        self.facing = [m['facing'] for m in ordered]
        self.next_status = [m['status'] for m in ordered]
        self.target_removed = snapshot['course']['removed']
        if new_race:
            self.removed = self.target_removed
            self.status = list(self.next_status)
        card = snapshot.get('currentCard')
        self.card_id = card['cardId'] if card else 'card_back'
        self.effect = card['effectLabel'] if card else '3枚バーン済み'
        effect = card['effectKind'] if card else ''
        self.active = COLORS.index(card['color']) if card and card['color'] in COLORS else 0
        self.targets = list(range(4)) if card and card['color'] == 'green' else [self.active]
        self.action = 'shorten' if self.target_removed != self.removed else effect.split('_')[0]
        self.remaining = snapshot['remaining']
        self.finished_entries = [(m['rank'], i, m['status']) for i, m in enumerate(ordered) if m['status'] != 'racing']
        self.finished_entries.sort()
        self.state = 'start' if snapshot['revealed'] == 0 else 'running'
        self.progress = 1 if new_race else 0
        self.moving = not new_race
        self.tick(0)

    def tick(self, dt):
        self.elapsed += dt
        self.progress = min(1, self.progress + dt / .75)
        t = self.progress * self.progress * (3 - 2 * self.progress)
        self.visual_positions = [a+(b-a)*t for a, b in zip(self.start_positions, self.target_positions)]
        self.visual_lanes = [a+(b-a)*t for a, b in zip(self.start_lanes, self.target_lanes)]
        self.moving = self.progress < 1
        if not self.moving:
            self.status = list(self.next_status)
            self.removed = self.target_removed


class LiveView(View):
    def __init__(self, font=None):
        super().__init__(font)
        self.model = LiveRaceModel()

    def draw_live(self, surface, snapshot, context):
        self.model.apply(snapshot)
        self.model.tick(context.get('dt', 0))
        self.draw(surface, self.model)
        self.ocean_panel(surface, pygame.Rect(20, 654, 1240, 50))
        self.text(surface, 'ENTER  →  次のカードをめくる', (45, 669), 20, (244, 252, 255))
        self.text(surface, snapshot['prompt']['text'], (520, 669), 20, (255, 237, 168), 700)
