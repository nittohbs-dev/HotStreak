"""SCR-display-003 / Issue #31: 通信・ゲーム演算を持たない会場画面モック。"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pygame

if __package__:
    from .setup_cards import DisplaySetupRoot, DisplaySetupCardsScreen, demo_state
else:
    from setup_cards import DisplaySetupRoot, DisplaySetupCardsScreen, demo_state


@dataclass(frozen=True)
class PlayerPreview:
    name: str
    mascot: str
    tickets: int


@dataclass(frozen=True)
class BettingPreview:
    label: str
    race: int
    round_label: str
    prompt: str
    players: tuple[PlayerPreview, ...]
    current_player: int | None
    stock: tuple[int, ...]
    ready: bool = False
    double_wait: bool = False


MASCOTS = ("Gobbler", "Hurley", "Dangle", "Mum")
NAMES = ("くま", "さかな", "とり", "うさぎ", "ねこ", "いぬ")


def preview_states():
    """表示の見本。手番計算・購入・在庫更新はせず、固定状態を切り替える。"""
    def players(counts):
        return tuple(PlayerPreview(name, MASCOTS[i % 4], counts[i]) for i, name in enumerate(NAMES))
    prompt = "レース中に、失格するマスコットはいる？"
    return (
        BettingPreview("開始前", 1, "1周目", prompt, players((0, 0, 0, 0, 0, 0)), 0, (3, 3, 3, 3, 3, 3)),
        BettingPreview("ドラフト中", 1, "2周目", prompt, players((1, 1, 1, 1, 1, 2)), 4, (0, 2, 2, 2, 2, 3)),
        BettingPreview("全員選択済み", 1, "選択完了", prompt, players((2, 2, 2, 2, 2, 2)), None, (0, 1, 1, 1, 1, 2), True),
        BettingPreview("第3レース・ダブル待ち", 3, "ダブル指定待ち", prompt, players((2, 2, 2, 2, 2, 2)), None, (0, 1, 1, 1, 1, 2), False, True),
    )


class DisplayBettingScreen:
    """CLS-betting-010のモック。矢印は開発時の見本切り替え専用。"""

    def __init__(self):
        self.states = preview_states()
        self.index = 1
        self.notice = ""

    @property
    def state(self):
        return self.states[self.index]

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            self.index = (self.index + (1 if event.key == pygame.K_RIGHT else -1)) % len(self.states)
            self.notice = ""
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.state.ready:
                self.notice = "進行確認OK。カード仕込み画面は今回のモック対象外です。"
            elif self.state.double_wait:
                self.notice = "スマホでダブルにする1枚を指定してください。"
            else:
                self.notice = "まだドラフト中です。全員の選択完了をお待ちください。"


class DisplayBettingRoot(DisplaySetupRoot):
    """CMP-betting-001〜004。公開カードと同じ背景・書体を使用。"""

    def panel(self, surface, rect, color=(124, 99, 67)):
        pygame.draw.rect(surface, (6, 8, 13), rect.move(5, 5))
        pygame.draw.rect(surface, (12, 15, 20), rect)
        pygame.draw.rect(surface, color, rect, 2)

    def draw(self, surface, screen):
        state = screen.state
        surface.blit(self.background, (0, 0))
        self.panel(surface, pygame.Rect(20, 16, 1240, 65), (202, 190, 159))
        self.text(surface, "マ券ドラフト", (44, 28), 32)
        self.text(surface, f"RACE {state.race} / 3", (890, 36), 24, (223, 191, 134))
        self.text(surface, "HOT STREAK", (1080, 42), 16, (200, 184, 144))

        self.panel(surface, pygame.Rect(72, 99, 1136, 87))
        self.text(surface, "SIDE BET  /  今回のお題", (94, 109), 20, (223, 191, 134))
        self.text(surface, state.prompt, (94, 141), 24, max_width=1088)

        self.panel(surface, pygame.Rect(72, 205, 476, 405))
        self.text(surface, "参加者・選択状況", (94, 220), 24)
        self.text(surface, state.round_label, (364, 224), 20, (223, 191, 134), 164)
        for i, player in enumerate(state.players):
            y = 266 + i * 53
            active = i == state.current_player
            if active:
                pygame.draw.rect(surface, (56, 37, 28), (87, y - 2, 446, 49))
                pygame.draw.rect(surface, (231, 125, 77), (87, y - 2, 446, 49), 2)
            self.mascot_icon(surface, player.mascot, (116, y + 21), 3)
            self.text(surface, player.name, (145, y + 7), 24)
            if active:
                self.text(surface, "選択中", (295, y + 9), 20, (231, 125, 77))
            elif player.tickets == 2:
                self.text(surface, "取得済み", (295, y + 9), 20, (165, 185, 117))
            else:
                self.text(surface, "待機", (295, y + 9), 20, (200, 184, 144))
            self.text(surface, f"{player.tickets} / 2枚", (424, y + 9), 20)

        self.panel(surface, pygame.Rect(570, 205, 638, 405))
        self.text(surface, "残りマ券", (593, 220), 24)
        self.text(surface, "選択・セーフ／リスキーの指定はスマホで", (594, 257), 20, (200, 184, 144))
        for i, amount in enumerate(state.stock):
            x, y = 593 + i % 3 * 200, 298 + i // 3 * 145
            color = self.COLORS[i] if i < 4 else (223, 191, 134)
            if not amount:
                color = (127, 130, 132)
            self.panel(surface, pygame.Rect(x, y, 181, 128), color)
            if i < 4:
                self.mascot_icon(surface, MASCOTS[i], (x + 31, y + 34), 3)
                label = MASCOTS[i]
            else:
                label = "YES" if i == 4 else "NO"
                self.text(surface, "?", (x + 16, y + 12), 32, color)
            self.text(surface, label, (x + 57, y + 19), 20, color, 113)
            self.text(surface, f"残り {amount} 枚", (x + 16, y + 64), 24, color)
            if not amount:
                self.text(surface, "在庫なし", (x + 16, y + 98), 20, color)

        self.panel(surface, pygame.Rect(72, 628, 1136, 48))
        if screen.notice:
            footer = screen.notice
        elif state.ready:
            footer = "全員の選択が完了しました。 ENTER → カード仕込みへ"
        elif state.double_wait:
            footer = "第3レース：スマホでダブルにする1枚を選んでください。"
        else:
            footer = f"{state.players[state.current_player].name} さんが選択中です。スマホでマ券を選んでください。"
        self.text(surface, footer, (92, 638), 24, (223, 191, 134), 1090)
        self.text(surface, f"MOCK  |  ← → 表示例切替：{state.label}  |  ESC 終了", (76, 689), 20, (200, 184, 144))


def main():
    parser = argparse.ArgumentParser(description="マ券ドラフト共有画面のモック（通信なし）")
    parser.add_argument("--windowed", action="store_true")
    parser.add_argument("--font")
    parser.add_argument("--state", type=int, choices=range(4), default=1)
    parser.add_argument("--from-setup", action="store_true", help="既存の公開カードデモからEnterで接続")
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    pygame.init()
    try:
        screen = DisplayBettingScreen()
        screen.index = args.state
        view = DisplayBettingRoot(args.font)
        setup_view = DisplaySetupRoot(args.font)
        stage = ["setup" if args.from_setup else "betting"]
        setup = DisplaySetupCardsScreen(lambda: stage.__setitem__(0, "betting"), lambda _: None)
        setup.handle_message("setup.state", demo_state(6))
        canvas = pygame.Surface((1280, 720))
        if args.screenshot:
            view.draw(canvas, screen)
            pygame.image.save(canvas, args.screenshot)
            return
        display = pygame.display.set_mode((1280, 720), pygame.RESIZABLE if args.windowed else pygame.FULLSCREEN)
        pygame.display.set_caption("ホットストリーク — 公開カード / マ券ドラフト [MOCK]")
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif stage[0] == "setup":
                    setup.handle_event(event)
                else:
                    screen.handle_event(event)
            if stage[0] == "setup":
                setup_view.draw(canvas, setup)
            else:
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
