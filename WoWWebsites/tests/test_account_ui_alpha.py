"""Alpha account card: 2004 login box, then the same card after sign-in."""

import unittest
from html import escape

from wowweb.account_ui import alpha
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
    return alpha.render(resolve("alpha"), **payload)


class AlphaAccountUiTests(unittest.TestCase):
    def test_era_title_login_action_and_current_password(self):
        login = _page("login", error="nope <script>")
        self.assertIn(alpha.ERA_TITLE, login)
        self.assertEqual(alpha.ERA_TITLE, "Account Login")
        self.assertIn('action="/account/login"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('name="password"', login)
        self.assertIn('href="/account/create"', login)
        self.assertIn('class="acct-error"', login)
        self.assertIn(escape("nope <script>"), login)
        self.assertIn("There is no emailed reset. Sign in and change the password here.", login)

        password = _page("password", user="Aldrea")
        self.assertIn(alpha.ERA_TITLE, password)
        self.assertIn('action="/account/password"', password)
        self.assertIn('name="current"', password)
        self.assertIn('name="password"', password)
        self.assertIn('name="confirm"', password)
        self.assertIn('href="/account/"', password)

    def test_create_summary_and_escaped_characters(self):
        create = _page("create", separate_game_name=True)
        self.assertIn("Create Account", create)
        self.assertNotIn(f"<h2 class=\"acct-title\">{alpha.ERA_TITLE}</h2>", create)
        self.assertIn('action="/account/create"', create)
        self.assertIn('name="identity"', create)
        self.assertIn('name="password"', create)
        self.assertIn('name="confirm"', create)
        self.assertNotIn('name="game_name"', create)

        summary = _page(
            "summary",
            user="Ald<rea>",
            email="aldrea@example.com",
            notice="Saved & done",
            characters=[{"name": "Mage<One>", "level": 10, "class_name": "Mage & more"}],
        )
        self.assertIn(alpha.ERA_TITLE, summary)
        self.assertIn(escape("Ald<rea>"), summary)
        self.assertIn(escape("Mage<One>"), summary)
        self.assertIn("10", summary)
        self.assertIn(escape("Mage & more"), summary)
        self.assertIn('class="acct-notice"', summary)
        self.assertIn(escape("Saved & done"), summary)
        self.assertIn('href="/account/password"', summary)
        self.assertIn('href="/account/logout"', summary)
        self.assertNotIn('name="game_name"', summary)
        self.assertLess(summary.find("Ald&lt;rea&gt;"), summary.find("Mage&lt;One&gt;"))
