import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/hotstreak_display"))
from card_assets import CardAssets


class CardAssetTests(unittest.TestCase):
    def test_catalog_matches_supplied_inventory(self):
        assets = CardAssets()
        cards = list(assets.cards.values())
        self.assertEqual(len(cards), 63)
        self.assertEqual(sum(c["quantity"] for c in cards), 65)
        self.assertEqual(sum(c["kind"] == "event" for c in cards), 12)
        for color in ("blue", "orange", "salmon", "yellow"):
            self.assertEqual(sum(c["color"] == color for c in cards), 11)
            self.assertNotIn(color + "_move_1", assets.cards)
        self.assertIn("左", assets.cards["blue_swerve_1"]["label"])
        self.assertIn("右", assets.cards["orange_swerve_1"]["label"])
        self.assertEqual(sum(c["quantity"] for c in cards if c["color"] == "green"), 9)

    def test_all_atlas_cells_load_and_cache(self):
        assets = CardAssets()
        for key in assets.cards:
            image = assets.card(key, (120, 168))
            self.assertEqual(image.get_size(), (120, 168))
            self.assertIs(image, assets.card(key, (120, 168)))


if __name__ == "__main__":
    unittest.main()
