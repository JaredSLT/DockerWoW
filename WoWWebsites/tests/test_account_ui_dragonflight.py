"""Dragonflight 10.2.7 Blizzard account page."""

import re
import unittest
from pathlib import Path

from wowweb.account_ui import dragonflight
from wowweb.catalog import resolve


class DragonflightAccountTests(unittest.TestCase):
    def setUp(self):
        self.exp = resolve("dragonflight")

    def _render(self, mode, **extra):
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
        return dragonflight.render(self.exp, **payload)

    def test_era_title_login_password_and_license_name(self):
        self.assertEqual(dragonflight.ERA_TITLE, "Blizzard Account")
        login = self._render("login", error="nope")
        create = self._render("create")
        password = self._render("password", user="Aldrea")
        summary = self._render(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Password changed.",
            characters=[{"name": "Aldrea", "level": 70, "class_name": "Evoker"}],
        )
        for page in (login, create, password, summary):
            self.assertIn(dragonflight.ERA_TITLE, page)
            self.assertNotIn("private server", page.lower())
            self.assertNotIn("mariadb", page.lower())
            for group in re.findall(r'class="([^"]*)"', page):
                for name in group.split():
                    self.assertTrue(name.startswith("acct-"), name)
        self.assertIn('action="/account/login"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('type="email"', login)
        self.assertIn('name="password"', login)
        self.assertIn('href="/account/create"', login)
        self.assertIn('class="acct-error"', login)
        self.assertIn("Overview", login)
        self.assertIn("Security", login)
        self.assertIn("no emailed password reset", login)
        self.assertIn('action="/account/create"', create)
        self.assertIn('name="game_name"', create)
        self.assertIn('maxlength="16"', create)
        self.assertIn('name="identity"', create)
        self.assertIn('name="password"', create)
        self.assertIn('name="confirm"', create)
        self.assertIn('action="/account/password"', password)
        self.assertIn('name="current"', password)
        self.assertIn('name="password"', password)
        self.assertIn('name="confirm"', password)
        self.assertIn('href="/account/"', password)
        self.assertIn("Security", password)
        self.assertIn("Change Password", password)
        self.assertIn("aldrea@example.com", summary)
        self.assertIn("Aldrea", summary)
        self.assertIn("70", summary)
        self.assertIn("Evoker", summary)
        self.assertIn("World of Warcraft license", summary)
        self.assertIn('href="/account/password"', summary)
        self.assertIn('href="/account/logout"', summary)
        self.assertIn('class="acct-notice"', summary)

    def test_escapes_dynamic_text(self):
        page = self._render(
            "summary",
            user="<Aldrea>",
            email="a&b@example.com",
            error="<bad>",
            notice='"ok"',
            characters=[{"name": "<Mage>", "level": 70, "class_name": "Evoker &"}],
        )
        self.assertIn("&lt;Aldrea&gt;", page)
        self.assertIn("a&amp;b@example.com", page)
        self.assertIn("&lt;bad&gt;", page)
        self.assertIn("&quot;ok&quot;", page)
        self.assertIn("&lt;Mage&gt;", page)
        self.assertIn("Evoker &amp;", page)
        self.assertNotIn("<Aldrea>", page)
        self.assertNotIn("<bad>", page)

    def test_game_name_follows_separate_game_name(self):
        joined = self._render("create", separate_game_name=False)
        self.assertNotIn('name="game_name"', joined)
        self.assertIn('type="email"', self._render("login", login_kind="email"))
        self.assertIn('type="text"', self._render("login", login_kind="account"))

    def test_stylesheet_uses_dragonflight_panel_colors(self):
        css = (Path(__file__).resolve().parents[1] / "static" / "css" / "account-dragonflight.css").read_text()
        self.assertIn(".acct-df", css)
        for color in ("#5ee0c5", "#1e7a78", "#0e1c22", "#0a1418", "#07141a", "#e7f7f4", "#b7d5d0", "#9aebdc"):
            self.assertIn(color, css)
