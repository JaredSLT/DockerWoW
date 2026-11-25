"""March 2025 War Within shell, English shop, and the pages that share that masthead."""

import tempfile
import unittest
from pathlib import Path

from wowweb.catalog import resolve
from wowweb.content import news_for
from wowweb.html.era import warwithin
from wowweb.html.guide import home_page
from wowweb.html.layout import layout
from wowweb.lab import load_lab

BANNED = ("private server", "recreation", "mariadb", "not affiliated")


def _ctx(path: str, dev: bool = False, user: str | None = None) -> dict:
    return {
        "exp": resolve("warwithin"),
        "user": user,
        "dev": dev,
        "qs": {},
        "path": path,
        "labcfg": load_lab(None),
        "data_dir": Path(tempfile.mkdtemp()),
    }


def _home() -> str:
    exp = resolve("warwithin")
    body = home_page(exp, news_for(exp), {"up": True, "name": exp.realm_name, "type": "Normal"})
    return layout(exp, "World of Warcraft", body, crumb="World of Warcraft")


class WarWithinSiteTests(unittest.TestCase):
    def test_home_uses_the_english_undermine_hero(self):
        page = _home()
        self.assertIn("THE UNDERMINE(D) CONTENT UPDATE IS NOW LIVE!", page)
        self.assertIn("D.R.I.V.E.", page)
        self.assertIn("Operation Floodgate", page)
        self.assertIn("Liberation of Undermine", page)
        self.assertIn("/static/img/warwithin/undermine-hero.jpg", page)
        self.assertIn("Latest News", page)
        self.assertIn("VIEW ALL NEWS", page)
        self.assertIn(">NEW<", page)
        for label in ("Game Info", "Expansions", "News", "Community", "Shop", "Try Free", "Subscribe Now"):
            self.assertIn(label, page)
        self.assertNotIn("ANNONCE DE", page)
        self.assertNotIn("S'abonner maintenant", page)
        self.assertNotIn("NOUVEAU", page)
        for href in (
            "/wow/",
            "/wow/news",
            "/wow/info",
            "/wow/info/classes",
            "/wow/info/races",
            "/wow/realmstatus",
            "/forums",
            "/forums/general",
            "/shop",
            "/account/login",
            "/account/create",
            "/account/",
            "/account/services",
            "/support/",
            "/armory",
        ):
            self.assertIn(f'href="{href}"', page)
        low = page.lower()
        for phrase in BANNED:
            self.assertNotIn(phrase, low)

    def test_dev_footer_is_opt_in(self):
        quiet = _home()
        loud = layout(resolve("warwithin"), "Page", "<p>Body</p>", dev=True)
        self.assertNotIn("Not affiliated", quiet)
        self.assertIn("Not affiliated", loud)
        self.assertIn("<p>Body</p>", loud)
        self.assertIn("Game Info", loud)

    def test_forum_board_collapses_nav_and_does_not_invent_topics(self):
        ctx = _ctx("/forums/bugs")
        taken = warwithin.take("/forums/bugs", ctx)
        self.assertIsNotNone(taken)
        title, body = taken
        self.assertIn("Website Bug Report", title)
        self.assertIn("Forums", body)
        self.assertIn("Support", body)
        self.assertIn("Website Bug Report", body)
        self.assertIn("Latest topics in Website Bug Report", body)
        for column in ("Topic", "Author", "Replies", "Views", "Activity"):
            self.assertIn(column, body)
        self.assertIn('data-nav="ellipsis"', body)
        self.assertNotIn("Panda Monk can not access housing", body)
        self.assertNotIn("Maguthul", body)
        page = layout(resolve("warwithin"), title, body)
        self.assertIn("…", page)
        self.assertIn("Game Info", page)
        self.assertIn(">NEW<", page)

    def test_profile_tabs_match_the_march_bar(self):
        html = warwithin.character_body(
            {
                "name": "Armory",
                "level": 50,
                "race": "Nightborne",
                "race_id": 27,
                "class": "Warrior",
                "realm": "Ragnaros",
                "achievements": 19610,
                "equipment": [],
            }
        )
        for label in (
            "CHARACTER",
            "ACHIEVEMENTS",
            "COLLECTIONS",
            "DUNGEONS",
            "PLAYER VS PLAYER",
            "REPUTATION",
        ):
            self.assertIn(label, html)
        self.assertIn("50", html)
        self.assertIn("Nightborne", html)
        self.assertIn("Warrior", html)
        self.assertIn("19610", html)
        self.assertIn("Ragnaros", html)
        self.assertIn("ILVL", html)
        self.assertNotIn("Oathsworn", html)
        self.assertNotIn("Nazmani", html)

    def test_english_shop_grid(self):
        html = warwithin.full("/shop", _ctx("/shop"))
        self.assertIsNotNone(html)
        self.assertIn("Battle.net", html)
        self.assertIn("World of Warcraft: Subscription", html)
        self.assertIn("From $12.99/month", html)
        self.assertIn("The War Within", html)
        self.assertIn("From $49.99", html)
        self.assertIn("Level 70 Boost", html)
        self.assertIn("Dragonflight", html)
        self.assertIn("20th Anniversary Edition", html)
        self.assertIn("Cataclysm Classic", html)
        self.assertIn("Black Ops 6", html)
        self.assertIn("Buy Now", html)
        self.assertNotIn("Valentinstag", html)
        self.assertNotIn("Empfohlen", html)
        self.assertNotIn("49,99", html)
        low = html.lower()
        for phrase in BANNED:
            self.assertNotIn(phrase, low)
        self.assertNotIn("card number", low)
        self.assertNotIn("cvv", low)

    def test_realm_status_columns(self):
        taken = warwithin.take("/wow/realmstatus", _ctx("/wow/realmstatus"))
        self.assertIsNotNone(taken)
        _title, body = taken
        self.assertIn("Status", body)
        self.assertIn("Realm Name", body)
        self.assertIn("Type", body)
        self.assertIn('data-bare="1"', body)
        page = layout(resolve("warwithin"), "Realm Status", body)
        self.assertIn("Game Info", page)
        self.assertIn(">NEW<", page)
        self.assertNotIn("MariaDB", page)
        self.assertNotIn("mariadb", page.lower())

    def test_news_and_guide_use_live_copy(self):
        news = warwithin.take("/wow/news", _ctx("/wow/news"))
        self.assertIsNotNone(news)
        self.assertIn("Take on Lei Shen", news[1])
        guide = warwithin.take("/wow/info", _ctx("/wow/info"))
        self.assertIsNotNone(guide)
        self.assertEqual(guide[0], "Game Guide")
        self.assertIn("Khaz Algar", guide[1])
        self.assertIn("Earthen", guide[1])
        self.assertIn("/wow/info/classes/warrior/talents.html", guide[1])
        self.assertIn('href="/wow/info/races/earthen"', guide[1])

    def test_services_page_says_there_is_no_screenshot(self):
        html = warwithin.full("/account/services", _ctx("/account/services"))
        self.assertIsNotNone(html)
        self.assertIn("There is no services screenshot", html)
        self.assertIn("Character Services", html)
        self.assertIn("Game Info", html)
        self.assertIn('href="/account/login"', html)
        self.assertIn(">NEW<", html)
        low = html.lower()
        for phrase in ("private server", "recreation", "not affiliated"):
            self.assertNotIn(phrase, low)


if __name__ == "__main__":
    unittest.main()
