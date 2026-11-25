"""Classic Era shell, realm-status table, and forum category cards."""

import html
import tempfile
import unittest
from pathlib import Path

from wowweb.account_ui import classic_era as account
from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era import classic_era
from wowweb.html.guide import home_page
from wowweb.html.layout import layout
from wowweb.lab import load_lab, realm_status


BANNED = ("private server", "recreation", "mariadb", "not affiliated")


def _ctx(exp, qs=None, data_dir=None):
    return {
        "exp": exp,
        "user": None,
        "dev": False,
        "qs": qs or {},
        "path": "",
        "labcfg": load_lab(None),
        "data_dir": data_dir,
    }


class ClassicEraSiteTests(unittest.TestCase):
    def setUp(self):
        self.exp = resolve("classic-era")
        root = Path(__file__).resolve().parents[1] / "data"
        root.mkdir(parents=True, exist_ok=True)
        self._tmp = tempfile.TemporaryDirectory(dir=root)
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def ctx(self, qs=None):
        return _ctx(self.exp, qs, self.data_dir)

    def test_shell_is_the_classic_era_skin(self):
        page = layout(self.exp, "Realm Status", "<p>Body</p>")
        self.assertIn("/static/css/era-classic-era.css", page)
        self.assertIn("<p>Body</p>", page)
        self.assertIn("World of Warcraft Classic", page)
        self.assertIn('class="ce-title"', page)
        self.assertNotIn("vanilla2006", page)
        self.assertNotIn("ssotd-container", page)
        self.assertNotIn("bnet-menu", page)
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())
        dev = layout(self.exp, "Realm Status", "<p>Body</p>", dev=True)
        self.assertIn("Not affiliated", dev)

    def test_home_uses_live_news_and_not_the_2006_home(self):
        news = news_for(self.exp)
        realm = {"up": True, "name": "Classic Era", "population": "4", "type": "PvP"}
        body = home_page(self.exp, news, realm)
        self.assertIn(news[0][0], body)
        self.assertIn("Classic Era", body)
        self.assertIn("Population", body)
        self.assertNotIn("Welcome to the Arena", body)
        page = layout(self.exp, "World of Warcraft Community Site", body)
        self.assertIn(">World of Warcraft Classic<", page)
        self.assertNotIn("Community Site", page)
        for phrase in BANNED:
            self.assertNotIn(phrase, page.lower())

    def test_realm_status_matches_the_classic_tab(self):
        ctx = self.ctx()
        live = realm_status(ctx["labcfg"], self.exp)
        title, body = classic_era.take("/wow/realmstatus", ctx)
        self.assertEqual(title, "Realm Status")
        self.assertIn("World of Warcraft Classic", body)
        self.assertIn('class="is-selected"', body)
        self.assertIn("Service Status Forum", body)
        self.assertIn(">Status<", body)
        self.assertIn("Realm Name", body)
        self.assertIn(">Type<", body)
        self.assertIn(">Population<", body)
        self.assertIn(">Timezone<", body)
        self.assertIn(">Locale<", body)
        self.assertIn("Classic Era", body)
        self.assertIn("PST", body)
        self.assertIn("ce-dot", body)
        self.assertIn(html.escape(str(live.get("name") or ""), quote=True), body)
        self.assertNotIn("127.0.0.1", body)
        self.assertNotIn("MariaDB", body)
        for phrase in BANNED:
            self.assertNotIn(phrase, body.lower())
        page = layout(self.exp, title, body)
        self.assertEqual(page.lower().count("<h1"), 1)
        self.assertIn("era-classic-era", page)

    def test_realm_filters_do_not_invent_realms(self):
        ctx = self.ctx({"game": ["retail"]})
        _title, body = classic_era.take("/wow/realmstatus", ctx)
        self.assertIn("No realms match these filters.", body)
        self.assertNotIn("ce-dot", body)
        ctx = self.ctx({"q": ["zzzz-no-such-realm"]})
        _title, body = classic_era.take("/wow/realmstatus", ctx)
        self.assertNotIn("ce-dot", body)

    def test_forums_use_the_category_card(self):
        ctx = self.ctx()
        title, body = classic_era.take("/forums", ctx)
        self.assertEqual(title, "All Categories")
        self.assertIn("WoW Classic", body)
        self.assertIn("Everything about World of Warcraft Classic belongs in these forums.", body)
        self.assertIn('href="/forums/general"', body)
        self.assertIn("WoW Classic – General", body)
        self.assertIn("Categories", body)
        self.assertIn('class="is-on"', body)
        self.assertNotIn("border: 3px solid red", body)
        self.assertNotIn("recreation", body.lower())
        page = layout(self.exp, title, body)
        self.assertIn("ce-main-board", page)

    def test_guest_services_page_is_a_document_not_a_redirect_body(self):
        title, body = classic_era.take("/account/services", self.ctx())
        self.assertEqual(title, "Character Services")
        self.assertIn('href="/account/login"', body)
        signed = self.ctx()
        signed["user"] = "Aldrea"
        self.assertIsNone(classic_era.take("/account/services", signed))
        self.assertIsNone(classic_era.full("/wow/", {}))
        self.assertIsNone(classic_era.take("/wow/news", self.ctx()))

    def test_account_contract_fields(self):
        self.assertEqual(account.ERA_TITLE, "Account Management")
        login = account.render(
            self.exp,
            user="",
            error="<nope>",
            notice="",
            mode="login",
            email="",
            characters=[],
            login_kind="email",
            separate_game_name=True,
        )
        self.assertIn(account.ERA_TITLE, login)
        self.assertIn('action="/account/login"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('name="password"', login)
        self.assertIn("acct-error", login)
        self.assertIn("&lt;nope&gt;", login)
        self.assertNotIn("private server", login.lower())
        create = account.render(
            self.exp,
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


if __name__ == "__main__":
    unittest.main()
