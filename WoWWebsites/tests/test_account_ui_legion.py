"""Legion Battle.net account settings fragment."""

import unittest

from wowweb.account_ui import legion
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
    return legion.render(resolve("legion"), **payload)


class LegionAccountTests(unittest.TestCase):
    def test_era_title_login_password_and_game_name(self):
        self.assertEqual(legion.ERA_TITLE, "Account Settings")

        login = _page("login", error="nope <bad>")
        self.assertIn(legion.ERA_TITLE, login)
        self.assertIn('action="/account/login"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('type="email"', login)
        self.assertIn('name="password"', login)
        self.assertIn('href="/account/create"', login)
        self.assertIn('class="acct-error"', login)
        self.assertIn("nope &lt;bad&gt;", login)
        self.assertIn("no emailed password reset", login.lower())
        self.assertNotIn('name="game_name"', login)
        self.assertNotIn("private server", login.lower())
        self.assertNotIn("mariadb", login.lower())

        create = _page("create")
        self.assertIn(legion.ERA_TITLE, create)
        self.assertIn('action="/account/create"', create)
        self.assertIn('name="identity"', create)
        self.assertIn('type="email"', create)
        self.assertIn('name="game_name"', create)
        self.assertIn('maxlength="16"', create)
        self.assertIn("World of Warcraft account name", create)
        self.assertIn('name="password"', create)
        self.assertIn('name="confirm"', create)

        password = _page("password", user="Aldrea")
        self.assertIn(legion.ERA_TITLE, password)
        self.assertIn('action="/account/password"', password)
        self.assertIn('name="current"', password)
        self.assertIn('name="password"', password)
        self.assertIn('name="confirm"', password)
        self.assertIn('href="/account/"', password)
        self.assertIn("Password &amp; Security", password)

        summary = _page(
            "summary",
            user="Aldrea",
            email="aldrea@example.com",
            notice="Password changed.",
            characters=[{"name": "Aldrea", "level": 110, "class_name": "Mage"}],
        )
        self.assertIn(legion.ERA_TITLE, summary)
        self.assertIn("aldrea@example.com", summary)
        self.assertIn("Aldrea", summary)
        self.assertIn("110", summary)
        self.assertIn("Mage", summary)
        self.assertIn('href="/account/password"', summary)
        self.assertIn('href="/account/logout"', summary)
        self.assertIn('class="acct-notice"', summary)
        self.assertIn("Password changed.", summary)

    def test_escapes_dynamic_text_and_omits_game_name_when_not_separate(self):
        summary = _page(
            "summary",
            user='A<b>"c"',
            email="a&b@example.com",
            characters=[{"name": "N<x>", "level": 1, "class_name": "Warlock &amp;"}],
        )
        self.assertIn("A&lt;b&gt;&quot;c&quot;", summary)
        self.assertIn("a&amp;b@example.com", summary)
        self.assertIn("N&lt;x&gt;", summary)
        self.assertIn("Warlock &amp;amp;", summary)
        self.assertNotIn("<b>", summary)

        create = _page("create", login_kind="account", separate_game_name=False)
        self.assertIn('type="text"', create)
        self.assertNotIn('type="email"', create)
        self.assertNotIn('name="game_name"', create)
        self.assertIn(legion.ERA_TITLE, create)
