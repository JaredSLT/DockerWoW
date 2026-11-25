import unittest
from html import unescape
from pathlib import Path

from wowweb import content
from wowweb.catalog import resolve

ROOT = Path(__file__).resolve().parents[1]
BANNED = ("local lab", "recreation", "private server")


class NewsCaptureTests(unittest.TestCase):
    def test_vanilla_opens_with_the_street_date(self):
        title, date, _body = content.news_for(resolve("vanilla"))[0]
        self.assertEqual(title, "The Burning Crusade Street Date Announced")
        self.assertEqual(date, "2006-11-09")

    def test_alpha_opens_with_the_items_post(self):
        title, _date, body = content.news_for(resolve("alpha"))[0]
        self.assertEqual(title, "World of Warcraft Items:")
        sentence = (
            "The game world is simply massive and there are tons of things to do, "
            "for both solo adventurers and groups of adventurers."
        )
        capture = (ROOT / "references" / "alpha" / "home.html").read_text(encoding="utf-8")
        self.assertIn(sentence, capture)
        self.assertIn(sentence, body)

    def test_wotlk_first_title_is_on_the_capture(self):
        news = content.news_for(resolve("wotlk"))
        self.assertTrue(news)
        capture = (ROOT / "references" / "wotlk" / "home.html").read_text(encoding="utf-8")
        self.assertIn(news[0][0], capture)

    def test_later_expansions_open_with_captured_headlines(self):
        for exp_id in (
            "cata",
            "mop",
            "wod",
            "legion",
            "bfa",
            "shadowlands",
            "dragonflight",
            "warwithin",
            "midnight",
        ):
            title = content.news_for(resolve(exp_id))[0][0]
            capture = (ROOT / "references" / exp_id / "home.html").read_text(encoding="utf-8")
            self.assertIn(title, unescape(capture), exp_id)

    def test_tbc_opens_with_the_august_feed(self):
        title, date, body = content.news_for(resolve("tbc"))[0]
        self.assertEqual(title, "World of Warcraft Arena in College Gaming League")
        self.assertEqual(date, "2008-08-28")
        self.assertEqual(body, "Posted by Nebu.")
        capture = (ROOT / "references" / "tbc" / "community.html").read_text(encoding="utf-8")
        self.assertIn(title, capture)

    def test_captured_feeds_do_not_describe_a_lab(self):
        for exp_id in ("alpha", "vanilla", "tbc", "wotlk"):
            blob = "\n".join(
                f"{title}\n{date}\n{body}" for title, date, body in content.news_for(resolve(exp_id))
            ).casefold()
            for phrase in BANNED:
                self.assertNotIn(phrase, blob)
