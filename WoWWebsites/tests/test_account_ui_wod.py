"""Warlords account page: email login, no separate game name."""

import unittest

from wowweb.account_ui.wod import ERA_TITLE, render
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
        separate_game_name=False,
    )
    payload.update(extra)
    return render(resolve("wod"), **payload)


class WodAccountUiTests(unittest.TestCase):
    def test_era_title_login_and_password_forms(self):
        self.assertEqual(ERA_TITLE, "Password and Security")
        login = _page("login", error="nope")
        self.assertIn(ERA_TITLE, login)
        self.assertIn('action="/account/login"', login)
        self.assertIn('method="post"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('type="email"', login)
        self.assertIn('name="password"', login)
        self.assertIn('href="/account/create"', login)
        self.assertIn('class="acct-error"', login)
        self.assertIn("Overview", login)
        self.assertIn("Settings", login)
        self.assertNotIn("private server", login.lower())
        self.assertNotIn("mariadb", login.lower())

        create = _page("create", separate_game_name=True)
        self.assertIn(ERA_TITLE, create)
        self.assertIn('action="/account/create"', create)
        self.assertIn('name="identity"', create)
        self.assertIn('name="password"', create)
        self.assertIn('name="confirm"', create)
        self.assertNotIn('name="game_name"', create)

        password = _page("password", user="admin@wod.local")
        self.assertIn(ERA_TITLE, password)
        self.assertIn('action="/account/password"', password)
        self.assertIn('name="current"', password)
        self.assertIn('name="password"', password)
        self.assertIn('name="confirm"', password)
        self.assertIn('href="/account/"', password)

    def test_summary_shows_address_name_and_characters(self):
        summary = _page(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Password changed.",
            characters=[
                {"name": "Aldrea", "level": 100, "class_name": "Mage"},
                {"name": "Drek", "level": 90, "class_name": "Shaman"},
            ],
        )
        self.assertIn(ERA_TITLE, summary)
        self.assertIn("Aldrea", summary)
        self.assertIn("aldrea@example.com", summary)
        self.assertIn("Email", summary)
        self.assertNotIn("Battle.net address", summary)
        self.assertIn("100", summary)
        self.assertIn("Mage", summary)
        self.assertIn("Drek", summary)
        self.assertIn("90", summary)
        self.assertIn("Shaman", summary)
        self.assertIn('href="/account/password"', summary)
        self.assertIn('href="/account/logout"', summary)
        self.assertIn('class="acct-notice"', summary)
        self.assertIn("acct-nav-current", summary)

    def test_dynamic_text_is_escaped(self):
        page = _page(
            "summary",
            user='<b>x</b>',
            email='a"@b.c',
            error="<bad>",
            characters=[{"name": "<i>n</i>", "level": 1, "class_name": "Mage&"}],
        )
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", page)
        self.assertIn("&lt;i&gt;n&lt;/i&gt;", page)
        self.assertIn("Mage&amp;", page)
        self.assertIn("&lt;bad&gt;", page)
        self.assertNotIn("<b>", page)
        self.assertNotIn("<i>", page)
