"""Armory SQL against lab character/world databases."""

from __future__ import annotations

from typing import Any

from ..catalog import Expansion
from ..lab import LabConfig, mysql, mysql_rows
from .constants import CLASSES, GENDERS, RACES, slot_label, slots_for_expansion


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "''")


def _level_at_least(value: Any, minimum: int) -> bool:
    try:
        return int(value or 0) >= minimum
    except (TypeError, ValueError):
        return False


def _has_table(cfg: LabConfig, db: str, name: str) -> bool:
    rows = mysql_rows(cfg, f"SHOW TABLES FROM `{db}` LIKE '{_esc(name)}';")
    return bool(rows)


def _columns(cfg: LabConfig, db: str, table: str) -> set[str]:
    rows = mysql_rows(cfg, f"SHOW COLUMNS FROM `{db}`.`{table}`;")
    return {r[0] for r in rows if r}


def character_store(cfg: LabConfig, exp: Expansion) -> str:
    """Empty when the character tables can be read. Otherwise a reason to show."""
    ok, _err = mysql(cfg, "SELECT 1;")
    if not ok:
        return "The realm database is not reachable."
    db = cfg.chars_db(exp)
    if not _has_table(cfg, db, "characters"):
        return "This realm has no character data."
    return ""


def search_characters(cfg: LabConfig, exp: Expansion, query: str, limit: int = 25) -> list[dict]:
    rows, _error = search_with_status(cfg, exp, query, limit)
    return rows


def search_with_status(
    cfg: LabConfig, exp: Expansion, query: str, limit: int = 25
) -> tuple[list[dict], str]:
    """Rows, plus an error when the query did not run. An empty list with no error is a real miss."""
    if not query.strip():
        return [], ""
    store = character_store(cfg, exp)
    if store:
        return [], store
    db = cfg.chars_db(exp)
    q = _esc(query.strip())
    ok, out = mysql(
        cfg,
        f"SELECT guid, name, race, class, gender, level FROM `{db}`.`characters` "
        f"WHERE name LIKE '%{q}%' AND level >= 10 ORDER BY name LIMIT {int(limit)};",
    )
    if not ok:
        return [], "The realm database is not reachable."
    rows = []
    for line in out.splitlines():
        if line == "":
            continue
        rows.append(line.split("\t"))
    out = []
    for r in rows:
        out.append(
            {
                "guid": r[0],
                "name": r[1],
                "race": RACES.get(int(r[2] or 0), r[2]),
                "class": CLASSES.get(int(r[3] or 0), r[3]),
                "gender": GENDERS.get(int(r[4] or 0), r[4]),
                "level": r[5],
                "realm": exp.realm_name,
            }
        )
    return [row for row in out if _level_at_least(row.get("level"), 10)], ""


def get_character(cfg: LabConfig, exp: Expansion, name: str) -> dict[str, Any] | None:
    db = cfg.chars_db(exp)
    if not _has_table(cfg, db, "characters"):
        return None
    n = _esc(name)
    cols = _columns(cfg, db, "characters")
    extra = []
    for c in ("money", "totaltime", "online", "zone", "honor_highest_rank", "stored_honorable_kills"):
        if c in cols:
            extra.append(c)
    extra_sql = (", " + ", ".join(extra)) if extra else ""
    rows = mysql_rows(
        cfg,
        f"SELECT guid, name, race, class, gender, level, account{extra_sql} "
        f"FROM `{db}`.`characters` WHERE name='{n}' LIMIT 1;",
    )
    if not rows:
        return None
    r = rows[0]
    if not _level_at_least(r[5], 10):
        return None
    char: dict[str, Any] = {
        "guid": r[0],
        "name": r[1],
        "race_id": int(r[2] or 0),
        "class_id": int(r[3] or 0),
        "gender_id": int(r[4] or 0),
        "level": r[5],
        "account": r[6],
        "race": RACES.get(int(r[2] or 0), r[2]),
        "class": CLASSES.get(int(r[3] or 0), r[3]),
        "gender": GENDERS.get(int(r[4] or 0), r[4]),
        "realm": exp.realm_name,
        "equipment": [],
        "guild": None,
        "achievements": 0,
        "arena_teams": [],
        "money": 0,
        "online": False,
    }
    extra_vals = r[7:]
    for key, val in zip(extra, extra_vals):
        if key == "money":
            try:
                copper = int(val or 0)
                char["money"] = copper
                char["money_text"] = _money(copper)
            except ValueError:
                pass
        elif key == "online":
            char["online"] = val not in ("0", "", None)
        elif key == "honor_highest_rank":
            char["honor_rank"] = val
        elif key == "stored_honorable_kills":
            char["honorable_kills"] = val
        elif key == "totaltime":
            char["played"] = val
        elif key == "zone":
            char["zone"] = val
    char["equipment"] = _equipment(cfg, exp, db, char["guid"], cols)
    char["guild"] = _guild_for_char(cfg, db, char["guid"])
    if exp.has_achievements and _has_table(cfg, db, "character_achievement"):
        ac = mysql_rows(
            cfg,
            f"SELECT COUNT(*) FROM `{db}`.`character_achievement` WHERE guid={int(char['guid'])};",
        )
        if ac:
            char["achievements"] = ac[0][0]
    return char


