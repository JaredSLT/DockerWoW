"""Era service defaults, arrival levels, and the expansion-move SQL."""

import unittest

from wowweb.account_ui import render_account
from wowweb.catalog import list_expansions, resolve
from wowweb.services.actions import build_transfer_sql, column_expr
from wowweb.services.config import load_config, transfer_targets
from wowweb.services.page import render_page, transfer_fields
from wowweb.services.rules import (
    arrival_level,
    capital_for,
    change_level_ok,
    combo_allowed,
    valid_character_name,
    valid_guild_name,
)

# name, appearance, race, faction, guild, transfer, cap, squish_above, squish_to, boost_level, token_gold
_EXPECTED = {
    "alpha": (1, 0, 0, 0, 0, 1, 60, 0, 0, 0, 0),
    "vanilla": (1, 0, 0, 0, 0, 1, 60, 0, 0, 0, 0),
    "classic-era": (1, 0, 0, 0, 0, 0, 60, 0, 0, 0, 0),
    "tbc": (1, 0, 0, 0, 0, 1, 70, 0, 0, 0, 0),
    "wotlk": (1, 1, 1, 1, 0, 1, 80, 0, 0, 0, 0),
    "wotlk-classic": (1, 1, 1, 1, 0, 0, 80, 0, 0, 0, 0),
    "cata": (1, 1, 1, 1, 1, 1, 85, 0, 0, 0, 0),
    "cata-classic": (1, 1, 1, 1, 1, 0, 85, 0, 0, 0, 0),
    "mop": (1, 1, 1, 1, 1, 1, 90, 0, 0, 0, 0),
    "wod": (1, 1, 1, 1, 1, 1, 100, 0, 0, 90, 100000),
    "legion": (1, 1, 1, 1, 1, 1, 110, 0, 0, 100, 100000),
    "bfa": (1, 1, 1, 1, 1, 1, 120, 0, 0, 120, 100000),
    "shadowlands": (1, 0, 1, 1, 1, 1, 60, 60, 50, 60, 100000),
    "dragonflight": (1, 0, 1, 1, 1, 1, 70, 70, 60, 70, 100000),
    "warwithin": (1, 0, 1, 1, 1, 1, 80, 80, 70, 70, 100000),
    "midnight": (1, 0, 1, 1, 1, 0, 90, 90, 80, 80, 100000),
}
_FLAG_KEYS = (
    "name_change",
    "appearance_change",
    "race_change",
    "faction_change",
    "guild_name_change",
    "expansion_transfer",
)
_NUMBER_KEYS = ("level_cap", "squish_above", "squish_to", "boost_level", "token_gold")


def _col(name, col_type="int", nullable=False, default="0", extra=""):
    return {"name": name, "type": col_type, "nullable": nullable, "default": default, "extra": extra}


class ServiceConfigTests(unittest.TestCase):
    def test_each_expansion_has_its_own_file(self):
        seen = {exp.id for exp in list_expansions()}
        self.assertEqual(seen, set(_EXPECTED))

    def test_boosts_and_tokens_ship_off_and_other_services_match_the_era(self):
        for exp_id, expected in _EXPECTED.items():
            settings = load_config(exp_id)
            self.assertFalse(settings["boost"], exp_id)
            self.assertFalse(settings["wow_token"], exp_id)
            for key, want in zip(_FLAG_KEYS, expected[:6]):
                self.assertEqual(bool(settings[key]), bool(want), f"{exp_id} {key}")
            for key, want in zip(_NUMBER_KEYS, expected[6:]):
                self.assertEqual(settings[key], want, f"{exp_id} {key}")

    def test_transfer_only_moves_forward(self):
        vanilla = transfer_targets(resolve("vanilla"))
        self.assertEqual(vanilla[0].id, "tbc")
        self.assertNotIn("classic-era", [exp.id for exp in vanilla])
        self.assertIn("midnight", [exp.id for exp in vanilla])
        self.assertNotIn("vanilla", [exp.id for exp in vanilla])
        wotlk = transfer_targets(resolve("wotlk"))
        self.assertEqual(wotlk[0].id, "cata")
        self.assertNotIn("wotlk-classic", [exp.id for exp in wotlk])
        self.assertEqual(transfer_targets(resolve("midnight")), [])
        self.assertEqual(transfer_targets(resolve("alpha"))[0].id, "vanilla")


