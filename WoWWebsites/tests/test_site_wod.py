"""February 2015 Warlords community shell."""

import unittest

from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era import wod
from wowweb.html.forums import forum_board
from wowweb.html.guide import home_page
from wowweb.html.layout import layout

NAV = (
    'href="/wow/"',
    'href="/wow/news"',
    'href="/wow/info"',
    'href="/wow/realmstatus"',
    'href="/forums/"',
    'href="/forums/general"',
    'href="/shop">Shop',
    'href="/account/login"',
    'href="/account/create"',
    'href="/account/"',
    'href="/account/services"',
    'href="/support/"',
    'href="/story"',
    'href="/armory/"',
)


def _home(dev=False, realm=None):
    exp = resolve("wod")
    status = {"name": "Warlords of Draenor", "up": True}
    if realm:
        status.update(realm)
    body = home_page(exp, news_for(exp), status)
    return layout(exp, "World of Warcraft", body, crumb="World of Warcraft", dev=dev)


class WodSiteTests(unittest.TestCase):
    def test_home_uses_the_february_shell(self):
        page = _home()
        self.assertIn("Warlords of Draenor", page)
        self.assertIn(">Home<", page)
        self.assertIn(">Game Guide<", page)
        self.assertIn(">Community<", page)
        self.assertIn(">Media<", page)
        self.assertIn(">Forums<", page)
        self.assertIn('href="/shop">Shop', page)
        self.assertIn("Expansion Set", page)
        self.assertIn("Available Now", page)
        self.assertIn(">Upgrade<", page)
        self.assertIn("Play Free Now", page)
        self.assertIn("Starter Edition", page)
        self.assertIn("Search characters, items, forums and more", page)
        self.assertIn("Log in now", page)
        self.assertIn("to enhance and personalize your experience", page)
        self.assertIn("Stay Connected", page)
        self.assertIn("New Expansion Info", page)
        self.assertIn(">Up<", page)
        self.assertIn("Blackrock Foundry Raid Schedule", page)
        self.assertIn("From the Forge", page)
        self.assertIn("Grommash Hellscream", page)
        self.assertIn("12/17/2014", page)
        self.assertIn("11/13/2014", page)
        self.assertIn("Unleashed", page)
        self.assertIn('href="/wow/news/0"', page)
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("recreation", page.lower())
        self.assertNotIn("mariadb", page.lower())
        self.assertNotIn("ssotd-container", page)

    def test_realm_error_stays_off_the_home(self):
        page = _home(realm={"up": False, "error": "MariaDB unreachable"})
        self.assertNotIn("MariaDB", page)
        self.assertNotIn("mariadb", page.lower())
        self.assertIn(">Down<", page)

    def test_dev_footer_is_opt_in(self):
        self.assertNotIn("Not affiliated", _home())
        self.assertIn("Not affiliated", _home(dev=True))

    def test_shell_keeps_the_shop_tab_and_nav_targets(self):
        page = layout(resolve("wod"), "Page", "<p>Body</p>")
        self.assertIn("<p>Body</p>", page)
        self.assertIn('href="/shop">Shop', page)
        for href in NAV:
            self.assertIn(href, page)
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("private server", page.lower())

    def test_shop_is_the_two_card_shelf(self):
        taken = wod.take("/shop", {"exp": resolve("wod")})
        self.assertIsNotNone(taken)
        title, body = taken
        page = layout(resolve("wod"), title, body, crumb=title)
        self.assertIn("Games and Subscriptions", body)
        self.assertIn("Warlords of Draenor (Expansion)", body)
        self.assertIn(">Buy<", body)
        self.assertIn("Try Free", body)
        self.assertIn("Free Services", body)
        self.assertIn("Character Services", body)
        self.assertIn("Recruit a Friend", body)
        self.assertIn("Faction Change", body)
        self.assertNotIn("<form", body.lower())
        self.assertNotIn("card number", body.lower())
        self.assertNotIn("cvv", body.lower())
        self.assertIn('href="/shop">Shop', page)
        self.assertIn("wod-tab-on", page)
        self.assertIsNone(wod.take("/wow/info", {}))
        self.assertIsNone(wod.full("/shop", {}))

    def test_guild_board_columns_are_not_hardcoded_threads(self):
        body = forum_board("Guild Recruitment", "guilds", [], None)
        page = layout(resolve("wod"), "Guild Recruitment", body)
        for column in ("Subject", "Author", "Replies", "Views", "Last Post"):
            self.assertIn(column, page)
        self.assertIn("Guild Recruitment", page)
        self.assertIn("Forums", page)
        self.assertIn("Community", page)
        self.assertNotIn("Please Do Not Bump Threads", page)
        self.assertNotIn("Asmongold", page)

    def test_signed_in_plate_uses_the_account(self):
        page = layout(resolve("wod"), "Forums", "<div class='forums forum-index'></div>", user="Aldrea")
        self.assertIn("Aldrea", page)
        self.assertIn('href="/account/logout"', page)
        self.assertNotIn("Log in now", page)
        self.assertIn('href="/shop">Shop', page)


if __name__ == "__main__":
    unittest.main()