def _money(copper: int) -> str:
    g, rest = divmod(copper, 10000)
    s, c = divmod(rest, 100)
    return f"{g}g {s}s {c}c"


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _template_cols(cfg: LabConfig, exp: Expansion) -> set[str]:
    world = cfg.world_db(exp)
    if not _has_table(cfg, world, "item_template"):
        return set()
    return _columns(cfg, world, "item_template")


def _display_col(cols: set[str]) -> str | None:
    for name in ("displayid", "display_id", "DisplayInfoID", "DisplayId"):
        if name in cols:
            return name
    return None


def _item_display_id(cfg: LabConfig, exp: Expansion, item_id: int, cols: set[str] | None = None) -> int:
    if not item_id:
        return 0
    if cols is None:
        cols = _template_cols(cfg, exp)
    col = _display_col(cols)
    if not col:
        return 0
    world = cfg.world_db(exp)
    rows = mysql_rows(
        cfg,
        f"SELECT `{col}` FROM `{world}`.`item_template` WHERE entry={int(item_id)} LIMIT 1;",
    )
    if not rows:
        return 0
    return _as_int(rows[0][0])


_PAIR_CACHE_KINDS = ("cmangos", "alpha")


def parse_equipment_cache(
    kind: str, expansion_level: int, raw: str | None
) -> list[tuple[str, int]]:
    """Parse equipmentCache into (slot name, item id).

    cmangos and alpha store item/enchant pairs. azerothcore, trinity, and
    skyfire store one item id per slot; a non-numeric token is skipped.
    Item id 0 is an empty slot and is omitted. Parsing stops at the era's
    slot-map length.
    """
    slots = slots_for_expansion(expansion_level)
    if raw is None:
        return []
    parts = raw.split() if isinstance(raw, str) else str(raw).split()
    if not parts:
        return []
    found: list[tuple[str, int]] = []
    core = (kind or "").strip().lower()
    if core in _PAIR_CACHE_KINDS:
        slot = 0
        index = 0
        while index + 1 < len(parts) and slot < len(slots):
            try:
                item_id = int(parts[index])
            except ValueError:
                break
            if item_id:
                found.append((slots[slot], item_id))
            slot += 1
            index += 2
        return found
    slot = 0
    for token in parts:
        if slot >= len(slots):
            break
        try:
            item_id = int(token)
        except ValueError:
            continue
        if item_id:
            found.append((slots[slot], item_id))
        slot += 1
    return found


def _equipment(cfg: LabConfig, exp: Expansion, db: str, guid: str, char_cols: set[str]) -> list[dict]:
    items: list[dict] = []
    tpl_cols = _template_cols(cfg, exp)
    if "equipmentCache" in char_cols:
        rows = mysql_rows(
            cfg, f"SELECT equipmentCache FROM `{db}`.`characters` WHERE guid={int(guid)} LIMIT 1;"
        )
        if rows and rows[0][0]:
            parsed = parse_equipment_cache(exp.kind, exp.expansion_level, rows[0][0])
            for slot_name, item_id in parsed:
                items.append(
                    {
                        "slot": slot_name,
                        "item_id": item_id,
                        "name": item_name(cfg, exp, item_id),
                        "display_id": _item_display_id(cfg, exp, item_id, tpl_cols),
                    }
                )
            return items
    if _has_table(cfg, db, "character_inventory"):
        inv_cols = _columns(cfg, db, "character_inventory")
        bag_filter = "AND bag=0" if "bag" in inv_cols else ""
        slot_limit = len(slots_for_expansion(exp.expansion_level))
        rows = mysql_rows(
            cfg,
            f"SELECT slot, item FROM `{db}`.`character_inventory` "
            f"WHERE guid={int(guid)} {bag_filter} AND slot < {slot_limit} ORDER BY slot;",
        )
        for slot, item in rows:
            try:
                sid = int(slot)
            except ValueError:
                continue
            name = slot_label(exp.expansion_level, sid)
            item_id = _item_template_id(cfg, db, item)
            items.append(
                {
                    "slot": name,
                    "item_id": item_id,
                    "name": item_name(cfg, exp, item_id) if item_id else f"Item {item}",
                    "display_id": _item_display_id(cfg, exp, item_id, tpl_cols),
                }
            )
    return items


