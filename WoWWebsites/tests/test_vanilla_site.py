"""November 2006 vanilla homepage and the shells around it."""

import unittest

from wowweb.catalog import resolve
from wowweb.html.guide import home_page
from wowweb.html.layout import layout
from wowweb.html.vanilla_pages import rewrite, special
from wowweb.html.vanilla_site import captured_html, home_document

HEADLINES = (
    "The Burning Crusade Street Date Announced",
    "New World of Warcraft Fan Art",
    "Gurubashi Screenshot Contest Winners",
    "WoW Comic Contest: Honorable Mentions",
    "New Burning Crusade Screenshots",
    "New World of Warcraft Wallpaper",
    "Burning Crusade Spells and Talents Updated",
    "Fansite Beta Key Contests",
    "WoW 2nd Year Anniversary Sweepstakes",
    "The Burning Crusade F.A.Q. Updated!",
    "Two Year Anniversary Contest Winners",
    "Database Maintenance",
)
MENUS = (
    "menuNews",
    "menuAccount",
    "menuGameGuide",
    "menuInteractive",
    "menuMedia",
    "menuForums",
    "menuCommunity",
    "menuSupport",
)


def _home() -> str:
    return home_document(resolve("vanilla"), [], "/static/img/ssotd-elwynn.jpg", False, None)


class VanillaHomeTests(unittest.TestCase):
    def test_homepage_uses_the_captured_shell(self):
        page = _home()
        self.assertIn("Welcome to the Arena", page)
        self.assertIn("New WoW.com Sneak Peek!", page)
        self.assertIn("Select Realm Transfers", page)
        self.assertIn("4-12-06", page)
        self.assertIn("Shadow of the Necropolis", page)
        self.assertIn("Community Site", page)
        self.assertIn("Class Forums", page)
        self.assertNotIn('href="/forums/deathknight"', page)
        self.assertIn('href="/support/"', page)
        self.assertIn("ssotd-container", page)
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn('id="mainFlash"', page)
        self.assertNotIn("The Burning Crusade Street Date Announced", page)
        self.assertNotIn("/shopsection1", page)
        self.assertNotIn("/wow//wow/", page)
        self.assertNotIn("/forums/thread.html", page)

    def test_dev_footer_is_opt_in(self):
        quiet = _home()
        loud = home_document(resolve("vanilla"), [], "/static/img/ssotd-elwynn.jpg", True, None)
        self.assertNotIn("Not affiliated", quiet)
        self.assertIn("Not affiliated", loud)

    def test_other_eras_keep_their_shell(self):
        for exp_id in ("tbc", "wotlk"):
            page = layout(resolve(exp_id), "Page", "<p>Body</p>")
            self.assertNotIn("/new-hp/css/loader_screen.css", page)
            self.assertNotIn("/static/js/vanilla.js", page)
            self.assertNotIn("news-expand", page)
            self.assertNotIn('class="vanilla', page)
        splash = home_page(resolve("tbc"), [], {"up": True})
        self.assertNotIn("news-expand", splash)
        self.assertNotIn("/new-hp/css/loader_screen.css", splash)

    def test_interior_shell_keeps_the_chrome_contract(self):
        page = layout(resolve("vanilla"), "Page", "<p>Body</p>")
        self.assertIn("<p>Body</p>", page)
        self.assertIn("ssotd-container", page)
        self.assertIn('href="/support/"', page)
        self.assertIn("Class Forums", page)
        self.assertNotIn('href="/forums/deathknight"', page)
        self.assertNotIn("Not affiliated", page)

    def test_old_paths_reach_live_tools_or_a_page(self):
        self.assertEqual(rewrite("/realmstatus"), "/wow/realmstatus")
        self.assertEqual(rewrite("/pvp"), "/wow/pvp/rankings")
        self.assertEqual(rewrite("/info/classes/warrior/talents.html"), "/wow/info/classes/warrior/talents.html")
        self.assertEqual(rewrite("/info/races/nightelf"), "/wow/info/races/nightelf")
        self.assertIsNotNone(special("/loginsupport/password.html"))
        self.assertIsNotNone(special("/info/basics/gettingstarted.html"))
        self.assertIsNone(special("/support/stuck"))
        self.assertIsNone(captured_html("/account"))
        self.assertIsNone(captured_html("/community"))
        self.assertIsNone(captured_html("/ptr"))
        self.assertIsNone(captured_html("/loginsupport"))
        downloads = captured_html("/downloads")
        self.assertIsNotNone(downloads)
        self.assertIn("loader_screen.css", downloads)


if __name__ == "__main__":
    unittest.main()
