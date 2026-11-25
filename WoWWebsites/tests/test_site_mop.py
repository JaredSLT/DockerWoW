"""November 2013 Mists shell: Shop tab, anniversary home, realm columns, shop."""

import unittest

from wowweb.catalog import resolve
from wowweb.html.armory import character_sheet
from wowweb.html.era import mop
from wowweb.html.guide import home_page
from wowweb.html.layout import layout

BANNED = ("private server", "recreation", "mariadb", "not affiliated")


def _home() -> str:
    exp = resolve("mop")
    body = home_page(exp, [], {"up": True, "name": exp.realm_name})
    return layout(exp, "World of Warcraft", body, crumb="World of Warcraft")


class MopSiteTests(unittest.TestCase):
    def test_shell_shop_tab_is_not_services(self):
        page = layout(resolve("mop"), "Page", "<p>Body</p>")
        self.assertIn('href="/shop">Shop', page)
        self.assertIn(">Home<", page)
        self.assertIn(">Game Guide<", page)
        self.assertIn(">Community<", page)
        self.assertIn(">Media<", page)
        self.assertIn(">Forums<", page)
        self.assertNotIn(">Services<", page)
        self.assertIn('href="/wow/realmstatus"', page)
        self.assertIn('href="/forums/general"', page)
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())

    def test_home_is_the_november_2013_anniversary(self):
        page = _home()
        self.assertIn("Happy Anniversary! World of Warcraft Celebrates 9 Years", page)
        self.assertIn("Exclusive Charity Bundle", page)
        self.assertIn("Make-A-Wish", page)
        self.assertIn("5.4 Hotfixes: November 21", page)
        self.assertIn("Siege of Orgrimmar", page)
        self.assertIn("Starter Edition", page)
        self.assertIn("Play Free Now", page)
        self.assertIn("WoW Source: Warlords of Draenor", page)
        self.assertNotIn("Warlords of Draenor Zone Preview", page)
        self.assertNotIn("Garrison Preview", page)
        self.assertNotIn(">Services<", page)
        self.assertIn('href="/shop">Shop', page)
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())

    def test_news_stays_on_the_november_posts(self):
        title, body = mop.take("/wow/news/3", {"exp": resolve("mop"), "dev": False})
        self.assertIn("5.4 Hotfixes", title)
        self.assertIn("Siege of Orgrimmar", body)
        self.assertNotIn("Zone Preview", body)
        index_title, index = mop.take("/wow/news", {"exp": resolve("mop")})
        self.assertIn("November 2013", index)
        self.assertEqual(index_title, "News")
        self.assertNotIn("Nagrand", index)

    def test_realm_status_columns(self):
        page = mop.realm_body(
            resolve("mop"),
            {"name": "Mists of Pandaria", "up": True, "type": "Normal", "population": "0", "error": ""},
            False,
        )
        for column in ("Status", "Realm Name", "Type", "Population", "Locale", "Queue"):
            self.assertIn(column, page)
        self.assertIn("Mists of Pandaria", page)
        self.assertIn("(PvE)", page)
        self.assertIn("English", page)
        self.assertIn(">Low<", page)
        self.assertIn(">Up<", page)
        quiet = mop.realm_body(
            resolve("mop"),
            {"name": "Mists of Pandaria", "up": False, "type": "", "population": "", "error": "MariaDB unreachable"},
            False,
        )
        self.assertNotIn("MariaDB", quiet)
        self.assertNotIn("mariadb", quiet.lower())
        loud = mop.realm_body(
            resolve("mop"),
            {"name": "Mists of Pandaria", "up": False, "type": "", "population": "", "error": "MariaDB unreachable"},
            True,
        )
        self.assertIn("MariaDB", loud)

    def test_shop_is_the_battle_net_shelf(self):
        page = mop.full("/shop", {"exp": resolve("mop"), "dev": False})
        self.assertIn("Battle.net Shop", page)
        self.assertIn("Evil is in its Prime", page)
        self.assertIn("Diablo", page)
        self.assertIn("Hearthstone", page)
        self.assertIn("Heart of the Swarm", page)
        self.assertIn("World of Warcraft", page)
        self.assertNotIn("<form", page.lower())
        self.assertNotIn("card number", page.lower())
        self.assertNotIn("cvv", page.lower())
        self.assertIsNone(mop.full("/wow/", {"exp": resolve("mop"), "dev": False}))
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())

    def test_services_form_keeps_its_post_and_shows_the_transfer_price(self):
        body = (
            "<h2>Character Services</h2>"
            "<form method='post' action='/account/services/name' class='acct-form'>"
            "<input name='name'></form>"
        )
        page = layout(resolve("mop"), "Character Services", body, user="Aldrea", crumb="Character Services")
        self.assertIn("action='/account/services/name'", page)
        self.assertIn("name='name'", page)
        self.assertIn("COST: $25.00 USD", page)
        self.assertIn("Select a character to continue", page)
        self.assertIn("Character Transfer", page)
        self.assertIn("Mists of Pandaria", page)
        self.assertNotIn("card number", page.lower())
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())

    def test_level_90_profile_uses_the_community_shell(self):
        exp = resolve("mop")
        char = {
            "name": "Aldrea",
            "level": 90,
            "race": "Pandaren",
            "class": "Monk",
            "online": 0,
            "money_text": "0g",
            "realm": exp.realm_name,
            "equipment": [],
            "achievements": 3,
        }
        page = layout(exp, char["name"], character_sheet(exp, char), crumb=char["name"])
        self.assertIn("Level 90", page)
        self.assertIn("Pandaren", page)
        self.assertIn("Monk", page)
        self.assertIn("Ranged", page)
        self.assertIn('href="/shop">Shop', page)
        self.assertIn("armory-profile", page)
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())


if __name__ == "__main__":
    unittest.main()
