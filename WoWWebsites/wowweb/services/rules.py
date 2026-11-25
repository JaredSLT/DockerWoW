"""Era rules for character services. No database access."""

from __future__ import annotations

import re

from ..catalog import Expansion

NAME_RE = re.compile(r"^[A-Z][a-z]{1,11}$")
GUILD_RE = re.compile(r"^[A-Za-z][A-Za-z ]{1,23}$")

# Login flags shared by CMaNGOS, AzerothCore, SkyFire, and Trinity.
AT_LOGIN_RESET_SPELLS = 0x02
AT_LOGIN_RESET_TALENTS = 0x04
AT_LOGIN_CUSTOMIZE = 0x08
AT_LOGIN_CHANGE_FACTION = 0x40
AT_LOGIN_CHANGE_RACE = 0x80

# Race ids. Neutral races that pick a faction use the Alliance city unless a
# later id is the Horde variant.
ALLIANCE = {1, 3, 4, 7, 11, 22, 25, 29, 30, 32, 34, 37, 52, 84}
HORDE = {2, 5, 6, 8, 9, 10, 26, 27, 28, 31, 35, 36, 70, 85}

# Classic race/class pairs. Death knights join every race from Wrath onward.
_VANILLA = {
    1: {1, 2, 4, 5, 8, 9},
    2: {1, 3, 4, 7, 9},
    3: {1, 2, 3, 4, 5},
    4: {1, 3, 4, 5, 11},
    5: {1, 4, 5, 8, 9},
    6: {1, 3, 7, 11},
    7: {1, 4, 8, 9},
    8: {1, 3, 4, 5, 7, 8},
}
_TBC = {
    10: {2, 3, 4, 5, 8, 9},
    11: {1, 2, 3, 5, 7, 8},
}
# Worgen: no paladin or shaman. Goblin: no paladin or druid.
_DENY = {
    22: {2, 7},
    9: {2, 11},
}


def valid_character_name(name: str) -> bool:
    return bool(NAME_RE.match(name or ""))


def valid_guild_name(name: str) -> bool:
    text = (name or "").strip()
    return bool(GUILD_RE.match(text)) and "  " not in text


def change_level_ok(level: int, class_id: int) -> bool:
    """Race and faction changes start at 10, or 55 for a death knight."""
    try:
        current = int(level)
        klass = int(class_id)
    except (TypeError, ValueError):
        return False
    if klass == 6:
        return current >= 55
    return current >= 10


def arrival_level(level: int, settings: dict) -> int:
    """Level a character arrives at on the destination expansion."""
    try:
        current = int(level)
    except (TypeError, ValueError):
        current = 1
    cap = int(settings.get("level_cap") or current or 1)
    above = int(settings.get("squish_above") or 0)
    landed = current
    if above and current > above:
        landed = int(settings.get("squish_to") or cap)
    if landed > cap:
        landed = cap
    return max(1, landed)


def _class_exists(exp: Expansion, class_id: int) -> bool:
    if class_id in {1, 2, 3, 4, 5, 7, 8, 9, 11}:
        return True
    if class_id == 6 and exp.expansion_level >= 2:
        return True
    if class_id == 10 and exp.expansion_level >= 4:
        return True
    if class_id == 12 and exp.expansion_level >= 6:
        return True
    if class_id == 13 and exp.expansion_level >= 9:
        return True
    return False


def combo_allowed(exp: Expansion, race: int, class_id: int) -> bool:
    """False when this expansion's character creation would reject the pair."""
    if not _class_exists(exp, class_id):
        return False
    if class_id in _DENY.get(race, set()):
        return False
    if exp.id in {"alpha", "vanilla"}:
        return class_id in _VANILLA.get(race, set())
    if exp.id == "tbc":
        return class_id in _VANILLA.get(race, _TBC.get(race, set()))
    if exp.id == "wotlk":
        base = _VANILLA.get(race, _TBC.get(race, set()))
        if class_id == 6:
            return bool(base)
        return class_id in base
    return True


def capital_for(race: int) -> dict[str, float | int]:
    """A city square that exists on every expansion's map."""
    if race in HORDE:
        return {
            "map": 1,
            "zone": 1637,
            "x": 1632.54,
            "y": -4440.77,
            "z": 15.46,
            "o": 2.2,
        }
    return {
        "map": 0,
        "zone": 1519,
        "x": -8913.23,
        "y": 554.63,
        "z": 93.79,
        "o": 0.67,
    }
