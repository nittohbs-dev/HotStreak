import os
from pathlib import Path
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/hotstreak_display/screens"))
import card_seed


class SeedMockTests(unittest.TestCase):
    def test_enter_does_not_complete_unfinished_seed(self):
        screen = card_seed.DisplaySeedScreen()
        for index in range(3):
            screen.index = index
            screen.handle_event(card_seed.pygame.event.Event(card_seed.pygame.KEYDOWN, key=card_seed.pygame.K_RETURN))
            self.assertFalse(screen.confirmed)
            self.assertEqual(screen.index, index)

    def test_ready_ack_is_not_changed_by_arrow_keys(self):
        screen = card_seed.DisplaySeedScreen()
        screen.index = 3
        screen.handle_event(card_seed.pygame.event.Event(card_seed.pygame.KEYDOWN, key=card_seed.pygame.K_RETURN))
        self.assertTrue(screen.confirmed)
        screen.handle_event(card_seed.pygame.event.Event(card_seed.pygame.KEYDOWN, key=card_seed.pygame.K_RIGHT))
        self.assertEqual(screen.index, 3)
        self.assertTrue(screen.confirmed)
        screen.handle_event(card_seed.pygame.event.Event(card_seed.pygame.KEYDOWN, key=card_seed.pygame.K_LEFT))
        self.assertEqual(screen.index, 3)
        self.assertTrue(screen.confirmed)

    def test_all_states_render_without_private_cards(self):
        card_seed.pygame.font.init()
        try:
            view = card_seed.DisplaySeedRoot()
        except RuntimeError:
            self.skipTest("日本語フォント未配置")
        screen = card_seed.DisplaySeedScreen()
        canvas = card_seed.pygame.Surface((1280, 720))
        for index in range(4):
            screen.index = index
            view.draw(canvas, screen)
            self.assertFalse(hasattr(screen.state, "hand"))
            self.assertEqual(screen.state.deck_count, 18)


if __name__ == "__main__":
    unittest.main()
