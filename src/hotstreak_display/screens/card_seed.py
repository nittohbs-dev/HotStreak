"""Issue #35 / SCR-display-004: カード仕込みの会場画面モック。"""

import argparse
from dataclasses import dataclass
from pathlib import Path

import pygame

if __package__:
    from .setup_cards import DisplaySetupRoot
else:
    from setup_cards import DisplaySetupRoot


@dataclass(frozen=True)
class SeedPreview:
    label: str
    completed: int
    total: int = 6
    deck_count: int = 18
    ready: bool = False


class DisplaySeedScreen:
    """固定表示例のみ。手札・抽選・通信・デッキ組成は扱わない。"""

    def __init__(self):
        self.states = (
            SeedPreview("仕込み待ち", 0),
            SeedPreview("仕込み中", 3),
            SeedPreview("カード束確定", 6),
            SeedPreview("準備完了", 6, ready=True),
        )
        self.index = 1
        self.confirmed = False

    @property
    def state(self):
        return self.states[self.index]

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.state.ready:
            self.confirmed = True


class DisplaySeedRoot(DisplaySetupRoot):
    """CMP-seed-001〜003: 進捗・裏向きカード束・準備完了表示。"""

    def panel(self, surface, rect):
        pygame.draw.rect(surface, (6, 8, 13), rect.move(5, 5))
        pygame.draw.rect(surface, (12, 15, 20), rect)
        pygame.draw.rect(surface, (124, 99, 67), rect, 2)

    def card_back(self, surface, x, y, muted=False):
        image = self.card_assets.card("card_back", (100, 140))
        if muted:
            image = image.copy()
            image.fill((155, 155, 155), special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(image, (x, y))

    def draw(self, surface, screen):
        state = screen.state
        complete = state.completed == state.total
        surface.blit(self.background, (0, 0))
        self.panel(surface, pygame.Rect(20, 16, 1240, 65))
        self.text(surface, "カード仕込み", (44, 28), 32)
        self.text(surface, "HOT STREAK", (1070, 42), 16, (200, 184, 144))

        self.panel(surface, pygame.Rect(104, 112, 1072, 113))
        title = "全員のカードが揃いました" if complete else "スマホでカードを1枚仕込んでください"
        self.text(surface, title, (130, 127), 24)
        self.text(surface, f"仕込み完了  {state.completed} / {state.total} 人", (824, 129), 24, (223, 191, 134))
        for i in range(state.total):
            rect = pygame.Rect(132 + i * 168, 177, 150, 19)
            pygame.draw.rect(surface, (39, 42, 47), rect)
            if i < state.completed:
                pygame.draw.rect(surface, (223, 191, 134), rect.inflate(-4, -4))

        label = f"レース用カード束  {state.deck_count} 枚" if complete else f"レース用カード束  完成時 {state.deck_count} 枚"
        self.text(surface, label, (104, 241), 24, (223, 191, 134))
        for i in range(state.deck_count):
            self.card_back(surface, 124 + i % 9 * 116, 286 + i // 9 * 152, not complete)

        if state.ready:
            overlay = pygame.Surface((1100, 328), pygame.SRCALPHA)
            overlay.fill((9, 12, 17, 190))
            surface.blit(overlay, (90, 275))
            self.panel(surface, pygame.Rect(266, 347, 748, 172))
            self.text(surface, "全員の準備が整いました", (365, 367), 32, (223, 191, 134))
            self.text(surface, "まもなく開始します", (438, 418), 24)
            footer = "進行確認OK（レース画面は次のモック）" if screen.confirmed else "ENTER  →  レースへ"
            self.text(surface, footer, (300 if screen.confirmed else 456, 472), 20)
        elif complete:
            self.text(surface, "公開カードと仕込みカードが揃いました", (358, 626), 24, (223, 191, 134))


def main():
    parser = argparse.ArgumentParser(description="カード仕込み〜準備完了モック（通信なし）")
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--font")
    parser.add_argument("--state", type=int, choices=range(4), default=1)
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    pygame.init()
    try:
        screen = DisplaySeedScreen()
        screen.index = args.state
        view = DisplaySeedRoot(args.font)
        canvas = pygame.Surface((1280, 720))
        if args.screenshot:
            view.draw(canvas, screen)
            pygame.image.save(canvas, args.screenshot)
            return
        display = pygame.display.set_mode((1280, 720), pygame.RESIZABLE if args.windowed else pygame.FULLSCREEN)
        pygame.display.set_caption("ホットストリーク — カード仕込み [MOCK]")
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    screen.handle_event(event)
            view.draw(canvas, screen)
            width, height = display.get_size()
            scale = min(width / 1280, height / 720)
            size = max(1, int(1280 * scale)), max(1, int(720 * scale))
            display.fill((9, 12, 17))
            display.blit(pygame.transform.scale(canvas, size), ((width - size[0]) // 2, (height - size[1]) // 2))
            pygame.display.flip()
            clock.tick(30)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
