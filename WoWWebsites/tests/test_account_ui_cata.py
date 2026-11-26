"""Cataclysm Services account panel."""

import unittest
from pathlib import Path

import wowweb.account_ui.cata as cata
from wowweb.catalog import resolve

ROOT = Path(__file__).resolve().parents[1]


class CataAccountServicesTests(unittest.TestCase):
    def setUp(self):
        self.exp = resolve("cata")

    def render(self, mode, **extra):
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
        return cata.render(self.exp, **payload)

    def test_login_create_password_and_summary(self):
        login = self.render("login", error='nope <b>')
        self.assertEqual(cata.ERA_TITLE, "Account Services")
        self.assertIn(cata.ERA_TITLE, login)
        self.assertIn('action="/account/login"', login)
        self.assertIn('method="post"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('name="password"', login)
        self.assertIn('href="/account/create"', login)
        self.assertIn('class="acct-error"', login)
        self.assertIn("nope &lt;b&gt;", login)
        self.assertIn("Email Address", login)
        self.assertNotIn('type="email"', login)
        self.assertNotIn('name="game_name"', login)
        self.assertNotIn("private server", login.lower())
        self.assertNotIn("mariadb", login.lower())
        self.assertIn("no emailed password reset", login.lower())
        for label in ("Account Summary", "Change Password", "Character Services"):
            self.assertIn(label, login)

        create = self.render("create", separate_game_name=True, login_kind="email")
        self.assertIn(cata.ERA_TITLE, create)
        self.assertIn('action="/account/create"', create)
        self.assertIn('name="identity"', create)
        self.assertIn('name="password"', create)
        self.assertIn('name="confirm"', create)
        self.assertNotIn('name="game_name"', create)
        self.assertNotIn('type="email"', create)

        password = self.render("password", user="Aldrea")
        self.assertIn(cata.ERA_TITLE, password)
        self.assertIn('action="/account/password"', password)
        self.assertIn('name="current"', password)
        self.assertIn('name="password"', password)
        self.assertIn('name="confirm"', password)
        self.assertIn('href="/account/"', password)

        summary = self.render(
            "summary",
            user="Aldrea",
            notice="Password changed.",
            characters=[
                {"name": "Aldrea", "level": 85, "class_name": "Mage"},
                {"name": "A <B>", "level": 80, "class_name": "Warrior"},
            ],
        )
        self.assertIn(cata.ERA_TITLE, summary)
        self.assertIn("Aldrea", summary)
        self.assertIn("level 85", summary)
        self.assertIn("Mage", summary)
        self.assertIn("A &lt;B&gt;", summary)
        self.assertIn("Warrior", summary)
        self.assertIn('href="/account/password"', summary)
        self.assertIn('href="/account/logout"', summary)
        self.assertIn('class="acct-notice"', summary)
        self.assertIn('id="acct-characters"', summary)
        self.assertNotIn("aldrea@example.com", summary)
        self.assertNotIn('name="game_name"', summary)

    def test_stylesheet_is_stone_and_red(self):
        css = (ROOT / "static" / "css" / "account-cata.css").read_text(encoding="utf-8")
        self.assertIn(".acct-cata", css)
        self.assertIn("#1a0f08", css)
        self.assertIn("#a32020", css)
        self.assertNotIn("private server", css.lower())
        self.assertNotIn("mariadb", css.lower())


if __name__ == "__main__":
    unittest.main()