def _item_template_id(cfg: LabConfig, db: str, instance_id: str) -> int:
    if not _has_table(cfg, db, "item_instance"):
        try:
            return int(instance_id)
        except ValueError:
            return 0
    cols = _columns(cfg, db, "item_instance")
    field = "itemEntry" if "itemEntry" in cols else ("itemid" if "itemid" in cols else None)
    if not field:
        return 0
    rows = mysql_rows(
        cfg, f"SELECT {field} FROM `{db}`.`item_instance` WHERE guid={int(instance_id)} LIMIT 1;"
    )
    if not rows:
        return 0
    try:
        return int(rows[0][0])
    except ValueError:
        return 0


def item_name(cfg: LabConfig, exp: Expansion, item_id: int) -> str:
    if not item_id:
        return ""
    world = cfg.world_db(exp)
    for table in ("item_template", "item_template_locale"):
        if not _has_table(cfg, world, table if table == "item_template" else "item_template"):
            continue
    if _has_table(cfg, world, "item_template"):
        cols = _columns(cfg, world, "item_template")
        name_col = "name" if "name" in cols else None
        if name_col:
            rows = mysql_rows(
                cfg,
                f"SELECT {name_col} FROM `{world}`.`item_template` WHERE entry={int(item_id)} LIMIT 1;",
            )
            if rows:
                return rows[0][0]
    return f"Item #{item_id}"


def get_item(cfg: LabConfig, exp: Expansion, item_id: int) -> dict | None:
    world = cfg.world_db(exp)
    if not _has_table(cfg, world, "item_template"):
        return None
    cols = _columns(cfg, world, "item_template")
    fields = [
        c
        for c in (
            "entry",
            "name",
            "class",
            "subclass",
            "Quality",
            "quality",
            "BuyPrice",
            "SellPrice",
            "ItemLevel",
            "RequiredLevel",
            "displayid",
            "display_id",
            "DisplayInfoID",
        )
        if c in cols
    ]
    if "entry" not in fields:
        return None
    rows = mysql_rows(
        cfg,
        f"SELECT {', '.join(fields)} FROM `{world}`.`item_template` WHERE entry={int(item_id)} LIMIT 1;",
    )
    if not rows:
        return None
    data = dict(zip(fields, rows[0]))
    data["name"] = data.get("name") or f"Item #{item_id}"
    data["quality"] = data.get("Quality") or data.get("quality") or "0"
    raw_display = data.get("displayid", data.get("display_id", data.get("DisplayInfoID")))
    data["display_id"] = _as_int(raw_display)
    return data


def _guild_for_char(cfg: LabConfig, db: str, guid: str) -> dict | None:
    if not _has_table(cfg, db, "guild_member"):
        return None
    cols = _columns(cfg, db, "guild_member")
    gid_col = "guildid" if "guildid" in cols else ("guildId" if "guildId" in cols else None)
    if not gid_col:
        return None
    rows = mysql_rows(
        cfg, f"SELECT {gid_col} FROM `{db}`.`guild_member` WHERE guid={int(guid)} LIMIT 1;"
    )
    if not rows:
        return None
    gid = rows[0][0]
    if not _has_table(cfg, db, "guild"):
        return {"id": gid, "name": f"Guild {gid}"}
    gcols = _columns(cfg, db, "guild")
    name_col = "name" if "name" in gcols else None
    id_col = "guildid" if "guildid" in gcols else "guildId"
    if not name_col:
        return {"id": gid, "name": f"Guild {gid}"}
    grows = mysql_rows(
        cfg, f"SELECT {name_col} FROM `{db}`.`guild` WHERE `{id_col}`={int(gid)} LIMIT 1;"
    )
    if not grows:
        return {"id": gid, "name": f"Guild {gid}"}
    return {"id": gid, "name": grows[0][0]}


