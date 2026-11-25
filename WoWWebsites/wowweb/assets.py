"""Resolve client thumbnails extracted by scripts/extract_thumbs.py.

Files live in static/img/client/<expansion>/. A later client falls back to
the nearest earlier extract, so Warlords can show Mists icons when its
CASC root has no Interface paths.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path

from .catalog import Expansion

ROOT = Path(__file__).resolve().parents[1] / "static" / "img" / "client"

# Newest first. Lookup tries the requested expansion, then walks this list.
_CHAIN = (
    "midnight",
    "warwithin",
    "dragonflight",
    "shadowlands",
    "bfa",
    "legion",
    "wod",
    "mop",
    "cata-classic",
    "cata",
    "wotlk-classic",
    "wotlk",
    "tbc",
    "classic-era",
    "vanilla",
    "alpha",
)

_CLASS_STEMS = {
    "warrior": ("Ability_Warrior_DefensiveStance", "Ability_Warrior_Charge", "INV_Sword_27"),
    "paladin": ("Spell_Holy_HolyBolt", "Spell_Holy_AuraOfLight", "Ability_ThunderBolt"),
    "hunter": ("Ability_Hunter_AimedShot", "Ability_Marksmanship", "INV_Weapon_Bow_07"),
    "rogue": ("Ability_Rogue_Eviscerate", "Ability_BackStab", "Ability_Rogue_Ambush"),
    "priest": ("Spell_Holy_PowerWordShield", "Spell_Holy_Heal", "Spell_Holy_WordFortitude"),
    "shaman": ("Spell_Nature_Lightning", "Spell_Nature_LightningShield"),
    "mage": ("Spell_Fire_FlameBolt", "Spell_Frost_FrostBolt02", "Spell_Nature_StarFall"),
    "warlock": ("Spell_Shadow_ShadowBolt", "Spell_Shadow_CurseOfMannoroth", "Spell_Shadow_UnholyFrenzy"),
    "druid": ("Ability_Druid_Maul", "Spell_Nature_StarFall", "Spell_Nature_Regeneration"),
    "deathknight": ("Spell_Deathknight_ClassIcon", "Spell_Shadow_RaiseDead", "Spell_Shadow_AnimateDead"),
    "monk": ("ClassIcon_Monk", "Ability_Monk_LegacyOfTheEmperor", "Spell_Monk_Brewmaster_Spec"),
    "demonhunter": ("ClassIcon_DemonHunter", "Ability_DemonHunter_DualWield"),
    "evoker": ("ClassIcon_Evoker", "Ability_Evoker_MasteryGiantkiller"),
}

_RACE_STEMS = {
    "human": ("Achievement_Character_Human_Male", "INV_Misc_Head_Human_01"),
    "orc": ("Achievement_Character_Orc_Male", "INV_Misc_Head_Orc_01"),
    "dwarf": ("Achievement_Character_Dwarf_Male", "INV_Misc_Head_Dwarf_01"),
    "nightelf": ("Achievement_Character_Nightelf_Male", "INV_Misc_Head_Elf_01"),
    "undead": ("Achievement_Character_Undead_Male", "INV_Misc_Head_Undead_01"),
    "scourge": ("Achievement_Character_Undead_Male", "INV_Misc_Head_Undead_01"),
    "tauren": ("Achievement_Character_Tauren_Male", "INV_Misc_Head_Tauren_01"),
    "gnome": ("Achievement_Character_Gnome_Male", "INV_Misc_Head_Gnome_01"),
    "troll": ("Achievement_Character_Troll_Male", "INV_Misc_Head_Troll_01"),
    "bloodelf": ("Achievement_Character_Bloodelf_Male", "INV_Misc_Head_Bloodelf_01"),
    "draenei": ("Achievement_Character_Draenei_Male", "INV_Misc_Head_Draenei_01"),
    "worgen": ("Achievement_Character_Worgen_Male",),
    "goblin": ("Achievement_Character_Goblin_Male",),
    "pandaren": ("Achievement_Character_Pandaren_Female",),
    "highmountain": ("Achievement_Character_HighmountainTauren_Male", "Achievement_Character_Highmountain_Male"),
    "haranir": ("Achievement_Character_Haranir_Male", "Achievement_Character_Haranir_Female"),
    "nightborne": ("Achievement_Character_Nightborne_Male",),
    "voidelf": ("Achievement_Character_VoidElf_Male",),
    "lightforged": ("Achievement_Character_LightforgedDraenei_Male",),
    "zandalari": ("Achievement_Character_Zandalari_Male",),
    "kultiran": ("Achievement_Character_KulTiran_Male",),
    "darkiron": ("Achievement_Character_DarkIronDwarf_Male",),
    "vulpera": ("Achievement_Character_Vulpera_Male",),
    "maghar": ("Achievement_Character_MagharOrc_Male",),
    "mechagnome": ("Achievement_Character_Mechagnome_Male",),
    "dracthyr": ("Achievement_Character_Dracthyr_Male",),
    "earthen": ("Achievement_Character_Earthen_Male",),
}


def _order(exp_id: str) -> list[str]:
    """Requested client, then older extracts, then the next newer client.

    A vanilla page should not pick a Midnight redraw when 1.12 already has
    the file, and an alpha page with no loading screens should show vanilla.
    """
    if exp_id not in _CHAIN:
        return [exp_id] + list(reversed(_CHAIN))
    idx = _CHAIN.index(exp_id)
    older = list(_CHAIN[idx + 1 :])
    newer = list(reversed(_CHAIN[:idx]))
    return [exp_id] + older + newer


def _era_folders(exp_id: str) -> list[str]:
    if exp_id not in _CHAIN:
        return [exp_id]
    idx = _CHAIN.index(exp_id)
    return [exp_id] + list(_CHAIN[idx + 1 :])


@lru_cache(maxsize=32)
def _icon_index(folder: str) -> dict[str, str]:
    """Map a case-folded stem to the PNG filename. Clients disagree on case."""
    directory = ROOT / folder / "icons"
    if not directory.is_dir():
        return {}
    found: dict[str, str] = {}
    for path in directory.glob("*.png"):
        found.setdefault(path.stem.casefold(), path.name)
    return found


def _icon_in(folders: list[str], stem: str) -> str | None:
    key = stem.casefold()
    for folder in folders:
        name = _icon_index(folder).get(key)
        if name:
            return f"/static/img/client/{folder}/icons/{name}"
    return None


def icon_src(exp_id: str, stem: str | None) -> str | None:
    if not stem:
        return None
    return _icon_in(_order(exp_id), stem)


def _first_stem(exp_id: str, stems: tuple[str, ...]) -> str | None:
    era = _era_folders(exp_id)
    for stem in stems:
        hit = _icon_in(era, stem)
        if hit:
            return hit
    for stem in stems:
        hit = icon_src(exp_id, stem)
        if hit:
            return hit
    return None


def class_icon(exp_id: str, slug: str) -> str | None:
    return _first_stem(exp_id, _CLASS_STEMS.get(slug.lower().replace(" ", "").replace("-", ""), ()))


def race_icon(exp_id: str, slug: str) -> str | None:
    key = slug.lower().replace(" ", "").replace("-", "").replace("'", "")
    return _first_stem(exp_id, _RACE_STEMS.get(key, ()))


@lru_cache(maxsize=32)
def _spell_rank(stem: str, count: int) -> tuple[int, int]:
    bad = stem in {"Temp", "INV_Misc_QuestionMark"} or stem.startswith(("Trade_", "INV_Inscription"))
    return (0 if bad else 1, count)


def _spells(exp_id: str) -> dict[str, str]:
    counts: dict[str, Counter[str]] = {}
    for folder in _order(exp_id):
        path = ROOT / folder / "spell-names.tsv"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "\t" not in line or line.startswith("name\t"):
                continue
            name, stem = line.split("\t", 1)
            counts.setdefault(name.casefold(), Counter())[stem.strip()] += 1
        if counts:
            break
    table: dict[str, str] = {}
    for name, counter in counts.items():
        stem = max(counter.items(), key=lambda item: _spell_rank(item[0], item[1]))[0]
        table[name] = stem
    return table


@lru_cache(maxsize=32)
def _displays(exp_id: str) -> dict[int, str]:
    table: dict[int, str] = {}
    for folder in _order(exp_id):
        path = ROOT / folder / "displays.tsv"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "\t" not in line or line.startswith("display\t"):
                continue
            raw_id, stem = line.split("\t", 1)
            try:
                table.setdefault(int(raw_id), stem.strip())
            except ValueError:
                continue
        if table:
            break
    return table


# Abbreviated trees for classes added after the last Spell.dbc we can read.
# Stems are the client filenames players saw on those buttons.
_TALENT_STEMS = {
    "elusive brew": "ability_monk_elusiveale",
    "guard": "ability_monk_guard",
    "keg smash": "spell_monk_brewmaster_spec",
    "soothing mist": "ability_monk_soothingmists",
    "renewing mist": "ability_monk_renewingmists",
    "thunder focus tea": "ability_monk_thunderfocustea",
    "combo breaker": "ability_monk_palmstrike",
    "fists of fury": "monk_ability_fistoffury",
    "energizing brew": "ability_monk_energizingwine",
    "fel mastery": "ability_demonhunter_felmastery",
    "demon blades": "ability_demonhunter_demonblades",
    "metamorphosis": "Ability_DemonHunter_MetamorphasisDPS",
    "felblade": "ability_demonhunter_felblade",
    "soul cleave": "ability_demonhunter_soulcleave",
    "demonic infusion": "ability_demonhunter_demonicinfusion",
    "pyre": "ability_evoker_pyre",
    "dragonrage": "ability_evoker_dragonrage",
    "echo": "ability_evoker_echo",
    "rewind": "ability_evoker_rewind",
    "ebon might": "ability_evoker_ebonmight",
    "breath of eons": "ability_evoker_breathofeons",
}


def talent_icon(exp: Expansion | str, talent_name: str) -> str | None:
    exp_id = exp if isinstance(exp, str) else exp.id
    table = _spells(exp_id)
    key = talent_name.casefold()
    # These names belong to a later class tree. A classic spell of the same
    # name would paint the wrong button, so the client stem wins.
    if key in _TALENT_STEMS:
        return icon_src(exp_id, _TALENT_STEMS[key])
    stem = table.get(key)
    if stem is None and key.startswith("improved "):
        stem = table.get(key[len("improved ") :])
    return icon_src(exp_id, stem)


def display_icon(exp: Expansion | str, display_id: int | str | None) -> str | None:
    exp_id = exp if isinstance(exp, str) else exp.id
    try:
        key = int(display_id or 0)
    except (TypeError, ValueError):
        return None
    if key <= 0:
        return None
    return icon_src(exp_id, _displays(exp_id).get(key))


def _screen_caption(stem: str) -> str:
    text = stem
    if text.lower().startswith("loadscreen"):
        text = text[len("loadscreen") :]
    text = text.replace("_", " ").strip()
    spaced: list[str] = []
    for i, ch in enumerate(text):
        prev = text[i - 1] if i else ""
        if i and ((ch.isupper() and prev.islower()) or (ch.isdigit() and prev.isalpha()) or (ch.isalpha() and prev.isdigit())):
            spaced.append(" ")
        spaced.append(ch)
    return "".join(spaced).strip() or stem


def screenshots(exp_id: str, limit: int = 24) -> list[tuple[str, str]]:
    """Return (url, caption) for loading-screen thumbnails."""
    found: list[tuple[str, str]] = []
    for folder in _order(exp_id):
        directory = ROOT / folder / "screens"
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.png")):
            caption = _screen_caption(path.stem)
            found.append((f"/static/img/client/{folder}/screens/{path.name}", caption))
            if len(found) >= limit:
                return found
        if found:
            return found
    return found
