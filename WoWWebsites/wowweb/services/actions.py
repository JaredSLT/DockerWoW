"""Character services against one realm's character database.

Name changes are written directly. Appearance, race, and faction set the
login flag the client already understands. A forward expansion move copies
the character in one MariaDB session and deletes the source only after the
new row exists. Boosts and the WoW Token stay off unless that expansion's
config file turns them on.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from .. import accounts
from ..catalog import Expansion, resolve
from ..lab import LabConfig, mysql, mysql_rows
from .config import load_config, transfer_targets
from . import rules

_IDENT = re.compile(r"^[A-Za-z0-9_]+$")
_MISMATCH = "That destination account already exists and this password does not match it."

# Child tables copied when both realms have them. guid is the character.
_COPY_TABLES = (
    ("character_spell", ("character_spell", "character_spells")),
    ("character_skills", ("character_skills", "character_skill")),
    ("character_reputation", ("character_reputation",)),
    ("character_action", ("character_action",)),
    ("character_queststatus", ("character_queststatus", "character_quest_state")),
    ("character_currency", ("character_currency",)),
)

_APPEARANCE_ALIAS = {
    "hairStyle": "hairstyle",
    "hairstyle": "hairStyle",
    "hairColor": "haircolour",
    "haircolour": "hairColor",
    "facialStyle": "facialhair",
    "facialhair": "facialStyle",
}

_ZERO = {
    "online",
    "at_login",
    "instance_id",
    "instanceid",
    "instance_mode_mask",
    "transguid",
    "trans_guid",
    "transporter",
    "transporter_guid",
    "trans_x",
    "trans_y",
    "trans_z",
    "trans_o",
    "trans_spawn_id",
    "guild",
    "guildid",
    "guild_id",
}

_RACE_NAMES = {
    1: "human",
    2: "orc",
    3: "dwarf",
    4: "night elf",
    5: "undead",
    6: "tauren",
    7: "gnome",
    8: "troll",
    9: "goblin",
    10: "blood elf",
    11: "draenei",
    22: "worgen",
    24: "pandaren",
    25: "pandaren",
    26: "pandaren",
    27: "nightborne",
    28: "highmountain tauren",
    29: "void elf",
    30: "lightforged draenei",
    31: "zandalari troll",
    32: "kul tiran",
    34: "dark iron dwarf",
    35: "vulpera",
    36: "mag'har orc",
    37: "mechagnome",
    52: "dracthyr",
    70: "dracthyr",
    84: "earthen",
    85: "earthen",
}


def _ok_ident(name: str) -> bool:
    return bool(_IDENT.match(name or ""))


def literal_for(col_type: str) -> str:
    """A safe literal for a NOT NULL column that has no default."""
    kind = (col_type or "").lower()
    if any(kind.startswith(prefix) for prefix in (
        "tinyint", "smallint", "mediumint", "int", "bigint", "float", "double", "decimal", "bit", "year",
    )):
        return "0"
    if "blob" in kind or kind.startswith("binary") or kind.startswith("varbinary"):
        return "0x"
    if kind.startswith("date") or kind.startswith("timestamp") or kind.startswith("time"):
        return "'1970-01-01 00:00:01'"
    return "''"


def _appearance_sql(name: str, src_names: set[str], alias: str) -> str:
    if name == "playerBytes" and {"skin", "face", "hairstyle", "haircolour"} <= src_names:
        return (
            f"(({alias}.`skin` & 255) | (({alias}.`face` & 255) << 8) | "
            f"(({alias}.`hairstyle` & 255) << 16) | (({alias}.`haircolour` & 255) << 24))"
        )
    if name == "playerBytes2" and "facialhair" in src_names:
        return f"({alias}.`facialhair` & 255)"
    if "playerBytes" in src_names:
        if name == "skin":
            return f"({alias}.`playerBytes` & 255)"
        if name == "face":
            return f"(({alias}.`playerBytes` >> 8) & 255)"
        if name in {"hairStyle", "hairstyle"}:
            return f"(({alias}.`playerBytes` >> 16) & 255)"
        if name in {"hairColor", "haircolour"}:
            return f"(({alias}.`playerBytes` >> 24) & 255)"
    if name in {"facialStyle", "facialhair"} and "playerBytes2" in src_names:
        return f"({alias}.`playerBytes2` & 255)"
    return ""


def column_expr(dest: dict, src_names: set[str], overrides: dict, src_alias: str = "s") -> str | None:
    """SELECT expression for one destination column, or None to omit it."""
    name = dest.get("name") or ""
    if not _ok_ident(name):
        return None
    if overrides.get(name) is not None:
        return str(overrides[name])
    extra = (dest.get("extra") or "").lower()
    if "generated" in extra or "virtual" in extra or "auto_increment" in extra:
        return None
    if name in src_names:
        return f"{src_alias}.`{name}`"
    alias_name = _APPEARANCE_ALIAS.get(name)
    if alias_name and alias_name in src_names:
        return f"{src_alias}.`{alias_name}`"
    derived = _appearance_sql(name, src_names, src_alias)
    if derived:
        return derived
    if dest.get("nullable") or dest.get("default") is not None:
        return None
    return literal_for(dest.get("type") or "")


def insert_pairs(dest_cols: list, src_names: set[str], overrides: dict, src_alias: str = "s") -> tuple[list[str], list[str]]:
    cols: list[str] = []
    exprs: list[str] = []
    for dest in dest_cols:
        expr = column_expr(dest, src_names, overrides, src_alias)
        if expr is None:
            continue
        cols.append(f"`{dest['name']}`")
        exprs.append(expr)
    return cols, exprs


def _names(cols: list | None) -> set[str]:
    return {col["name"] for col in (cols or []) if col.get("name")}


def character_overrides(dest_names: set[str], account_id: int, name: str, level: int, level_changed: bool, capital: dict) -> dict:
    overrides = {
        "guid": "@newguid",
        "account": str(int(account_id)),
        "name": f"'{accounts._esc(name)}'",
        "level": str(int(level)),
        "online": "0",
        "at_login": "0",
        "position_x": str(capital["x"]),
        "position_y": str(capital["y"]),
        "position_z": str(capital["z"]),
        "map": str(int(capital["map"])),
        "zone": str(int(capital["zone"])),
        "orientation": str(capital["o"]),
    }
    if level_changed:
        overrides["xp"] = "0"
    for col in _ZERO:
        if col in dest_names:
            overrides[col] = "0"
    return overrides


def homebind_numbers(cols: list, capital: dict) -> dict:
    names = _names(cols)
    values = {
        "map": int(capital["map"]),
        "mapId": int(capital["map"]),
        "zone": int(capital["zone"]),
        "zoneId": int(capital["zone"]),
        "position_x": capital["x"],
        "posX": capital["x"],
        "position_y": capital["y"],
        "posY": capital["y"],
        "position_z": capital["z"],
        "posZ": capital["z"],
        "orientation": capital["o"],
    }
    return {key: str(val) for key, val in values.items() if key in names}


def inventory_owner_col(cols: list | None) -> str:
    names = _names(cols)
    if "item" in names and "guid" in names:
        return "guid"
    if "owner" in names:
        return "owner"
    return ""


def _public_sql_error(err: str, secret: str = "") -> str:
    text = err or ""
    if secret:
        text = text.replace(secret, "")
    if "Duplicate" in text:
        return "That name is already in use on this realm."
    for part in text.splitlines():
        line = part.strip()
        if line.startswith("ERROR") or "Unknown column" in line or "doesn't exist" in line:
            return "Could not update that character. " + line[:240]
    return "Could not update that character."


def _meta(cfg: LabConfig, db: str, table: str) -> list | None:
    if not _ok_ident(db) or not _ok_ident(table):
        return None
    ok, out = mysql(cfg, f"SHOW COLUMNS FROM `{db}`.`{table}`;")
    if not ok:
        return None
    cols = []
    for line in out.splitlines():
        if line == "":
            continue
        parts = line.split("\t")
        while len(parts) < 6:
            parts.append("")
        default = parts[4]
        if default in {"NULL", "\\N", "None"}:
            default = None
        if not _ok_ident(parts[0]):
            continue
        cols.append({
            "name": parts[0],
            "type": parts[1],
            "nullable": parts[2] == "YES",
            "key": parts[3],
            "default": default,
            "extra": parts[5],
        })
    return cols


def _has_column(cols: list | None, name: str) -> bool:
    return name in _names(cols)


def account_id(cfg: LabConfig, exp: Expansion, username: str) -> int | None:
    auth = cfg.auth_db(exp)
    if not _ok_ident(auth):
        return None
    safe = accounts._esc(username)
    if exp.kind == "alpha":
        sql = f"SELECT id FROM `{auth}`.`accounts` WHERE UPPER(name)=UPPER('{safe}') LIMIT 1;"
    else:
        sql = f"SELECT id FROM `{auth}`.`account` WHERE UPPER(username)=UPPER('{safe}') LIMIT 1;"
    rows = mysql_rows(cfg, sql)
    if not rows or not rows[0] or not rows[0][0].isdigit():
        return None
    return int(rows[0][0])


def list_characters(cfg: LabConfig, exp: Expansion, username: str) -> list[dict]:
    owner = account_id(cfg, exp, username)
    chars = cfg.chars_db(exp)
    if owner is None or not _ok_ident(chars):
        return []
    cols = _meta(cfg, chars, "characters")
    if not cols:
        return []
    wanted = [name for name in ("guid", "name", "level", "race", "class", "online") if _has_column(cols, name)]
    if "guid" not in wanted or "name" not in wanted:
        return []
    sql = (
        f"SELECT {', '.join('`' + name + '`' for name in wanted)} FROM `{chars}`.`characters` "
        f"WHERE account={owner} ORDER BY level DESC, name LIMIT 20;"
    )
    found = []
    for row in mysql_rows(cfg, sql):
        data = {wanted[i]: row[i] if i < len(row) else "" for i in range(len(wanted))}
        try:
            class_id = int(data.get("class") or 0)
            level = int(data.get("level") or 0)
            guid = int(data.get("guid") or 0)
            race = int(data.get("race") or 0)
            online = int(data.get("online") or 0)
        except ValueError:
            continue
        found.append({
            "guid": guid,
            "name": data.get("name") or "",
            "level": level,
            "race": race,
            "class_id": class_id,
            "online": online,
            "class_name": accounts.CLASS_NAMES.get(class_id, "Adventurer"),
        })
    return found


def _owned(cfg: LabConfig, exp: Expansion, username: str, guid: int) -> dict | None:
    for row in list_characters(cfg, exp, username):
        if row["guid"] == guid:
            return row
    return None


def _offline_or_error(row: dict | None) -> str:
    if not row:
        return "That character is not on this account."
    if row["online"]:
        return "Log out of that character in game first."
    return ""


def change_name(cfg: LabConfig, exp: Expansion, username: str, guid: int, new_name: str) -> tuple[bool, str]:
    if not load_config(exp.id).get("name_change"):
        return False, "That service is not available on this realm."
    new_name = (new_name or "").strip()
    if not rules.valid_character_name(new_name):
        return False, "Character names are 2–12 letters, with the first letter capitalized."
    row = _owned(cfg, exp, username, guid)
    problem = _offline_or_error(row)
    if problem:
        return False, problem
    chars = cfg.chars_db(exp)
    owner = account_id(cfg, exp, username)
    taken = mysql_rows(
        cfg,
        f"SELECT guid FROM `{chars}`.`characters` WHERE LOWER(name)=LOWER('{accounts._esc(new_name)}') "
        f"AND guid<>{int(guid)} LIMIT 1;",
    )
    if taken:
        return False, "That name is already in use on this realm."
    ok, out = mysql(
        cfg,
        f"UPDATE `{chars}`.`characters` SET name='{accounts._esc(new_name)}' "
        f"WHERE guid={int(guid)} AND account={int(owner)} AND online=0; SELECT ROW_COUNT();",
    )
    if not ok:
        return False, _public_sql_error(out)
    if not any(line.strip() == "1" for line in out.splitlines()):
        return False, "Log out of that character in game first."
    return True, f"{row['name']} is now {new_name}."


def _set_flag(cfg: LabConfig, exp: Expansion, username: str, guid: int, bit: int, success: str, check_level: bool) -> tuple[bool, str]:
    row = _owned(cfg, exp, username, guid)
    problem = _offline_or_error(row)
    if problem:
        return False, problem
    if check_level and not rules.change_level_ok(row["level"], row["class_id"]):
        if row["class_id"] == 6:
            return False, "A death knight can change race or faction from level 55."
        return False, "A character can change race or faction from level 10."
    chars = cfg.chars_db(exp)
    cols = _meta(cfg, chars, "characters")
    if not _has_column(cols, "at_login"):
        return False, "This expansion cannot apply that change from the website."
    owner = account_id(cfg, exp, username)
    ok, out = mysql(
        cfg,
        f"UPDATE `{chars}`.`characters` SET at_login = at_login | {int(bit)} "
        f"WHERE guid={int(guid)} AND account={int(owner)} AND online=0; SELECT ROW_COUNT();",
    )
    if not ok:
        return False, _public_sql_error(out)
    if not any(line.strip() == "1" for line in out.splitlines()):
        return False, "Log out of that character in game first."
    return True, success


def change_appearance(cfg: LabConfig, exp: Expansion, username: str, guid: int) -> tuple[bool, str]:
    if not load_config(exp.id).get("appearance_change"):
        return False, "That service is not available on this realm."
    return _set_flag(
        cfg, exp, username, guid, rules.AT_LOGIN_CUSTOMIZE,
        "Log in with that character. The game will ask you to customize them, including gender.",
        False,
    )


def change_race(cfg: LabConfig, exp: Expansion, username: str, guid: int) -> tuple[bool, str]:
    if not load_config(exp.id).get("race_change"):
        return False, "That service is not available on this realm."
    return _set_flag(
        cfg, exp, username, guid, rules.AT_LOGIN_CHANGE_RACE,
        "Log in with that character. The game will walk you through a race change on the same faction.",
        True,
    )


def change_faction(cfg: LabConfig, exp: Expansion, username: str, guid: int) -> tuple[bool, str]:
    if not load_config(exp.id).get("faction_change"):
        return False, "That service is not available on this realm."
    return _set_flag(
        cfg, exp, username, guid, rules.AT_LOGIN_CHANGE_FACTION,
        "Log in with that character. The game will walk you through a faction change. Race, appearance, and name can change with it.",
        True,
    )


def list_guilds(cfg: LabConfig, exp: Expansion, username: str) -> list[dict]:
    if not load_config(exp.id).get("guild_name_change"):
        return []
    owner = account_id(cfg, exp, username)
    chars = cfg.chars_db(exp)
    if owner is None or not _ok_ident(chars):
        return []
    guild_cols = _meta(cfg, chars, "guild")
    member_cols = _meta(cfg, chars, "guild_member")
    if not guild_cols or not member_cols:
        return []
    gnames = _names(guild_cols)
    mnames = _names(member_cols)
    gid = "guildid" if "guildid" in gnames else "guild_id" if "guild_id" in gnames else ""
    mid = "guildid" if "guildid" in mnames else "guild_id" if "guild_id" in mnames else ""
    if not gid or not mid or "name" not in gnames or "guid" not in mnames or "rank" not in mnames:
        return []
    sql = (
        f"SELECT g.`{gid}`, g.`name` FROM `{chars}`.`guild` g "
        f"JOIN `{chars}`.`guild_member` m ON m.`{mid}`=g.`{gid}` AND m.`rank`=0 "
        f"JOIN `{chars}`.`characters` c ON c.`guid`=m.`guid` "
        f"WHERE c.account={owner} ORDER BY g.`name` LIMIT 20;"
    )
    found = []
    for row in mysql_rows(cfg, sql):
        if len(row) < 2 or not str(row[0]).isdigit():
            continue
        found.append({"id": int(row[0]), "name": row[1]})
    return found


def _soap_rename(old: str, new: str) -> bool:
    try:
        runtime = accounts._runtime()
        return bool(runtime.soap_command(f'guild rename "{old}" "{new}"', timeout=2))
    except Exception:
        return False


def rename_guild(cfg: LabConfig, exp: Expansion, username: str, guild_id: int, new_name: str) -> tuple[bool, str]:
    if not load_config(exp.id).get("guild_name_change"):
        return False, "That service is not available on this realm."
    new_name = (new_name or "").strip()
    if not rules.valid_guild_name(new_name):
        return False, "Guild names are 2–24 letters and spaces, without a double space."
    led = [row for row in list_guilds(cfg, exp, username) if row["id"] == int(guild_id)]
    if not led:
        return False, "Only the guild master can rename a guild."
    chars = cfg.chars_db(exp)
    guild_cols = _meta(cfg, chars, "guild") or []
    gnames = _names(guild_cols)
    gid = "guildid" if "guildid" in gnames else "guild_id"
    taken = mysql_rows(
        cfg,
        f"SELECT `{gid}` FROM `{chars}`.`guild` WHERE LOWER(name)=LOWER('{accounts._esc(new_name)}') "
        f"AND `{gid}`<>{int(guild_id)} LIMIT 1;",
    )
    if taken:
        return False, "That guild name is already in use on this realm."
    ok, err = mysql(
        cfg,
        f"UPDATE `{chars}`.`guild` SET name='{accounts._esc(new_name)}' WHERE `{gid}`={int(guild_id)};",
    )
    if not ok:
        return False, _public_sql_error(err)
    if _soap_rename(led[0]["name"], new_name):
        return True, f"The guild is now {new_name}."
    return True, (
        f"The guild is now {new_name} in the database. "
        "If the world server is running, it can write the old name back until that server is restarted."
    )


def boost_character(cfg: LabConfig, exp: Expansion, username: str, guid: int) -> tuple[bool, str]:
    settings = load_config(exp.id)
    if not settings.get("boost"):
        return False, "That service is not available on this realm."
    target = int(settings.get("boost_level") or 0)
    if target <= 0:
        return False, f"Set boost_level in wowweb/services/config/{exp.id}.json before using a boost."
    row = _owned(cfg, exp, username, guid)
    problem = _offline_or_error(row)
    if problem:
        return False, problem
    if row["level"] >= target:
        return False, "This character is already at that level."
    chars = cfg.chars_db(exp)
    cols = _names(_meta(cfg, chars, "characters"))
    sets = [f"level={target}"]
    if "xp" in cols:
        sets.append("xp=0")
    if "at_login" in cols:
        flag = rules.AT_LOGIN_RESET_SPELLS | rules.AT_LOGIN_RESET_TALENTS
        sets.append(f"at_login = at_login | {flag}")
    owner = account_id(cfg, exp, username)
    ok, out = mysql(
        cfg,
        f"UPDATE `{chars}`.`characters` SET {', '.join(sets)} "
        f"WHERE guid={int(guid)} AND account={int(owner)} AND online=0; SELECT ROW_COUNT();",
    )
    if not ok:
        return False, _public_sql_error(out)
    if not any(line.strip() == "1" for line in out.splitlines()):
        return False, "Log out of that character in game first."
    return True, f"{row['name']} will log in at level {target}. Spells and talents reset on that login. Gear is unchanged."


def _token_db(data_dir: Path) -> sqlite3.Connection:
    path = Path(data_dir) / "tokens.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS token_balance ("
        "expansion TEXT NOT NULL, account TEXT NOT NULL, balance INTEGER NOT NULL, "
        "PRIMARY KEY (expansion, account))"
    )
    return conn


def token_balance(data_dir: Path, exp_id: str, username: str) -> int:
    conn = _token_db(data_dir)
    try:
        row = conn.execute(
            "SELECT balance FROM token_balance WHERE expansion=? AND account=?",
            (exp_id, username.upper()),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0]) if row else 0


def _add_tokens(data_dir: Path, exp_id: str, username: str, delta: int) -> None:
    conn = _token_db(data_dir)
    try:
        key = (exp_id, username.upper())
        row = conn.execute(
            "SELECT balance FROM token_balance WHERE expansion=? AND account=?", key
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE token_balance SET balance=balance+? WHERE expansion=? AND account=?",
                (delta, key[0], key[1]),
            )
        else:
            conn.execute(
                "INSERT INTO token_balance (expansion, account, balance) VALUES (?, ?, ?)",
                (key[0], key[1], delta),
            )
        conn.commit()
    finally:
        conn.close()


def exchange_token(cfg: LabConfig, exp: Expansion, username: str, guid: int, side: str, data_dir: Path) -> tuple[bool, str]:
    settings = load_config(exp.id)
    if not settings.get("wow_token"):
        return False, "That service is not available on this realm."
    gold = int(settings.get("token_gold") or 0)
    if gold <= 0:
        return False, f"Set token_gold in wowweb/services/config/{exp.id}.json before using the WoW Token."
    row = _owned(cfg, exp, username, guid)
    problem = _offline_or_error(row)
    if problem:
        return False, problem
    chars = cfg.chars_db(exp)
    if not _has_column(_meta(cfg, chars, "characters"), "money"):
        return False, "This expansion does not store gold on the character."
    owner = account_id(cfg, exp, username)
    copper = gold * 10000
    if side == "buy":
        ok, err = mysql(
            cfg,
            f"UPDATE `{chars}`.`characters` SET money=money-{copper} "
            f"WHERE guid={int(guid)} AND account={int(owner)} AND online=0 AND money>={copper}; "
            "SELECT ROW_COUNT();",
        )
        if not ok:
            return False, _public_sql_error(err)
        count = 0
        for line in (err or "").splitlines():
            if line.strip().isdigit():
                count = int(line.strip())
        if count != 1:
            return False, "That character does not have enough gold, or they are still online."
        try:
            _add_tokens(data_dir, exp.id, username, 1)
        except sqlite3.Error:
            mysql(
                cfg,
                f"UPDATE `{chars}`.`characters` SET money=money+{copper} "
                f"WHERE guid={int(guid)} AND account={int(owner)};",
            )
            return False, "Could not record the token. The gold was returned."
        return True, f"Bought one WoW Token for {gold} gold. This account now holds {token_balance(data_dir, exp.id, username)}."
    if side != "sell":
        return False, "Choose whether to buy or sell a token."
    conn = _token_db(data_dir)
    try:
        conn.execute("BEGIN IMMEDIATE")
        key = (exp.id, username.upper())
        current = conn.execute(
            "SELECT balance FROM token_balance WHERE expansion=? AND account=?", key
        ).fetchone()
        if not current or int(current[0]) < 1:
            conn.rollback()
            return False, "You do not have a WoW Token on this account."
        conn.execute(
            "UPDATE token_balance SET balance=balance-1 WHERE expansion=? AND account=?",
            key,
        )
        ok, err = mysql(
            cfg,
            f"UPDATE `{chars}`.`characters` SET money=money+{copper} "
            f"WHERE guid={int(guid)} AND account={int(owner)} AND online=0; SELECT ROW_COUNT();",
        )
        paid = ok and any(line.strip() == "1" for line in (err or "").splitlines())
        if not paid:
            conn.rollback()
            return False, "Log out of that character in game first."
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        return False, "Could not record the token."
    finally:
        conn.close()
    return True, f"Sold one WoW Token. {gold} gold was added to {row['name']}."


def _source_identity(cfg: LabConfig, exp: Expansion, username: str) -> str:
    if accounts.email_login(exp):
        email = (accounts.account_summary(cfg, exp, username).get("email") or "").strip()
        if email:
            return email
    return username


def _email_taken(cfg: LabConfig, exp: Expansion, email: str) -> bool:
    auth = cfg.auth_db(exp)
    if exp.proto != "bnet" or not _ok_ident(auth):
        return False
    rows = mysql_rows(
        cfg,
        f"SELECT id FROM `{auth}`.`battlenet_accounts` WHERE LOWER(email)=LOWER('{accounts._esc(email)}') LIMIT 1;",
    )
    return bool(rows)


def ensure_destination_account(
    cfg: LabConfig,
    dest: Expansion,
    username: str,
    password: str,
    email: str,
    game_name: str,
    account_name: str,
) -> tuple[bool, str, str]:
    """Create the destination login, or accept it when the same password already matches."""
    email = (email or "").strip()
    game_name = (game_name or "").strip()
    account_name = (account_name or "").strip()
    if not game_name and accounts.USER_RE.match(username or ""):
        game_name = username
    if dest.id == "wod":
        if not email:
            return False, "Enter the email address for the destination account.", ""
        if accounts.account_exists(cfg, dest, email):
            ok, name = accounts.authenticate(cfg, dest, email, password)
            if not ok:
                return False, _MISMATCH, ""
            return True, "", name
        return accounts.create_account(cfg, dest, email, password, email, "")
    if dest.proto == "bnet":
        if not email:
            return False, "Enter the email address for the destination account.", ""
        if not accounts.USER_RE.match(game_name or ""):
            return False, "Choose a World of Warcraft account name: 3–16 letters, numbers, or underscore.", ""
        if _email_taken(cfg, dest, email):
            ok, name = accounts.authenticate(cfg, dest, email, password)
            if not ok:
                return False, _MISMATCH, ""
            return True, "", name
        return accounts.create_account(cfg, dest, game_name, password, email, game_name)
    if not account_name and accounts.USER_RE.match(username or ""):
        account_name = username
    if not accounts.USER_RE.match(account_name or ""):
        return False, "Choose an account name on the destination: 3–16 letters, numbers, or underscore.", ""
    if accounts.account_exists(cfg, dest, account_name):
        ok, name = accounts.authenticate(cfg, dest, account_name, password)
        if not ok:
            return False, _MISMATCH, ""
        return True, "", name
    return accounts.create_account(cfg, dest, account_name, password, "", "")


def _fk_deletes(cfg: LabConfig, db: str) -> list[tuple[str, str]]:
    if not _ok_ident(db):
        return []
    rows = mysql_rows(
        cfg,
        "SELECT table_name, column_name FROM information_schema.key_column_usage "
        f"WHERE constraint_schema='{db}' AND referenced_table_schema='{db}' "
        "AND referenced_table_name='characters' AND referenced_column_name='guid';",
    )
    found = []
    for row in rows:
        if len(row) >= 2 and _ok_ident(row[0]) and _ok_ident(row[1]):
            found.append((row[0], row[1]))
    return found


def _find_table(cfg: LabConfig, db: str, choices: tuple[str, ...]) -> tuple[str, list] | None:
    for name in choices:
        cols = _meta(cfg, db, name)
        if cols:
            return name, cols
    return None


def build_transfer_sql(
    *,
    src_db: str,
    dest_db: str,
    world_db: str,
    src_cols: list,
    dest_cols: list,
    src_guid: int,
    src_account: int,
    dest_account: int,
    name: str,
    arrival: int,
    level_changed: bool,
    capital: dict,
    src_inv: list | None,
    dest_inv: list | None,
    src_items: list | None,
    dest_items: list | None,
    has_template: bool,
    children: list,
    src_home: list | None,
    dest_home: list | None,
    fk_deletes: list,
    extra_deletes: list | None = None,
) -> str:
    """One MariaDB script. Source deletes run only when the new character row exists."""
    for db in (src_db, dest_db, world_db):
        if not _ok_ident(db):
            raise ValueError("bad database name")
    dest_names = _names(dest_cols)
    overrides = character_overrides(dest_names, dest_account, name, arrival, level_changed, capital)
    insert_cols, insert_exprs = insert_pairs(dest_cols, _names(src_cols), overrides, "s")
    if "`guid`" not in insert_cols or "`name`" not in insert_cols:
        raise ValueError("destination character table has no guid or name")
    lock = f"wowweb_xfer_{dest_db}"
    lines = [
        f"SELECT GET_LOCK('{lock}', 15) INTO @locked;",
        "CREATE TEMPORARY TABLE IF NOT EXISTS wowweb_xfer_item ("
        "oldg BIGINT NOT NULL, newg BIGINT NOT NULL, bag INT NOT NULL, slot INT NOT NULL, "
        "entry INT NOT NULL, stack INT NOT NULL, PRIMARY KEY (oldg));",
        "DELETE FROM wowweb_xfer_item;",
        "START TRANSACTION;",
        f"SET @oldguid := {int(src_guid)};",
        f"SET @newguid := (SELECT IFNULL(MAX(guid),0)+1 FROM `{dest_db}`.`characters`);",
        f"INSERT INTO `{dest_db}`.`characters` ({', '.join(insert_cols)}) "
        f"SELECT {', '.join(insert_exprs)} FROM `{src_db}`.`characters` s "
        f"WHERE s.guid=@oldguid AND s.account={int(src_account)} AND s.online=0 AND @locked=1;",
        "SET @ok := ROW_COUNT();",
    ]
    item_mode = ""
    src_inv_names = _names(src_inv)
    if has_template and dest_items and src_items and "item" in src_inv_names and "itemEntry" in _names(src_items):
        item_mode = "instance"
    elif has_template and dest_items and "owner" in src_inv_names and "item_template" in src_inv_names:
        item_mode = "inline"
    if item_mode:
        lines.append(f"SET @ibase := (SELECT IFNULL(MAX(guid),0) FROM `{dest_db}`.`item_instance`);")
        if item_mode == "instance":
            lines.append(
                "INSERT INTO wowweb_xfer_item (oldg, newg, bag, slot, entry, stack) "
                "SELECT ii.guid, @ibase + ROW_NUMBER() OVER (ORDER BY ii.guid), "
                "IFNULL(inv.bag,0), IFNULL(inv.slot,0), ii.itemEntry, IFNULL(ii.`count`,1) "
                f"FROM `{src_db}`.`character_inventory` inv "
                f"JOIN `{src_db}`.`item_instance` ii ON ii.guid=inv.item "
                f"WHERE inv.guid=@oldguid AND @ok=1 AND EXISTS ("
                f"SELECT 1 FROM `{world_db}`.`item_template` t WHERE t.entry=ii.itemEntry);"
            )
            item_over = {"guid": "m.newg", "owner_guid": "@newguid"}
            item_cols, item_exprs = insert_pairs(dest_items, _names(src_items), item_over, "ii")
            if item_cols:
                lines.append(
                    f"INSERT INTO `{dest_db}`.`item_instance` ({', '.join(item_cols)}) "
                    f"SELECT {', '.join(item_exprs)} FROM wowweb_xfer_item m "
                    f"JOIN `{src_db}`.`item_instance` ii ON ii.guid=m.oldg WHERE @ok=1;"
                )
        else:
            lines.append(
                "INSERT INTO wowweb_xfer_item (oldg, newg, bag, slot, entry, stack) "
                "SELECT inv.guid, @ibase + ROW_NUMBER() OVER (ORDER BY inv.guid), "
                "IFNULL(inv.bag,0), IFNULL(inv.slot,0), inv.item_template, IFNULL(inv.stackcount,1) "
                f"FROM `{src_db}`.`character_inventory` inv "
                f"WHERE inv.owner=@oldguid AND @ok=1 AND EXISTS ("
                f"SELECT 1 FROM `{world_db}`.`item_template` t WHERE t.entry=inv.item_template);"
            )
            item_over = {
                "guid": "m.newg",
                "itemEntry": "m.entry",
                "owner_guid": "@newguid",
                "count": "m.stack",
                "durability": "100",
            }
            item_cols, item_exprs = insert_pairs(dest_items, set(), item_over, "m")
            if item_cols:
                lines.append(
                    f"INSERT INTO `{dest_db}`.`item_instance` ({', '.join(item_cols)}) "
                    f"SELECT {', '.join(item_exprs)} FROM wowweb_xfer_item m WHERE @ok=1;"
                )
        if dest_inv:
            inv_over = {}
            owner_col = inventory_owner_col(dest_inv)
            if owner_col:
                inv_over[owner_col] = "@newguid"
            for key, expr in (("bag", "m.bag"), ("slot", "m.slot"), ("item", "m.newg"), ("item_template", "m.entry"), ("stackcount", "m.stack")):
                if key in _names(dest_inv):
                    inv_over[key] = expr
            inv_cols, inv_exprs = insert_pairs(dest_inv, set(), inv_over, "m")
            if inv_cols:
                lines.append(
                    f"INSERT INTO `{dest_db}`.`character_inventory` ({', '.join(inv_cols)}) "
                    f"SELECT {', '.join(inv_exprs)} FROM wowweb_xfer_item m WHERE @ok=1;"
                )
    for dest_table, src_table, src_meta, dest_meta in children:
        if "guid" not in _names(src_meta) or "guid" not in _names(dest_meta):
            continue
        child_cols, child_exprs = insert_pairs(dest_meta, _names(src_meta), {"guid": "@newguid"}, "s")
        if not child_cols:
            continue
        lines.append(
            f"INSERT INTO `{dest_db}`.`{dest_table}` ({', '.join(child_cols)}) "
            f"SELECT {', '.join(child_exprs)} FROM `{src_db}`.`{src_table}` s "
            "WHERE s.guid=@oldguid AND @ok=1;"
        )
    if dest_home:
        home_over = {"guid": "@newguid"}
        home_over.update(homebind_numbers(dest_home, capital))
        if src_home and "guid" in _names(src_home):
            home_cols, home_exprs = insert_pairs(dest_home, _names(src_home), home_over, "s")
            lines.append(
                f"INSERT INTO `{dest_db}`.`character_homebind` ({', '.join(home_cols)}) "
                f"SELECT {', '.join(home_exprs)} FROM `{src_db}`.`character_homebind` s "
                "WHERE s.guid=@oldguid AND @ok=1;"
            )
        fresh_cols, fresh_exprs = insert_pairs(dest_home, set(), home_over, "s")
        lines.append(
            f"INSERT INTO `{dest_db}`.`character_homebind` ({', '.join(fresh_cols)}) "
            f"SELECT {', '.join(fresh_exprs)} FROM DUAL WHERE @ok=1 AND NOT EXISTS ("
            f"SELECT 1 FROM `{dest_db}`.`character_homebind` WHERE guid=@newguid);"
        )
    lines.append("SET FOREIGN_KEY_CHECKS=0;")
    seen = set()
    for table, col in list(fk_deletes or []) + list(extra_deletes or []):
        if not _ok_ident(table) or not _ok_ident(col) or (table, col) in seen:
            continue
        seen.add((table, col))
        lines.append(f"DELETE FROM `{src_db}`.`{table}` WHERE `{col}`=@oldguid AND @ok=1;")
    if item_mode == "instance":
        lines.append(
            f"DELETE ii FROM `{src_db}`.`item_instance` ii "
            "JOIN wowweb_xfer_item m ON m.oldg=ii.guid WHERE @ok=1;"
        )
    for _dest_table, src_table, src_meta, _dest_meta in children:
        if "guid" in _names(src_meta):
            lines.append(f"DELETE FROM `{src_db}`.`{src_table}` WHERE `guid`=@oldguid AND @ok=1;")
    if src_home:
        lines.append(f"DELETE FROM `{src_db}`.`character_homebind` WHERE `guid`=@oldguid AND @ok=1;")
    lines.append(
        f"DELETE FROM `{src_db}`.`characters` WHERE `guid`=@oldguid AND `account`={int(src_account)} AND @ok=1;"
    )
    lines.append("SET FOREIGN_KEY_CHECKS=1;")
    lines.append("COMMIT;")
    lines.append(f"SELECT RELEASE_LOCK('{lock}');")
    lines.append("SELECT @ok, @newguid;")
    return "\n".join(lines) + "\n"


def _parse_move(out: str) -> tuple[int, int]:
    ok_flag, new_guid = 0, 0
    for line in (out or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        try:
            ok_flag = int(parts[0])
            new_guid = int(parts[1])
        except ValueError:
            continue
    return ok_flag, new_guid


def transfer_character(
    cfg: LabConfig,
    src: Expansion,
    username: str,
    guid: int,
    dest_id: str,
    password: str,
    confirm: str,
    email: str = "",
    game_name: str = "",
    account_name: str = "",
) -> tuple[bool, str]:
    if not load_config(src.id).get("expansion_transfer"):
        return False, "That service is not available on this realm."
    if not password:
        return False, "Enter the password for this account."
    row = _owned(cfg, src, username, guid)
    problem = _offline_or_error(row)
    if problem:
        return False, problem
    if (confirm or "").strip() != row["name"]:
        return False, "Type the character's name to confirm the move."
    dest = resolve(dest_id or "")
    targets = transfer_targets(src)
    if dest is None or dest.id == src.id or dest.id not in {item.id for item in targets}:
        return False, "Pick a later expansion. A character moves forward from this realm."
    if not rules.combo_allowed(dest, row["race"], row["class_id"]):
        race = _RACE_NAMES.get(row["race"], "that race")
        klass = accounts.CLASS_NAMES.get(row["class_id"], "that class")
        return False, f"A {race} {klass} cannot play on {dest.name}."
    settings = load_config(dest.id)
    arrival = rules.arrival_level(row["level"], settings)
    src_db = cfg.chars_db(src)
    dest_db = cfg.chars_db(dest)
    world_db = cfg.world_db(dest)
    if not all(_ok_ident(db) for db in (src_db, dest_db, world_db)):
        return False, "Could not update that character."
    taken = mysql_rows(
        cfg,
        f"SELECT guid FROM `{dest_db}`.`characters` WHERE LOWER(name)=LOWER('{accounts._esc(row['name'])}') LIMIT 1;",
    )
    if taken:
        return False, "That name is already in use on the destination realm."
    src_account = account_id(cfg, src, username)
    if src_account is None:
        return False, "That character is not on this account."
    identity = _source_identity(cfg, src, username)
    authed, auth_name = accounts.authenticate(cfg, src, identity, password)
    if not authed or auth_name.upper() != username.upper():
        return False, "That password does not match this account."
    summary = accounts.account_summary(cfg, src, username)
    known_email = (email or summary.get("email") or "").strip()
    made, msg, dest_user = ensure_destination_account(
        cfg, dest, username, password, known_email, game_name, account_name
    )
    if not made or not dest_user:
        return False, msg or "Could not prepare the destination account."
    dest_account = account_id(cfg, dest, dest_user)
    if dest_account is None:
        return False, "Could not prepare the destination account."
    src_cols = _meta(cfg, src_db, "characters")
    dest_cols = _meta(cfg, dest_db, "characters")
    if not src_cols or not dest_cols:
        return False, "Could not update that character."
    src_inv = _meta(cfg, src_db, "character_inventory")
    extra_deletes = []
    inv_key = inventory_owner_col(src_inv)
    if src_inv and inv_key:
        extra_deletes.append(("character_inventory", inv_key))
    guild_members = _meta(cfg, src_db, "guild_member")
    if guild_members and "guid" in _names(guild_members):
        extra_deletes.append(("guild_member", "guid"))
    template = _meta(cfg, world_db, "item_template")
    has_template = bool(template and _has_column(template, "entry"))
    children = []
    for _label, choices in _COPY_TABLES:
        src_found = _find_table(cfg, src_db, choices)
        dest_found = _find_table(cfg, dest_db, choices)
        if src_found and dest_found:
            children.append((dest_found[0], src_found[0], src_found[1], dest_found[1]))
    try:
        script = build_transfer_sql(
            src_db=src_db,
            dest_db=dest_db,
            world_db=world_db,
            src_cols=src_cols,
            dest_cols=dest_cols,
            src_guid=int(guid),
            src_account=src_account,
            dest_account=dest_account,
            name=row["name"],
            arrival=arrival,
            level_changed=arrival != row["level"],
            capital=rules.capital_for(row["race"]),
            src_inv=src_inv,
            dest_inv=_meta(cfg, dest_db, "character_inventory"),
            src_items=_meta(cfg, src_db, "item_instance"),
            dest_items=_meta(cfg, dest_db, "item_instance"),
            has_template=has_template,
            children=children,
            src_home=_meta(cfg, src_db, "character_homebind"),
            dest_home=_meta(cfg, dest_db, "character_homebind"),
            fk_deletes=_fk_deletes(cfg, src_db),
            extra_deletes=extra_deletes,
        )
    except ValueError:
        return False, "Could not update that character."
    ok, out = mysql(cfg, script, db=dest_db, timeout=30)
    if not ok:
        return False, _public_sql_error(out, password)
    moved, new_guid = _parse_move(out)
    if moved != 1 or new_guid <= 0:
        return False, "That character could not be moved. They are still on this realm."
    arrived = mysql_rows(
        cfg,
        f"SELECT level, map FROM `{dest_db}`.`characters` WHERE guid={int(new_guid)} AND account={int(dest_account)} LIMIT 1;",
    )
    if not arrived:
        return False, "The move reported success but the character is not on the destination. Check both realms before trying again."
    city = "Orgrimmar" if row["race"] in rules.HORDE else "Stormwind"
    shown = arrived[0][0] if arrived[0] else str(arrival)
    return True, (
        f"Moved {row['name']} to {dest.name} at level {shown}. "
        f"They will appear in {city}. Log in there with the destination account. "
        "Gear that exists in the new world came along. Anything else was left behind."
    )
