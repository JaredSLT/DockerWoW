"""Per-expansion service switches.

Each expansion has wowweb/services/config/<id>.json. Missing keys fall back
to the defaults below. Boosts and the WoW Token ship turned off.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..catalog import Expansion, list_expansions

CONFIG_DIR = Path(__file__).resolve().parent / "config"

DEFAULTS = {
    "name_change": True,
    "appearance_change": False,
    "race_change": False,
    "faction_change": False,
    "guild_name_change": False,
    "expansion_transfer": False,
    "boost": False,
    "wow_token": False,
    "level_cap": 60,
    "squish_above": 0,
    "squish_to": 0,
    "boost_level": 0,
    "token_gold": 0,
}

SERVICE_KEYS = (
    "name_change",
    "appearance_change",
    "race_change",
    "faction_change",
    "guild_name_change",
    "expansion_transfer",
    "boost",
    "wow_token",
)


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def load_config(exp_id: str) -> dict:
    path = CONFIG_DIR / f"{exp_id}.json"
    found = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    merged = dict(DEFAULTS)
    merged.update(found)
    for key in SERVICE_KEYS:
        merged[key] = _as_bool(merged.get(key))
    for key in ("level_cap", "squish_above", "squish_to", "boost_level", "token_gold"):
        merged[key] = int(merged.get(key) or 0)
    return merged


def service_enabled(exp_id: str, key: str) -> bool:
    return bool(load_config(exp_id).get(key))


def transfer_targets(src: Expansion) -> list[Expansion]:
    """Later expansions a character from src may move forward into."""
    if not service_enabled(src.id, "expansion_transfer"):
        return []
    order = list_expansions()
    ids = [exp.id for exp in order]
    if src.id not in ids:
        return []
    later = order[ids.index(src.id) + 1 :]
    # A side realm can opt out of being a destination. A missing key stays eligible.
    return [exp for exp in later if load_config(exp.id).get("accepts_transfer", True)]
