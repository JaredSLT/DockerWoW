"""Shadowlands community shell against the accepted 2021–2022 references."""

import tempfile
import unittest
from pathlib import Path

from wowweb.catalog import resolve
from wowweb.content.news import news_for
from wowweb.html.era import shadowlands as sl
from wowweb.html.guide import home_page
from wowweb.html.layout import layout

BANNED = ("private server", "recreation", "mariadb", "not affiliated")


def _exp():
    return resolve("shadowlands")


def _ctx(path, **extra):
    payload = {
        "exp": _exp(),
        "user": None,
        "dev": False,
        "qs": {},
        "path": path,
        "labcfg": None,
        "data_dir": None,
    }
    payload.update(extra)
    return payload


def _page(title, body, dev=False):
    return sl.shell(_exp(), title, body, None, title, dev)


class ShadowlandsSiteTests(unittest.TestCase):
    def test_shell_uses_the_july_2022_bar_without_a_screenshot_rail(self):
        page = _page("Page", "<p>Body</p>")
        self.assertIn('href="/wow/info">Game', page)
        self.assertIn('href="/wow/news">News', page)
        self.assertIn('href="/forums">Forums', page)
        self.assertIn('href="/shop">Shop', page)
        self.assertIn('href="/esports">Esports', page)
        self.assertIn('href="/classic">WoW Classic', page)
        self.assertIn('href="/shop">Subscribe', page)
        self.assertNotIn("ssotd-container", page)
        self.assertNotIn("Try Free", page)
        lowered = page.lower()
        for phrase in BANNED:
            self.assertNotIn(phrase, lowered)

    def test_dev_footer_is_opt_in(self):
        quiet = _page("Page", "<p>Body</p>")
        loud = _page("Page", "<p>Body</p>", dev=True)
        self.assertNotIn("Not affiliated", quiet)
        self.assertIn("Not affiliated", loud)

    def test_home_is_the_dragonflight_pre_purchase(self):
        exp = _exp()
        news = news_for(exp)
        page = layout(exp, "Home", home_page(exp, news, {"up": True, "name": "Shadowlands"}))
        self.assertIn("Pre-Purchase Dragonflight", page)
        self.assertIn("Dragon Isles", page)
        self.assertIn("Drakks", page)
        self.assertIn("View all news", page)
        self.assertIn('href="/shop">Subscribe', page)
        self.assertNotIn("Dragonflight is now live", page)
        self.assertNotIn("ssotd-container", page)
        for title, _date, _body in news:
            self.assertIn(title, page)
        self.assertNotIn("evoker", page.lower())

    def test_news_index_and_article_use_live_stories(self):
        exp = _exp()
        news = news_for(exp)
        index = sl.shell(exp, "News", sl.take("/wow/news", _ctx("/wow/news"))[1], None, "News", False)
        self.assertIn('href="/wow/news/0"', index)
        self.assertIn(news[0][0], index)
        self.assertIn('href="/shop">Subscribe', index)
        title, body = sl.take("/wow/news/0", _ctx("/wow/news/0"))
        article = sl.shell(exp, title, body, None, title, False)
        self.assertIn(news[0][0], article)
        self.assertIn("by Blizzard Entertainment", article)
        self.assertIn('href="/account/login">Log In', article)
        self.assertIn('href="/trial">Try Free', article)
        self.assertIn('href="/shop">Subscribe', article)
        self.assertIsNone(sl.take("/wow/news/99", _ctx("/wow/news/99")))

    def test_human_guide_closes_the_2021_shell(self):
        title, body = sl.take("/wow/info/races/human", _ctx("/wow/info/races/human"))
        page = sl.shell(_exp(), title, body, None, title, False)
        self.assertEqual(title, "Human")
        self.assertIn(">Human<", page)
        self.assertIn("Home City: Stormwind", page)
        self.assertIn("Racial Mount: Horse", page)
        self.assertIn("Leader: King Anduin Wrynn", page)
        self.assertIn("Available Classes", page)
        self.assertIn("Racial Traits", page)
        self.assertIn("Will to Survive", page)
        self.assertIn('href="/trial">Try Free', page)
        self.assertNotIn("Evoker", page)
        self.assertIn('href="/wow/info/races/human"', sl.take("/wow/info/races", _ctx("/wow/info/races"))[1])
        guide = sl.take("/wow/info", _ctx("/wow/info"))[1]
        self.assertIn("Game Guide", guide)
        self.assertNotIn("Evoker", guide)
        self.assertNotIn("Dragon Isles", guide)

    def test_realm_status_has_three_games_and_no_wrath_tab(self):
        _title, body = sl.take("/wow/realmstatus", _ctx("/wow/realmstatus"))
        page = sl.shell(_exp(), "Realm Status", body, None, "Realm Status", False)
        self.assertIn("Realm Status", page)
        self.assertIn("World of Warcraft Classic", page)
        self.assertIn("Burning Crusade Classic", page)
        self.assertIn("Service Status Forum", page)
        self.assertIn(">Status<", page)
        self.assertIn(">Realm Name<", page)
        self.assertIn(">Population<", page)
        self.assertNotIn("Wrath Classic", page)
        self.assertNotIn("Wrath of the Lich King Classic", page)
        self.assertNotIn("mariadb", page.lower())
        self.assertIn('href="/shop">Subscribe', page)

    def test_classic_promo_and_trial(self):
        classic = sl.take("/classic", _ctx("/classic"))[1]
        self.assertIn("The Dark Portal Reopens Soon", classic)
        self.assertIn("Burning Crusade", classic)
        self.assertNotIn("Dragonflight is now live", classic)
        trial = sl.shell(_exp(), "Free Trial", sl.take("/trial", _ctx("/trial"))[1], None, "Free Trial", False)
        self.assertIn("play FREE up to Level 20", trial)
        self.assertIn("World of Warcraft® Free Trial", trial)
        self.assertIn('href="/trial">Try Free', trial)
        self.assertIn("Download WoW", trial)

    def test_shop_matches_the_battle_net_shelf(self):
        page = sl.full("/shop", _ctx("/shop"))
        self.assertIn("Black Ops", page)
        self.assertIn("Cold War", page)
        self.assertIn("Sale ends August 2", page)
        self.assertIn("Special Subscription Offer", page)
        self.assertIn("Burning Crusade Classic", page)
        self.assertIn("Diablo® II: Resurrected", page)
        self.assertNotIn("<form method=\"post\"", page.lower())
        self.assertNotIn("card number", page.lower())
        self.assertNotIn("cvv", page.lower())
        lowered = page.lower()
        for phrase in BANNED:
            self.assertNotIn(phrase, lowered)

    def test_forums_index_and_bug_report_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx = _ctx("/forums", data_dir=Path(tmp))
            index = sl.full("/forums", ctx)
            self.assertIn("All Categories", index)
            self.assertIn("General Discussion", index)
            self.assertIn("Bug Report", index)
            self.assertIn(">Classes<", index)
            self.assertNotIn("Evoker", index)
            self.assertNotIn("mailto:", index)
            board = sl.full("/forums/bugs", _ctx("/forums/bugs", data_dir=Path(tmp), qs={"view": ["latest"]}))
            self.assertIn("Bug Report", board)
            self.assertIn(">Topic<", board)
            self.assertIn(">Author<", board)
            self.assertIn(">Replies<", board)
            self.assertIn(">Views<", board)
            self.assertIn(">Activity<", board)
            self.assertIn("Blizz Tracker", board)
            self.assertNotIn("mailto:", board)
            general = sl.full("/forums/general", _ctx("/forums/general", data_dir=Path(tmp)))
            self.assertIn("General Discussion", general)
            self.assertIn(">Topic<", general)

    def test_profile_tabs_are_english(self):
        char = {
            "name": "Lurog",
            "level": 60,
            "race": "Orc",
            "class": "Hunter",
            "realm": "Shadowlands",
            "achievements": 12,
            "equipment": [
                {"slot": "Head", "item_id": 100, "name": "Shadow Helm", "display_id": 0},
            ],
            "guild": None,
        }
        page = sl.shell(_exp(), "Lurog", sl.character_profile(_exp(), char), None, "Lurog", False)
        for label in (
            "Character",
            "Achievements",
            "Collections",
            "Dungeons &amp; Raids",
            "Player vs Player",
            "Reputation",
        ):
            self.assertIn(label, page)
        self.assertIn("Lurog", page)
        self.assertIn("60", page)
        self.assertIn("Orc", page)
        self.assertIn("Hunter", page)
        self.assertIn('href="/shop">Subscribe', page)
        self.assertNotIn("Evoker", page)
        self.assertNotIn("ssotd-container", page)

    def test_logged_out_services_answer(self):
        page = sl.full("/account/services", _ctx("/account/services"))
        self.assertIn("Character Services", page)
        self.assertIn('href="/account/login"', page)
        self.assertIsNone(sl.full("/account/services", _ctx("/account/services", user="Aldrea")))
        self.assertIsNone(sl.full("/missing", _ctx("/missing")))


if __name__ == "__main__":
    unittest.main()
