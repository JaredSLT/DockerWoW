"""Equipment cache parsing and character-sheet eras. No database."""

import unittest
from pathlib import Path

from wowweb.armory.constants import slot_label, slots_for_expansion
from wowweb.armory.queries import parse_equipment_cache
from wowweb.catalog import resolve
from wowweb.html.armory import character_sheet

ROOT = Path(__file__).resolve().parents[1]


class EquipmentCacheTests(unittest.TestCase):
    def test_cmangos_pairs_on_vanilla(self):
        parsed = parse_equipment_cache("cmangos", 0, "123 0 456 0")
        self.assertEqual(parsed, [("Head", 123), ("Neck", 456)])

    def test_alpha_uses_the_same_pairs(self):
        parsed = parse_equipment_cache("alpha", 0, "123 foo 456 bar")
        self.assertEqual(parsed, [("Head", 123), ("Neck", 456)])

    def test_cmangos_stops_without_an_enchant_token(self):
        parsed = parse_equipment_cache("cmangos", 0, "123 0 456")
        self.assertEqual(parsed, [("Head", 123)])

    def test_trinity_one_id_per_slot_on_vanilla(self):
        parsed = parse_equipment_cache("trinity", 0, "123 456")
        self.assertEqual(parsed, [("Head", 123), ("Neck", 456)])

    def test_single_id_cores_skip_non_numeric_tokens(self):
        raw = "123 nope 456"
        for kind in ("azerothcore", "trinity", "skyfire"):
            with self.subTest(kind=kind):
                parsed = parse_equipment_cache(kind, 0, raw)
                self.assertEqual(parsed, [("Head", 123), ("Neck", 456)])

    def test_zero_item_advances_the_slot(self):
        parsed = parse_equipment_cache("trinity", 2, "123 0 456")
        self.assertEqual(parsed, [("Head", 123), ("Shoulders", 456)])

    def test_wod_trinity_cache_does_not_label_ranged(self):
        raw = " ".join(str(i) for i in range(1, 20))
        parsed = parse_equipment_cache("trinity", 5, raw)
        names = [name for name, _item in parsed]
        self.assertNotIn("Ranged", names)
        self.assertEqual(len(parsed), 18)
        self.assertEqual(parsed[15], ("Main Hand", 16))
        self.assertEqual(parsed[16], ("Off Hand", 17))
        self.assertEqual(parsed[17], ("Tabard", 18))

    def test_mop_still_has_ranged(self):
        raw = " ".join(str(i) for i in range(1, 21))
        parsed = parse_equipment_cache("skyfire", 4, raw)
        self.assertEqual(parsed[17], ("Ranged", 18))
        self.assertEqual(parsed[18], ("Tabard", 19))
        self.assertEqual(len(parsed), 19)

    def test_slot_map_by_expansion_level(self):
        for level in (0, 1, 2, 3, 4):
            names = slots_for_expansion(level)
            self.assertEqual(len(names), 19)
            self.assertEqual(names[17], "Ranged")
            self.assertEqual(names[-1], "Tabard")
        for level in (5, 6, 11):
            names = slots_for_expansion(level)
            self.assertEqual(len(names), 18)
            self.assertNotIn("Ranged", names)
            self.assertEqual(names[15:], ("Main Hand", "Off Hand", "Tabard"))

    def test_inventory_index_outside_the_map_is_slot_n(self):
        self.assertEqual(slot_label(5, 17), "Tabard")
        self.assertEqual(slot_label(0, 17), "Ranged")
        self.assertEqual(slot_label(5, 18), "Slot 18")
        self.assertEqual(slot_label(0, 19), "Slot 19")

    def test_empty_cache(self):
        self.assertEqual(parse_equipment_cache("trinity", 5, ""), [])
        self.assertEqual(parse_equipment_cache("trinity", 5, None), [])


def _character(equipment=None):
    return {
        "name": "Thrall",
        "level": 80,
        "race": "Orc",
        "class": "Shaman",
        "online": False,
        "money_text": "1g",
        "realm": "Test Realm",
        "achievements": 0,
        "equipment": equipment or [],
    }


