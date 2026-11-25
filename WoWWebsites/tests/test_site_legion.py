"""Legion masthead, live sections, and the Battle.net shop gate."""

import tempfile
import unittest
from pathlib import Path

from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era import legion
from wowweb.html.guide import home_page
from wowweb.html.layout import layout


def _ctx(path="/", **extra):
    ctx = {
        "exp": resolve("legion"),
        "user": None,
        "dev": False,
        "qs": {},
        "path": path,
        "labcfg": None,
        "data_dir": None,
    }
    ctx.update(extra)
    return ctx


class LegionSiteTests(unittest.TestCase):
    def test_shell_matches_the_2016_masthead(self):
        page = layout(resolve("legion"), "Page", "<p>Body</p>")
        self.assertIn("<p>Body</p>", page)
        self.assertIn(">Game<", page)
        self.assertIn(">Story<", page)
        self.assertIn(">News<", page)
        self.assertIn(">Forums<", page)
        self.assertIn(">Shop<", page)
        self.assertIn('href="/story"', page)
        self.assertIn('href="/shop"', page)
        self.assertIn('href="/esports"', page)
        self.assertIn('href="/support/"', page)
        self.assertIn('href="/account/">Your Account', page)
        self.assertNotIn('href="/account/">Shop', page)
        self.assertNotIn("ssotd-container", page)
        self.assertNotIn("Not affiliated", page)
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("mariadb", page.lower())
        self.assertIn("New Players: Getting Started", page)
        self.assertIn("Talent Calculator", page)
        self.assertIn("Realm Status", page)
        self.assertIn("Dungeons, Raids, Scenarios", page)
        self.assertIn("/static/css/era-legion.css", page)
        self.assertIn("Try Free", page)
        self.assertIn('href="/account/login"', page)
        self.assertIn('href="/account/create"', page)

    def test_dev_footer_is_opt_in_and_sign_in_is_named(self):
        exp = resolve("legion")
        quiet = layout(exp, "Page", "<p>Body</p>", dev=False)
        loud = layout(exp, "Page", "<p>Body</p>", dev=True, user="Aldrea")
        self.assertNotIn("Not affiliated", quiet)
        self.assertIn("Not affiliated", loud)
        self.assertIn("Aldrea", loud)
        self.assertIn('href="/account/logout"', loud)

    def test_home_is_the_legion_arrival(self):
        exp = resolve("legion")
        news = news_for(exp)
        body = home_page(exp, news, {"up": False, "error": "MariaDB unreachable", "name": "Legion"})
        page = layout(exp, "Home", body)
        self.assertIn("LEGION ARRIVES 08.30.16", page)
        self.assertIn("Learn More", page)
        self.assertIn("Pre-Purchase", page)
        self.assertIn("Latest News", page)
        self.assertIn(news[0][0], body)
        self.assertIn('href="/wow/news/0"', body)
        self.assertNotIn("from the lab", page.lower())
        self.assertNotIn("mariadb", page.lower())
        self.assertNotIn("private server", page.lower())
        self.assertNotIn("recreation", page.lower())
        self.assertNotIn("ssotd", page.lower())
        self.assertNotIn("Not affiliated", page)

    def test_classes_story_news_and_talents(self):
        classes = legion.take("/wow/info/classes", _ctx())[1]
        self.assertIn(">Classes<", classes)
        self.assertIn("Warrior", classes)
        self.assertIn("Paladin", classes)
        self.assertIn("Demon Hunter", classes)
        self.assertIn("Outlaw", classes)
        self.assertIn('href="/wow/info/classes/priest"', classes)

        talents = legion.take(
            "/wow/info/classes/priest/talents.html",
            _ctx(qs={"spec": ["holy"]}),
        )[1]
        self.assertIn("Talent Calculator", talents)
        self.assertIn("Priest", talents)
        self.assertIn("Discipline", talents)
        self.assertIn("Holy", talents)
        self.assertIn("Shadow", talents)
        self.assertIn("Warrior", talents)
        self.assertIn("Demon Hunter", talents)
        self.assertIn("Choose a Specialization", talents)
        self.assertIn("Choose Talents", talents)
        self.assertIn('class="lg-spec is-on" data-tree="1"', talents)
        self.assertIn('class="lg-pick', talents)
        self.assertIn("addEventListener", talents)
        self.assertIn('href="/wow/info/classes/demonhunter/talents.html"', talents)

        story = legion.take("/story", _ctx())[1]
        self.assertIn("Illidan Stormrage", story)
        self.assertIn("The Betrayer", story)
        self.assertIn("Illidari", story)
        self.assertIn("Night Elf", story)
        self.assertIn("Broken Isles", story)
        self.assertIn("Argus", story)

        news = news_for(resolve("legion"))
        index = legion.take("/wow/news", _ctx())[1]
        self.assertIn(news[0][0], index)
        self.assertIn('href="/wow/news/0"', index)
        article = legion.take("/wow/news/0", _ctx())
        self.assertEqual(article[0], news[0][0])
        self.assertIn(news[0][0], article[1])
        self.assertIsNone(legion.take("/wow/news/99", _ctx()))

    def test_forums_use_live_boards_and_not_fake_threads(self):
        index = legion.take("/forums", _ctx())[1]
        self.assertIn("Welcome to the official World of Warcraft forums", index)
        self.assertIn("Legion Order Hall Campaigns and Missions", index)
        self.assertIn('href="/forums/classhalls"', index)
        self.assertIn('href="/forums/general"', index)
        self.assertIn('href="/support/"', index)
        self.assertNotIn("PTR Discussion", index)
        self.assertNotIn("Kaivax", index)
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx(data_dir=Path(tmp))
            board = legion.take("/forums/classhalls", ctx)[1]
            self.assertIn("Legion Order Hall Campaigns and Missions", board)
            self.assertIn("World of Warcraft", board)
            self.assertIn("New Topic", board)
            self.assertIn("No threads yet.", board)
            self.assertNotIn("Demon Hunter Artifact and Order Hall Feedback", board)
            self.assertNotIn("Kaivax", board)
        self.assertIsNone(legion.take("/forums/not-a-board", _ctx()))

    def test_shop_is_the_two_card_gate_and_one_product(self):
        shop = legion.full("/shop", _ctx("/shop"))
        self.assertIn("Complete Collection", shop)
        self.assertIn("Save 25%", shop)
        self.assertIn("GBP 9.99", shop)
        self.assertIn("GBP 29.99", shop)
        self.assertIn("GBP 39.99", shop)
        self.assertEqual(shop.count("Buy Now"), 2)
        self.assertIn("Nothing here is charged", shop)
        self.assertIn('href="/shop/battletag"', shop)
        self.assertNotIn("<form", shop.lower())
        self.assertNotIn("card number", shop.lower())
        self.assertNotIn("ssotd-container", shop)
        product = legion.full("/shop/battletag", _ctx())
        self.assertIn("BattleTag Change", product)
        self.assertIn("GBP 8.00", product)
        self.assertNotIn("<form", product.lower())

    def test_account_gate_and_services_without_a_session(self):
        login = legion.full("/account/login", _ctx())
        self.assertIn("Account Settings", login)
        self.assertIn('action="/account/login"', login)
        self.assertIn('name="identity"', login)
        self.assertIn('type="email"', login)
        self.assertIn('name="password"', login)
        self.assertNotIn("ssotd-container", login)
        self.assertNotIn("private server", login.lower())
        services = legion.full("/account/services", _ctx())
        self.assertIn("Character Services", services)
        self.assertIn('href="/account/login"', services)
        self.assertIn('href="/support/"', services)
        self.assertIsNone(legion.full("/account/services", _ctx(user="Aldrea")))
        self.assertIsNone(legion.full("/account/password", _ctx()))

    def test_esports_stays_a_simple_page_in_the_shell(self):
        page = layout(resolve("legion"), "Esports", "<section class=\"esports\"><h2>Esports</h2></section>")
        self.assertIn("Esports", page)
        self.assertIn(">Game<", page)
        self.assertNotIn("ssotd-container", page)


if __name__ == "__main__":
    unittest.main()
