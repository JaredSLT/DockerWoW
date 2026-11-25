"""Talent tree records."""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class Talent:
    name: str
    max_rank: int
    col: int
    row: int
    desc: str = ""
    requires: str = ""


@dataclass(frozen=True)
class Tree:
    name: str
    talents: tuple[Talent, ...]


def _t(name: str, ranks: int, col: int, row: int, desc: str = "", requires: str = "") -> Talent:
    return Talent(name, ranks, col, row, desc, requires)


