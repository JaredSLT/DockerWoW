"""April 2006 community shell, forum board, account summary, and creation receipt."""

import unittest

from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era.vanilla import full, home_body, shell, take
from wowweb.html.layout import layout
from wowweb.html.vanilla_site import home_document
from wowweb.account_ui.vanilla import render


def _ctx(**extra):
    payload = {"exp": resolve("vanilla"), "user": None, "dev": False, "qs": {}, "path": "/"}
    payload.update(extra)
    return payload


class VanillaSiteTests(unittest.TestCase):
    def test_home_is_the_april_community_page(self):
        page = home_document(resolve("vanilla"), [], "/static/img/ssotd-elwynn.jpg", False, None)
        for text in (
            "World of Warcraft Community Site",
            "Welcome to the Arena",
            "New WoW.com Sneak Peek!",
            "Select Realm Transfers",
            "4-12-06",
            "Shadow of the Necropolis",
            "Class Forums",
            "Game Guide",
            "Workshop",
            "Screenshot of the Day",
        ):
            self.assertIn(text, page)
        self.assertIn('href="/support/"', page)
        self.assertIn("ssotd-container", page)
        self.assertNotIn('href="/forums/deathknight"', page)
        self.assertNotIn("The Burning Crusade Street Date Announced", page)
        self.assertNotIn("private-server", page)
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("MariaDB", page)

    def test_live_news_does_not_replace_the_april_home(self):
        body = home_body(resolve("vanilla"), news_for(resolve("vanilla")), {"up": True}, None)
        self.assertIn("4-12-06", body)
        self.assertNotIn("The Burning Crusade Street Date Announced", body)

    def test_menu_order_matches_the_home(self):
        page = shell(resolve("vanilla"), "Page", "<p>Body</p>", None, "", False)
        pos = -1
        for label in (
            "News",
            "Account",
            "Game Guide",
            "Workshop",
            "Media",
            "Forums",
            "Community",
            "Support",
        ):
            found = page.find(f"<span>{label}</span>")
            self.assertGreater(found, pos, label)
            pos = found
        self.assertIn('class="v-sec v-sec-guide" open', page)
        self.assertIn('class="v-sec v-sec-workshop" open', page)
        self.assertIn('class="v-sec v-sec-forums" open', page)
        self.assertNotIn('class="v-sec v-sec-news" open', page)
        for href in (
            'href="/wow/"',
            'href="/wow/news"',
            'href="/forums/general"',
            'href="/forums/"',
            'href="/wow/realmstatus"',
            'href="/account/login"',
            'href="/account/create"',
            'href="/story"',
            'href="/wow/info/races"',
            'href="/wow/info/classes/"',
            'href="/wow/pvp/rankings"',
            'href="/wow/media/screenshots"',
        ):
            self.assertIn(href, page)
        self.assertNotIn('href="/forums/deathknight"', page)

    def test_interior_keeps_one_masthead(self):
        page = layout(resolve("vanilla"), "Realm Status", "<p>Realm status</p>")
        self.assertIn("World of Warcraft Community Site", page)
        self.assertIn("<p>Realm status</p>", page)
        self.assertIn("ssotd-container", page)
        self.assertEqual(page.count("v-header"), 1)

    def test_receipt_is_a_separate_document(self):
        page = full("/account/completed", _ctx(user="Aldrea"))
        self.assertIn("Account Creation Complete", page)
        self.assertIn("Account Creation", page)
        self.assertIn("Please print this page", page)
        self.assertIn("Getting Started page", page)
        self.assertIn("1 Month Recurring - $14.99", page)
        self.assertIn("signup.worldofwarcraft.com/completed.html", page)
        self.assertIn("Aldrea", page)
        self.assertNotIn("tarou9876", page)
        self.assertNotIn("Hamamatsu", page)
        self.assertNotIn("v-menu", page)
        self.assertIsNone(full("/wow/", _ctx()))

    def test_logged_out_services_stay_on_the_community_page(self):
        taken = take("/account/services", _ctx())
        self.assertIsNotNone(taken)
        title, body = taken
        self.assertEqual(title, "Character Services")
        self.assertIn('href="/account/login"', body)
        self.assertIsNone(take("/account/services", _ctx(user="Aldrea")))
        self.assertIsNone(take("/wow/news", _ctx()))

    def test_summary_panels_skip_the_photograph(self):
        page = render(
            resolve("vanilla"),
            user="Aldrea",
            error="",
            notice="",
            mode="summary",
            email="a@example.com",
            characters=[{"name": "Aldrea", "level": 60, "class_name": "Mage"}],
            login_kind="account",
            separate_game_name=False,
        )
        for text in (
            "Manage Your Account",
            "Account Information",
            "Contact Information",
            "Upgrade Your Trial Account",
            "Retail Authentication Key",
            'href="/account/services"',
            "<th>Name</th><th>Level</th><th>Class</th>",
        ):
            self.assertIn(text, page)
        self.assertNotIn("tarou9876", page)
        self.assertNotIn("Hamamatsu", page)
        self.assertNotIn("Minatoku", page)
        login = render(
            resolve("vanilla"),
            user="",
            error="",
            notice="",
            mode="login",
            email="",
            characters=[],
            login_kind="account",
            separate_game_name=False,
        )
        self.assertNotIn('href="/account/services"', login)


if __name__ == "__main__":
    unittest.main()
