"""Race/class/slot labels."""

from __future__ import annotations

RACES = {
    1: "Human",
    2: "Orc",
    3: "Dwarf",
    4: "Night Elf",
    5: "Undead",
    6: "Tauren",
    7: "Gnome",
    8: "Troll",
    9: "Goblin",
    10: "Blood Elf",
    11: "Draenei",
    22: "Worgen",
    24: "Pandaren",
    25: "Alliance Pandaren",
    26: "Horde Pandaren",
    27: "Nightborne",
    28: "Highmountain Tauren",
    29: "Void Elf",
    30: "Lightforged Draenei",
    31: "Zandalari Troll",
    32: "Kul Tiran",
    34: "Dark Iron Dwarf",
    35: "Vulpera",
    36: "Mag'har Orc",
    37: "Mechagnome",
    52: "Dracthyr",
    70: "Dracthyr",
    84: "Earthen",
    85: "Earthen",
}

CLASSES = {
    1: "Warrior",
    2: "Paladin",
    3: "Hunter",
    4: "Rogue",
    5: "Priest",
    6: "Death Knight",
    7: "Shaman",
    8: "Mage",
    9: "Warlock",
    10: "Monk",
    11: "Druid",
    12: "Demon Hunter",
    13: "Evoker",
}

GENDERS = {0: "Male", 1: "Female"}

# Classic equipment indices: Ranged is 17, Tabard is 18.
SLOTS_CLASSIC: tuple[str, ...] = (
    "Head",
    "Neck",
    "Shoulders",
    "Shirt",
    "Chest",
    "Waist",
    "Legs",
    "Feet",
    "Wrists",
    "Hands",
    "Finger 1",
    "Finger 2",
    "Trinket 1",
    "Trinket 2",
    "Back",
    "Main Hand",
    "Off Hand",
    "Ranged",
    "Tabard",
)

# WoD dropped the ranged slot. Tabard follows Off Hand. No relic slots.
SLOTS_WOD: tuple[str, ...] = (
    "Head",
    "Neck",
    "Shoulders",
    "Shirt",
    "Chest",
    "Waist",
    "Legs",
    "Feet",
    "Wrists",
    "Hands",
    "Finger 1",
    "Finger 2",
    "Trinket 1",
    "Trinket 2",
    "Back",
    "Main Hand",
    "Off Hand",
    "Tabard",
)

# Classic list kept for callers that still want the 19 vanilla names.
SLOT_NAMES = list(SLOTS_CLASSIC)


def slots_for_expansion(expansion_level: int) -> tuple[str, ...]:
    """Equipment slot names for an expansion_level.

    Levels 0-1 (alpha, vanilla, tbc) and 2-4 (wotlk, cata, mop) use the
    19 classic slots, including Ranged. Level 5+ (wod onward) drops Ranged.
    """
    try:
        level = int(expansion_level)
    except (TypeError, ValueError):
        level = 0
    if level >= 5:
        return SLOTS_WOD
    return SLOTS_CLASSIC


def slot_label(expansion_level: int, index: int) -> str:
    """Name for an inventory slot index. Indices past the era map are `Slot N`."""
    slots = slots_for_expansion(expansion_level)
    try:
        sid = int(index)
    except (TypeError, ValueError):
        return f"Slot {index}"
    if 0 <= sid < len(slots):
        return slots[sid]
    return f"Slot {sid}"

