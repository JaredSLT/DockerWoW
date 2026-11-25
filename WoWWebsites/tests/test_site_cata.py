"""Cataclysm shell, home, guide, and forum columns."""

import tempfile
import unittest
from pathlib import Path

from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era import cata
from wowweb.html.guide import home_page
from wowweb.html.layout import layout

_NAV = ("Summary", "Talents & Glyphs", "Auctions", "Events", "Achievements", "Statistics", "Reputation", "PvP", "Activity Feed", "Guild")


def _ctx(path: str, data_dir: Path, qs=None) -> dict:
    return {
        "exp": resolve("cata"),
        "user": None,
        "dev": False,
        "qs": qs or {},
        "path": path,
        "labcfg": None,
        "data_dir": data_dir,
    }


class CataSiteTests(unittest.TestCase):
    def test_shell_tabs_end_in_services(self):
        page = layout(resolve("cata"), "Page", "<p>Body</p>")
        self.assertIn("<p>Body</p>", page)
        self.assertIn('href="/account/services">Services', page)
        self.assertIn('href="/support/"', page)
        self.assertNotIn('href="/shop">Services', page)
        self.assertIn("era-cata.css", page)
        self.assertIn("Cataclysm", page)
        self.assertIn("©2011", page)
        self.assertIn('action="/wow/search"', page)
        self.assertIn('href="/wow/">Home', page)
        self.assertIn('href="/wow/info">Game', page)
        self.assertIn('href="/community">Community', page)
        self.assertIn('href="/wow/media/screenshots">Media', page)
        self.assertIn('href="/forums/">Forums', page)
        order = [page.index(f">{label}<") for label in ("Home", "Game", "Community", "Media", "Forums", "Services")]
        self.assertEqual(order, sorted(order))
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())

    def test_dev_footer_is_opt_in(self):
        quiet = layout(resolve("cata"), "Page", "<p>Body</p>")
        loud = layout(resolve("cata"), "Page", "<p>Body</p>", dev=True)
        self.assertNotIn("Not affiliated", quiet)
        self.assertIn("Not affiliated", loud)

    def test_home_uses_live_news_in_the_late_2011_grid(self):
        exp = resolve("cata")
        news = news_for(exp)
        page = home_page(exp, news, {"up": True, "name": "Cataclysm", "type": "PvE", "population": "Medium"})
        self.assertIn("New Warcraft Art", page)
        self.assertIn("Comic", page)
        self.assertIn('href="/wow/news/0"', page)
        self.assertIn("Play it Free", page)
        self.assertIn('href="/account/create"', page)
        self.assertIn("Mists of Pandaria", page)
        self.assertIn('href="/wow/realmstatus"', page)
        self.assertIn("Cataclysm is Up", page)
        self.assertIn("Next", page)
        self.assertNotIn("private server", page.lower())

    def test_game_guide_keeps_the_crop_labels(self):
        _title, body = cata.take("/wow/info", _ctx("/wow/info", Path(".")))
        self.assertIn("Beginner's Guide", body)
        self.assertIn("Races", body)
        self.assertIn("Dungeons &amp; Raids", body)
        self.assertIn("Professions", body)
        self.assertIn("Factions", body)
        self.assertIn("Worgen", body)
        self.assertIn("Goblin", body)
        self.assertIn("Forsaken", body)
        self.assertIn('href="/wow/info/races/worgen"', body)
        self.assertIn('href="/wow/info/races/undead"', body)
        self.assertIn("Archaeology", body)
        self.assertIn('href="/wow/info/basics"', body)
        self.assertIn("Death Knight", body)
        self.assertNotIn("Pandaren", body)
        self.assertNotIn(">Monk<", body)

    def test_forums_use_live_threads_and_board_columns(self):
        exp = resolve("cata")
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            index_title, index = cata.take("/forums", _ctx("/forums", data))
            self.assertEqual(index_title, "Forums")
            self.assertIn("General Discussion", index)
            self.assertIn("Latest Blizzard Posts", index)
            self.assertIn("Death Knight", index)
            self.assertIn("Welcome to the community forums", index)
            self.assertNotIn("Welcome: Please Read", index)
            self.assertNotIn("Lylirra", index)
            self.assertNotIn("Sageratta", index)
            board = cata.take("/forums/general", _ctx("/forums/general", data))
            self.assertIsNotNone(board)
            title, body = board
            self.assertIn("Forums", title)
            for column in ("Subject", "Author", "Replies", "Views", "Last Poster"):
                self.assertIn(column, body)
            self.assertIn("Welcome to the community forums", body)
            self.assertNotIn("Simple and Advanced Forum Views", body)
            self.assertIsNone(cata.take("/forums/no-such-board", _ctx("/forums/no-such-board", data)))
        self.assertIsNone(cata.full("/wow/", {"exp": exp}))

    def test_profile_nav_and_item_sheet_do_not_invent_stats(self):
        exp = resolve("cata")
        profile = cata.character_body(exp, {
            "name": "Baldibar",
            "level": 85,
            "race": "Blood Elf",
            "class": "Paladin",
            "realm": "Moonglade",
            "achievements": 12,
            "equipment": [],
            "guild": {"name": "Emergence"},
            "online": False,
        })
        for label in _NAV:
            self.assertIn(label.replace("&", "&amp;"), profile)
        self.assertIn("Baldibar", profile)
        self.assertIn("85 Blood Elf Paladin", profile)
        self.assertIn('href="/armory/guild/Emergence"', profile)
        self.assertNotIn("Retribution Paladin", profile)
        self.assertNotIn("7235", profile)
        item = cata.item_body(exp, {
            "name": "Sword of Decay",
            "entry": 1,
            "class": "2",
            "subclass": "7",
            "quality": "2",
            "ItemLevel": 28,
            "RequiredLevel": 23,
            "SellPrice": 4562,
        })
        self.assertIn("Sword of Decay", item)
        self.assertIn("One-Hand", item)
        self.assertIn("Sword", item)
        self.assertIn("Cost and Facts", item)
        self.assertIn("45", item)
        self.assertIn("62", item)
        self.assertNotIn("33 - 62", item)
        self.assertNotIn("Reduces target", item)

    def test_search_page_is_english(self):
        body = cata.search_body(_ctx("/wow/search", Path("."), {"q": [""]}))
        self.assertIn("Search characters, items, forums and more.", body)
        self.assertNotIn("Suchergebnisse", body)


if __name__ == "__main__":
    unittest.main()
