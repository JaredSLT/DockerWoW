import unittest

from wowweb import accounts, content, forums, html as H
from wowweb.catalog import ORDER, resolve
from wowweb.lab import realm_type_label
from wowweb.talents import classes_for, encode_build, parse_build, trees_for


class CatalogTests(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(resolve("wrath").id, "wotlk")
        self.assertEqual(resolve("wotlk").id, "wotlk")
        self.assertEqual(resolve("bc").id, "tbc")
        self.assertEqual(resolve("classic").id, "vanilla")
        self.assertEqual(resolve("wow-classic-era").id, "classic-era")
        self.assertEqual(resolve("wrath-classic").id, "wotlk-classic")
        self.assertEqual(resolve("tww").id, "warwithin")
        self.assertIsNone(resolve("beta"))

    def test_order_has_no_beta(self):
        self.assertNotIn("beta", ORDER)
        self.assertIn("alpha", ORDER)
        self.assertIn("midnight", ORDER)

    def test_visual_chrome_follows_the_live_site(self):
        self.assertEqual(resolve("alpha").visual(), "alpha")
        self.assertEqual(resolve("vanilla").visual(), "gen1")
        self.assertEqual(resolve("wotlk").visual(), "gen1")
        self.assertEqual(resolve("cata").visual(), "gen2")
        self.assertEqual(resolve("mop").visual(), "gen2")
        self.assertEqual(resolve("wod").visual(), "gen2")
        self.assertEqual(resolve("wod").generation, "gen3")
        self.assertEqual(resolve("legion").visual(), "wowcom")
        self.assertEqual(resolve("bfa").visual(), "wowcom")
        self.assertEqual(resolve("shadowlands").visual(), "wowcom")
        self.assertEqual(resolve("dragonflight").visual(), "gen4")
        self.assertEqual(resolve("midnight").visual(), "gen4")

    def test_midnight_is_trinity(self):
        m = resolve("midnight")
        self.assertEqual(m.kind, "trinity")
        self.assertEqual(m.proto, "bnet")
        self.assertEqual(m.world_port, 18096)

    def test_runtime_kind_overlay_stays_on_a_known_kind(self):
        import os

        self.assertEqual(resolve("wotlk").kind, "azerothcore")
        os.environ["WOW_SHORT"] = "wotlk"
        os.environ["WOW_KIND"] = "trinity"
        try:
            self.assertEqual(resolve("wotlk").kind, "trinity")
            self.assertEqual(resolve("vanilla").kind, "cmangos")
            self.assertIn(resolve("wotlk").kind, {"alpha", "cmangos", "azerothcore", "trinity", "skyfire"})
        finally:
            os.environ.pop("WOW_SHORT", None)
            os.environ.pop("WOW_KIND", None)


class TalentTests(unittest.TestCase):
    def test_build_roundtrip(self):
        exp = resolve("vanilla")
        trees = trees_for(exp, "mage")
        ranks = parse_build(trees, "31" + "0" * 80)
        self.assertGreater(sum(ranks), 0)
        self.assertEqual(parse_build(trees, encode_build(ranks))[:2], ranks[:2])

    def test_dk_locked_in_vanilla(self):
        self.assertIsNone(trees_for(resolve("vanilla"), "deathknight"))
        self.assertIsNotNone(trees_for(resolve("wotlk"), "deathknight"))
        self.assertIn("deathknight", classes_for(resolve("wotlk")))


class VerifierTests(unittest.TestCase):
    def test_sha1_verifier_rejects_a_different_password(self):
        salt, verifier = accounts.srp6_sha1("Azoth", "secret")
        self.assertEqual(accounts.srp6_sha1_verifier("Azoth", "secret", salt), verifier)
        self.assertNotEqual(accounts.srp6_sha1_verifier("Azoth", "wrong", salt), verifier)

    def test_sha256_verifier_rejects_a_different_password(self):
        salt, verifier = accounts.srp6_sha256("HERO@LOCALHOST", "secret")
        self.assertEqual(accounts.srp6_sha256_verifier("HERO@LOCALHOST", "secret", salt), verifier)
        self.assertNotEqual(accounts.srp6_sha256_verifier("HERO@LOCALHOST", "wrong", salt), verifier)


class EraTableTests(unittest.TestCase):
    def test_races_follow_the_patch(self):
        self.assertNotIn("voidelf", content.races_for(resolve("wod")))
        self.assertIn("voidelf", content.races_for(resolve("legion")))
        self.assertNotIn("zandalari", content.races_for(resolve("legion")))
        self.assertIn("zandalari", content.races_for(resolve("bfa")))
        self.assertIn("dracthyr", content.races_for(resolve("dragonflight")))
        self.assertNotIn("earthen", content.races_for(resolve("dragonflight")))
        self.assertIn("earthen", content.races_for(resolve("warwithin")))
        self.assertIn("haranir", content.races_for(resolve("midnight")))
        self.assertNotIn("haranir", content.races_for(resolve("warwithin")))

    def test_capitals_follow_the_patch(self):
        self.assertEqual(content.race_facts(resolve("legion"), "nightelf")[2], "Darnassus")
        self.assertEqual(content.race_facts(resolve("bfa"), "nightelf")[2], "Stormwind")
        self.assertEqual(content.race_facts(resolve("dragonflight"), "nightelf")[2], "Bel'ameth")
        self.assertEqual(content.race_facts(resolve("bfa"), "undead")[2], "Lordaeron")

    def test_spec_names_follow_the_patch(self):
        self.assertIn("Combat", content.class_facts(resolve("wod"), "rogue")[2])
        self.assertIn("Outlaw", content.class_facts(resolve("legion"), "rogue")[2])
        self.assertNotIn("Guardian", content.class_facts(resolve("cata"), "druid")[2])
        self.assertIn("Guardian", content.class_facts(resolve("mop"), "druid")[2])

    def test_professions_follow_the_patch(self):
        def names(exp_id: str) -> set[str]:
            return {name for name, _desc in content.professions_for(resolve(exp_id))}

        self.assertNotIn("Jewelcrafting", names("vanilla"))
        self.assertIn("First Aid", names("vanilla"))
        self.assertIn("Jewelcrafting", names("tbc"))
        self.assertNotIn("Inscription", names("tbc"))
        self.assertIn("Inscription", names("wotlk"))
        self.assertNotIn("Archaeology", names("wotlk"))
        self.assertIn("Archaeology", names("cata"))
        self.assertIn("First Aid", names("legion"))
        self.assertNotIn("First Aid", names("bfa"))
        self.assertIn("Archaeology", names("shadowlands"))
        self.assertNotIn("Archaeology", names("dragonflight"))


class ForumBoardTests(unittest.TestCase):
    def _slugs(self, exp_id: str) -> set[str]:
        return {slug for slug, _title in forums.boards_for(resolve(exp_id))}

    def test_boards_stay_inside_the_expansion(self):
        self.assertIn("monk", self._slugs("mop"))
        self.assertNotIn("monk", self._slugs("cata"))
        self.assertIn("garrisons", self._slugs("wod"))
        self.assertNotIn("demonhunter", self._slugs("wod"))
        self.assertNotIn("classhalls", self._slugs("wod"))
        self.assertIn("classhalls", self._slugs("legion"))
        self.assertIn("demonhunter", self._slugs("legion"))
        for exp_id in ("bfa", "shadowlands", "dragonflight"):
            self.assertNotIn("delves", self._slugs(exp_id))
            self.assertNotIn("housing", self._slugs(exp_id))
        self.assertNotIn("evoker", self._slugs("shadowlands"))
        self.assertIn("evoker", self._slugs("dragonflight"))
        self.assertIn("delves", self._slugs("warwithin"))
        self.assertIn("housing", self._slugs("midnight"))
        self.assertIn("trading", self._slugs("alpha"))


class PublicPageTests(unittest.TestCase):
    def test_archive_footer_is_dev_only(self):
        exp = resolve("vanilla")
        public = H.layout(exp, "Home", "<p>News</p>")
        self.assertNotIn("Not affiliated", public)
        self.assertNotIn("127.0.0.1", public)
        dev = H.layout(exp, "Home", "<p>News</p>", dev=True)
        self.assertIn("Not affiliated", dev)

    def test_realm_page_hides_the_lab_address(self):
        exp = resolve("vanilla")
        body = H.realm_page(
            exp,
            {
                "name": "Vanilla",
                "up": True,
                "population": "4",
                "type": "PvE",
                "port": 18085,
                "address": "127.0.0.1",
                "error": "MariaDB unreachable",
            },
        )
        self.assertNotIn("127.0.0.1", body)
        self.assertNotIn("MariaDB", body)
        self.assertIn("4", body)
        self.assertIn("PvE", body)
        self.assertNotIn("18085", body)


class RealmTypeLabelTests(unittest.TestCase):
    def test_core_icon_codes(self):
        self.assertEqual(realm_type_label(0), "Normal")
        self.assertEqual(realm_type_label("1"), "PvP")
        self.assertEqual(realm_type_label(4), "Normal")
        self.assertEqual(realm_type_label(6), "RP")
        self.assertEqual(realm_type_label(8), "RP PvP")
        self.assertEqual(realm_type_label(16), "FFA PvP")
        self.assertIsNone(realm_type_label(2))
        self.assertIsNone(realm_type_label("nope"))
        self.assertIsNone(realm_type_label(None))


if __name__ == "__main__":
    unittest.main()
