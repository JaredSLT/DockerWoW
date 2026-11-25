"""The War Within Battle.net account page."""

import unittest

from wowweb.account_ui import warwithin
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
    return warwithin.render(resolve("warwithin"), **payload)


class WarWithinAccountTests(unittest.TestCase):
    def test_era_title_is_sign_in_and_security(self):
        self.assertEqual(warwithin.ERA_TITLE, "Sign-in & Security")
        for mode in ("login", "create", "password", "summary"):
            html = _page(mode, user="Aldrea", email="aldrea@example.com")
            self.assertIn(warwithin.ERA_TITLE, html)
            self.assertNotIn("Sign-in &amp; Security", html)
            self.assertIn("Overview", html)
            self.assertIn('href="/account/"', html)
            self.assertIn('href="/account/password"', html)

    def test_login_posts_email_identity(self):
        html = _page("login", error="nope<script>")
        self.assertIn('action="/account/login"', html)
        self.assertIn('name="identity"', html)
        self.assertIn('type="email"', html)
        self.assertIn('name="password"', html)
        self.assertIn('href="/account/create"', html)
        self.assertIn('class="acct-error"', html)
        self.assertIn("nope&lt;script&gt;", html)
        self.assertIn("no emailed password reset", html.lower())
        self.assertNotIn("private server", html.lower())
        self.assertNotIn("mariadb", html.lower())

    def test_create_has_game_name(self):
        html = _page("create")
        self.assertIn('action="/account/create"', html)
        self.assertIn('name="identity"', html)
        self.assertIn('name="game_name"', html)
        self.assertIn('maxlength="16"', html)
        self.assertIn('name="password"', html)
        self.assertIn('name="confirm"', html)

    def test_password_is_change_password(self):
        html = _page("password", user="Aldrea")
        self.assertIn("Change Password", html)
        self.assertIn('action="/account/password"', html)
        self.assertIn('name="current"', html)
        self.assertIn('name="password"', html)
        self.assertIn('name="confirm"', html)
        self.assertIn('href="/account/"', html)

    def test_overview_lists_email_account_and_characters(self):
        html = _page(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Saved & ready",
            characters=[{"name": "Brann", "level": 80, "class_name": "Hunter"}],
        )
        self.assertIn("aldrea@example.com", html)
        self.assertIn("Aldrea", html)
        self.assertIn("Brann", html)
        self.assertIn("80", html)
        self.assertIn("Hunter", html)
        self.assertIn('class="acct-notice"', html)
        self.assertIn("Saved &amp; ready", html)
        self.assertIn('href="/account/password"', html)
        self.assertIn('href="/account/logout"', html)
        self.assertIn("World of Warcraft account name", html)
