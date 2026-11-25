"""Shadowlands account security page."""

import unittest

from wowweb.account_ui import shadowlands
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
    return shadowlands.render(resolve("shadowlands"), **payload)


class ShadowlandsAccountUiTests(unittest.TestCase):
    def test_era_title_login_and_password(self):
        self.assertEqual(shadowlands.ERA_TITLE, "Security")
        login = _page("login", error="nope")
        self.assertIn(shadowlands.ERA_TITLE, login)
        self.assertIn("<h2", login)
        self.assertIn('action="/account/login"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('name="password"', login)
        self.assertIn('href="/account/create"', login)
        self.assertIn('class="acct-error"', login)
        self.assertIn("Sign in and change the password here.", login)
        self.assertNotIn('name="game_name"', login)
        self.assertNotIn("private server", login.lower())
        self.assertNotIn("mariadb", login.lower())

        password = _page("password", user="Aldrea")
        self.assertIn(shadowlands.ERA_TITLE, password)
        self.assertIn('action="/account/password"', password)
        self.assertIn('name="current"', password)
        self.assertIn('name="password"', password)
        self.assertIn('name="confirm"', password)
        self.assertIn('href="/account/"', password)
        self.assertIn("Overview", password)
        self.assertIn("Security", password)

    def test_create_includes_game_name(self):
        page = _page("create")
        self.assertIn(shadowlands.ERA_TITLE, page)
        self.assertIn('action="/account/create"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="game_name"', page)
        self.assertIn('maxlength="16"', page)
        self.assertIn("World of Warcraft account name", page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)

    def test_summary_lists_email_game_account_and_characters(self):
        page = _page(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Password changed.",
            characters=[{"name": "Aldrea", "level": 60, "class_name": "Mage"}],
        )
        self.assertIn(shadowlands.ERA_TITLE, page)
        self.assertIn("aldrea@example.com", page)
        self.assertIn("Aldrea", page)
        self.assertIn("60", page)
        self.assertIn("Mage", page)
        self.assertIn('class="acct-notice"', page)
        self.assertIn('href="/account/password"', page)
        self.assertIn('href="/account/logout"', page)
        self.assertIn("Overview", page)

    def test_escapes_dynamic_text(self):
        page = _page(
            "summary",
            user="<Aldrea>",
            email="a&b@example.com",
            error='<bad>',
            characters=[{"name": "<Mage>", "level": 1, "class_name": "A&B"}],
        )
        self.assertIn("&lt;Aldrea&gt;", page)
        self.assertIn("a&amp;b@example.com", page)
        self.assertIn("&lt;bad&gt;", page)
        self.assertIn("&lt;Mage&gt;", page)
        self.assertIn("A&amp;B", page)
        self.assertNotIn("<Aldrea>", page)
        self.assertNotIn("<Mage>", page)