def get_guild(cfg: LabConfig, exp: Expansion, name: str) -> dict | None:
    db = cfg.chars_db(exp)
    if not _has_table(cfg, db, "guild"):
        return None
    n = _esc(name)
    gcols = _columns(cfg, db, "guild")
    id_col = "guildid" if "guildid" in gcols else "guildId"
    rows = mysql_rows(cfg, f"SELECT `{id_col}`, name FROM `{db}`.`guild` WHERE name='{n}' LIMIT 1;")
    if not rows:
        return None
    gid, gname = rows[0]
    members = []
    if _has_table(cfg, db, "guild_member"):
        mcols = _columns(cfg, db, "guild_member")
        mg = "guildid" if "guildid" in mcols else "guildId"
        mrows = mysql_rows(
            cfg,
            f"SELECT gm.guid, c.name, c.level, c.class FROM `{db}`.`guild_member` gm "
            f"JOIN `{db}`.`characters` c ON c.guid=gm.guid WHERE gm.`{mg}`={int(gid)} "
            f"ORDER BY c.level DESC LIMIT 100;",
        )
        for r in mrows:
            members.append(
                {
                    "guid": r[0],
                    "name": r[1],
                    "level": r[2],
                    "class": CLASSES.get(int(r[3] or 0), r[3]),
                }
            )
    return {"id": gid, "name": gname, "members": members, "realm": exp.realm_name}


def arena_ladder(cfg: LabConfig, exp: Expansion, limit: int = 25) -> list[dict]:
    db = cfg.chars_db(exp)
    if not _has_table(cfg, db, "arena_team"):
        return []
    cols = _columns(cfg, db, "arena_team")
    rating = "rating" if "rating" in cols else None
    name = "name" if "name" in cols else None
    ttype = "type" if "type" in cols else None
    if not (rating and name):
        return []
    extra = f", {ttype}" if ttype else ""
    rows = mysql_rows(
        cfg,
        f"SELECT {name}, {rating}{extra} FROM `{db}`.`arena_team` ORDER BY {rating} DESC LIMIT {int(limit)};",
    )
    out = []
    for r in rows:
        out.append({"name": r[0], "rating": r[1], "type": r[2] if len(r) > 2 else ""})
    return out


def auctions(cfg: LabConfig, exp: Expansion, limit: int = 40) -> list[dict]:
    db = cfg.chars_db(exp)
    if not _has_table(cfg, db, "auctionhouse"):
        return []
    cols = _columns(cfg, db, "auctionhouse")
    item_col = "item" if "item" in cols else ("itemguid" if "itemguid" in cols else None)
    buy = "buyoutprice" if "buyoutprice" in cols else ("buyout" if "buyout" in cols else None)
    if not item_col:
        return []
    select = f"SELECT {item_col}" + (f", {buy}" if buy else "") + f" FROM `{db}`.`auctionhouse` LIMIT {int(limit)};"
    rows = mysql_rows(cfg, select)
    out = []
    for r in rows:
        try:
            inst = int(r[0])
        except ValueError:
            continue
        iid = _item_template_id(cfg, db, str(inst)) or inst
        out.append(
            {
                "item_id": iid,
                "name": item_name(cfg, exp, iid),
                "buyout": _money(int(r[1])) if buy and len(r) > 1 and (r[1] or "").isdigit() else "—",
            }
        )
    return out


def honor_ladder(cfg: LabConfig, exp: Expansion, limit: int = 25) -> list[dict]:
    db = cfg.chars_db(exp)
    if not _has_table(cfg, db, "characters"):
        return []
    cols = _columns(cfg, db, "characters")
    if "stored_honorable_kills" not in cols:
        return []
    rows = mysql_rows(
        cfg,
        f"SELECT name, level, class, stored_honorable_kills, honor_highest_rank "
        f"FROM `{db}`.`characters` ORDER BY stored_honorable_kills DESC LIMIT {int(limit)};",
    )
    out = []
    for r in rows:
        out.append(
            {
                "name": r[0],
                "level": r[1],
                "class": CLASSES.get(int(r[2] or 0), r[2]),
                "kills": r[3],
                "rank": r[4],
            }
        )
    return out
