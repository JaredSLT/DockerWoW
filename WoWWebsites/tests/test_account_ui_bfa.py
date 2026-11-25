"""Battle for Azeroth Battle.net account overview."""

import unittest

from wowweb.account_ui import bfa
from wowweb.catalog import resolve


def _page(mode, **extra):
    payload = dict(
        user="",
        error="",
        notice="",
        mode=mode,
        email="",
        characters=[],
        login_kind="email",
        separate_game_name=True,
    )
    payload.update(extra)
    return bfa.render(resolve("bfa"), **payload)


class BfaAccountUiTests(unittest.TestCase):
    def test_login_is_the_account_overview(self):
        page = _page("login", error="nope<script>")
        self.assertEqual(bfa.ERA_TITLE, "Account Overview")
        self.assertIn(bfa.ERA_TITLE, page)
        self.assertIn('action="/account/login"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="password"', page)
        self.assertIn('class="acct-error"', page)
        self.assertIn('href="/account/create"', page)
        self.assertIn("no emailed password reset", page.lower())
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())

    def test_create_asks_for_the_game_account_name(self):
        page = _page("create")
        self.assertIn(bfa.ERA_TITLE, page)
        self.assertIn('action="/account/create"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="game_name"', page)
        self.assertIn('maxlength="16"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)

    def test_password_asks_for_the_current_battlenet_password(self):
        page = _page("password", user="Aldrea")
        self.assertIn(bfa.ERA_TITLE, page)
        self.assertIn("Change Password", page)
        self.assertIn("Current Battle.net password", page)
        self.assertIn('action="/account/password"', page)
        self.assertIn('name="current"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertIn('href="/account/"', page)

    def test_summary_lists_email_game_name_and_characters(self):
        page = _page(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Password changed.",
            characters=[
                {"name": "Aldrea", "level": 60, "class_name": "Mage"},
                {"name": "Brynn", "level": 12, "class_name": "Hunter"},
            ],
        )
        self.assertIn(bfa.ERA_TITLE, page)
        self.assertIn("Aldrea", page)
        self.assertIn("aldrea@example.com", page)
        self.assertIn("Brynn", page)
        self.assertIn("60", page)
        self.assertIn("Mage", page)
        self.assertIn("12", page)
        self.assertIn("Hunter", page)
        self.assertIn('class="acct-notice"', page)
        self.assertIn('href="/account/password"', page)
        self.assertIn('href="/account/logout"', page)
        self.assertIn("Game account name", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())

    def test_summary_escapes_dynamic_text(self):
        page = _page(
            "summary",
            user="<b>Aldrea</b>",
            email="a&b@example.com",
            notice="<i>ok</i>",
            characters=[{"name": "<Mage>", "level": 1, "class_name": "Rogue&"}],
        )
        self.assertIn("&lt;b&gt;Aldrea&lt;/b&gt;", page)
        self.assertIn("a&amp;b@example.com", page)
        self.assertIn("&lt;i&gt;ok&lt;/i&gt;", page)
        self.assertIn("&lt;Mage&gt;", page)
        self.assertIn("Rogue&amp;", page)
        self.assertNotIn("<b>Aldrea</b>", page)


if __name__ == "__main__":
    unittest.main()
