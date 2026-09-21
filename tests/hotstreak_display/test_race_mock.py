"""Enter境界と固定カード表示の回帰テスト。"""
from argparse import Namespace
import unittest
import pygame
from src.hotstreak_display.screens.race import Model


class RaceInputTest(unittest.TestCase):
    def setUp(self):
        self.model = Model(Namespace(state='start'))

    def press(self):
        self.model.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN))

    def release(self):
        self.model.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_RETURN))

    def test_one_press_reveals_one_card(self):
        self.press()
        self.assertEqual(self.model.index,1)
        self.assertEqual(self.model.card_id,'blue_move_3')
        self.assertEqual(self.model.remaining,14)
        self.assertEqual(self.model.positions,(5,2,2,2))

    def test_hold_does_not_repeat(self):
        for _ in range(20):
            self.press()
        self.assertEqual(self.model.index,1)
        self.model.update(2)
        self.release()
        self.press()
        self.assertEqual(self.model.index,2)
        self.assertEqual(self.model.card_id,'orange_move_2')

    def test_os_repeat_and_other_keys_do_not_advance(self):
        self.model.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN,repeat=True))
        self.model.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT))
        self.assertEqual(self.model.index,0)

    def test_demo_deck_stops_without_inventing_result(self):
        for _ in range(len(self.model.SAMPLES)):
            self.press()
            self.model.update(2)
            self.release()
        self.assertEqual(self.model.index,len(self.model.SAMPLES))
        self.assertEqual(self.model.remaining,15-len(self.model.SAMPLES))
        self.assertNotEqual(self.model.state,'finish')

    def test_finished_enter_restarts(self):
        self.model.set_state('finish')
        self.press()
        self.assertEqual(self.model.positions,(2,2,2,2))
        self.assertEqual(self.model.state,'start')

    def test_full_race_shortens_and_finishes(self):
        shortened=False
        for n in range(19):
            if self.model.state=='finish': break
            self.release(); self.press(); self.model.update(1.2)
            if self.model.action=='shorten':
                self.model.update(2); shortened=True
                self.assertEqual(self.model.removed,3)
                self.assertEqual(self.model.status[3],'dq')
        self.assertTrue(shortened)
        self.assertEqual(self.model.state,'finish')
        self.assertEqual(self.model.standings,[0,1,2,3])

if __name__ == '__main__': unittest.main()
