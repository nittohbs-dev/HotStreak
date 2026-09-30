import unittest
from random import Random
from hotstreak_core.cards import CardSupply, STARTERS


class DealTests(unittest.TestCase):
    def test_counts_and_physical_card_conservation(self):
        for n in range(3, 9):
            for seed in range(30):
                public, hands, unused = CardSupply(Random(seed)).deal(list(range(n)))
                self.assertEqual(len(public), 18-n)
                self.assertTrue(set(STARTERS) <= {c.card_id for c in public})
                self.assertTrue(all(len(h) == 3 for h in hands.values()))
                all_cards = public + sum(hands.values(), []) + unused
                self.assertEqual(len(all_cards), 53)
                self.assertEqual(len({c.instance_id for c in all_cards}), 53)

    def test_invalid_player_count(self):
        for n in (0, 2, 9):
            with self.assertRaises(ValueError):
                CardSupply(Random()).deal(list(range(n)))
