import unittest

from wowweb import assets
from wowweb.catalog import ORDER, resolve
from wowweb.content.sections import SUPPORT_SLUGS
from wowweb.html.sections import (
    classic_page,
    esports_page,
    shop_page,
    story_page,
    support_article,
    support_index,
)

BANNED = ("local archive", "recreation", "private server", "mariadb", "not affiliated")


class SectionTests(unittest.TestCase):
    def test_arena_article_starts_in_tbc(self):
        self.assertIsNone(support_article(resolve("vanilla"), "arena"))
        self.assertIsNotNone(support_article(resolve("tbc"), "arena"))

    def test_dungeon_finder_starts_in_wrath(self):
        self.assertIsNone(support_article(resolve("vanilla"), "dungeon-finder"))
        self.assertIsNone(support_article(resolve("tbc"), "dungeon-finder"))
        self.assertIsNotNone(support_article(resolve("wotlk"), "dungeon-finder"))

    def test_password_article_has_no_emailed_reset(self):
        page = support_article(resolve("vanilla"), "password")
        self.assertIn("There is no emailed reset on this realm.", page)
        self.assertIn("There is no emailed reset on this realm.", support_article(resolve("legion"), "password"))

    def test_support_index_uses_shared_slugs(self):
        vanilla = support_index(resolve("vanilla"))
        for slug in ("stuck", "password", "addons", "talents", "honor"):
            self.assertIn(slug, SUPPORT_SLUGS)
            self.assertIn(f"/support/{slug}", vanilla)
        self.assertNotIn("/support/arena", vanilla)
        self.assertNotIn("/support/dungeon-finder", vanilla)
        tbc = support_index(resolve("tbc"))
        self.assertIn("/support/arena", tbc)
        self.assertNotIn("/support/dungeon-finder", tbc)
        self.assertIn("/support/dungeon-finder", support_index(resolve("wotlk")))
        midnight = support_index(resolve("midnight"))
        for slug in SUPPORT_SLUGS:
            self.assertIn(f"/support/{slug}", midnight)
        self.assertIsNone(support_article(resolve("legion"), "billing"))

    def test_shop_creates_an_account_and_takes_no_card(self):
        for era in ("vanilla", "tbc", "legion", "bfa", "midnight"):
            page = shop_page(resolve(era))
            self.assertNotIn("/account/create", page)
            self.assertNotIn("<input", page.lower())
            self.assertNotIn("<form", page.lower())
            self.assertNotIn("card number", page.lower())
            self.assertNotIn("cvv", page.lower())
            self.assertNotIn("payment", page.lower())
            self.assertNotIn("credit-card", page.lower())
            self.assertNotIn("credit card", page.lower())
            self.assertEqual(page.count("href="), 0)
            self.assertNotIn("<!DOCTYPE", page)
            self.assertNotIn("<html", page.lower())

    def test_bfa_shop_says_subscribe(self):
        self.assertIn("Subscribe", shop_page(resolve("bfa")))
        self.assertIn("Subscribe", shop_page(resolve("shadowlands")))
        for era in ("alpha", "vanilla", "tbc", "wotlk", "cata", "mop", "wod", "legion", "dragonflight", "warwithin", "midnight"):
            page = shop_page(resolve(era))
            self.assertIn("Buy Now", page)
            self.assertNotIn("Subscribe", page)

    def test_shop_section_carries_its_era(self):
        for era in ORDER:
            page = shop_page(resolve(era))
            self.assertIn(f'<section class="shop-shelf shop-{era}">', page)
            self.assertNotIn('href="/account/create"', page)
            self.assertIn("Nothing here is charged", page)

    def test_story_hero_is_a_local_loading_screen(self):
        for era in ORDER:
            page = story_page(resolve(era))
            shots = assets.screenshots(era, limit=1)
            src = shots[0][0] if shots else ""
            if not src.startswith("/static/"):
                self.assertNotIn("<img", page.lower())
                continue
            self.assertEqual(page.lower().count("<img"), 1)
            self.assertIn(f'src="{src}"', page)
            self.assertIn('class="hero"', page)
            self.assertNotIn("http://", page.lower())
            self.assertNotIn("https://", page.lower())

    def test_legion_story_names_the_isles_and_argus(self):
        page = story_page(resolve("legion"))
        self.assertTrue("Argus" in page or "Broken Isles" in page)
        self.assertIn("Argus", page)
        self.assertIn("Broken Isles", page)

    def test_stories_follow_the_era(self):
        self.assertIn("Outland", story_page(resolve("tbc")))
        self.assertIn("Northrend", story_page(resolve("wotlk")))
        self.assertIn("Cataclysm", story_page(resolve("cata")))
        self.assertIn("Pandaria", story_page(resolve("mop")))
        wod = story_page(resolve("wod"))
        self.assertIn("Draenor", wod)
        self.assertNotIn("Argus", wod)
        self.assertIn("Kul Tiras", story_page(resolve("bfa")))
        self.assertIn("Zandalar", story_page(resolve("bfa")))
        self.assertIn("Shadowlands", story_page(resolve("shadowlands")))
        self.assertIn("Dragon Isles", story_page(resolve("dragonflight")))
        self.assertIn("Khaz Algar", story_page(resolve("warwithin")))
        midnight = story_page(resolve("midnight"))
        self.assertIn("Thalas", midnight)
        self.assertIn("Void", midnight)

    def test_vanilla_esports_links_rankings(self):
        page = esports_page(resolve("vanilla"))
        self.assertIn("/wow/pvp/rankings", page)
        self.assertNotIn("/armory/arena", page)
        self.assertNotIn("Arena World Championship", page)

    def test_esports_split_by_era(self):
        tbc = esports_page(resolve("tbc"))
        self.assertIn("/wow/pvp/rankings", tbc)
        self.assertIn("/armory/arena", tbc)
        for era in ("legion", "bfa", "shadowlands", "dragonflight", "warwithin", "midnight"):
            page = esports_page(resolve(era))
            self.assertIn("Arena World Championship", page)
            self.assertIn("Mythic Dungeon International", page)
            self.assertIn(str(resolve(era).year), page)
            self.assertNotIn("/wow/pvp/rankings", page)
            self.assertNotIn("/armory/arena", page)
        wod = esports_page(resolve("wod"))
        self.assertIn("/wow/pvp/rankings", wod)
        self.assertIn("/armory/arena", wod)

    def test_classic_promo_starts_at_bfa(self):
        for era in ("bfa", "shadowlands", "dragonflight", "warwithin", "midnight"):
            page = classic_page(resolve(era))
            self.assertIn("WoW Classic", page)
            self.assertIn("original Azeroth", page)
            self.assertIn("1.12", page)
        for era in ("alpha", "vanilla", "tbc", "wotlk", "cata", "mop", "wod", "legion"):
            page = classic_page(resolve(era))
            self.assertIn("original world", page.lower())
            self.assertNotIn("WoW Classic", page)
        for era in ORDER:
            page = classic_page(resolve(era))
            self.assertNotIn("href=", page)
            self.assertNotIn("127.0.0.", page)

    def test_visitor_copy_avoids_archive_language(self):
        for era in ORDER:
            exp = resolve(era)
            pages = [
                support_index(exp),
                shop_page(exp),
                story_page(exp),
                esports_page(exp),
                classic_page(exp),
            ]
            for slug in SUPPORT_SLUGS:
                article = support_article(exp, slug)
                if article is not None:
                    pages.append(article)
            blob = "\n".join(pages).lower()
            for phrase in BANNED:
                self.assertNotIn(phrase, blob, msg=f"{era} contains {phrase}")


if __name__ == "__main__":
    unittest.main()
