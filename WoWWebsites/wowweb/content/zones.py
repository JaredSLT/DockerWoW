"""Continents and zones that exist at an expansion.

Zone names are read from the lab area tables. A row is used only when its map
name is one of the continents below. Deepholm is a zone of The Maelstrom.
No names are invented when the database or the table is empty.
"""

from __future__ import annotations

from ..catalog import Expansion
from ..lab import load_lab, mysql_rows, port_open

# Minimum expansion_level, then the continent name. Cataclysm keeps the old
# world on Eastern Kingdoms and Kalimdor; it does not add a third old-world continent.
_CONTINENTS = (
    (0, "Eastern Kingdoms"),
    (0, "Kalimdor"),
    (1, "Outland"),
    (2, "Northrend"),
    (3, "The Maelstrom"),
    (4, "Pandaria"),
    (5, "Draenor"),
    (6, "Broken Isles"),
    (7, "Kul Tiras"),
    (7, "Zandalar"),
    (8, "The Shadowlands"),
    (9, "Dragon Isles"),
    (10, "Khaz Algar"),
    (11, "Quel'Thalas"),
)

# Display name on the map table -> continent in the list above.
_MAP_CONTINENT = {
    "Deepholm": "The Maelstrom",
}

# database, area table, map table. Each expansion reads only its own table.
_SOURCES = {
    "wotlk": ("wotlk_world", "areatable_dbc", "map_dbc"),
    "legion": ("legion_hotfixes", "area_table", "map"),
    "bfa": ("bfa_hotfixes", "area_table", "map"),
    "shadowlands": ("shadowlands_hotfixes", "area_table", "map"),
    "dragonflight": ("dragonflight_hotfixes", "area_table", "map"),
    "warwithin": ("warwithin_hotfixes", "area_table", "map"),
    "midnight": ("midnight_hotfixes", "area_table", "map"),
}

_AREA_NAME_COLS = ("AreaName_Lang_enUS", "AreaName_enUS", "AreaName")
_MAP_NAME_COLS = ("MapName_Lang_enUS", "MapName_enUS", "MapName")
_MAP_ID_COLS = ("MapID", "ContinentID")
_PARENT_COLS = ("ParentAreaID", "ParentAreaNum")


def continents_for(level: int) -> list[str]:
    return [name for minimum, name in _CONTINENTS if level >= minimum]


def _continent_for_map(map_name: str, allowed: set[str]) -> str | None:
    cleaned = map_name.strip()
    continent = _MAP_CONTINENT.get(cleaned, cleaned)
    if continent in allowed:
        return continent
    return None


def group_zones(
    areas: list[tuple[int, str, int, int | None]],
    maps: dict[int, str],
    allowed: list[str],
) -> dict[str, list[str]]:
    """Place area rows on continents.

    ``areas`` is (id, name, map id, parent id) in the order to keep.
    A row is skipped when the map name is not a continent, when the row is
    the continent itself, or when its parent is another zone (a subzone).
    """
    allowed_set = set(allowed)
    names_by_id: dict[int, str] = {}
    for area_id, name, _map_id, _parent in areas:
        cleaned = name.strip()
        if cleaned:
            names_by_id[area_id] = cleaned
    grouped = {name: [] for name in allowed}
    seen = {name: set() for name in allowed}
    for area_id, name, map_id, parent_id in areas:
        cleaned = name.strip()
        if not cleaned:
            continue
        map_name = maps.get(map_id)
        if not map_name:
            continue
        continent = _continent_for_map(map_name, allowed_set)
        if continent is None or cleaned == continent:
            continue
        if parent_id not in (None, 0):
            if names_by_id.get(parent_id) != continent:
                continue
        if cleaned in seen[continent]:
            continue
        seen[continent].add(cleaned)
        grouped[continent].append(cleaned)
    return grouped


def _columns(db: str, table: str) -> set[str]:
    rows = mysql_rows(load_lab(), f"SHOW COLUMNS FROM `{db}`.`{table}`;")
    return {row[0] for row in rows if row and row[0]}


def _pick(columns: set[str], options: tuple[str, ...]) -> str | None:
    for name in options:
        if name in columns:
            return name
    return None


def _cell(value: str | None) -> str:
    if value is None:
        return ""
    text = value.strip()
    if text in ("", "\\N", "NULL"):
        return ""
    return text


def _num(value: str | None) -> int | None:
    text = _cell(value)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _select(db: str, table: str, columns: list[str], order_by_id: bool) -> list[list[str]]:
    cols = ", ".join(f"`{col}`" for col in columns)
    order = " ORDER BY `ID`" if order_by_id else ""
    return mysql_rows(load_lab(), f"SELECT {cols} FROM `{db}`.`{table}`{order};")


def _read_areas(exp: Expansion) -> tuple[list[tuple[int, str, int, int | None]], dict[int, str]]:
    source = _SOURCES.get(exp.id)
    if source is None:
        return [], {}
    cfg = load_lab()
    if not port_open(cfg.mysql_host, cfg.mysql_port):
        return [], {}
    db, area_table, map_table = source
    area_cols = _columns(db, area_table)
    map_cols = _columns(db, map_table)
    area_name = _pick(area_cols, _AREA_NAME_COLS)
    map_id_col = _pick(area_cols, _MAP_ID_COLS)
    map_name = _pick(map_cols, _MAP_NAME_COLS)
    if not area_name or not map_id_col or not map_name or "ID" not in area_cols or "ID" not in map_cols:
        return [], {}
    parent_col = _pick(area_cols, _PARENT_COLS)
    area_select = ["ID", area_name, map_id_col]
    if parent_col:
        area_select.append(parent_col)
    maps: dict[int, str] = {}
    for row in _select(db, map_table, ["ID", map_name], True):
        if len(row) < 2:
            continue
        map_id = _num(row[0])
        name = _cell(row[1])
        if map_id is None or not name:
            continue
        maps[map_id] = name
    areas: list[tuple[int, str, int, int | None]] = []
    for row in _select(db, area_table, area_select, True):
        if len(row) < 3:
            continue
        area_id = _num(row[0])
        name = _cell(row[1])
        map_id = _num(row[2])
        if area_id is None or map_id is None or not name:
            continue
        parent_id = _num(row[3]) if parent_col and len(row) > 3 else 0
        areas.append((area_id, name, map_id, parent_id))
    return areas, maps


def zones_for(exp: Expansion) -> list[dict]:
    allowed = continents_for(exp.expansion_level)
    areas, maps = _read_areas(exp)
    grouped = group_zones(areas, maps, allowed)
    return [{"continent": name, "zones": grouped[name]} for name in allowed]