class CharacterSheetEraTests(unittest.TestCase):
    def test_outer_sheet_class_follows_the_expansion(self):
        char = _character()
        for era in ("tbc", "wotlk"):
            html = character_sheet(resolve(era), char)
            self.assertIn('class="sheet armory-classic"', html)
            self.assertNotIn("armory-profile", html)
            self.assertNotIn("armory-later", html)
        for era in ("cata", "mop", "wod"):
            html = character_sheet(resolve(era), char)
            self.assertIn('class="sheet armory-profile"', html)
        for era in ("legion", "bfa", "shadowlands", "dragonflight", "warwithin", "midnight"):
            html = character_sheet(resolve(era), char)
            self.assertIn('class="sheet armory-later"', html)
        for era in ("alpha", "vanilla"):
            html = character_sheet(resolve(era), char)
            self.assertIn('class="sheet"', html)
            self.assertNotIn("armory-classic", html)
            self.assertNotIn("armory-profile", html)
            self.assertNotIn("armory-later", html)

    def test_paperdoll_structure_stays(self):
        html = character_sheet(resolve("wotlk"), _character())
        self.assertIn('class="paperdoll"', html)
        self.assertIn('class="doll"', html)
        self.assertIn('class="doll-left"', html)
        self.assertIn('class="doll-main"', html)
        self.assertIn('class="doll-right"', html)
        self.assertIn('class="doll-weapons"', html)
        self.assertIn(
            '<div class="doll-slot"><span class="doll-socket"></span><span class="doll-label">Head</span></div>',
            html,
        )
        self.assertEqual(html.count('class="doll-socket"'), 19)
        wod = character_sheet(resolve("wod"), _character())
        self.assertEqual(wod.count('class="doll-socket"'), 18)
        self.assertIn('class="doll-label">Main Hand', wod)
        self.assertNotIn('class="doll-label">Ranged', wod)

    def test_enchant_and_gem_print_under_the_item_name(self):
        item = {
            "slot": "Head",
            "item_id": 123,
            "name": "Valorous Helm",
            "enchant": "Arcanum of Burning Mysteries",
            "gem": ["Bold Scarlet Ruby", "Rigid Kings Amber"],
        }
        html = character_sheet(resolve("wotlk"), _character([item]))
        head = html.split('class="doll-label">Head', 1)[1].split('class="doll-label">', 1)[0]
        self.assertLess(head.find("Valorous Helm"), head.find("Arcanum of Burning Mysteries"))
        self.assertLess(head.find("Arcanum of Burning Mysteries"), head.find("Bold Scarlet Ruby"))
        self.assertLess(head.find("Bold Scarlet Ruby"), head.find("Rigid Kings Amber"))
        self.assertIn('class="doll-enchant"', head)
        self.assertEqual(head.count('class="doll-gem"'), 2)
        self.assertNotIn('class="doll-socket"', head.split("</div>", 1)[0])

    def test_missing_enchant_and_gem_print_nothing_extra(self):
        plain = {"slot": "Head", "item_id": 123, "name": "Valorous Helm"}
        html = character_sheet(resolve("cata"), _character([plain]))
        self.assertIn("Valorous Helm", html)
        self.assertNotIn("doll-enchant", html)
        self.assertNotIn("doll-gem", html)
        blank = {
            "slot": "Head",
            "item_id": 123,
            "name": "Valorous Helm",
            "enchant": "  ",
            "gem": [],
        }
        quiet = character_sheet(resolve("legion"), _character([blank]))
        self.assertNotIn("doll-enchant", quiet)
        self.assertNotIn("doll-gem", quiet)

    def test_enchant_and_gem_are_escaped(self):
        item = {
            "slot": "Neck",
            "item_id": 9,
            "name": "Amulet",
            "enchant": "<script>",
            "gem": "Red & Blue",
        }
        html = character_sheet(resolve("mop"), _character([item]))
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertIn("Red &amp; Blue", html)

    def test_era_css_stays_under_sheet(self):
        css = (ROOT / "static" / "css" / "armory.css").read_text(encoding="utf-8")
        classic = css.split("div.sheet.armory-classic", 1)[1].split("div.sheet.armory-profile", 1)[0]
        profile = css.split("div.sheet.armory-profile", 1)[1].split("div.sheet.armory-later", 1)[0]
        later = css.split("div.sheet.armory-later", 1)[1]
        self.assertIn('url("/static/img/parchment.jpg")', classic)
        self.assertIn("#120c08", classic)
        self.assertIn(".doll-socket", classic)
        self.assertNotIn("display: none", classic)
        self.assertIn("#111111", profile)
        self.assertIn("#c9a227", profile)
        self.assertIn(".doll-socket", profile)
        self.assertNotIn("display: none", profile)
        self.assertIn("var(--accent", later)
        self.assertNotIn("parchment", later)
        self.assertIn(".doll-socket", later)
        self.assertNotIn("display: none", later)
        self.assertNotIn("visibility: hidden", css)

    def test_wotlk_auction_flag_follows_the_capture(self):
        capture = (ROOT / "references" / "wotlk" / "home.html").read_text(encoding="utf-8")
        self.assertIn('href="http://us.wowarmory.com/auctionhouse/"', capture)
        self.assertTrue(resolve("wotlk").has_auction)
        self.assertFalse(resolve("tbc").has_auction)


if __name__ == "__main__":
    unittest.main()
