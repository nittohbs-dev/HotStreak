"""Issue #31の固定モック状態・画面操作を確認。"""

import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/hotstreak_display/screens"))
import betting


class BettingMockTests(unittest.TestCase):
    def test_fixture_controls_do_not_purchase_or_mutate_stock(self):
        screen = betting.DisplayBettingScreen()
        originals = screen.states
        for _ in range(8):
            screen.handle_event(betting.pygame.event.Event(betting.pygame.KEYDOWN, key=betting.pygame.K_RIGHT))
            screen.handle_event(betting.pygame.event.Event(betting.pygame.KEYDOWN, key=betting.pygame.K_RETURN))
        self.assertEqual(screen.states, originals)
        self.assertEqual(screen.index, 1)

    def test_enter_waits_for_players_or_double(self):
        screen = betting.DisplayBettingScreen()
        for index in (0, 1, 3):
            screen.index = index
            screen.handle_event(betting.pygame.event.Event(betting.pygame.KEYDOWN, key=betting.pygame.K_RETURN))
            self.assertNotIn("進行確認OK", screen.notice)
        self.assertIn("ダブル", screen.notice)

    def test_ready_preview_acknowledges_without_creating_next_screen(self):
        screen = betting.DisplayBettingScreen()
        screen.index = 2
        screen.handle_event(betting.pygame.event.Event(betting.pygame.KEYDOWN, key=betting.pygame.K_KP_ENTER))
        self.assertIn("進行確認OK", screen.notice)
        self.assertEqual(screen.index, 2)

    def test_all_preview_states_render(self):
        betting.pygame.font.init()
        try:
            view = betting.DisplayBettingRoot()
        except RuntimeError:
            self.skipTest("日本語フォント未配置")
        screen = betting.DisplayBettingScreen()
        surface = betting.pygame.Surface((1280, 720))
        for i in range(4):
            screen.index = i
            view.draw(surface, screen)
            self.assertEqual(surface.get_size(), (1280, 720))


if __name__ == "__main__":
    unittest.main()
