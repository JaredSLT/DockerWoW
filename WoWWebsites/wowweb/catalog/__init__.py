"""Expansion catalog aligned with the private-server lab."""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Optional

from .eras import EXPANSIONS, ORDER
from .models import Expansion

__all__ = ["Expansion", "EXPANSIONS", "ORDER", "resolve", "list_expansions"]

_KINDS = {"alpha", "cmangos", "azerothcore", "trinity", "skyfire"}


def _apply_runtime(exp: Expansion) -> Expansion:
    """The realm container sets WOW_SHORT and WOW_KIND from the selected core."""
    short = os.environ.get("WOW_SHORT", "").strip()
    kind = os.environ.get("WOW_KIND", "").strip()
    if not short or not kind or kind not in _KINDS:
        return exp
    if exp.lab_short != short and exp.id != short:
        return exp
    if exp.kind == kind:
        return exp
    return replace(exp, kind=kind)


def resolve(token: str) -> Optional[Expansion]:
    if not token:
        return None
    key = token.strip().lower().replace(" ", "-").replace("_", "-")
    found: Optional[Expansion] = None
    if key in EXPANSIONS:
        found = EXPANSIONS[key]
    else:
        for exp in EXPANSIONS.values():
            if key == exp.lab_short or key in exp.aliases:
                found = exp
                break
            if key == exp.name.lower().replace(" ", "-"):
                found = exp
                break
    if found is None:
        return None
    return _apply_runtime(found)


def list_expansions() -> list[Expansion]:
    return [_apply_runtime(EXPANSIONS[i]) for i in ORDER]