class RuleTests(unittest.TestCase):
    def test_names(self):
        self.assertTrue(valid_character_name("Aldrea"))
        self.assertFalse(valid_character_name("aldrea"))
        self.assertFalse(valid_character_name("A"))
        self.assertFalse(valid_character_name("Aldrea1"))
        self.assertTrue(valid_guild_name("The Valor"))
        self.assertFalse(valid_guild_name("The  Valor"))
        self.assertFalse(valid_guild_name("A"))

    def test_arrival_keeps_low_levels_and_squishes_the_later_caps(self):
        shadow = load_config("shadowlands")
        dragon = load_config("dragonflight")
        war = load_config("warwithin")
        midnight = load_config("midnight")
        self.assertEqual(arrival_level(120, shadow), 50)
        self.assertEqual(arrival_level(60, shadow), 60)
        self.assertEqual(arrival_level(60, midnight), 60)
        self.assertEqual(arrival_level(100, dragon), 60)
        self.assertEqual(arrival_level(70, dragon), 70)
        self.assertEqual(arrival_level(80, dragon), 60)
        self.assertEqual(arrival_level(85, war), 70)
        self.assertEqual(arrival_level(20, load_config("tbc")), 20)

    def test_race_and_class_follow_the_expansion(self):
        self.assertTrue(combo_allowed(resolve("vanilla"), 1, 1))
        self.assertFalse(combo_allowed(resolve("vanilla"), 6, 2))
        self.assertFalse(combo_allowed(resolve("vanilla"), 1, 6))
        self.assertFalse(combo_allowed(resolve("tbc"), 1, 6))
        self.assertTrue(combo_allowed(resolve("tbc"), 10, 2))
        self.assertTrue(combo_allowed(resolve("wotlk"), 1, 6))
        self.assertFalse(combo_allowed(resolve("cata"), 22, 2))
        self.assertFalse(combo_allowed(resolve("cata"), 9, 2))
        self.assertFalse(combo_allowed(resolve("cata"), 1, 10))
        self.assertTrue(combo_allowed(resolve("mop"), 1, 10))
        self.assertFalse(combo_allowed(resolve("wod"), 1, 12))
        self.assertTrue(combo_allowed(resolve("legion"), 1, 12))
        self.assertFalse(combo_allowed(resolve("bfa"), 52, 13))
        self.assertTrue(combo_allowed(resolve("dragonflight"), 52, 13))

    def test_service_levels_and_capitals(self):
        self.assertFalse(change_level_ok(9, 1))
        self.assertTrue(change_level_ok(10, 1))
        self.assertFalse(change_level_ok(54, 6))
        self.assertTrue(change_level_ok(55, 6))
        self.assertEqual(capital_for(2)["map"], 1)
        self.assertEqual(capital_for(1)["map"], 0)
        self.assertEqual(capital_for(24)["zone"], 1519)

    def test_alpha_appearance_packs_into_player_bytes(self):
        dest = _col("playerBytes")
        src = {"skin", "face", "hairstyle", "haircolour", "facialhair"}
        expr = column_expr(dest, src, {})
        self.assertIn("hairstyle", expr)
        self.assertIn("haircolour", expr)
        unpacked = column_expr(_col("hairStyle"), {"playerBytes", "playerBytes2"}, {})
        self.assertIn("playerBytes", unpacked)


class TransferSqlTests(unittest.TestCase):
    def _script(self):
        src = [
            _col("guid", extra="auto_increment"),
            _col("account"),
            _col("name", "varchar(12)", default=None),
            _col("race"),
            _col("class"),
            _col("gender"),
            _col("level"),
            _col("xp"),
            _col("money"),
            _col("skin"),
            _col("face"),
            _col("hairstyle"),
            _col("haircolour"),
            _col("facialhair"),
            _col("position_x", "float"),
            _col("position_y", "float"),
            _col("position_z", "float"),
            _col("map"),
            _col("zone"),
            _col("orientation", "float"),
            _col("online"),
        ]
        dest = [
            _col("guid"),
            _col("account"),
            _col("name", "varchar(12)"),
            _col("race"),
            _col("class"),
            _col("gender"),
            _col("level"),
            _col("xp"),
            _col("money"),
            _col("playerBytes"),
            _col("playerBytes2"),
            _col("position_x", "float"),
            _col("position_y", "float"),
            _col("position_z", "float"),
            _col("map"),
            _col("zone"),
            _col("orientation", "float"),
            _col("online"),
            _col("at_login"),
            _col("taximask", "text", default=None),
        ]
        src_inv = [
            _col("guid"),
            _col("owner"),
            _col("bag"),
            _col("slot"),
            _col("item_template"),
            _col("stackcount"),
        ]
        dest_inv = [_col("guid"), _col("bag"), _col("slot"), _col("item"), _col("item_template")]
        dest_items = [
            _col("guid"),
            _col("itemEntry"),
            _col("owner_guid"),
            _col("count"),
            _col("durability"),
            _col("enchantments", "text", default=None),
        ]
        return build_transfer_sql(
            src_db="alpha_realm",
            dest_db="vanilla_characters",
            world_db="vanilla_world",
            src_cols=src,
            dest_cols=dest,
            src_guid=15,
            src_account=4,
            dest_account=9,
            name="Aldrea",
            arrival=20,
            level_changed=False,
            capital=capital_for(1),
            src_inv=src_inv,
            dest_inv=dest_inv,
            src_items=None,
            dest_items=dest_items,
            has_template=True,
            children=[],
            src_home=None,
            dest_home=[_col("guid"), _col("map"), _col("zone"), _col("position_x", "float"), _col("position_y", "float"), _col("position_z", "float")],
            fk_deletes=[("character_spells", "guid")],
            extra_deletes=[("character_inventory", "owner")],
        )

    def test_move_keeps_the_source_until_the_insert_lands(self):
        sql = self._script()
        self.assertIn("s.online=0", sql)
        self.assertIn("AND @ok=1", sql)
        self.assertIn("DELETE FROM `alpha_realm`.`characters`", sql)
        self.assertIn("playerBytes", sql)
        self.assertIn("hairstyle", sql)
        self.assertIn("durability", sql)
        self.assertIn("100", sql)
        self.assertIn("''", sql)
        self.assertIn("SET @newguid", sql)
        self.assertNotIn("password", sql.lower())
        self.assertNotIn("private server", sql.lower())
        delete_at = sql.index("DELETE FROM `alpha_realm`.`characters`")
        insert_at = sql.index("INSERT INTO `vanilla_characters`.`characters`")
        self.assertLess(insert_at, delete_at)
        self.assertIn("WHERE `guid`=@oldguid AND `account`=4 AND @ok=1", sql)


