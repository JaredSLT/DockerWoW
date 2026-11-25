"""Armory page bodies."""

from __future__ import annotations

from ..armory.constants import slots_for_expansion
from ..assets import display_icon
from ..catalog import Expansion
from .layout import e

# In-game paperdoll columns. Ranged is only present through Mists.
_LEFT = ("Head", "Neck", "Shoulders", "Back", "Chest", "Shirt", "Tabard", "Wrists")
_RIGHT = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEAPONS = ("Main Hand", "Off Hand", "Ranged")


def _item_icon(exp: Expansion, display_id) -> str:
    src = display_icon(exp, display_id)
    if not src:
        return ""
    return f'<img class="item-icon" src="{e(src)}" alt="">'


def armory_home(
    exp: Expansion,
    results: list[dict],
    q: str,
    coming: bool,
    store_error: str = "",
) -> str:
    if coming:
        return """
<h2>The Armory</h2>
<p>The World of Warcraft Armory opens during The Burning Crusade. Character sheets,
guilds, and arena ladders will live here once this realm reaches Outland.</p>
<p>Until then, use <a href="/wow/pvp/rankings">PvP Rankings</a> and the
<a href="/wow/realmstatus/">Realm Status</a> page.</p>
"""
    cells = []
    for r in results:
        icon = _item_icon(exp, r.get("display_id")) if "display_id" in r else ""
        cells.append(
            f"<tr><td>{icon}<a href='/armory/character/{e(r['name'])}'>{e(r['name'])}</a></td>"
            f"<td>{e(r['level'])}</td><td>{e(r['race'])}</td><td>{e(r['class'])}</td></tr>"
        )
    if store_error:
        empty = f"<tr><td colspan='4'>{e(store_error)}</td></tr>"
    elif not q:
        empty = ""
    else:
        empty = "<tr><td colspan='4'>No characters found. Log into the game on this realm, then search again.</td></tr>"
    rows = "".join(cells) or empty
    table = ""
    if q or store_error:
        table = f"<table class='grid'><tr><th>Name</th><th>Level</th><th>Race</th><th>Class</th></tr>{rows}</table>"
    return f"""
<h2>The Armory</h2>
<p>Search characters on <strong>{e(exp.realm_name)}</strong>. Data is read from the last logout on the realm database.</p>
<form class="acct" method="get" action="/armory/">
  <label>Character name <input name="q" value="{e(q)}"></label>
  <button type="submit">Search</button>
</form>
{table}
<p><a href="/armory/arena">Arena Ladders</a>
{" · <a href='/armory/auctions'>Auction House</a>" if exp.has_auction else ""}</p>
"""


def _era_class(level: int) -> str:
    # TBC and Wrath used the old Armory. Cataclysm through Warlords used the
    # Battle.net profile. Legion and later use a flat accent panel.
    if 1 <= level <= 2:
        return "armory-classic"
    if 3 <= level <= 5:
        return "armory-profile"
    if level >= 6:
        return "armory-later"
    return ""


def _extra_text(value) -> list[str]:
    if value is None or isinstance(value, bool):
        return []
    if isinstance(value, str):
        text = value.strip()
        return [e(text)] if text else []
    if isinstance(value, (int, float)):
        if value == 0:
            return []
        return [e(value)]
    if isinstance(value, dict):
        for key in ("name", "text", "description"):
            if value.get(key):
                return _extra_text(value[key])
        return []
    if isinstance(value, (list, tuple)):
        lines: list[str] = []
        for part in value:
            lines.extend(_extra_text(part))
        return lines
    text = str(value).strip()
    return [e(text)] if text else []


def _field_lines(item: dict, key: str, css: str) -> str:
    if key not in item:
        return ""
    return "".join(f'<span class="{css}">{line}</span>' for line in _extra_text(item.get(key)))


