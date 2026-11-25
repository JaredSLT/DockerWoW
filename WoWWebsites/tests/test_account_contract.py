"""Every expansion's account page must log in, create, and change a password."""

import importlib
import unittest

from wowweb.account_ui import render_account
from wowweb.catalog import list_expansions


def _page(exp, mode, **extra):
    payload = dict(
        user="",
        error="",
        notice="",
        mode=mode,
        email="",
        characters=[],
        login_kind="email" if exp.proto == "bnet" or exp.id == "wod" else "account",
        separate_game_name=exp.proto == "bnet",
    )
    payload.update(extra)
    return render_account(exp, **payload)


class AccountContractTests(unittest.TestCase):
    def test_each_expansion_has_login_create_and_password_forms(self):
        for exp in list_expansions():
            login = _page(exp, "login", error="nope")
            self.assertIn('action="/account/login"', login, exp.id)
            self.assertIn('name="identity"', login, exp.id)
            if exp.id == "midnight":
                self.assertNotIn('name="password"', login, exp.id)
                step = _page(exp, "login-password", email="user@example.com")
                self.assertIn('name="password"', step, exp.id)
                self.assertIn('name="identity"', step, exp.id)
            else:
                self.assertIn('name="password"', login, exp.id)
            self.assertIn('class="acct-error"', login, exp.id)
            self.assertNotIn("private server", login.lower(), exp.id)
            self.assertNotIn("mariadb", login.lower(), exp.id)

            create = _page(exp, "create")
            self.assertIn('action="/account/create"', create, exp.id)
            self.assertIn('name="identity"', create, exp.id)
            self.assertIn('name="password"', create, exp.id)
            self.assertIn('name="confirm"', create, exp.id)
            if exp.proto == "bnet":
                self.assertIn('name="game_name"', create, exp.id)
            else:
                self.assertNotIn('name="game_name"', create, exp.id)

            summary = _page(
                exp,
                "summary",
                user="Aldrea",
                email="aldrea@example.com",
                notice="Password changed.",
                characters=[{"name": "Aldrea", "level": 60, "class_name": "Mage"}],
            )
            self.assertIn("Aldrea", summary, exp.id)
            self.assertIn('href="/account/password"', summary, exp.id)
            self.assertIn('class="acct-notice"', summary, exp.id)

            password = _page(exp, "password", user="Aldrea")
            self.assertIn('action="/account/password"', password, exp.id)
            self.assertIn('name="current"', password, exp.id)
            self.assertIn('name="password"', password, exp.id)
            self.assertIn('name="confirm"', password, exp.id)

            try:
                module = importlib.import_module(f"wowweb.account_ui.{exp.id}")
            except ModuleNotFoundError:
                module = importlib.import_module("wowweb.account_ui.fallback")
            if exp.id != "midnight":
                self.assertIn(module.ERA_TITLE, login, exp.id)
            self.assertIn(module.ERA_TITLE, summary, exp.id)
