"""June 2004 beta chrome and the separate 2001 announcement site."""

import tempfile
import unittest
from pathlib import Path

from wowweb.catalog import resolve
from wowweb.html.era import alpha
from wowweb.html.layout import layout

BANNED = ("private server", "recreation", "mariadb", "not affiliated")


def _shell(**kw) -> str:
    exp = resolve("alpha")
    return alpha.shell(exp, "Page", "<p>Body</p>", kw.get("user"), "", kw.get("dev", False), kw.get("online", ""))


class AlphaSiteTests(unittest.TestCase):
    def test_beta_shell_matches_the_june_nav_and_login(self):
        page = _shell()
        self.assertIn("Beta Web Site", page)
        self.assertIn("Current News", page)
        self.assertIn('href="/support/"', page)
        self.assertIn('action="/account/login"', page)
        self.assertIn('name="stay" value="sidebar"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="password"', page)
        self.assertIn(">Login:</span>", page)
        self.assertIn(">Pass:</span>", page)
        for label in (
            "Archived News",
            "Game Info",
            "Races",
            "Classes",
            "Basics",
            "Trade Skills",
            "Items",
            "Quest Discussion",
            "PvP Discussion",
            "Off-topic",
            "Guild Recruitment",
            "Trading Post",
            "Role-playing",
            "UI Customization",
            "Suggestions",
            "Server Status",
            "Technical Support",
            "Beta Readme",
            "Game Masters",
            "Policies",
            "Support Forum",
            "Movies and Music",
            "Fan Site Program",
            "More about WoW",
            "What is World of Warcraft?",
            "Retrieve Password",
            "Latest Patch Notes",
            "Signups Concluded",
            "Beta Server",
            "PvP Server",
        ):
            self.assertIn(label, page)
        self.assertIn('href="/wow/realmstatus"', page)
        self.assertIn('href="/story"', page)
        self.assertNotIn("journey of brann", page.lower())
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())

    def test_dev_note_stays_off_the_public_shell(self):
        self.assertNotIn("Not affiliated", _shell())
        self.assertIn("Not affiliated", _shell(dev=True))

    def test_signed_in_sidebar_and_realm_checks(self):
        page = _shell(user="Aldrea", online="up")
        self.assertIn("Aldrea", page)
        self.assertIn('href="/account/"', page)
        self.assertIn('href="/account/logout"', page)
        self.assertNotIn('name="identity"', page)
        self.assertEqual(page.count(" checked"), 2)
        down = _shell(online="down")
        self.assertNotIn(" checked", down)

    def test_home_keeps_the_june_posts_and_the_live_feed(self):
        news = [("World of Warcraft Items:", "2004-04-08", "A long captured note.")]
        body = alpha.home_body(resolve("alpha"), news, {"up": True, "name": "Alpha 0.5"}, None)
        self.assertIn("A Peek at the Next Patch", body)
        self.assertIn("Katricia on 06/28/04", body)
        self.assertIn("The level cap will be increased to 50.", body)
        self.assertIn("Sunken Temple", body)
        self.assertIn("European Beta Sign-up Date Announced!", body)
        self.assertIn("Indoflaven on 06/28/04", body)
        self.assertIn('href="/wow/news/0"', body)
        self.assertIn("World of Warcraft Items:", body)
        self.assertIn("04/08/04", body)
        wrapped = layout(resolve("alpha"), "Current News", body)
        self.assertIn("Beta Web Site", wrapped)
        self.assertIn("level cap", wrapped)
        for phrase in BANNED:
            self.assertNotIn(phrase, wrapped.lower())

    def test_announce_home_and_features_share_the_2001_frame(self):
        ctx = {"exp": resolve("alpha"), "user": None, "dev": False, "qs": {}, "path": "/announce", "labcfg": None, "data_dir": "."}
        home = alpha.full("/announce", ctx)
        features = alpha.full("/announce/features", ctx)
        self.assertIn('data-nav="updates|features|screenshots|journey of brann|wallpapers|movies|f.a.q"', home)
        self.assertIn("our years have passed since the aftermath", home)
        self.assertIn("10/05/01", home)
        self.assertIn("Screenshot Gallery Updated", home)
        # The beta subtitle belongs to the 2004 masthead, not this forest page.
        self.assertNotIn("Beta Web Site", home)
        self.assertNotIn("Current News", home)
        self.assertIn("Game Features", features)
        self.assertIn("seamless, persistent world", features)
        self.assertIn("our years have passed since the aftermath", features)
        self.assertNotIn("Screenshot Gallery Updated", features)
        self.assertIn('href="/announce/forums"', home)
        for phrase in BANNED:
            self.assertNotIn(phrase, home.lower())
            self.assertNotIn(phrase, features.lower())

    def test_announce_panels_and_unknown_path(self):
        ctx = {"exp": resolve("alpha"), "user": None, "dev": False, "qs": {}, "path": "/announce", "labcfg": None, "data_dir": "."}
        self.assertIsNone(alpha.full("/wow/", ctx))
        for path, needle in (
            ("/announce/screenshots", "Screenshots"),
            ("/announce/brann", "Elwynn"),
            ("/announce/wallpapers", "Imagination"),
            ("/announce/movies", "cinematics"),
            ("/announce/faq", "no emailed reset"),
            ("/announce/privacy", "does not mail a password reset"),
        ):
            page = alpha.full(path, ctx)
            self.assertIn(needle, page)
            self.assertIn("updates|features|screenshots", page)

    def test_logged_out_services_stay_on_the_beta_page(self):
        ctx = {"exp": resolve("alpha"), "user": None, "dev": False, "qs": {}, "path": "/account/services", "labcfg": None, "data_dir": "."}
        title, body = alpha.take("/account/services", ctx)
        self.assertEqual(title, "Character Services")
        self.assertIn('href="/account/login"', body)
        self.assertIn('href="/account/create"', body)
        self.assertIsNone(alpha.take("/account/services", dict(ctx, user="Aldrea")))
        self.assertIsNone(alpha.take("/wow/news", ctx))

    def test_2001_forum_uses_the_backend_not_the_screenshot_threads(self):
        exp = resolve("alpha")
        with tempfile.TemporaryDirectory() as tmp:
            ctx = {
                "exp": exp,
                "user": None,
                "dev": False,
                "qs": {},
                "path": "/announce/forums",
                "labcfg": None,
                "data_dir": Path(tmp),
            }
            page = alpha.full("/announce/forums", ctx)
        self.assertIn("Search Forum", page)
        self.assertIn("Post Message", page)
        self.assertIn("General Discussion", page)
        self.assertIn("Forum Rules", page)
        self.assertIn('href="/support/"', page)
        self.assertIn("Welcome to the community forums", page)
        self.assertIn('href="/forums/general/', page)
        self.assertNotIn("I GOT ANOTHER ONE", page)
        self.assertNotIn("LagMonster", page)
        self.assertNotIn(">Beta Web Site<", page)
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())


if __name__ == "__main__":
    unittest.main()
