"""Races, classes, professions."""

from __future__ import annotations

from ..catalog import Expansion

_CORE = ["human", "dwarf", "nightelf", "gnome", "orc", "undead", "tauren", "troll"]
_TBC = ["human", "dwarf", "nightelf", "gnome", "draenei", "orc", "undead", "tauren", "troll", "bloodelf"]
_CATA = ["human", "dwarf", "nightelf", "gnome", "draenei", "worgen", "orc", "undead", "tauren", "troll", "bloodelf", "goblin"]
_MOP = ["human", "dwarf", "nightelf", "gnome", "draenei", "worgen", "pandaren", "orc", "undead", "tauren", "troll", "bloodelf", "goblin"]
_LEGION = _MOP + ["voidelf", "lightforged", "nightborne", "highmountain"]
_BFA = _LEGION + ["darkiron", "kultiran", "maghar", "zandalari", "mechagnome", "vulpera"]
_DF = _BFA + ["dracthyr"]
_TWW = _DF + ["earthen"]
_MIDNIGHT = _TWW + ["haranir"]

RACES_BY_ERA = {
    "alpha": list(_CORE),
    "vanilla": list(_CORE),
    "tbc": list(_TBC),
    "wotlk": list(_TBC),
    "cata": list(_CATA),
    "mop": list(_MOP),
    "wod": list(_MOP),
    "legion": list(_LEGION),
    "bfa": list(_BFA),
    "shadowlands": list(_BFA),
    "dragonflight": list(_DF),
    "warwithin": list(_TWW),
    "midnight": list(_MIDNIGHT),
    "classic-era": list(_CORE),
    "wotlk-classic": list(_TBC),
    "cata-classic": list(_CATA),
}

# Capitals that changed after the city on the older race page was lost.
_CAPITALS = {
    ("bfa", "nightelf"): "Stormwind",
    ("shadowlands", "nightelf"): "Stormwind",
    ("dragonflight", "nightelf"): "Bel'ameth",
    ("warwithin", "nightelf"): "Bel'ameth",
    ("midnight", "nightelf"): "Bel'ameth",
    ("bfa", "undead"): "Lordaeron",
    ("shadowlands", "undead"): "Lordaeron",
    ("dragonflight", "undead"): "Lordaeron",
    ("warwithin", "undead"): "Lordaeron",
    ("midnight", "undead"): "Lordaeron",
}

RACE_INFO = {
    "human": ("Human", "Alliance", "Stormwind", "The Kingdom of Stormwind stands as the heart of the Alliance, a people of diplomacy, paladins, and stubborn hope."),
    "dwarf": ("Dwarf", "Alliance", "Ironforge", "Forged in the snows of Khaz Modan, dwarves are explorers, riflemen, and keepers of titan secrets."),
    "nightelf": ("Night Elf", "Alliance", "Darnassus", "Ancient guardians of Kalimdor, the kaldorei walk the line between druidic peace and a long memory of war."),
    "gnome": ("Gnome", "Alliance", "Gnomeregan", "Escapees of a fallen city, gnomes bring invention, curiosity, and an alarming number of explosives."),
    "draenei": ("Draenei", "Alliance", "The Exodar", "Exiles of Argus who crashed upon Azeroth, the draenei bring the Light and the naaru with them."),
    "worgen": ("Worgen", "Alliance", "Gilneas", "Cursed citizens of a walled kingdom, worgen fight as both men and wolves."),
    "pandaren": ("Pandaren", "Neutral", "The Wandering Isle", "Children of a wandering island who choose Alliance or Horde when they set foot on the wider world."),
    "orc": ("Orc", "Horde", "Orgrimmar", "A people who broke the demon blood and built a new home in Durotar under a red banner."),
    "undead": ("Undead", "Horde", "Undercity", "The Forsaken walk a grim path between vengeance and survival beneath Lordaeron."),
    "tauren": ("Tauren", "Horde", "Thunder Bluff", "The shu'halo of the plains honor the Earth Mother and stand with the Horde as its conscience."),
    "troll": ("Troll", "Horde", "Sen'jin / Orgrimmar", "Darkspear trolls left the islands for a place among the Horde, bringing voodoo and fierce loyalty."),
    "bloodelf": ("Blood Elf", "Horde", "Silvermoon", "Sin'dorei of Quel'Thalas, hungry for magic and determined to reclaim their sunlit city."),
    "goblin": ("Goblin", "Horde", "Bilgewater Harbor", "Cartel entrepreneurs who turned a volcanic disaster into a business opportunity with the Horde."),
    "voidelf": ("Void Elf", "Alliance", "Telogrus Rift", "Ren'dorei who stepped into the Void and came back changed, still sworn to the Alliance."),
    "lightforged": ("Lightforged Draenei", "Alliance", "The Vindicaar", "Army of the Light draenei, forged in a thousand years of war on Argus."),
    "nightborne": ("Nightborne", "Horde", "Suramar", "Shal'dorei of Suramar who broke the Nightwell's hold and joined the Horde."),
    "highmountain": ("Highmountain Tauren", "Horde", "Thunder Totem", "Tauren of Highmountain, moose-riders who stood with the Horde against the Legion."),
    "darkiron": ("Dark Iron Dwarf", "Alliance", "Shadowforge City", "The Dark Iron clan, masters of magma and Shadowforge, returned to the Alliance."),
    "kultiran": ("Kul Tiran", "Alliance", "Boralus", "Sea-hardened humans of Kul Tiras, proud of their fleet and their tidesages."),
    "maghar": ("Mag'har Orc", "Horde", "Orgrimmar", "Uncorrupted orcs of alternate Draenor who followed the Horde home to Azeroth."),
    "zandalari": ("Zandalari Troll", "Horde", "Dazar'alor", "The empire of Zandalar, golden fleet and loa, standing with the Horde."),
    "mechagnome": ("Mechagnome", "Alliance", "Mechagon", "Gnomes of Mechagon who rebuilt themselves in clockwork and joined the Alliance."),
    "vulpera": ("Vulpera", "Horde", "Vol'dun", "Desert foxfolk of Vol'dun, scavengers and survivors who threw in with the Horde."),
    "dracthyr": ("Dracthyr", "Neutral", "The Forbidden Reach", "Dracthyr of the Dragon Isles who choose Alliance or Horde after they wake."),
    "earthen": ("Earthen", "Neutral", "Dornogal", "Titan-forged earthen of Khaz Algar, free to choose a faction in Dornogal."),
    "haranir": ("Haranir", "Neutral", "The Den", "Root-wardens of Harandar who leave The Den to fight for either faction."),
}

