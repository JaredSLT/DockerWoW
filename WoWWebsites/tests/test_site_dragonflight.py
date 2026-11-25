"""Dragonflight community site against the 2022–2023 references."""

import tempfile
import unittest
from pathlib import Path

from wowweb.catalog import resolve
from wowweb.html.era import dragonflight
from wowweb.html.guide import home_page
from wowweb.html.layout import layout
from wowweb.lab import load_lab

BANNED = ("private server", "recreation", "mariadb", "not affiliated")


class DragonflightSiteTests(unittest.TestCase):
    def setUp(self):
        self.exp = resolve("dragonflight")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def ctx(self, **extra):
        payload = {
            "exp": self.exp,
            "user": None,
            "dev": False,
            "qs": {},
            "path": "/",
            "labcfg": load_lab(),
            "data_dir": Path(self.tmp.name),
        }
        payload.update(extra)
        return payload

    def test_home_is_the_june_2023_season_two_page(self):
        body = home_page(self.exp, [], {"up": True, "name": "Dragonflight"})
        self.assertIn("DRAGONFLIGHT SEASON 2 NOW LIVE!", body)
        self.assertIn("Scalecommander Sarkareth", body)
        self.assertIn("Get Hot Summer Rewards in the July Trading Post", body)
        self.assertIn("This Week in WoW: 26 June 2023", body)
        self.assertIn("Heed the Call of the Crusade", body)
        self.assertIn("The WoW Summer Sale is here!", body)
        self.assertIn("27 June 2023", body)
        self.assertIn("20 June 2023", body)
        self.assertIn('href="/shop"', body)
        self.assertNotIn("from the lab", body)
        self.assertNotIn("ssotd-container", body)
        page = layout(self.exp, "Home", body)
        self.assertIn("Game Info", page)
        self.assertIn("Expansions", page)
        self.assertIn("Community", page)
        self.assertIn(">Try Free<", page)
        self.assertIn(">Subscribe Now<", page)
        self.assertNotIn("ssotd-container", page)
        self._public(page)

    def test_shell_links_the_community_nav(self):
        page = layout(self.exp, "Page", "<p>Body</p>")
        self.assertIn("<p>Body</p>", page)
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
            "/support",
            "/armory",
            "/esports",
        ):
            self.assertIn(f'href="{href}"', page)
        self.assertNotIn("ssotd-container", page)
        self._public(page)
        dev = layout(self.exp, "Page", "<p>Body</p>", dev=True)
        self.assertIn("Not affiliated", dev)

    def test_forums_index_matches_october_2023(self):
        page = dragonflight.full("/forums", self.ctx())
        self.assertIn("All Categories", page)
        self.assertIn("In Development", page)
        self.assertIn("Embers of Neltharion PTR", page)
        self.assertIn("Evoker", page)
        self.assertIn("Death Knight", page)
        self.assertIn('href="/forums/evoker"', page)
        self.assertNotIn("ssotd-container", page)
        self._public(page)

    def test_realm_status_matches_november_2022(self):
        page = dragonflight.full("/wow/realmstatus", self.ctx())
        self.assertIn("Realm Status", page)
        self.assertIn("World of Warcraft Classic", page)
        self.assertIn("Wrath of the Lich King Classic", page)
        self.assertIn("Aegwynn", page)
        self.assertIn("Alexstrasza", page)
        self.assertIn("DRAGONFLIGHT", page)
        self.assertIn("AVAILABLE NOW", page)
        self.assertIn('href="/shop"', page)
        self.assertIn("Service Status Forum", page)
        self._public(page)
        classic = dragonflight.full("/wow/realmstatus", self.ctx(qs={"tab": ["classic"]}))
        self.assertIn("Atiesh", classic)
        self.assertIn("df-tab-on", classic)

    def test_shop_is_the_mounts_grid(self):
        page = dragonflight.full("/shop", self.ctx())
        self.assertIn("Wondrous Wavewhisker", page)
        self.assertIn("Hogrus, Swine of Good Fortune", page)
        self.assertIn("Jade, Bright Foreseer", page)
        self.assertIn(">Mounts<", page)
        self.assertIn("$25.00", page)
        self.assertIn("Battle.net Balance", page)
        self.assertIn("Nothing here is charged", page)
        self.assertNotIn("card number", page.lower())
        self._public(page)

    def test_account_pages_follow_the_august_screens(self):
        login = dragonflight.full("/account/login", self.ctx())
        self.assertIn("BATTLE.NET", login)
        self.assertIn(">Log In<", login)
        self.assertIn('name="identity"', login)
        self.assertIn('type="email"', login)
        self.assertIn("Or log in with", login)
        self.assertIn("Blizzard Account", login)
        self._public(login)
        create = dragonflight.full("/account/create", self.ctx())
        self.assertIn('name="game_name"', create)
        self.assertIn('maxlength="16"', create)

    def test_pages_without_their_own_reference_use_this_masthead(self):
        ctx = self.ctx()
        news = dragonflight.take("/wow/news", ctx)
        guide = dragonflight.take("/wow/info", ctx)
        board = dragonflight.take("/forums/general", ctx)
        services = dragonflight.take("/account/services", ctx)
        self.assertIsNotNone(news)
        self.assertIsNotNone(guide)
        self.assertIsNotNone(board)
        self.assertIsNotNone(services)
        for title, body in (news, guide, board, services):
            page = layout(self.exp, title, body)
            self.assertIn("Game Info", page)
            self.assertNotIn("ssotd-container", page)
            self._public(page)
        self.assertIn("Get Hot Summer Rewards", news[1])
        self.assertIn("Archive", news[1])
        self.assertIn("Dragon Isles", guide[1])
        self.assertIn("Dracthyr", guide[1])
        self.assertIn("Evoker", guide[1])
        self.assertIn("Augmentation", guide[1])
        self.assertIn("General Discussion", board[1])
        self.assertIn("Welcome to the community forums", board[1])
        self.assertIn('href="/account/login"', services[1])
        profile = dragonflight.profile_body(
            self.exp,
            {
                "name": "Aldrea",
                "level": 70,
                "race": "Dracthyr",
                "class": "Evoker",
                "realm": "Dragonflight",
                "equipment": [{"slot": "Head", "name": "Visage Helm", "item_id": 1}],
                "guild": None,
                "achievements": 3,
                "online": False,
                "money_text": "1g 0s 0c",
            },
        )
        wrapped = layout(self.exp, "Aldrea", profile)
        self.assertIn("Game Info", wrapped)
        self.assertIn("Aldrea", profile)
        self.assertIn("Evoker", profile)
        self.assertIn("Visage Helm", profile)
        self.assertNotIn("Khaz Algar", profile)
        self.assertNotIn("Haranir", profile)
        self.assertNotIn("warband", profile.lower())
        self._public(wrapped)

    def _public(self, page: str) -> None:
        low = page.lower()
        for phrase in BANNED:
            self.assertNotIn(phrase, low, phrase)
