"""July 2019 Battle for Azeroth shell, Rise of Azshara home, forums, and shop."""

import unittest

from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era.bfa import full, home_body, shell, take
from wowweb.html.layout import layout

BANNED = ("private server", "recreation", "mariadb", "not affiliated")


def _ctx(user=None, dev=False):
    return {
        "exp": resolve("bfa"),
        "user": user,
        "dev": dev,
        "qs": {},
        "path": "",
        "labcfg": None,
        "data_dir": None,
    }


def _home(dev=False):
    exp = resolve("bfa")
    realm = {"name": exp.realm_name, "up": True}
    body = home_body(exp, news_for(exp), realm, None)
    return shell(exp, "World of Warcraft", body, None, "World of Warcraft", dev)


class BfaSiteTests(unittest.TestCase):
    def test_home_matches_the_july_2019_hero(self):
        page = _home()
        self.assertIn("RISE OF AZSHARA NOW LIVE!", page)
        self.assertIn("Nazjatar", page)
        self.assertIn("home turf of the naga", page)
        self.assertIn("Benthic", page)
        self.assertIn("Mechagon", page)
        self.assertIn("Rustbolt Resistance", page)
        self.assertIn("Heritage Armor", page)
        self.assertIn("Explore Battle for Azeroth", page)
        self.assertIn(">Buy Now<", page)
        self.assertIn(">Launch Trailer<", page)
        self.assertIn(">52<", page)
        self.assertIn(">03<", page)
        self.assertIn("Global release in", page)
        self.assertIn('href="/classic">WoW Classic', page)
        self.assertIn('href="/shop">Shop', page)
        self.assertIn(">Game<", page)
        self.assertIn(">News<", page)
        self.assertIn(">Forums<", page)
        self.assertIn(">Esports<", page)
        self.assertNotIn(">Story<", page)
        self.assertNotIn('href="/shop">Subscribe', page)
        self.assertNotIn("ssotd-container", page)
        self.assertIn("Tune In July 8 for a Shadowlands Update", page)
        self.assertIn("Battle for Azeroth is Up", page)

    def test_public_home_hides_the_lab_note(self):
        quiet = _home(False).lower()
        for phrase in BANNED:
            self.assertNotIn(phrase, quiet)
        loud = _home(True)
        self.assertIn("Not affiliated", loud)

    def test_interior_shell_keeps_the_july_bar(self):
        page = layout(resolve("bfa"), "Page", "<p>Body</p>")
        self.assertIn("<p>Body</p>", page)
        self.assertIn('href="/classic">WoW Classic', page)
        self.assertIn('href="/shop">Shop', page)
        self.assertNotIn(">Story<", page)
        self.assertNotIn('href="/shop">Subscribe', page)
        self.assertNotIn("Not affiliated", page)

    def test_forums_index_matches_the_2019_categories(self):
        page = full("/forums", _ctx())
        self.assertIn("All Categories", page)
        self.assertIn("Demon Hunter", page)
        self.assertIn("Monk", page)
        self.assertNotIn("Evoker", page)
        self.assertIn('href="/forums/demonhunter"', page)
        self.assertIn('href="/forums/monk"', page)
        self.assertIn('href="/forums/general"', page)
        self.assertIn('href="/forums/islands"', page)
        self.assertIn("©2019", page)
        self.assertIn("Runetotem and Uther", page)
        self.assertNotIn(">Story<", page)
        self.assertNotIn("private server", page.lower())
        self.assertIsNone(full("/wow/news", _ctx()))

    def test_shop_is_the_family_grid(self):
        page = full("/shop", _ctx())
        self.assertIn("Battle for Azeroth", page)
        self.assertIn("Great for new players", page)
        self.assertIn("Complete Collection", page)
        self.assertIn("From €49.99", page)
        self.assertIn('href="/wow/info"', page)
        self.assertNotIn("card number", page.lower())
        self.assertNotIn("cvv", page.lower())
        self.assertNotIn("credit card", page.lower())
        self.assertNotIn("private server", page.lower())

    def test_news_and_logged_out_services_stay_in_the_shell(self):
        title, body = take("/wow/news", _ctx())
        self.assertEqual(title, "News")
        self.assertIn("/wow/news/0", body)
        self.assertIn("Weekly Timewalking Holidays Incoming!", body)
        gate = take("/account/services", _ctx())
        self.assertEqual(gate[0], "Character Services")
        self.assertIn('href="/account/login"', gate[1])
        self.assertIsNone(take("/account/services", _ctx(user="Aldrea")))
        self.assertIsNone(take("/wow/info", _ctx()))


if __name__ == "__main__":
    unittest.main()
