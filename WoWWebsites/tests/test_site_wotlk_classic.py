"""May 2022 Wrath of the Lich King Classic product site."""

import tempfile
import unittest
from pathlib import Path

from wowweb.account_ui.wotlk_classic import ERA_TITLE, render
from wowweb.catalog import resolve
from wowweb.html.era.wotlk_classic import full, take
from wowweb.html.guide import home_page
from wowweb.html.layout import layout

BANNED = ("private server", "recreation", "mariadb", "not affiliated")


def _exp():
    return resolve("wotlk-classic")


def _ctx(**extra):
    payload = {
        "exp": _exp(),
        "user": None,
        "dev": False,
        "qs": {},
        "path": "",
        "labcfg": None,
        "data_dir": None,
    }
    payload.update(extra)
    return payload


def _home() -> str:
    exp = _exp()
    body = home_page(exp, [], {"up": True, "name": "Wrath Classic"})
    return layout(exp, "World of Warcraft Community Site", body, crumb="World of Warcraft Community Site")


class WotlkClassicSiteTests(unittest.TestCase):
    def test_home_is_the_may_2022_product_page(self):
        page = _home()
        self.assertIn("The Lich King Returns", page)
        self.assertIn("Play Burning Crusade Classic™ today and face the Lich King in 2022", page)
        self.assertIn('href="/wow/" aria-current="page">Overview</a>', page)
        self.assertIn('href="/story">The Lich King</a>', page)
        self.assertIn('href="/wow/info/features">Features</a>', page)
        self.assertIn('href="/wow/info/basics">Getting Started</a>', page)
        self.assertIn('href="/wow/media/screenshots">Media</a>', page)
        self.assertIn(">SUBSCRIBE NOW<", page)
        self.assertIn("BETA OPT-IN", page)
        self.assertIn("/static/css/era-wotlk-classic.css", page)
        self.assertIn("/static/img/wotlk-classic/hero.jpg", page)
        self.assertIn("Wrath Classic is Up", page)
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())

    def test_dev_footer_is_opt_in(self):
        quiet = _home()
        loud = layout(_exp(), "Page", "<p>Body</p>", dev=True)
        self.assertNotIn("Not affiliated", quiet)
        self.assertIn("Not affiliated", loud)
        self.assertIn("<p>Body</p>", loud)

    def test_shop_matches_the_august_2022_upgrades(self):
        title, body = take("/shop", _ctx())
        self.assertEqual(title, "Shop")
        self.assertIn("Northrend Heroic Upgrade", body)
        self.assertIn("$49.99", body)
        self.assertIn("Northrend Epic Upgrade", body)
        self.assertIn("$79.99", body)
        self.assertIn("Buy Now", body)
        self.assertIn("Pebble, a penguin pet", body)
        self.assertIn("Fishspeaker", body)
        self.assertIn("Lucky Lure", body)
        self.assertIn("Whalebone Glider", body)
        self.assertIn("Tuskarr Shoreglider", body)
        self.assertIn("30 Days of Game Time", body)
        self.assertIn("Nothing here is charged", body)
        self.assertIn("/static/img/wotlk-classic/shop-compare.png", body)
        self.assertIn("/static/img/wotlk-classic/shop-heroic.jpg", body)
        self.assertIn("/static/img/wotlk-classic/shop-epic.jpg", body)
        self.assertNotIn("<form", body.lower())
        self.assertNotIn("Subscribe", body)

    def test_realm_status_defaults_to_this_realms_row(self):
        title, body = take("/wow/realmstatus", _ctx())
        self.assertEqual(title, "Realm Status")
        self.assertIn("World of Warcraft", body)
        self.assertIn("World of Warcraft Classic", body)
        self.assertIn('class="wc-tab is-on" aria-current="page">Wrath of the Lich King Classic</a>', body)
        self.assertIn("Wrath Classic", body)
        self.assertIn("Service Status Forum", body)
        self.assertIn("Realm Name", body)
        retail_title, retail = take("/wow/realmstatus", _ctx(qs={"game": ["retail"]}))
        self.assertEqual(retail_title, "Realm Status")
        self.assertIn('class="wc-tab is-on" aria-current="page">World of Warcraft</a>', retail)
        self.assertNotIn(">Wrath Classic<", retail)
        for name in (
            "Aegwynn",
            "Aerie Peak",
            "Agamaggan",
            "Aggramar",
            "Akama",
            "Alexstrasza",
            "Alleria",
            "Altar of Storms",
            "Alterac Mountains",
            "Aman&#x27;Thul",
            "Andorhal",
        ):
            self.assertIn(name, retail)
        self.assertIn("New Players", retail)
        self.assertIn("AEDT", retail)
        self.assertIn(">Oceanic<", retail)
        self.assertIn("/static/img/wotlk-classic/realm-retail.png", retail)
        filtered_title, filtered = take("/wow/realmstatus", _ctx(qs={"game": ["retail"], "q": ["Aegwynn"]}))
        self.assertEqual(filtered_title, "Realm Status")
        self.assertIn("Aegwynn", filtered)
        self.assertNotIn("realm-retail.png", filtered)
        self.assertNotIn("Aerie Peak", filtered)

    def test_pages_without_a_reference_still_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(data_dir=Path(tmp))
            news_title, news = take("/wow/news", ctx)
            guide_title, guide = take("/wow/info", ctx)
            forum_title, forums = take("/forums", ctx)
            board_title, board = take("/forums/general", _ctx(data_dir=Path(tmp), user="Aldrea"))
            profile_title, profile = take("/armory/character/Aldrea", ctx)
            gate_title, gate = take("/account/services", ctx)
        self.assertEqual(news_title, "News")
        self.assertEqual(guide_title, "Game Guide")
        self.assertEqual(forum_title, "Forums")
        self.assertEqual(board_title, "General Discussion")
        self.assertEqual(profile_title, "Aldrea")
        self.assertEqual(gate_title, "Character Services")
        for body in (news, guide, forums, board, profile, gate):
            self.assertNotIn("No reference screenshot", body)
        self.assertIn("Death Knight", guide)
        self.assertIn("Blood", guide)
        self.assertIn('href="/forums/general"', forums)
        self.assertNotIn("forum-index", forums)
        self.assertNotIn("World of Warcraft Forums", forums)
        self.assertIn('action="/forums/general/new"', board)
        signed = take("/account/services", _ctx(user="Aldrea"))
        self.assertIsNone(signed)

    def test_full_does_not_replace_the_shell(self):
        self.assertIsNone(full("/wow/", _ctx()))

    def test_account_forms_post_to_the_existing_routes(self):
        exp = _exp()
        login = render(
            exp,
            user="",
            error="nope",
            notice="",
            mode="login",
            email="",
            characters=[],
            login_kind="email",
            separate_game_name=True,
        )
        self.assertIn(ERA_TITLE, login)
        self.assertIn('action="/account/login"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('name="password"', login)
        self.assertIn('class="acct-error"', login)
        create = render(
            exp,
            user="",
            error="",
            notice="",
            mode="create",
            email="",
            characters=[],
            login_kind="email",
            separate_game_name=True,
        )
        self.assertIn('action="/account/create"', create)
        self.assertIn('name="game_name"', create)
        self.assertIn('name="confirm"', create)
        summary = render(
            exp,
            user="Aldrea",
            error="",
            notice="Password changed.",
            mode="summary",
            email="aldrea@example.com",
            characters=[{"name": "Aldrea", "level": 70, "class_name": "Mage"}],
            login_kind="email",
            separate_game_name=True,
        )
        self.assertIn(ERA_TITLE, summary)
        self.assertIn('href="/account/password"', summary)
        self.assertIn('class="acct-notice"', summary)
        self.assertNotIn("No reference screenshot", summary)
        for blob in (login, create, summary):
            for phrase in BANNED:
                self.assertNotIn(phrase, blob.lower())


if __name__ == "__main__":
    unittest.main()
