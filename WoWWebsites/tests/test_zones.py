import unittest

from wowweb.catalog import resolve
from wowweb.content import professions_for
from wowweb.content.zones import group_zones, zones_for
from wowweb.html import profession_index, profession_page, zone_map


def _names(exp_id: str) -> list[str]:
    return [row["continent"] for row in zones_for(resolve(exp_id))]


class ZoneMapTests(unittest.TestCase):
    def test_vanilla_map_is_eastern_kingdoms_and_kalimdor(self):
        rows = zones_for(resolve("vanilla"))
        self.assertEqual(_names("vanilla"), ["Eastern Kingdoms", "Kalimdor"])
        self.assertEqual(set(rows[0]), {"continent", "zones"})
        self.assertIsInstance(rows[0]["zones"], list)
        body = zone_map(resolve("vanilla"))
        self.assertIn("Eastern Kingdoms", body)
        self.assertIn("Kalimdor", body)
        self.assertLess(body.index("Eastern Kingdoms"), body.index("Kalimdor"))
        self.assertNotIn("Outland", body)
        low = body.casefold()
        self.assertNotIn("flash", low)
        self.assertNotIn("recreation", low)
        self.assertNotIn("private-server", low)
        self.assertNotIn("private server", low)

    def test_tbc_map_adds_outland_without_northrend(self):
        names = _names("tbc")
        self.assertIn("Outland", names)
        self.assertNotIn("Northrend", names)
        body = zone_map(resolve("tbc"))
        self.assertIn("Outland", body)
        self.assertNotIn("Northrend", body)

    def test_midnight_map_has_quelthalas(self):
        self.assertEqual(_names("midnight")[-1], "Quel'Thalas")
        body = zone_map(resolve("midnight"))
        self.assertIn("Quel'Thalas", body)

    def test_continents_arrive_with_the_expansion(self):
        self.assertNotIn("The Maelstrom", _names("wotlk"))
        self.assertIn("The Maelstrom", _names("cata"))
        self.assertNotIn("Pandaria", _names("cata"))
        self.assertIn("Pandaria", _names("mop"))
        self.assertNotIn("Draenor", _names("mop"))
        self.assertIn("Draenor", _names("wod"))
        self.assertNotIn("Broken Isles", _names("wod"))
        self.assertIn("Broken Isles", _names("legion"))
        self.assertNotIn("Kul Tiras", _names("legion"))
        bfa = _names("bfa")
        self.assertIn("Kul Tiras", bfa)
        self.assertIn("Zandalar", bfa)
        self.assertLess(bfa.index("Kul Tiras"), bfa.index("Zandalar"))
        self.assertNotIn("The Shadowlands", bfa)
        self.assertIn("The Shadowlands", _names("shadowlands"))
        self.assertNotIn("Dragon Isles", _names("shadowlands"))
        self.assertIn("Dragon Isles", _names("dragonflight"))
        self.assertNotIn("Khaz Algar", _names("dragonflight"))
        self.assertIn("Khaz Algar", _names("warwithin"))
        self.assertNotIn("Quel'Thalas", _names("warwithin"))

    def test_deepholm_is_a_zone_of_the_maelstrom(self):
        allowed = ["Eastern Kingdoms", "Kalimdor", "The Maelstrom"]
        areas = [
            (1, "Eastern Kingdoms", 0, 0),
            (12, "Elwynn Forest", 0, 0),
            (87, "Goldshire", 0, 12),
            (646, "Deepholm", 646, 0),
            (5034, "Temple of Earth", 646, 646),
            (999, "Mechagon", 999, 0),
            (530, "Hellfire Peninsula", 530, 0),
        ]
        maps = {
            0: "Eastern Kingdoms",
            530: "Outland",
            646: "Deepholm",
            999: "Mechagon City",
        }
        grouped = group_zones(areas, maps, allowed)
        self.assertEqual(grouped["Eastern Kingdoms"], ["Elwynn Forest"])
        self.assertEqual(grouped["Kalimdor"], [])
        self.assertEqual(grouped["The Maelstrom"], ["Deepholm"])
        self.assertNotIn("Hellfire Peninsula", grouped["Eastern Kingdoms"])

    def test_zone_parented_to_the_continent_area_is_kept(self):
        areas = [
            (44, "Eastern Kingdoms", 0, 0),
            (12, "Elwynn Forest", 0, 44),
            (87, "Goldshire", 0, 12),
        ]
        grouped = group_zones(areas, {0: "Eastern Kingdoms"}, ["Eastern Kingdoms"])
        self.assertEqual(grouped["Eastern Kingdoms"], ["Elwynn Forest"])


class ProfessionPageTests(unittest.TestCase):
    def test_jewelcrafting_page_starts_in_tbc(self):
        self.assertIsNone(profession_page(resolve("vanilla"), "jewelcrafting"))
        page = profession_page(resolve("tbc"), "jewelcrafting")
        self.assertIsNotNone(page)
        desc = dict(professions_for(resolve("tbc")))["Jewelcrafting"]
        self.assertIn("<h2>Jewelcrafting</h2>", page)
        self.assertIn(desc, page)

    def test_first_aid_page_is_gone_in_bfa(self):
        self.assertIsNone(profession_page(resolve("bfa"), "firstaid"))

    def test_index_links_one_slug_per_profession(self):
        vanilla = profession_index(resolve("vanilla"))
        self.assertIn('href="/wow/info/professions/firstaid"', vanilla)
        self.assertNotIn("/wow/info/professions/jewelcrafting", vanilla)
        tbc = profession_index(resolve("tbc"))
        self.assertIn('href="/wow/info/professions/jewelcrafting"', tbc)
        self.assertNotIn("firstaid", profession_index(resolve("bfa")).lower())


if __name__ == "__main__":
    unittest.main()
