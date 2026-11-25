"""Vanilla (November 2006) account management fragment."""

import re
import unittest
from pathlib import Path

import wowweb.account_ui.vanilla as vanilla
from wowweb.catalog import resolve

ROOT = Path(__file__).resolve().parents[1]


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
    return vanilla.render(resolve("vanilla"), **payload)


class VanillaAccountUiTests(unittest.TestCase):
    def test_era_title_login_action_and_current_password(self):
        self.assertEqual(vanilla.ERA_TITLE, "Account Management")
        login = _page("login", error="nope")
        self.assertIn(vanilla.ERA_TITLE, login)
        self.assertIn('method="post"', login)
        self.assertIn('action="/account/login"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('name="password"', login)
        self.assertIn('href="/account/create"', login)
        self.assertIn("There is no emailed password reset. Sign in and change the password here.", login)
        self.assertIn('class="acct-error"', login)
        password = _page("password", user="Aldrea")
        self.assertIn(vanilla.ERA_TITLE, password)
        self.assertIn('name="current"', password)
        self.assertIn('action="/account/password"', password)
        self.assertIn('href="/account/"', password)

    def test_every_mode_uses_account_name_and_escapes(self):
        for mode in ("login", "create", "password", "summary"):
            page = _page(mode, user="Aldrea" if mode in {"summary", "password"} else "")
            self.assertIn(vanilla.ERA_TITLE, page)
            self.assertNotIn('name="game_name"', page)
            self.assertNotIn("private server", page.lower())
            self.assertNotIn("mariadb", page.lower())
            self.assertNotIn('type="email"', page)

        create = _page("create", separate_game_name=True, login_kind="email")
        self.assertIn('action="/account/create"', create)
        self.assertIn('name="identity"', create)
        self.assertIn('name="password"', create)
        self.assertIn('name="confirm"', create)
        self.assertIn("Account Name", create)
        self.assertNotIn('name="game_name"', create)

        summary = _page(
            "summary",
            user='A"<ldrea>',
            email="a<b>@example.com",
            notice="Saved <b>ok</b>",
            error="Bad <i>try</i>",
            characters=[{"name": "<Aldrea>", "level": 60, "class_name": "Mage & Rogue"}],
        )
        self.assertIn("A&quot;&lt;ldrea&gt;", summary)
        self.assertIn("a&lt;b&gt;@example.com", summary)
        self.assertIn("Saved &lt;b&gt;ok&lt;/b&gt;", summary)
        self.assertIn("Bad &lt;i&gt;try&lt;/i&gt;", summary)
        self.assertIn("&lt;Aldrea&gt;", summary)
        self.assertIn("Mage &amp; Rogue", summary)
        self.assertIn("<th>Name</th><th>Level</th><th>Class</th>", summary)
        self.assertIn(">60<", summary)
        self.assertIn('class="acct-notice"', summary)
        self.assertIn('href="/account/password"', summary)
        self.assertIn('href="/account/logout"', summary)
        self.assertIn("Account Summary", summary)
        self.assertIn("Change Password", summary)
        self.assertIn("Create Account", summary)

    def test_css_classes_start_with_acct(self):
        css = (ROOT / "static" / "css" / "account-vanilla.css").read_text(encoding="utf-8")
        selectors = re.findall(r"\.([A-Za-z_][\w-]*)", css)
        self.assertTrue(selectors)
        for name in selectors:
            self.assertTrue(name.startswith("acct-"), name)
        page = _page("summary", user="Aldrea", characters=[{"name": "Aldrea", "level": 60, "class_name": "Mage"}])
        for attr in re.findall(r'class="([^"]+)"', page):
            for name in attr.split():
                self.assertTrue(name.startswith("acct-"), name)
