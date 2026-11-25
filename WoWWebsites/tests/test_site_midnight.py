"""October 2026 Midnight community pages."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era import midnight
from wowweb.html.guide import home_page
from wowweb.html.layout import layout


def _page(body: str, dev: bool = False) -> str:
    return layout(resolve("midnight"), "Page", body, dev=dev)


class MidnightSiteTests(unittest.TestCase):
    def test_home_is_the_october_masthead_and_forever_hero(self):
        exp = resolve("midnight")
        page = _page(home_page(exp, news_for(exp), {"up": True, "name": "Midnight"}))
        self.assertIn("Explore an Azeroth Reborn", page)
        self.assertIn("Game Versions", page)
        self.assertIn(">Armory<", page)
        self.assertIn("Try Free", page)
        self.assertIn("Subscribe Now", page)
        self.assertIn('href="/support/"', page)
        self.assertIn("Midnight's 12.1.5 Content Update is Now Live", page)
        self.assertIn("Curse of Ula", page)
        self.assertNotIn("289985", page)
        self.assertNotIn("Game Info", page)
        low = page.lower()
        self.assertNotIn("private server", low)
        self.assertNotIn("recreation", low)
        self.assertNotIn("mariadb", low)
        self.assertNotIn("not affiliated", low)

    def test_dev_note_is_opt_in(self):
        quiet = _page("<p>Body</p>")
        loud = _page("<p>Body</p>", dev=True)
        self.assertNotIn("Not affiliated", quiet)
        self.assertIn("Not affiliated", loud)

    def test_news_classes_races_housing_and_shop(self):
        exp = resolve("midnight")
        ctx = {"exp": exp, "user": None, "dev": False, "qs": {}, "path": "", "labcfg": None, "data_dir": None}
        _title, news = midnight.take("/wow/news", ctx)
        self.assertIn("Hotfixes", news)
        self.assertIn(news_for(exp)[0][0], news)
        _title, classes = midnight.take("/wow/info/classes", ctx)
        self.assertIn("Classes", classes)
        self.assertIn("TANK, DAMAGE", classes)
        self.assertIn("Evoker", classes)
        self.assertIn("For as long as war has raged", classes)
        _title, races = midnight.take("/wow/info/races", ctx)
        self.assertIn("Denizens of Azeroth", races)
        self.assertIn("For the Horde", races)
        self.assertIn("Haranir", races)
        self.assertIn("Dracthyr", races)
        _title, housing = midnight.take("/housing", ctx)
        self.assertIn("Player Housing", housing)
        _title, shop = midnight.take("/shop", ctx)
        self.assertIn("World of Warcraft: Forever", shop)
        self.assertIn("World of Warcraft: Midnight", shop)
        self.assertIn("Subscription", shop)
        self.assertIn("Level 80", shop)
        self.assertIn("$60.00", shop)
        self.assertIn('href="/support/"', shop)
        self.assertNotIn("289985", shop)

    def test_forums_status_and_services_heading(self):
        exp = resolve("midnight")
        with TemporaryDirectory() as tmp:
            ctx = {
                "exp": exp,
                "user": None,
                "dev": False,
                "qs": {},
                "path": "/forums",
                "labcfg": None,
                "data_dir": Path(tmp),
            }
            _title, index = midnight.take("/forums", ctx)
            self.assertIn("Categories", index)
            self.assertIn("Gameplay", index)
            self.assertIn('href="/forums/general"', index)
            _title, board = midnight.take("/forums/general", ctx)
            self.assertIn("Topic", board)
            self.assertIn("Author", board)
            self.assertIn("Replies", board)
            self.assertIn("Views", board)
            self.assertIn("Activity", board)
            self.assertIn("General Discussion", board)
        ctx = {
            "exp": exp,
            "user": None,
            "dev": False,
            "qs": {},
            "path": "/account/services",
            "labcfg": None,
            "data_dir": None,
        }
        _title, services = midnight.take("/account/services", ctx)
        self.assertIn("Character and Guild Services", services)
        self.assertIn('href="/account/login"', services)

    def test_profile_tabs_use_the_character_record(self):
        exp = resolve("midnight")
        page = midnight.character_profile(
            exp,
            {
                "name": "Anhag",
                "level": 90,
                "race": "Earthen",
                "class": "Warrior",
                "realm": "Area 52",
                "achievements": 3,
                "equipment": [{"slot": "Head", "item_id": 1, "name": "Visor of the Predator"}],
                "guild": {"name": "Afterlife"},
            },
            "character",
        )
        self.assertIn("Anhag", page)
        self.assertIn("Character", page)
        self.assertIn("Achievements", page)
        self.assertIn("Collections", page)
        self.assertIn("Dungeons &amp; Raids", page)
        self.assertIn("Player vs Player", page)
        self.assertIn("Reputation", page)
        self.assertIn("Visor of the Predator", page)
        self.assertNotIn("30375", page)
        self.assertNotIn("289985", page)


if __name__ == "__main__":
    unittest.main()
