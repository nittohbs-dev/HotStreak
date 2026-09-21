from argparse import Namespace
import unittest
from src.hotstreak_display.screens.race import Model

class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.m=Model(Namespace(state='start'))
        self.m.positions=(4,6,7,4)
        self.m.visual_positions=list(self.m.positions)

    def play(self,card):
        self.assertTrue(self.m.apply_card(card))
        self.m.update(1.2)

    def test_star_forward_back_and_no_next(self):
        self.play('blue_star'); self.assertEqual(self.m.positions[0],5)
        self.m.facing[0]=-1
        self.play('blue_star'); self.assertEqual(self.m.positions[0],0)
        self.play('blue_star'); self.assertEqual(self.m.positions[0],0)

    def test_negative_reverses_with_facing(self):
        self.play('blue_move_minus_2'); self.assertEqual(self.m.positions[0],2)
        self.m.facing[0]=-1
        self.play('blue_move_minus_2'); self.assertEqual(self.m.positions[0],4)

    def test_fallen_star_and_numbers_crawl(self):
        self.m.fallen[0]=True
        self.play('blue_move_3'); self.assertEqual(self.m.positions[0],5)
        self.play('blue_star'); self.assertEqual(self.m.positions[0],6)
        self.play('blue_move_minus_2'); self.assertEqual(self.m.positions[0],5)

    def test_recover_before_move_resets_both(self):
        self.m.fallen[0]=True; self.m.facing[0]=-1
        self.play('blue_recover_2')
        self.assertEqual(self.m.positions[0],6)
        self.assertFalse(self.m.fallen[0]); self.assertEqual(self.m.facing[0],1)

    def test_swerve_relative_to_facing(self):
        self.m.lanes[0]=1; self.m.facing[0]=-1
        self.play('blue_swerve_2')
        self.assertEqual((self.m.positions[0],self.m.lanes[0]),(2,2))

    def test_crawling_still_swerves(self):
        self.m.lanes[0]=2; self.m.fallen[0]=True
        self.play('blue_swerve_3')
        self.assertEqual((self.m.positions[0],self.m.lanes[0]),(5,1))

    def test_collision_pass_through_falls_stationary(self):
        self.m.lanes=[1,1,2,3]
        self.play('blue_move_3')
        self.assertTrue(self.m.fallen[1]); self.assertFalse(self.m.fallen[0])
        self.assertEqual(self.m.status[1],'racing')

    def test_collision_again_knocks_out(self):
        self.m.lanes=[1,1,2,3]; self.m.fallen[1]=True
        self.play('blue_move_3')
        self.assertEqual(self.m.status[1],'dq'); self.assertEqual(self.m.standings[3],1)

    def test_lateral_collision(self):
        self.m.lanes=[2,1,2,3]
        self.play('blue_swerve_2'); self.assertTrue(self.m.fallen[1])

    def test_second_fall_knocks_out(self):
        self.play('blue_fall'); self.play('blue_fall')
        self.assertEqual(self.m.status[0],'dq')

    def test_out_of_bounds_side_and_back(self):
        self.play('blue_swerve_1'); self.assertEqual(self.m.status[0],'dq')
        self.m.positions=(4,1,7,4)
        self.play('orange_move_minus_2'); self.assertEqual(self.m.status[1],'dq')

    def test_goal_precedes_swerve_out(self):
        self.m.positions=(11,6,7,4)
        self.play('blue_swerve_2')
        self.assertEqual(self.m.status[0],'goal'); self.assertEqual(self.m.lanes[0],0)

    def test_star_can_goal(self):
        self.m.positions=(9,6,7,4)
        self.play('blue_star'); self.assertEqual(self.m.status[0],'goal')

    def test_green_no_collisions_no_goal(self):
        self.m.positions=(10,11,10,10); self.m.lanes=[1,1,1,1]
        self.m.fallen[1]=True
        self.play('green_move_3')
        self.assertEqual(self.m.positions,(11,11,11,11))
        self.assertEqual(self.m.status,['racing']*4)
        self.assertEqual(self.m.fallen,[False,True,False,False])

    def test_green_recover_and_dq_ties(self):
        self.m.fallen=[True]*4; self.m.facing=[-1]*4
        self.play('green_recover_2')
        self.assertEqual(self.m.positions,(6,8,9,6)); self.assertEqual(self.m.fallen,[False]*4)
        self.m.positions=(0,0,7,6)
        self.play('green_move_minus_2')
        self.assertEqual(self.m.status[:2],['dq','dq'])
        self.assertEqual(self.m.tie_ranks,{0:4,1:4})

    def test_live_standings_show_dq_from_bottom(self):
        self.m.place(3,'dq')
        self.assertEqual(self.m.finished_entries,[(4,3,'dq')])
        self.m.place(1,'dq')
        self.assertEqual(self.m.finished_entries,[(3,1,'dq'),(4,3,'dq')])
        self.m.place(0,'goal')
        self.assertEqual(self.m.finished_entries,[(1,0,'goal'),(3,1,'dq'),(4,3,'dq')])

    def test_all_catalog_effects_execute(self):
        for card in self.m.catalog:
            with self.subTest(card=card['id']):
                self.setUp(); self.play(card['id'])

if __name__=='__main__': unittest.main()
