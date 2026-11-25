"""Midnight account page is the current Blizzard shell."""

import unittest

from wowweb.account_ui import midnight
from wowweb.catalog import resolve


def _render(mode, **extra):
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
    return midnight.render(resolve("midnight"), **payload)


class MidnightAccountUiTests(unittest.TestCase):
    def test_era_title_and_email_login(self):
        self.assertEqual(midnight.ERA_TITLE, "Account Security")
        page = _render("login", error="nope<script>")
        self.assertIn("Log in or sign up", page)
        self.assertNotIn(midnight.ERA_TITLE, page)
        self.assertIn('action="/account/login"', page)
        self.assertIn('name="identity"', page)
        self.assertIn("Email or Phone", page)
        self.assertNotIn('name="password"', page)
        self.assertIn('href="/account/create"', page)
        self.assertIn('class="acct-error"', page)
        self.assertIn("Continue", page)
        self.assertIn('type="button"', page)
        self.assertIn("nope&lt;script&gt;", page)
        step = _render("login-password", email="user@example.com")
        self.assertIn('name="password"', step)
        self.assertIn('name="identity"', step)
        self.assertIn("user@example.com", step)
        self.assertIn("There is no emailed password reset. Sign in and change the password here.", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())
        self.assertNotIn("<!DOCTYPE", page)
        self.assertNotIn('name="game_name"', page)

    def test_create_includes_game_name(self):
        page = _render("create")
        self.assertIn(midnight.ERA_TITLE, page)
        self.assertIn('action="/account/create"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('type="email"', page)
        self.assertIn('name="game_name"', page)
        self.assertIn('maxlength="16"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        omitted = _render("create", separate_game_name=False)
        self.assertNotIn('name="game_name"', omitted)

    def test_security_is_the_password_form(self):
        page = _render("password", user="Aldrea")
        self.assertIn(midnight.ERA_TITLE, page)
        self.assertIn('action="/account/password"', page)
        self.assertIn('name="current"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertIn('href="/account/"', page)
        self.assertIn("acct-nav-on", page)
        self.assertIn(">Security</a>", page)

    def test_summary_lists_license_characters(self):
        page = _render(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Password changed.",
            characters=[
                {"name": "Aldrea", "level": 60, "class_name": "Mage"},
                {"name": "Bob", "level": 12, "class_name": "Warrior"},
            ],
        )
        self.assertIn(midnight.ERA_TITLE, page)
        self.assertIn("Aldrea", page)
        self.assertIn("aldrea@example.com", page)
        self.assertIn("World of Warcraft", page)
        self.assertIn("level 60", page)
        self.assertIn("Mage", page)
        self.assertIn("level 12", page)
        self.assertIn("Warrior", page)
        self.assertIn('href="/account/password"', page)
        self.assertIn('href="/account/logout"', page)
        self.assertIn('class="acct-notice"', page)
        self.assertIn("Password changed.", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())

    def test_escapes_dynamic_text(self):
        page = _render(
            "summary",
            user='A"<b>',
            email="a&b@example.com",
            characters=[{"name": "X<y>", "level": 1, "class_name": "Mage&"}],
        )
        self.assertIn("A&quot;&lt;b&gt;", page)
        self.assertIn("a&amp;b@example.com", page)
        self.assertIn("X&lt;y&gt;", page)
        self.assertIn("Mage&amp;", page)
        self.assertNotIn("X<y>", page)