def _doll_slot(exp: Expansion, slot: str, item: dict | None) -> str:
    label = f'<span class="doll-label">{e(slot)}</span>'
    if not item or not item.get("item_id"):
        return (
            f'<div class="doll-slot">'
            f'<span class="doll-socket"></span>'
            f"{label}"
            f"</div>"
        )
    icon = _item_icon(exp, item.get("display_id"))
    name = e(item.get("name") or f"Item #{item['item_id']}")
    extras = _field_lines(item, "enchant", "doll-enchant") + _field_lines(item, "gem", "doll-gem")
    return (
        f'<div class="doll-slot">'
        f'<a href="/armory/item/{e(item["item_id"])}">'
        f"{icon}<span class=\"doll-text\">{label}"
        f'<span class="doll-item">{name}</span>{extras}</span></a></div>'
    )


def _doll_column(exp: Expansion, names: tuple[str, ...], equipped: dict[str, dict]) -> str:
    return "".join(_doll_slot(exp, name, equipped.get(name)) for name in names)


def character_sheet(exp: Expansion, char: dict) -> str:
    known = set(slots_for_expansion(exp.expansion_level))
    equipped: dict[str, dict] = {}
    extras: list[dict] = []
    for item in char.get("equipment") or []:
        slot = str(item.get("slot") or "")
        if slot in known:
            equipped[slot] = item
        elif item.get("item_id"):
            extras.append(item)
    weapons = _doll_column(exp, tuple(name for name in _WEAPONS if name in known), equipped)
    weapons += "".join(
        _doll_slot(exp, str(item.get("slot") or "Slot"), item) for item in extras
    )
    guild = "<p>No guild</p>"
    if char.get("guild"):
        guild = (
            f"<p>Guild: <a href='/armory/guild/{e(char['guild']['name'])}'>"
            f"{e(char['guild']['name'])}</a></p>"
        )
    online = "Online" if char.get("online") else "Offline"
    money = e(char.get("money_text", ""))
    era = _era_class(exp.expansion_level)
    sheet_class = "sheet" if not era else f"sheet {era}"
    return f"""
<div class="{sheet_class}">
  <div class="paperdoll">
    <div class="doll">
      <div class="doll-left">{_doll_column(exp, _LEFT, equipped)}</div>
      <div class="doll-main">
        <h2>{e(char['name'])}</h2>
        <p>Level {e(char['level'])} {e(char['race'])} {e(char['class'])}</p>
        <p>{online}</p>
        <p>{money}</p>
        <p>{e(char.get('realm', ''))}</p>
        {guild}
        <p>Achievements: {e(char.get('achievements', 0))}</p>
      </div>
      <div class="doll-right">{_doll_column(exp, _RIGHT, equipped)}</div>
      <div class="doll-weapons">{weapons}</div>
    </div>
  </div>
</div>
"""


def item_page(exp: Expansion, item: dict) -> str:
    icon = _item_icon(exp, item.get("display_id"))
    return f"""
<div class="item-page">
  <h2>{icon}{e(item.get("name"))}</h2>
  <p>Item level {e(item.get("ItemLevel", ""))}</p>
  <p>Required level {e(item.get("RequiredLevel", ""))}</p>
  <p>Quality {e(item.get("quality", ""))}</p>
  <p>Item #{e(item.get("entry", ""))}</p>
</div>
"""


def guild_page(g: dict) -> str:
    rows = "".join(
        f"<tr><td><a href='/armory/character/{e(m['name'])}'>{e(m['name'])}</a></td>"
        f"<td>{e(m['level'])}</td><td>{e(m['class'])}</td></tr>"
        for m in g.get("members") or []
    ) or "<tr><td colspan='3'>Empty roster.</td></tr>"
    return f"<h2>&lt;{e(g['name'])}&gt;</h2><p>{e(g['realm'])}</p><table class='grid'><tr><th>Name</th><th>Level</th><th>Class</th></tr>{rows}</table>"

