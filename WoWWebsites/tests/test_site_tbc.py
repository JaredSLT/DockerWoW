"""Burning Crusade community shell, forum index, and Armory sheet."""

import tempfile
import unittest
from pathlib import Path

from wowweb.catalog import resolve
from wowweb.html.era import tbc
from wowweb.html.layout import layout

_REBUILT = (
    "Welcome, Please Read!",
    "Warcraft Weekly",
    "Brand New Realms",
    "Flamingcow",
    "Arena Tournament Information Page Released",
)


class TbcSiteTests(unittest.TestCase):
    def setUp(self):
        self.exp = resolve("tbc")

    def test_community_shell_matches_the_2007_menu(self):
        page = tbc.shell(self.exp, "Page", "<p>Body</p>", None, "", False)
        self.assertIn("<p>Body</p>", page)
        self.assertIn("/static/css/era-tbc.css", page)
        self.assertIn("WorldofWarcraft.com", page)
        self.assertIn("The Armory", page)
        self.assertIn(">Forums<", page)
        self.assertIn('href="/support/"', page)
        self.assertIn("Quick Links", page)
        self.assertIn("Screenshot of the Day", page)
        self.assertIn("ssotd-container", page)
        for label in (
            "News",
            "Account",
            "Game Guide",
            "Workshop",
            "Media",
            "Forums",
            "Community",
            "Support",
            "Getting Started",
            "Burning Crusade",
            "Wrath of the Lich King",
            "Previous Patches",
            "Talent Calculators",
            "Parental Controls",
            "Realm Status",
            "Guild Relations",
        ):
            self.assertIn(label, page, label)
        self.assertNotIn('href="/forums/deathknight"', page)
        self.assertNotIn('class="vanilla', page)
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("MariaDB", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("recreation", page.lower())
        loud = tbc.shell(self.exp, "Page", "<p>Body</p>", None, "", True)
        self.assertIn("Not affiliated", loud)

    def test_layout_uses_the_era_shell(self):
        page = layout(self.exp, "Page", "<p>Body</p>")
        self.assertIn("era-tbc.css", page)
        self.assertIn("WorldofWarcraft.com", page)
        self.assertNotIn("news-expand", page)
        self.assertNotIn("/static/js/vanilla.js", page)

    def test_home_is_parchment_news(self):
        body = tbc.home_body(self.exp, [], {"up": True, "name": "The Burning Crusade"}, None)
        self.assertIn("tbc-post", body)
        self.assertIn("World of Warcraft Arena in College Gaming League", body)
        self.assertIn("Posted by: Nebu", body)
        self.assertIn("08-28-08", body)
        self.assertNotIn("news-expand", body)
        self.assertNotIn("recreation", body.lower())
        page = tbc.shell(self.exp, "Community", body, None, "", False)
        self.assertIn("tbc-parch", page)
        self.assertIn("Screenshot of the Day", page)

    def test_upgrade_receipt(self):
        doc = tbc.full(
            "/account/burning-crusade-upgrade.html",
            {"exp": self.exp, "user": None, "dev": False, "qs": {}, "path": "", "labcfg": None, "data_dir": None},
        )
        self.assertIn("Upgrade Your Account", doc)
        self.assertIn("Account Upgraded", doc)
        self.assertIn("The Burning Crusade", doc)
        self.assertIn("Outland", doc)
        self.assertIn('href="/support/"', doc)
        self.assertIn("Game Guide", doc)
        self.assertNotIn("Not affiliated", doc)
        self.assertIsNone(tbc.full("/wow/", {"exp": self.exp, "dev": False}))

    def test_forums_index_and_board_do_not_rebuild_threads(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = {
                "exp": self.exp,
                "user": None,
                "dev": False,
                "qs": {},
                "path": "/forums",
                "labcfg": None,
                "data_dir": Path(tmp),
            }
            title, body = tbc.take("/forums", ctx)
            page = tbc.shell(self.exp, title, body, None, "", False)
            self.assertIn("Forum Community", page)
            self.assertIn("2008", page)
            self.assertIn("General Discussion", page)
            self.assertIn('href="/forums/general"', page)
            self.assertIn("Classes", page)
            self.assertIn('href="/forums/realm"', body)
            title, board = tbc.take("/forums/general", ctx)
            self.assertIn("Subject", board)
            self.assertIn("Author", board)
            self.assertIn("Replies", board)
            self.assertIn("Views", board)
            self.assertIn("Last Post", board)
            self.assertIn('name="identity"', board)
            self.assertIn('name="password"', board)
            for banned in _REBUILT:
                self.assertNotIn(banned, board)
            relations = tbc.take("/forums/guildrelations", ctx)
            self.assertIsNotNone(relations)
            self.assertIn("Guild Relations", relations[1])

    def test_armory_search_table_and_talent_trees(self):
        html = tbc.search_markup(
            self.exp,
            [{"name": "Paprika", "level": 70, "race": "Human", "class": "Mage", "realm": "The Burning Crusade"}],
            "paprika",
        )
        for column in ("Name", "Level", "Race", "Class", "Faction", "Guild", "Realm"):
            self.assertIn(column, html)
        self.assertIn("Paprika", html)
        self.assertIn("Alliance", html)
        self.assertIn("tbc-armory", html)
        self.assertNotIn("MariaDB", html)
        title, landing = tbc.take(
            "/armory/character",
            {"exp": self.exp, "user": None, "dev": False, "qs": {}, "path": "/armory/character", "labcfg": None, "data_dir": None},
        )
        self.assertEqual(title, "The Armory")
        self.assertIn("Search", landing)
        char = {
            "name": "Vip",
            "level": 70,
            "race": "Gnome",
            "class": "Warlock",
            "realm": "Bloodscalp",
            "guild": {"name": "Substance"},
            "equipment": [],
        }
        sheet = tbc.character_markup(
            self.exp,
            char,
            "talents",
            {"name": "Substance", "members": [{"name": "Vip", "level": 70, "class": "Warlock"}]},
        )
        for tab in ("Character Sheet", "Reputation", "Skills", "Talents", "Arena Teams", "Guild"):
            self.assertIn(tab, sheet)
        self.assertIn("Affliction", sheet)
        self.assertIn("Demonology", sheet)
        self.assertIn("Destruction", sheet)
        self.assertIn("tbc-trees", sheet)
        self.assertIn("Guild Roster", sheet)
        self.assertIn("Substance", sheet)
        self.assertIn('class="is-on"', sheet)
        profile = tbc.character_markup(self.exp, char, "guild", {"name": "Substance", "members": []})
        self.assertIn("Profile", profile)
        self.assertIn("Resistances", profile)
        self.assertIn("Base Stats", profile)

    def test_missing_pages_stay_on_the_community_chrome(self):
        ctx = {"exp": self.exp, "user": None, "dev": False, "qs": {}, "path": "/wow/news", "labcfg": None, "data_dir": None}
        title, news = tbc.take("/wow/news", ctx)
        self.assertEqual(title, "Archived News")
        self.assertIn("tbc-post", news)
        self.assertIsNone(tbc.take("/wow/info", ctx))
        self.assertIsNone(tbc.take("/armory/item/123", ctx))
        gate = tbc.take("/account/services", ctx)
        self.assertIn("Log In", gate[1])
        signed = dict(ctx)
        signed["user"] = "Aldrea"
        self.assertIsNone(tbc.take("/account/services", signed))
        realm = tbc.take("/wow/realmstatus", ctx)
        self.assertIn("Realm Status", realm[1])
        self.assertNotIn("MariaDB", realm[1])


if __name__ == "__main__":
    unittest.main()
