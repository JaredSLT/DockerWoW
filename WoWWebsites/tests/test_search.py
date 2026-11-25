import shutil
import tempfile
import unittest
from pathlib import Path

from wowweb import forums
from wowweb.catalog import resolve
from wowweb.lab import LabConfig
from wowweb.search import search, support_articles


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.cfg = LabConfig(root=Path("/tmp/wowweb-search-dummy-root"))
        self.vanilla = resolve("vanilla")
        self.tbc = resolve("tbc")
        self.data = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.data, ignore_errors=True)

    def test_empty_query_returns_nothing(self):
        for query in ("", " ", "\t", "\n"):
            for search_type in ("site", "", "encyclopedia", "ingamesupport", "techsupport"):
                self.assertEqual(search(self.cfg, self.vanilla, self.data, query, search_type), [])

    def test_site_finds_vanilla_news_and_race(self):
        news = search(self.cfg, self.vanilla, self.data, "The Burning Crusade Street Date Announced", "site")
        self.assertTrue(
            any("The Burning Crusade Street Date Announced" in hit["title"] and hit["href"].startswith("/wow/news/") for hit in news)
        )
        races = search(self.cfg, self.vanilla, self.data, "nIGHT eLF", "")
        self.assertTrue(
            any(
                hit["title"] == "Night Elf"
                and hit["href"] == "/wow/info/races/nightelf"
                and hit["kind"] == "race"
                for hit in races
            )
        )
        self.assertLessEqual(len(search(self.cfg, self.vanilla, self.data, "a", "site")), 25)

    def test_encyclopedia_skips_forum_only_noise(self):
        conn = forums.connect(self.data)
        forums.create_thread(
            conn,
            self.vanilla,
            "general",
            "Tester",
            "Zxq Forum Only Needle",
            "This thread is not an encyclopedia entry.",
        )
        conn.close()
        encyclopedia = search(self.cfg, self.vanilla, self.data, "Zxq Forum Only Needle", "encyclopedia")
        self.assertEqual(encyclopedia, [])
        site = search(self.cfg, self.vanilla, self.data, "Zxq Forum Only Needle", "site")
        self.assertTrue(any(hit["kind"] == "thread" and hit["href"].startswith("/forums/general/") for hit in site))
        tauren = search(self.cfg, self.vanilla, self.data, "Tauren", "encyclopedia")
        self.assertTrue(any(hit["kind"] == "race" and hit["href"] == "/wow/info/races/tauren" for hit in tauren))
        self.assertFalse(any(hit["kind"] == "thread" for hit in tauren))

    def test_arena_support_follows_the_expansion(self):
        vanilla_hits = search(self.cfg, self.vanilla, self.data, "arena", "ingamesupport")
        self.assertFalse(any(hit["href"] == "/support/arena" for hit in vanilla_hits))
        self.assertNotIn("arena", [article["slug"] for article in support_articles(self.vanilla)])
        self.assertNotIn("dungeon-finder", [article["slug"] for article in support_articles(self.vanilla)])
        tbc_hits = search(self.cfg, self.tbc, self.data, "arena", "ingamesupport")
        self.assertTrue(any(hit["href"] == "/support/arena" and hit["kind"] == "support" for hit in tbc_hits))
        arena = next(article for article in support_articles(self.tbc) if article["slug"] == "arena")
        self.assertEqual(arena["audience"], "game")
        self.assertNotIn("dungeon-finder", [article["slug"] for article in support_articles(self.tbc)])
        self.assertIn("dungeon-finder", [article["slug"] for article in support_articles(resolve("wotlk"))])

    def test_tech_support_returns_a_connection_article(self):
        hits = search(self.cfg, self.vanilla, self.data, "connection", "techsupport")
        self.assertTrue(any(hit["href"] == "/support/connection-failed" and hit["kind"] == "tech" for hit in hits))
        article = next(item for item in support_articles(self.vanilla) if item["slug"] == "connection-failed")
        self.assertEqual(article["audience"], "tech")
        self.assertIn("connection", article["summary"].casefold())
        self.assertNotIn("recreation", article["body"].casefold())
        self.assertNotIn("archive", article["body"].casefold())

    def test_password_article_does_not_invent_a_mailer(self):
        article = next(item for item in support_articles(self.vanilla) if item["slug"] == "forgot-password")
        body = article["body"].casefold()
        self.assertIn("does not email a reset", body)
        self.assertIn("create the account again only if it is yours", body)
        self.assertNotIn("mailer", body)
        hits = search(self.cfg, self.vanilla, self.data, "password", "ingamesupport")
        self.assertTrue(any(hit["href"] == "/support/forgot-password" for hit in hits))

    def test_missing_forum_file_is_skipped(self):
        blocked = self.data / "not-a-directory"
        blocked.write_text("nope", encoding="utf-8")
        hits = search(self.cfg, self.vanilla, blocked, "Human", "site")
        self.assertTrue(any(hit["href"] == "/wow/info/races/human" for hit in hits))

    def test_item_query_escapes_quotes_without_a_database(self):
        import wowweb.search as search_mod

        seen = {}

        def fake_rows(cfg, sql, db=""):
            seen["sql"] = sql
            return [["123", "O'Brien's Sword"]]

        original = search_mod.mysql_rows
        search_mod.mysql_rows = fake_rows
        try:
            hits = search(self.cfg, self.vanilla, self.data, "O'Brien", "encyclopedia")
        finally:
            search_mod.mysql_rows = original
        sql = seen["sql"]
        self.assertIn("`vanilla_world`.`item_template`", sql)
        self.assertIn("name LIKE '%O''Brien%'", sql)
        self.assertIn("LIMIT 25", sql)
        self.assertTrue(any(hit["title"] == "O'Brien's Sword" and hit["href"] == "/armory/item/123" for hit in hits))
        self.assertTrue(any(hit["kind"] == "race" for hit in search(self.cfg, self.vanilla, self.data, "Orc", "encyclopedia")))


if __name__ == "__main__":
    unittest.main()
