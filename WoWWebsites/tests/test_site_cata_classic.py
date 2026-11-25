"""Cataclysm Classic uses the May 2024 Classic shop shot as its shell."""

import unittest
from pathlib import Path

from wowweb.account_ui import cata_classic as account
from wowweb.catalog import resolve
from wowweb.html.era import cata_classic
from wowweb.html.guide import home_page
from wowweb.html.layout import layout

ROOT = Path(__file__).resolve().parents[1]
EXP = resolve("cata-classic")


def _home(dev: bool = False) -> str:
    body = home_page(EXP, [], {"up": True, "name": EXP.realm_name})
    return layout(EXP, "World of Warcraft", body, crumb="World of Warcraft", dev=dev)


class CataClassicShopTests(unittest.TestCase):
    def test_home_matches_the_classic_family_shop(self):
        page = _home()
        self.assertIn("Cataclysm Classic", page)
        self.assertIn("Subscriptions", page)
        self.assertIn("Begin your journey or renew your subscription.", page)
        self.assertIn("World of Warcraft®: Subscription", page)
        self.assertIn("World of Warcraft®: Special Subscription Offer", page)
        self.assertIn("WORLD OF WARCRAFT CLASSIC CATACLYSM", page)
        self.assertIn("Season of Discovery and Hardcore Realms!", page)
        self.assertIn("Auspicious Arborwyrm", page)
        self.assertIn("Kalu", page)
        self.assertIn("Whalebone Glider", page)
        self.assertIn("Re-Awakened Phase-Hunter Mount", page)
        self.assertIn("€25.00", page)
        self.assertIn("€15.00", page)
        self.assertIn("Learn More", page)
        self.assertIn(">NEW<", page)
        self.assertIn("/static/img/cata-classic/sub-cataclysm.jpg", page)
        self.assertIn("/static/img/cata-classic/mount-phasehunter.jpg", page)
        self.assertIn("/static/css/era-cata-classic.css", page)
        self.assertIn("/static/css/account-cata-classic.css", page)
        self.assertTrue((ROOT / "static/css/era-cata-classic.css").is_file())
        self.assertTrue((ROOT / "static/img/cata-classic/sub-offer.jpg").is_file())

    def test_shop_bar_is_the_visible_chrome(self):
        page = _home()
        for label in ("Warcraft", "Call of Duty", "Diablo", "Overwatch", "StarCraft", "More"):
            self.assertIn(label, page)
        self.assertIn("Search Shop", page)
        self.assertIn("Battle.net Balance", page)
        self.assertIn("World of Warcraft Classic", page)
        self.assertIn('href="/support/"', page)
        self.assertIn('href="/forums/general"', page)
        self.assertIn('href="/wow/realmstatus"', page)
        self.assertNotIn('class="bnet-menu"', page)
        self.assertNotIn(">HOME<", page)
        self.assertNotIn(">GAME<", page)
        self.assertNotIn(">COMMUNITY<", page)

    def test_public_copy_skips_the_lab_strip(self):
        page = _home()
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("MariaDB", page)
        self.assertNotIn("recreation", page.lower())
        loud = _home(dev=True)
        self.assertIn("Not affiliated", loud)

    def test_shop_route_is_the_same_family_page(self):
        taken = cata_classic.take("/shop", {"user": None, "exp": EXP, "dev": False})
        self.assertIsNotNone(taken)
        title, body = taken
        page = layout(EXP, title, body, crumb=title)
        self.assertIn("Cataclysm Classic", page)
        self.assertIn("Auspicious Arborwyrm", page)
        self.assertNotIn("Buy Now", page)
        self.assertNotIn("<!DOCTYPE", body)
        self.assertIsNone(cata_classic.full("/shop", {}))
        self.assertIsNone(cata_classic.take("/wow/news", {}))

    def test_signed_out_services_stay_on_the_site(self):
        taken = cata_classic.take("/account/services", {"user": None})
        self.assertIn("Sign in", taken[1])
        self.assertIn('href="/account/login"', taken[1])
        self.assertIsNone(cata_classic.take("/account/services", {"user": "Aldrea"}))

    def test_account_forms_match_the_contract(self):
        login = account.render(
            EXP,
            user="",
            error="nope",
            notice="",
            mode="login",
            email="",
            characters=[],
            login_kind="email",
            separate_game_name=True,
        )
        self.assertIn(account.ERA_TITLE, login)
        self.assertEqual(account.ERA_TITLE, "Account Management")
        self.assertIn('name="identity"', login)
        self.assertIn('name="password"', login)
        self.assertIn('class="acct-error"', login)
        self.assertNotIn('name="game_name"', login)
        create = account.render(
            EXP,
            user="",
            error="",
            notice="",
            mode="create",
            email="",
            characters=[],
            login_kind="email",
            separate_game_name=True,
        )
        self.assertIn('name="game_name"', create)
        self.assertIn('name="confirm"', create)
        self.assertIn('action="/account/create"', create)