CLASS_INFO = {
    "warrior": ("Warrior", "Plate", "Arms, Fury, Protection", "Masters of melee combat who tank, rage, and hold the line."),
    "paladin": ("Paladin", "Plate", "Holy, Protection, Retribution", "Knights of the Light who heal, shield, and smite."),
    "hunter": ("Hunter", "Mail", "Beast Mastery, Marksmanship, Survival", "Rangers who fight with pets, traps, and a long shot."),
    "rogue": ("Rogue", "Leather", "Assassination, Combat, Subtlety", "Stealth, poisons, and a knife where it hurts."),
    "priest": ("Priest", "Cloth", "Discipline, Holy, Shadow", "The Light's shepherds — or its shadow."),
    "shaman": ("Shaman", "Mail", "Elemental, Enhancement, Restoration", "Callers of the elements who totem, shock, and mend."),
    "mage": ("Mage", "Cloth", "Arcane, Fire, Frost", "Scholars of the arcane who freeze, ignite, and blink."),
    "warlock": ("Warlock", "Cloth", "Affliction, Demonology, Destruction", "Bargainers with demons who drain, summon, and burn."),
    "druid": ("Druid", "Leather", "Balance, Feral, Restoration", "Shapeshifters of the wild who heal, claw, and call the stars."),
    "deathknight": ("Death Knight", "Plate", "Blood, Frost, Unholy", "The Lich King's former champions, now free to spend unholy power as they choose."),
    "monk": ("Monk", "Leather", "Brewmaster, Mistweaver, Windwalker", "Students of the pandaren martial path."),
    "demonhunter": ("Demon Hunter", "Leather", "Havoc, Vengeance", "Illidari who hunt demons with the enemy's own fel."),
    "evoker": ("Evoker", "Mail", "Devastation, Preservation, Augmentation", "Dracthyr who breathe the Aspects' gifts."),
}

# (name, description, first expansion_level, last expansion_level inclusive)
_PROFESSION_ROWS = [
    ("Alchemy", "Brew potions, flasks, and transmutes.", 0, 99),
    ("Blacksmithing", "Forge weapons and plate.", 0, 99),
    ("Enchanting", "Disenchant gear and lace it with magic.", 0, 99),
    ("Engineering", "Gadgets, bombs, and goggles.", 0, 99),
    ("Herbalism", "Gather living reagents.", 0, 99),
    ("Jewelcrafting", "Cut gems and set them in jewelry.", 1, 99),
    ("Inscription", "Mill herbs into inks, glyphs, and darkmoon cards.", 2, 99),
    ("Leatherworking", "Armor from hide and scale.", 0, 99),
    ("Mining", "Ore, stone, and bars.", 0, 99),
    ("Skinning", "Hides from the fallen.", 0, 99),
    ("Tailoring", "Cloth armor and bags.", 0, 99),
    ("Archaeology", "Dig up fragments of the peoples who came before.", 3, 8),
    ("Cooking", "Food that keeps a raid standing.", 0, 99),
    ("First Aid", "Bandages in the field.", 0, 6),
    ("Fishing", "Azeroth's most patient profession.", 0, 99),
]

PROFESSIONS = [(name, desc) for name, desc, _start, _end in _PROFESSION_ROWS if _start == 0]


def races_for(exp: Expansion) -> list[str]:
    return list(RACES_BY_ERA.get(exp.id, RACES_BY_ERA["vanilla"]))


def race_facts(exp: Expansion, slug: str) -> tuple[str, str, str, str]:
    name, faction, capital, blurb = RACE_INFO[slug]
    return name, faction, _CAPITALS.get((exp.id, slug), capital), blurb


def class_facts(exp: Expansion, slug: str) -> tuple[str, str, str, str]:
    name, armor, specs, blurb = CLASS_INFO[slug]
    if slug == "rogue" and exp.expansion_level >= 6:
        specs = "Assassination, Outlaw, Subtlety"
    if slug == "druid" and exp.expansion_level >= 4:
        specs = "Balance, Feral, Guardian, Restoration"
    return name, armor, specs, blurb


def professions_for(exp: Expansion) -> list[tuple[str, str]]:
    level = exp.expansion_level
    return [(name, desc) for name, desc, start, end in _PROFESSION_ROWS if start <= level <= end]


def classes_for(exp: Expansion) -> list[str]:
    names = ["warrior", "paladin", "hunter", "rogue", "priest", "shaman", "mage", "warlock", "druid"]
    if exp.expansion_level >= 2:
        names.append("deathknight")
    if exp.expansion_level >= 4:
        names.append("monk")
    if exp.expansion_level >= 6:
        names.append("demonhunter")
    if exp.expansion_level >= 9:
        names.append("evoker")
    return names

