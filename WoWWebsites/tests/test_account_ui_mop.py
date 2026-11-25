"""Mists account sheet: Battle.net overview, game account name."""

import re
import unittest

from wowweb.account_ui import mop
from wowweb.catalog import resolve


def _render(mode, **extra):
    payload = dict(
        user="",
        error="",
        notice="",
        mode=mode,
        email="aldrea@example.com",
        characters=[],
        login_kind="account",
        separate_game_name=False,
    )
    payload.update(extra)
    return mop.render(resolve("mop"), **payload)


class MopAccountTests(unittest.TestCase):
    def test_era_title_on_every_mode(self):
        self.assertEqual(mop.ERA_TITLE, "Battle.net")
        for mode in ("login", "create", "password", "summary"):
            user = "Aldrea" if mode in {"password", "summary"} else ""
            page = _render(mode, user=user)
            self.assertIn(mop.ERA_TITLE, page)

    def test_login_form(self):
        page = _render("login", error="nope<script>")
        self.assertIn('action="/account/login"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="password"', page)
        self.assertIn('href="/account/create"', page)
        self.assertIn('class="acct-error"', page)
        self.assertIn("Account Name", page)
        self.assertIn("nope&lt;script&gt;", page)
        self.assertNotIn("nope<script>", page)
        self.assertIn("no emailed password reset", page.lower())
        self.assertIn("change the password here", page.lower())
        self.assertNotIn('type="email"', page)
        self.assertNotIn('name="game_name"', page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())

    def test_create_has_no_game_name_or_email(self):
        page = _render(
            "create",
            login_kind="email",
            separate_game_name=True,
            email="aldrea@example.com",
        )
        self.assertIn('action="/account/create"', page)
        self.assertIn('name="identity"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertNotIn('name="game_name"', page)
        self.assertNotIn('type="email"', page)
        self.assertNotIn("aldrea@example.com", page)
        self.assertIn("Account Name", page)
        self.assertNotIn(">Email<", page)

    def test_password_form(self):
        page = _render("password", user="Aldrea")
        self.assertIn('action="/account/password"', page)
        self.assertIn('name="current"', page)
        self.assertIn('name="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertIn('href="/account/"', page)
        self.assertIn("Aldrea", page)

    def test_summary_shows_account_name_and_characters(self):
        page = _render(
            "summary",
            user='Ald<rea>',
            notice="Password changed.",
            characters=[
                {"name": "Aldrea", "level": 90, "class_name": "Monk"},
                {"name": "N<b>", "level": "1<2>", "class_name": "M&age"},
            ],
        )
        self.assertIn("Ald&lt;rea&gt;", page)
        self.assertIn("Aldrea", page)
        self.assertIn("90", page)
        self.assertIn("Monk", page)
        self.assertIn("N&lt;b&gt;", page)
        self.assertIn("1&lt;2&gt;", page)
        self.assertIn("M&amp;age", page)
        self.assertIn('href="/account/password"', page)
        self.assertIn('href="/account/logout"', page)
        self.assertIn('class="acct-notice"', page)
        self.assertIn("Password and Security", page)
        self.assertIn("Account Name", page)
        self.assertNotIn("aldrea@example.com", page)
        self.assertNotIn('name="game_name"', page)

    def test_classes_start_with_acct_prefix(self):
        pages = [
            _render("login", error="x"),
            _render("create"),
            _render("password", user="Aldrea"),
            _render(
                "summary",
                user="Aldrea",
                notice="ok",
                characters=[{"name": "Aldrea", "level": 90, "class_name": "Monk"}],
            ),
        ]
        for page in pages:
            for group in re.findall(r'class="([^"]+)"', page):
                for token in group.split():
                    self.assertTrue(token.startswith("acct-"), token)
