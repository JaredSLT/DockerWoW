"""Nav targets for the section pages, and the public copy that must stay off the page."""

import unittest

from wowweb.catalog import resolve
from wowweb.content.news import intro_blurb
from wowweb.html.guide import home_page
from wowweb.html.layout import layout


def shell(exp_id: str) -> str:
    return layout(resolve(exp_id), "Page", "<p>Body</p>")


class ChromeLinkTests(unittest.TestCase):
    def test_support_is_its_own_page(self):
        for exp_id in ("alpha", "vanilla", "cata", "legion", "midnight"):
            self.assertIn('href="/support/"', shell(exp_id))

    def test_legion_nav_opens_story_shop_and_esports(self):
        page = shell("legion")
        self.assertIn('href="/story"', page)
        self.assertIn('href="/shop"', page)
        self.assertIn('href="/esports"', page)
        self.assertNotIn('href="/account/">Shop', page)

    def test_bfa_nav_opens_classic_and_subscribe(self):
        page = shell("bfa")
        self.assertIn('href="/classic">WoW Classic', page)
        self.assertIn('href="/shop">Shop', page)  # references/screenshots/bfa/home-2019-07.jpg
        self.assertNotIn(">Story<", page)

    def test_cata_services_stay_on_the_account_page(self):
        page = shell("cata")
        self.assertIn('href="/account/services">Services', page)
        self.assertNotIn('href="/shop">Services', page)

    def test_mop_and_wod_shop_links(self):
        self.assertIn('href="/shop">Shop', shell("mop"))
        self.assertIn('href="/shop">Shop', shell("wod"))

    def test_screenshot_rail_stops_at_legion(self):
        self.assertIn("ssotd-container", shell("vanilla"))
        self.assertNotIn("ssotd-container", shell("legion"))
        self.assertNotIn("ssotd-container", shell("shadowlands"))
        self.assertNotIn("ssotd-container", shell("dragonflight"))

    def test_public_shell_hides_the_lab_strip(self):
        page = shell("vanilla")
        self.assertNotIn("private-server", page)
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("MariaDB", page)
        dev = layout(resolve("vanilla"), "Page", "<p>Body</p>", dev=True)
        self.assertIn("Not affiliated", dev)

    def test_class_forums_open_their_boards(self):
        vanilla = shell("vanilla")
        self.assertIn("Class Forums", vanilla)
        self.assertNotIn('href="/forums/deathknight"', vanilla)
        self.assertIn('href="/forums/"', shell("wotlk"))

    def test_home_buy_now_opens_the_shop(self):
        page = home_page(resolve("dragonflight"), [], {"up": True})
        self.assertIn('href="/shop"', page)
        self.assertNotIn("from the lab", page)
        self.assertNotIn("recreation", intro_blurb(resolve("vanilla")).lower())
        self.assertNotIn("local lab", intro_blurb(resolve("legion")).lower())


if __name__ == "__main__":
    unittest.main()
