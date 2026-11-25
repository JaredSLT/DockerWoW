"""March 2010 Wrath community shell, forums, Armory, and the expansion splash."""

import tempfile
import unittest
from pathlib import Path

from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era import wotlk
from wowweb.html.guide import home_page
from wowweb.html.layout import layout
from wowweb.lab import LabConfig


def _ctx(path: str, data_dir: Path, **extra) -> dict:
    payload = {
        "exp": resolve("wotlk"),
        "user": None,
        "dev": False,
        "qs": {},
        "path": path,
        "labcfg": LabConfig(root=Path("/tmp/wowweb-wotlk-test")),
        "data_dir": data_dir,
    }
    payload.update(extra)
    return payload


class WotlkSiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _home(self, dev: bool = False) -> str:
        exp = resolve("wotlk")
        body = home_page(exp, news_for(exp), {"up": True, "name": exp.realm_name})
        return layout(exp, "World of Warcraft Community Site", body, dev=dev)

    def test_march_2010_home_chrome(self):
        page = self._home()
        self.assertIn("PrintWarcraft.com Custom Poster Contest Week Three", page)
        self.assertIn("3-5-10", page)
        self.assertIn("Fall of the Lich King", page)
        self.assertIn("Gift World of Warcraft", page)
        self.assertIn("Cataclysm", page)
        self.assertIn("Wrath of Lich King", page)
        self.assertIn("WorldofWarcraft.com", page)
        self.assertIn("The Armory", page)
        self.assertIn('href="/forums/"', page)
        self.assertIn('href="/wrath"', page)
        self.assertIn('href="/account/services"', page)
        self.assertIn(news_for(resolve("wotlk"))[0][0], page)
        self.assertIn("is Up", page)
        self.assertNotIn("MariaDB", page)
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("news-expand", page)
        self.assertNotIn('class="vanilla', page)

    def test_dev_footer_is_opt_in(self):
        self.assertNotIn("Not affiliated", self._home(False))
        self.assertIn("Not affiliated", self._home(True))

    def test_news_and_realm_stay_live(self):
        ctx = _ctx("/wow/news", self.data)
        title, body = wotlk.take("/wow/news", ctx)
        self.assertEqual(title, "Archived News")
        self.assertIn(news_for(resolve("wotlk"))[0][0], body)
        self.assertNotIn("mariadb", body.lower())
        realm = wotlk.take("/wow/realmstatus", ctx)
        self.assertIsNotNone(realm)
        self.assertIn("Realm Status", realm[1])
        self.assertNotIn("mariadb", realm[1].lower())
        self.assertIsNone(wotlk.take("/account/services", dict(ctx, user="Aldrea")))
        guest = wotlk.take("/account/services", ctx)
        self.assertIn('href="/account/login"', guest[1])

    def test_forums_index_and_board_columns(self):
        ctx = _ctx("/forums", self.data)
        index = wotlk.full("/forums", ctx)
        self.assertIn("Forums Index", index)
        self.assertIn("Welcome to the official World of Warcraft forums!", index)
        self.assertIn("©2009", index)
        self.assertIn("General Discussion", index)
        self.assertIn("Cataclysm", index)
        self.assertIn('class="fi-cols"', index)
        self.assertIn('href="/forums/general"', index)
        self.assertIn('href="/forums/"', index)
        board = wotlk.full("/forums/general", ctx)
        for column in ("Subject", "Author", "Replies", "Views", "Last Post"):
            self.assertIn(f"<th>{column}</th>", board)
        self.assertIn("Welcome to the community forums", board)
        self.assertNotIn("Key forum rules", board)
        self.assertNotIn("Account-Wide Death Knight Creation", board)

    def test_armory_home_search_and_profile_labels(self):
        ctx = _ctx("/armory", self.data)
        home = wotlk.full("/armory", ctx)
        self.assertIn("The Armory", home)
        self.assertIn('name="q"', home)
        self.assertIn("1/13/2010", home)
        self.assertIn('href="/forums/"', home)
        self.assertNotIn("mariadb", home.lower())
        sheet = wotlk.character_markup(
            resolve("wotlk"),
            {
                "name": "Symphdk",
                "level": 80,
                "race": "Blood Elf",
                "class": "Death Knight",
                "realm": "Stormrage",
                "guild": {"name": "Atma Weapon"},
                "achievements": 4,
                "equipment": [
                    {"slot": "Head", "item_id": 32, "name": "Test Helm", "display_id": 0},
                ],
            },
        )
        self.assertIn("Profile", sheet)
        self.assertIn("Talents and Glyphs", sheet)
        self.assertIn('href="/wow/info/classes/deathknight/talents.html"', sheet)
        self.assertIn('href="/armory/guild/Atma%20Weapon"', sheet)
        self.assertIn('href="/armory/item/32"', sheet)
        for label in ("Strength", "Agility", "Stamina", "Intellect", "Spirit"):
            self.assertIn(label, sheet)
        self.assertIn("Last Updated", sheet)
        self.assertIn("Blood", sheet)

    def test_expansion_splash_and_portal_are_not_the_home(self):
        ctx = _ctx("/wrath", self.data)
        wrath = wotlk.full("/wrath", ctx)
        self.assertIn("Death Knight", wrath)
        self.assertIn("Northrend", wrath)
        self.assertIn(">Features<", wrath)
        self.assertIn('href="/forums/"', wrath)
        self.assertIn("2008", wrath)
        self.assertNotIn("PrintWarcraft", wrath)
        self.assertNotIn("wlk-menu", wrath)
        portal = wotlk.full("/bnet", ctx)
        self.assertIn("Battle.net Account", portal)
        self.assertIn("Classic Community Site", portal)
        self.assertIn("Classic Forums", portal)
        self.assertIn('href="/wow/"', portal)
        self.assertIn('href="/forums/"', portal)
        self.assertIn("2009", portal)
        self.assertNotIn("PrintWarcraft", portal)
        self.assertIsNone(wotlk.full("/wow/info", ctx))

    def test_account_login_uses_battle_net_chrome(self):
        from wowweb.account_ui import wotlk as acct

        exp = resolve("wotlk")
        login = layout(exp, "Log In", acct.render(
            exp, user="", error="", notice="", mode="login", email="", characters=[],
            login_kind="account", separate_game_name=False,
        ))
        self.assertIn("Account Login", login)
        self.assertIn("era-wotlk-account", login)
        self.assertIn('href="/forums/"', login)
        self.assertNotIn("wlk-menu", login)
        create = layout(exp, "Create Account", acct.render(
            exp, user="", error="", notice="", mode="create", email="", characters=[],
            login_kind="account", separate_game_name=False,
        ))
        self.assertIn("era-wotlk-signup", create)
        self.assertNotIn("era-wotlk-account", create)
        self.assertNotIn('type="email"', create)


if __name__ == "__main__":
    unittest.main()
