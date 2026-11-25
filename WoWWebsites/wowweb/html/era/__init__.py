"""Per-expansion shells. One module per catalog id.

Hyphenated ids load the underscored module (`classic-era` → `classic_era`).
"""

from __future__ import annotations

import importlib

_SKINNED = (
    "alpha",
    "vanilla",
    "classic-era",
    "tbc",
    "wotlk",
    "wotlk-classic",
    "cata",
    "cata-classic",
    "mop",
    "wod",
    "legion",
    "bfa",
    "shadowlands",
    "dragonflight",
    "warwithin",
    "midnight",
)


def module(exp_id: str):
    if exp_id not in _SKINNED:
        return None
    name = exp_id.replace("-", "_")
    try:
        return importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError:
        return None
