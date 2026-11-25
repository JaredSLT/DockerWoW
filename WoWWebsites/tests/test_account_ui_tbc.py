"""Burning Crusade account page: account-name login, two columns, character list."""

import unittest
from pathlib import Path

from wowweb.account_ui import tbc
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
    return tbc.render(resolve("tbc"), **payload)


class TbcAccountUiTests(unittest.TestCase):
    def test_era_title_constant(self):
        self.assertEqual(tbc.ERA_TITLE, "Burning Crusade Account")

    def test_login_posts_account_name(self):
        page = _page("login", error="<nope>")
        self.assertIn(tbc.ERA_TITLE, page)
        self.assertIn('method="post"', page)
        self.assertIn('action="/account/login"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="password"', page)
        self.assertIn('href="/account/create"', page)
        self.assertIn('class="acct-error"', page)
        self.assertIn("&lt;nope&gt;", page)
        self.assertIn("There is no emailed password reset. Sign in and change the password here.", page)
        self.assertIn("acct-cols", page)
        self.assertNotIn('type="email"', page)
        self.assertNotIn('name="game_name"', page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())

    def test_create_has_no_game_name(self):
        page = _page("create", login_kind="email", separate_game_name=True)
        self.assertIn(tbc.ERA_TITLE, page)
        self.assertIn('action="/account/create"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertNotIn('name="game_name"', page)
        self.assertNotIn('type="email"', page)

    def test_password_panel_uses_current(self):
        page = _page("password", user="Aldrea")
        self.assertIn(tbc.ERA_TITLE, page)
        self.assertIn("Change Password", page)
        self.assertIn("acct-password", page)
        self.assertIn('action="/account/password"', page)
        self.assertIn('name="current"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertIn('href="/account/"', page)

    def test_summary_lists_character_status(self):
        page = _page(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Saved & ready",
            characters=[
                {"name": "Aldrea", "level": 70, "class_name": "Paladin"},
                {"name": "A&B", "level": 60, "class_name": "Mage"},
            ],
        )
        self.assertIn(tbc.ERA_TITLE, page)
        self.assertIn("Character Status", page)
        self.assertIn("acct-chars", page)
        self.assertIn("Aldrea", page)
        self.assertIn("level 70", page)
        self.assertIn("Paladin", page)
        self.assertIn("A&amp;B", page)
        self.assertIn("level 60", page)
        self.assertIn("Mage", page)
        self.assertIn('class="acct-notice"', page)
        self.assertIn("Saved &amp; ready", page)
        self.assertIn('href="/account/password"', page)
        self.assertIn('href="/account/logout"', page)
        self.assertNotIn("aldrea@example.com", page)
        self.assertNotIn('name="game_name"', page)

    def test_title_and_columns_on_every_mode(self):
        for mode in ("login", "create", "password", "summary", "other"):
            page = _page(mode, user="Aldrea")
            self.assertIn(tbc.ERA_TITLE, page, mode)
            self.assertIn('class="acct-cols"', page, mode)
            self.assertIn('class="acct-main"', page, mode)
            self.assertIn('class="acct-side"', page, mode)
            self.assertTrue(page.startswith('<section class="acct acct-tbc">'), mode)

    def test_empty_roster_still_lists_character_status(self):
        page = _page("summary", user="Aldrea", characters=[])
        self.assertIn("Character Status", page)
        self.assertIn("No characters on this realm yet.", page)
        self.assertIn("Account name", page)
        self.assertIn("Aldrea", page)

    def test_css_uses_a_fel_green_left_rule(self):
        css = (Path(__file__).resolve().parents[1] / "static" / "css" / "account-tbc.css").read_text()
        self.assertIn(".acct-tbc .acct-cols", css)
        self.assertIn("border-left: 4px solid #6bd12a", css)


if __name__ == "__main__":
    unittest.main()
