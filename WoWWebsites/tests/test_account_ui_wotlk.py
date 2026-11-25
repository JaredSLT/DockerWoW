"""Wrath account page: account-name login, ice summary, password panel."""

import unittest

from wowweb.account_ui import wotlk
from wowweb.catalog import resolve


def _page(mode, **extra):
    payload = dict(
        user="",
        error="",
        notice="",
        mode=mode,
        email="",
        characters=[],
        login_kind="account",
        separate_game_name=False,
    )
    payload.update(extra)
    return wotlk.render(resolve("wotlk"), **payload)


class WotlkAccountUiTests(unittest.TestCase):
    def test_era_title_constant(self):
        self.assertEqual(wotlk.ERA_TITLE, "Manage Your Account")

    def test_login_is_account_name(self):
        page = _page("login", error="<nope>")
        self.assertIn(wotlk.ERA_TITLE, page)
        self.assertIn('method="post"', page)
        self.assertIn('action="/account/login"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="password"', page)
        self.assertIn('href="/account/create"', page)
        self.assertIn('class="acct-error"', page)
        self.assertIn("&lt;nope&gt;", page)
        self.assertIn("There is no emailed password reset. Sign in and change the password here.", page)
        self.assertNotIn('type="email"', page)
        self.assertNotIn('name="game_name"', page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())

    def test_create_has_no_game_name(self):
        page = _page("create", login_kind="email", separate_game_name=True)
        self.assertIn(wotlk.ERA_TITLE, page)
        self.assertIn('action="/account/create"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertNotIn('name="game_name"', page)
        self.assertNotIn('type="email"', page)

    def test_password_panel_uses_current(self):
        page = _page("password", user="Aldrea")
        self.assertIn(wotlk.ERA_TITLE, page)
        self.assertIn("Change Password", page)
        self.assertIn("acct-password", page)
        self.assertIn('action="/account/password"', page)
        self.assertIn('name="current"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertIn('href="/account/"', page)

    def test_summary_is_an_icy_character_table(self):
        page = _page(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Saved & ready",
            characters=[
                {"name": "Aldrea", "level": 80, "class_name": "Death Knight"},
                {"name": "A&B", "level": 70, "class_name": "Mage"},
            ],
        )
        self.assertIn(wotlk.ERA_TITLE, page)
        self.assertIn("acct-summary", page)
        self.assertIn("Aldrea", page)
        self.assertIn("Death Knight", page)
        self.assertIn(">80<", page)
        self.assertIn("A&amp;B", page)
        self.assertIn("<th>Name</th>", page)
        self.assertIn("<th>Level</th>", page)
        self.assertIn("<th>Class</th>", page)
        self.assertIn('class="acct-notice"', page)
        self.assertIn("Saved &amp; ready", page)
        self.assertIn('href="/account/password"', page)
        self.assertIn('href="/account/logout"', page)
        self.assertNotIn("aldrea@example.com", page)
        self.assertNotIn('name="game_name"', page)

    def test_title_is_on_every_mode(self):
        for mode in ("login", "create", "password", "summary", "other"):
            page = _page(mode, user="Aldrea")
            self.assertIn(wotlk.ERA_TITLE, page, mode)
            self.assertTrue(page.startswith('<section class="acct acct-wotlk">'), mode)

    def test_empty_roster_still_has_the_table(self):
        page = _page("summary", user="Aldrea", characters=[])
        self.assertIn("No characters on this realm yet.", page)
        self.assertIn("<th>Name</th>", page)
