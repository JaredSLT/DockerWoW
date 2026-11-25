"""Era talent calculators. Builds are digit strings, one digit per talent in order."""

from __future__ import annotations

from ..catalog import Expansion
from .later import DH, DK, EVOKER, MONK
from .models import Talent, Tree
from .vanilla import VANILLA

__all__ = [
    "Talent",
    "Tree",
    "classes_for",
    "trees_for",
    "points_available",
    "parse_build",
    "encode_build",
    "can_spend",
    "can_unspend",
]


def classes_for(exp: Expansion) -> list[str]:
    names = ["warrior", "paladin", "hunter", "rogue", "priest", "shaman", "mage", "warlock", "druid"]
    if exp.expansion_level >= 2:
        names.insert(5, "deathknight")
    if exp.expansion_level >= 4:
        names.append("monk")
    if exp.expansion_level >= 6:
        names.append("demonhunter")
    if exp.expansion_level >= 9:
        names.append("evoker")
    return names


def trees_for(exp: Expansion, class_id: str) -> tuple[Tree, ...] | None:
    cid = class_id.lower().replace(" ", "").replace("-", "")
    if cid in ("deathknight", "dk"):
        return DK if exp.expansion_level >= 2 else None
    if cid == "monk":
        return MONK if exp.expansion_level >= 4 else None
    if cid == "demonhunter":
        return DH if exp.expansion_level >= 6 else None
    if cid == "evoker":
        return EVOKER if exp.expansion_level >= 9 else None
    return VANILLA.get(cid)


def points_available(exp: Expansion) -> int:
    # Vanilla 1.12: 51 points (level 60). +1 per extra 10 levels-ish is wrong;
    # last-patch caps: 60/70/80/85/90/100/110/120/60/70/80/90
    caps = {0: 51, 1: 61, 2: 71, 3: 41, 4: 46, 5: 51, 6: 56, 7: 61, 8: 50, 9: 50, 10: 50, 11: 50}
    if exp.generation in ("gen2", "gen3", "gen4") and exp.expansion_level >= 4:
        return 0  # MoP+ used spec rows, not classic trees — calculator still shows era trees for pre-MoP
    return caps.get(exp.expansion_level, 51)


def parse_build(trees: tuple[Tree, ...], digits: str) -> list[int]:
    total = sum(len(t.talents) for t in trees)
    raw = "".join(ch for ch in digits if ch.isdigit())
    ranks = [0] * total
    for i, ch in enumerate(raw[:total]):
        ranks[i] = int(ch)
    return ranks


def encode_build(ranks: list[int]) -> str:
    return "".join(str(max(0, int(r))) for r in ranks)


def _slots(trees) -> list[tuple[int, Talent]]:
    slots = []
    for tree_index, tree in enumerate(trees):
        for talent in tree.talents:
            slots.append((tree_index, talent))
    return slots


def _values(ranks, count: int) -> list[int]:
    values = [0] * count
    for i, raw in enumerate(ranks):
        if i >= count:
            break
        values[i] = raw if raw > 0 else 0
    return values


def _tree_total(slots: list[tuple[int, Talent]], values: list[int], tree_index: int) -> int:
    return sum(values[i] for i, (ti, _talent) in enumerate(slots) if ti == tree_index)


def _require_index(slots: list[tuple[int, Talent]], tree_index: int, name: str) -> int | None:
    if not name:
        return None
    for i, (ti, talent) in enumerate(slots):
        if ti == tree_index and talent.name == name:
            return i
    return None


def can_spend(trees, ranks, index: int, max_points: int) -> bool:
    """Row N needs 5*N points already in that tree. The new point does not count."""
    slots = _slots(trees)
    if max_points <= 0 or index < 0 or index >= len(slots):
        return False
    values = _values(ranks, len(slots))
    tree_index, talent = slots[index]
    if values[index] >= talent.max_rank:
        return False
    if sum(values) >= max_points:
        return False
    if _tree_total(slots, values, tree_index) < 5 * talent.row:
        return False
    if talent.requires:
        required = _require_index(slots, tree_index, talent.requires)
        if required is None or values[required] < slots[required][1].max_rank:
            return False
    return True


def can_unspend(trees, ranks, index: int) -> bool:
    """False when the lower rank would strand a higher row or an arrow dependent."""
    slots = _slots(trees)
    if index < 0 or index >= len(slots):
        return False
    values = _values(ranks, len(slots))
    if values[index] <= 0:
        return False
    tree_index, talent = slots[index]
    values[index] -= 1
    tree_points = _tree_total(slots, values, tree_index)
    for i, (ti, other) in enumerate(slots):
        if ti != tree_index or values[i] <= 0:
            continue
        if tree_points < 5 * other.row:
            return False
    if values[index] < talent.max_rank:
        for i, (ti, other) in enumerate(slots):
            if ti == tree_index and other.requires == talent.name and values[i] > 0:
                return False
    return True