class ServicesPageTests(unittest.TestCase):
    def _row(self):
        return {"guid": 3, "name": "Aldrea", "level": 20, "class_name": "Warrior", "online": 0}

    def test_pages_offer_only_the_enabled_services(self):
        vanilla = render_page(resolve("vanilla"), user="Aldrea", characters=[self._row()], email="")
        self.assertIn("These services are free.", vanilla)
        self.assertIn("action='/account/services/name'", vanilla)
        self.assertIn("action='/account/services/transfer'", vanilla)
        self.assertIn("name='dest_email'", vanilla)
        self.assertIn("(the usual next step)", vanilla)
        self.assertNotIn("/account/services/appearance", vanilla)
        self.assertNotIn("/account/services/boost", vanilla)
        self.assertNotIn("Character boosts are turned off", vanilla)
        self.assertNotIn("private server", vanilla.lower())
        self.assertNotIn("mariadb", vanilla.lower())

        wod = render_page(resolve("wod"), user="hero@wod.local", characters=[self._row()], email="hero@wod.local")
        self.assertIn("Character boosts are turned off", wod)
        self.assertIn("The WoW Token is turned off", wod)
        self.assertIn("wowweb/services/config/wod.json", wod)
        self.assertNotIn("action='/account/services/boost'", wod)
        self.assertNotIn("action='/account/services/token'", wod)
        self.assertIn("action='/account/services/appearance'", wod)
        self.assertIn("name='dest_game'", wod)

        midnight = render_page(resolve("midnight"), user="Aldrea", characters=[self._row()], email="a@midnight.local")
        self.assertNotIn("action='/account/services/transfer'", midnight)
        self.assertNotIn("/account/services/appearance", midnight)
        self.assertIn("action='/account/services/race'", midnight)
        self.assertIn("The WoW Token is turned off", midnight)

        wotlk = render_page(resolve("wotlk"), user="Aldrea", characters=[self._row()])
        self.assertIn("/account/services/faction", wotlk)
        self.assertNotIn("/account/services/guild", wotlk)

    def test_summary_links_to_character_services(self):
        page = render_account(
            resolve("vanilla"),
            user="Aldrea",
            error="",
            notice="",
            mode="summary",
            email="",
            characters=[],
            login_kind="account",
            separate_game_name=False,
        )
        self.assertIn('href="/account/services"', page)
        login = render_account(
            resolve("vanilla"),
            user="",
            error="",
            notice="",
            mode="login",
            email="",
            characters=[],
            login_kind="account",
            separate_game_name=False,
        )
        self.assertNotIn('href="/account/services"', login)

    def test_login_type_changes_ask_for_the_missing_name(self):
        later = transfer_targets(resolve("vanilla"))
        fields = transfer_fields(resolve("vanilla"), "", "Aldrea", later)
        self.assertTrue(fields["email"])
        self.assertFalse(fields["game"])
        self.assertFalse(fields["account"])
        wod_later = transfer_targets(resolve("wod"))
        fields = transfer_fields(resolve("wod"), "hero@wod.local", "hero@wod.local", wod_later)
        self.assertFalse(fields["email"])
        self.assertTrue(fields["game"])
        self.assertFalse(fields["account"])


if __name__ == "__main__":
    unittest.main()
