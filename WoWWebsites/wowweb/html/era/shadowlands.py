"""Shadowlands community site, 2021 through mid-2022, before Dragonflight went live."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from wowweb import armory, assets, content, forums, lab, talents

from .common import dev_note, document, esc, styles

_SCREENS = "/static/img/client/shadowlands/screens"
_ICONS = "/static/img/client/shadowlands/icons"
_HERO_DF = "/static/img/hero-dragonflight.jpg"
_HERO_SL = "/static/img/hero-shadowlands.jpg"

_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

_HUMAN_CLASSES = (
    "warrior", "paladin", "hunter", "rogue", "priest",
    "mage", "warlock", "monk", "deathknight",
)
_HUMAN_TRAITS = (
    ("Will to Survive", "Break free from stun effects."),
    ("The Human Spirit", "Secondary stats from all sources are increased."),
    ("Diplomacy", "Reputation gains are increased."),
)
_HUMAN_INTRO = (
    "The human kingdom of Stormwind forms the backbone of the Alliance. "
    "Stormwind's willingness to work with others to find diplomatic solutions "
    "stands out as one of its true strengths. Its citizens hold fast to the "
    "principles of honor and justice as they defend their settlements, and the "
    "Alliance, against any aggressors."
)
_HUMAN_CARDS = (
    (
        "Home City: Stormwind",
        f"{_SCREENS}/LoadScreenEasternKingdom.png",
        "No city better demonstrates the courageous heart of humanity than Stormwind. "
        "Busy districts embrace the diversity of the Alliance and vast monuments honor "
        "the sacrifices from heroes past and present, inspiring citizens all over the Eastern Kingdoms.",
    ),
    (
        "Racial Mount: Horse",
        f"{_ICONS}/Ability_Mount_RidingHorse.png",
        "These trusty steeds have carried their human masters to battle since before the First War. "
        "Known for their swiftness and spirited temperaments, these mounts are perfectly suited for their heroic riders.",
    ),
    (
        "Leader: King Anduin Wrynn",
        f"{_ICONS}/Achievement_Character_Human_Male.png",
        "All his young life, Anduin Wrynn sought to use diplomacy and tact to avoid conflict. "
        "However, as he strived to end the bloodshed his allies faced in the Fourth War, "
        "Anduin learned the heavy price that freedom and peace exact.",
    ),
)

_CLASS_FORUMS = (
    "deathknight", "demonhunter", "druid", "hunter", "mage", "monk",
    "paladin", "priest", "rogue", "shaman", "warlock", "warrior",
)
_LEFT_SLOTS = ("Head", "Neck", "Shoulders", "Back", "Chest", "Shirt", "Tabard", "Wrists")
_RIGHT_SLOTS = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEAPON_SLOTS = ("Main Hand", "Off Hand")

_PROFILE_TABS = (
    ("character", "Character"),
    ("achievements", "Achievements"),
    ("collections", "Collections"),
    ("dungeons", "Dungeons & Raids"),
    ("pvp", "Player vs Player"),
    ("reputation", "Reputation"),
)


def _long_date(iso: str) -> str:
    parts = (iso or "").split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = (int(part) for part in parts)
        if 1 <= month <= 12:
            return f"{_MONTHS[month - 1]} {day}, {year}"
    return iso


def _ago(stamp) -> str:
    try:
        then = int(stamp or 0)
    except (TypeError, ValueError):
        return ""
    if then <= 0:
        return ""
    delta = max(0, int(time.time()) - then)
    if delta < 60:
        return f"{delta}s"
    if delta < 3600:
        return f"{delta // 60}m"
    if delta < 86400:
        return f"{delta // 3600}h"
    return f"{delta // 86400}d"


def _stamp(stamp) -> str:
    try:
        when = datetime.fromtimestamp(int(stamp), timezone.utc)
    except (TypeError, ValueError, OSError):
        return ""
    return when.strftime("%Y-%m-%d %H:%M")


def _icon(src: str | None, alt: str = "") -> str:
    if not src:
        return ""
    return f'<img src="{esc(src)}" alt="{esc(alt)}">'


def _guide(inner: str) -> str:
    return f'<div class="sl-guide" data-bar="2021">{inner}</div>'


def _service(user: str | None) -> str:
    who = esc(user) if user else "My Account"
    return f"""<div class="sl-service">
  <a class="sl-blizz" href="/wow/">Blizzard</a>
  <nav class="sl-service-links" aria-label="Battle.net">
    <a href="/wow/">Games</a>
    <a href="/shop">Shop</a>
    <a href="/wow/news">News</a>
    <a href="/esports">Esports</a>
  </nav>
  <nav class="sl-service-right" aria-label="Account and support">
    <a href="/support/">Support</a>
    <a href="/account/">{who}</a>
  </nav>
</div>"""


def _wowbar(user: str | None, bar: str) -> str:
    if bar == "2021":
        if user:
            tail = f'<a class="sl-login" href="/account/">{esc(user)}</a>'
        else:
            tail = '<a class="sl-login" href="/account/login">Log In</a>'
        tail += '<a class="sl-sub" href="/shop">Subscribe</a><a class="sl-try" href="/trial">Try Free</a>'
    else:
        tail = '<a class="sl-sub" href="/shop">Subscribe</a>'
        if user:
            tail += f'<a class="sl-chip" href="/account/"><span>{esc(user)}</span></a>'
    return f"""<header class="sl-wowbar">
  <a class="sl-logo" href="/wow/"><span>World of</span><strong>Warcraft</strong></a>
  <nav class="sl-nav" aria-label="World of Warcraft">
    <div class="sl-drop">
      <a href="/wow/info">Game</a>
      <div class="sl-menu">
        <a href="/wow/info">Game Guide</a>
        <a href="/wow/info/races">Races</a>
        <a href="/wow/info/classes">Classes</a>
        <a href="/wow/info/professions">Professions</a>
        <a href="/wow/realmstatus">Realm Status</a>
      </div>
    </div>
    <a href="/wow/news">News</a>
    <a href="/forums">Forums</a>
    <a href="/shop">Shop</a>
    <div class="sl-drop">
      <a href="/esports">Esports</a>
      <div class="sl-menu">
        <a href="/esports">Arena World Championship</a>
        <a href="/esports">Mythic Dungeon International</a>
      </div>
    </div>
    <span class="sl-classic-wrap"><a href="/classic">WoW Classic</a><em class="sl-new">New</em></span>
  </nav>
  <a class="sl-search" href="/wow/search">Search</a>
  <div class="sl-actions">{tail}</div>
</header>"""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = crumb, online, login_error
    if "acct-shadowlands" in (body or ""):
        kind = "sl-account-manage" if "acct-manage" in body else "sl-account-gate"
        inner = f'<div class="sl-acct-root">{body}</div>'
        body_class = f"era-shadowlands sl-account {kind}"
    else:
        bar = "2021" if 'data-bar="2021"' in (body or "") else "2022"
        inner = (
            f'<div class="sl-site">{_service(user)}{_wowbar(user, bar)}'
            f'<div class="sl-stage">{body}</div></div>'
        )
        body_class = "era-shadowlands"
    return document(
        f"{title} — World of Warcraft",
        styles("shadowlands"),
        body_class,
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    _ = exp, realm, user
    cards = []
    explore = "/wow/news"
    for i, (title, _date, _body) in enumerate(news or []):
        thumb = (
            _HERO_DF,
            f"{_SCREENS}/LoadScreenEasternKingdom.png",
            f"{_SCREENS}/loadscreenicecrowncitadel.png",
            f"{_SCREENS}/LoadScreenOutland.png",
        )[i % 4]
        if "waking shores" in title.lower() or "dragonflight" in title.lower():
            explore = f"/wow/news/{i}"
        cards.append(
            f'<a class="sl-card" href="/wow/news/{i}">'
            f'<img src="{thumb}" alt="">'
            f'<span>{esc(title)}</span></a>'
        )
    strip = ""
    if cards:
        strip = (
            '<section class="sl-latest">'
            "<header><h2>Latest News and Updates</h2>"
            '<a href="/wow/news">View all news</a></header>'
            f'<div class="sl-cards">{"".join(cards)}</div></section>'
        )
    return f"""<div class="sl-home">
  <section class="sl-hero">
    <div class="sl-hero-copy">
      <h1>Pre-Purchase Dragonflight</h1>
      <p>The dragonflights of Azeroth will soon return, called to defend their ancestral home, the Dragon Isles. Master the power of dragonriding in 2022 and get the Drakks pet, along with a host of items included in your Dragonflight Epic Edition pre-purchase.</p>
      <p><a class="sl-textlink" href="/wow/media/screenshots">Cinematic Trailer</a></p>
      <p class="sl-hero-actions">
        <a class="sl-btn sl-btn-fill" href="/shop">Pre-Purchase Now</a>
        <a class="sl-btn sl-btn-line" href="{esc(explore)}">Explore Dragonflight</a>
      </p>
    </div>
  </section>
  {strip}
</div>"""


def _news_index(exp) -> str:
    rows = []
    for i, (title, date, body) in enumerate(content.news_for(exp)):
        rows.append(
            "<li>"
            f'<a href="/wow/news/{i}">{esc(title)}</a>'
            f'<span class="sl-when">{esc(_long_date(date))}</span>'
            f"<p>{esc(body)}</p></li>"
        )
    inner = "".join(rows) or "<li>No stories yet.</li>"
    return f'<section class="sl-news-index"><h1>News</h1><ul class="sl-news-list">{inner}</ul></section>'


def _article(title: str, date: str, body: str, index: int) -> str:
    shots = (
        _HERO_SL,
        _HERO_DF,
        f"{_SCREENS}/LoadScreenBlackTemple.png",
        f"{_SCREENS}/LoadScreenOutland.png",
    )
    return f"""<article class="sl-article" data-bar="2021">
  <div class="sl-article-hero" style="background-image:url('{shots[index % len(shots)]}')"></div>
  <div class="sl-article-copy">
    <h1>{esc(title)}</h1>
    <p class="sl-byline">{esc(_long_date(date))} by Blizzard Entertainment</p>
    <div class="sl-article-body"><p>{esc(body)}</p></div>
  </div>
</article>"""


def _guide_hub(exp) -> str:
    races = []
    for slug in content.races_for(exp):
        name = content.RACE_INFO[slug][0]
        races.append(
            f'<a class="sl-tile" href="/wow/info/races/{esc(slug)}">'
            f'{_icon(assets.race_icon(exp.id, slug), name)}<span>{esc(name)}</span></a>'
        )
    classes = []
    for slug in content.classes_for(exp):
        name = content.CLASS_INFO[slug][0]
        classes.append(
            f'<a class="sl-tile" href="/wow/info/classes/{esc(slug)}">'
            f'{_icon(assets.class_icon(exp.id, slug), name)}<span>{esc(name)}</span></a>'
        )
    feats = "".join(f"<li>{esc(item)}</li>" for item in content.features_for(exp))
    return _guide(
        "<h1>Game Guide</h1>"
        f"<p>{esc(content.intro_blurb(exp))}</p>"
        '<h2>Races</h2><div class="sl-tiles">' + "".join(races) + "</div>"
        '<h2>Classes</h2><div class="sl-tiles">' + "".join(classes) + "</div>"
        f"<h2>Features</h2><ul>{feats}</ul>"
        '<p><a href="/wow/info/basics">New Players</a> · '
        '<a href="/wow/info/basics/map">World Map</a> · '
        '<a href="/wow/realmstatus">Realm Status</a></p>'
    )


def _race_index(exp) -> str:
    tiles = []
    for slug in content.races_for(exp):
        name, faction, _city, _blurb = content.race_facts(exp, slug)
        tiles.append(
            f'<a class="sl-tile" href="/wow/info/races/{esc(slug)}">'
            f'{_icon(assets.race_icon(exp.id, slug), name)}'
            f"<span>{esc(name)}</span><small>{esc(faction)}</small></a>"
        )
    return _guide('<h1>Races</h1><div class="sl-tiles">' + "".join(tiles) + "</div>")


def _human(exp) -> str:
    classes = []
    for slug in _HUMAN_CLASSES:
        if slug not in content.CLASS_INFO:
            continue
        name = content.CLASS_INFO[slug][0]
        classes.append(
            f'<a href="/wow/info/classes/{esc(slug)}" title="{esc(name)}">'
            f'{_icon(assets.class_icon(exp.id, slug), name)}<span>{esc(name)}</span></a>'
        )
    traits = []
    for name, desc in _HUMAN_TRAITS:
        traits.append(f'<li title="{esc(desc)}"><span>{esc(name)}</span><small>{esc(desc)}</small></li>')
    cards = []
    for heading, src, text in _HUMAN_CARDS:
        cards.append(
            "<article>"
            f'<img src="{esc(src)}" alt="">'
            f"<h3>{esc(heading)}</h3><p>{esc(text)}</p></article>"
        )
    return _guide(
        f"""<div class="sl-human">
  <div class="sl-human-hero">
    {_icon(f"{_ICONS}/Achievement_Character_Human_Male.png", "Human")}
    {_icon(f"{_ICONS}/inv_misc_tournaments_symbol_human.png", "")}
    {_icon(f"{_ICONS}/Achievement_Character_Human_Female.png", "Human")}
    <h1>Human</h1>
  </div>
  <p class="sl-human-lead">{esc(_HUMAN_INTRO)}</p>
  <div class="sl-human-cols">
    <section><h2>Available Classes</h2><div class="sl-class-row">{"".join(classes)}</div></section>
    <section><h2>Racial Traits</h2><ul class="sl-traits">{"".join(traits)}</ul></section>
  </div>
  <div class="sl-human-cards">{"".join(cards)}</div>
</div>"""
    )


def _race(exp, slug: str) -> str:
    if slug == "human":
        return _human(exp)
    name, faction, city, blurb = content.race_facts(exp, slug)
    return _guide(
        f'<div class="sl-race">{_icon(assets.race_icon(exp.id, slug), name)}'
        f"<h1>{esc(name)}</h1>"
        f'<p class="sl-kicker">{esc(faction)} · Home City: {esc(city)}</p>'
        f"<p>{esc(blurb)}</p>"
        f'<p><a href="/wow/info/races">All races</a></p></div>'
    )


def _class_index(exp) -> str:
    tiles = []
    for slug in content.classes_for(exp):
        name, _armor, specs, _blurb = content.class_facts(exp, slug)
        tiles.append(
            f'<a class="sl-tile" href="/wow/info/classes/{esc(slug)}">'
            f'{_icon(assets.class_icon(exp.id, slug), name)}'
            f"<span>{esc(name)}</span><small>{esc(specs)}</small></a>"
        )
    return _guide('<h1>Classes</h1><div class="sl-tiles">' + "".join(tiles) + "</div>")


def _class_page(exp, slug: str) -> str:
    name, armor, specs, blurb = content.class_facts(exp, slug)
    return _guide(
        f'<div class="sl-class">{_icon(assets.class_icon(exp.id, slug), name)}'
        f"<h1>{esc(name)}</h1>"
        f'<p class="sl-kicker">{esc(armor)} · {esc(specs)}</p>'
        f"<p>{esc(blurb)}</p>"
        f'<p><a href="/wow/info/classes/{esc(slug)}/talents.html">Talent Calculator</a></p></div>'
    )


def _talent_page(exp, slug: str, build: str) -> str | None:
    trees = talents.trees_for(exp, slug)
    if not trees:
        return None
    ranks = talents.parse_build(trees, build or "")
    points = talents.points_available(exp)
    name = content.CLASS_INFO[slug][0]
    idx = 0
    cols = []
    for tree_i, tree in enumerate(trees):
        base = idx
        by_name = {}
        for offset, tal in enumerate(tree.talents):
            by_name.setdefault(tal.name, base + offset)
        cells = []
        for tal in tree.talents:
            rank = ranks[idx] if idx < len(ranks) else 0
            rank = min(rank, tal.max_rank)
            req = by_name.get(tal.requires, "") if tal.requires else ""
            icon = assets.talent_icon(exp, tal.name)
            img = _icon(icon, "")
            cells.append(
                f'<button type="button" class="talent" data-i="{idx}" data-max="{tal.max_rank}" '
                f'data-tree="{tree_i}" data-row="{tal.row}" data-requires="{esc(req)}" '
                f'title="{esc(tal.name)} ({rank}/{tal.max_rank}) {esc(tal.desc)}" '
                f'style="grid-column:{tal.col + 1};grid-row:{tal.row + 1}">'
                f'{img}<span class="tname">{esc(tal.name)}</span>'
                f'<span class="trank" data-rank>{rank}/{tal.max_rank}</span></button>'
            )
            idx += 1
        cols.append(
            f'<div class="tree"><h3>{esc(tree.name)}</h3>'
            f'<div class="talent-grid">{"".join(cells)}</div></div>'
        )
    encoded = talents.encode_build(ranks)
    return _guide(
        f"<h1>{esc(name)} Talents</h1>"
        f'<p>Available points: <strong id="pts">{points}</strong> · Build '
        f'<code id="build">{esc(encoded)}</code></p>'
        f'<div class="trees">{"".join(cols)}</div>'
        f'<p><a href="/wow/info/classes/{esc(slug)}">{esc(name)}</a></p>'
        "<script>document.addEventListener('DOMContentLoaded',function(){"
        f"if(window.initTalents)initTalents({int(points)});}});</script>"
    )


def _profession_slug(name: str) -> str:
    return name.lower().replace(" ", "")


def _professions(exp) -> str:
    items = []
    for name, _desc in content.professions_for(exp):
        slug = _profession_slug(name)
        items.append(f'<li><a href="/wow/info/professions/{esc(slug)}">{esc(name)}</a></li>')
    return _guide(f"<h1>Professions</h1><ul>{''.join(items)}</ul>")


def _profession(exp, slug: str) -> str | None:
    want = _profession_slug(slug)
    for name, desc in content.professions_for(exp):
        if _profession_slug(name) == want:
            return _guide(f"<h1>{esc(name)}</h1><p>{esc(desc)}</p>")
    return None


def _basics() -> str:
    return _guide(
        "<h1>New Players</h1>"
        "<p>Choose a race, a class, and a realm. Quest, group, and find a profession. "
        "The world map and the class pages are the two places to start.</p>"
        "<ul>"
        '<li><a href="/account/create">Create an account</a></li>'
        '<li><a href="/wow/info/races">Read the race pages</a></li>'
        '<li><a href="/wow/info/classes">Pick a class</a></li>'
        '<li><a href="/wow/realmstatus">Check realm status</a></li>'
        '<li><a href="/trial">Play free up to level 20</a></li>'
        "</ul>"
    )


def _map(exp) -> str:
    level = getattr(exp, "expansion_level", 8)
    names = content_continents(level)
    items = "".join(f"<li>{esc(name)}</li>" for name in names)
    return _guide(f"<h1>World Map</h1><p>Continents in {esc(exp.name)}.</p><ul>{items}</ul>")


def content_continents(level: int) -> list[str]:
    from wowweb.content.zones import continents_for

    return continents_for(level)


def _patches(exp) -> str:
    note = content.PATCH_NOTES.get(exp.id, "")
    return _guide(
        "<h1>Previous Patches</h1>"
        f"<p>{esc(note)}</p><p>Last patch: <strong>{esc(exp.last_patch)}</strong></p>"
    )


def _take_info(path: str, ctx: dict):
    exp = ctx["exp"]
    rest = path[len("/wow/info"):].strip("/")
    qs = ctx.get("qs") or {}
    if rest in ("", "introduction"):
        return ("Game Guide", _guide_hub(exp))
    if rest == "features":
        items = "".join(f"<li>{esc(item)}</li>" for item in content.features_for(exp))
        return ("Features", _guide(f"<h1>Features</h1><ul>{items}</ul>"))
    if rest == "races":
        return ("Races", _race_index(exp))
    if rest.startswith("races/"):
        slug = rest.split("/", 1)[1]
        if "/" in slug or slug not in content.RACE_INFO:
            return None
        if slug not in content.races_for(exp):
            return ("Races", _guide("<h1>Races</h1><p>That race is not part of this era.</p>"))
        return (content.race_facts(exp, slug)[0], _race(exp, slug))
    if rest == "classes":
        return ("Classes", _class_index(exp))
    if rest.startswith("classes/"):
        tail = rest[len("classes/"):]
        parts = [part for part in tail.split("/") if part]
        if not parts:
            return ("Classes", _class_index(exp))
        slug = parts[0]
        if slug not in content.CLASS_INFO:
            return None
        if slug not in content.classes_for(exp):
            return ("Classes", _guide("<h1>Classes</h1><p>That class is not part of this era.</p>"))
        if len(parts) == 1:
            return (content.CLASS_INFO[slug][0], _class_page(exp, slug))
        if len(parts) == 2 and parts[1] == "talents.html":
            build = (qs.get("build") or [""])[0]
            body = _talent_page(exp, slug, build)
            if body is None:
                return None
            return (f"{content.CLASS_INFO[slug][0]} Talents", body)
        return None
    if rest == "professions":
        return ("Professions", _professions(exp))
    if rest.startswith("professions/"):
        body = _profession(exp, rest.split("/", 1)[1])
        if body is None:
            return None
        return ("Professions", body)
    if rest in ("basics", "beginners"):
        return ("New Players", _basics())
    if rest == "basics/map":
        return ("World Map", _map(exp))
    if rest == "patches":
        return ("Previous Patches", _patches(exp))
    if rest == "awards":
        return ("Awards", _guide("<h1>Awards</h1><p>World of Warcraft collected a wall of industry awards through this era.</p>"))
    return None


def _realm_page(ctx: dict) -> str:
    exp = ctx["exp"]
    qs = ctx.get("qs") or {}
    game = ((qs.get("game") or ["retail"])[0] or "retail").lower()
    if game not in ("retail", "classic", "tbc"):
        game = "retail"
    query = ((qs.get("q") or [""])[0] or "").strip()
    cfg = ctx.get("labcfg")
    if cfg is None:
        realm = {"name": exp.realm_name, "up": False, "population": "", "type": "", "timezone": "PST"}
    else:
        realm = lab.realm_status(cfg, exp)
        realm = {key: value for key, value in realm.items() if key != "error"}
    tabs = (
        ("retail", "World of Warcraft", "/wow/realmstatus"),
        ("classic", "World of Warcraft Classic", "/wow/realmstatus?game=classic"),
        ("tbc", "Burning Crusade Classic", "/wow/realmstatus?game=tbc"),
    )
    tab_html = []
    for key, label, href in tabs:
        mark = " sl-tab-on" if key == game else ""
        tab_html.append(f'<a class="sl-tab{mark}" href="{esc(href)}">{esc(label)}</a>')
    row = ""
    if game == "retail":
        name = str(realm.get("name") or exp.realm_name)
        if not query or query.lower() in name.lower():
            flag = "sl-up" if realm.get("up") else "sl-down"
            label = "Up" if realm.get("up") else "Down"
            pop = realm.get("population")
            pop_text = "—" if pop in (None, "") else str(pop)
            kind = realm.get("type") or "—"
            zone = realm.get("timezone") or "—"
            row = (
                "<tr>"
                f'<td><span class="sl-status {flag}">{label}</span></td>'
                f"<td>{esc(name)}</td>"
                f"<td>{esc(kind)}</td>"
                f"<td>{esc(pop_text)}</td>"
                f"<td>{esc(zone)}</td>"
                "<td>—</td>"
                "</tr>"
            )
    if not row:
        row = '<tr class="sl-empty"><td colspan="6">No realms in this view.</td></tr>'
    return f"""<section class="sl-realms" data-bar="2021">
  <h1>Realm Status</h1>
  <p class="sl-realm-lead">This page lists all available World of Warcraft realms and has information on whether or not a realm is up or down. You can find more information about realm status and scheduled maintenances in the <a href="/forums/realm">Service Status Forum</a>. If your realm is listed as down, rest assured that we're aware of it and working diligently to bring it back online as quickly as possible.</p>
  <div class="sl-realm-bar">
    <nav class="sl-tabs" aria-label="Games">{"".join(tab_html)}</nav>
    <form class="sl-filters" method="get" action="/wow/realmstatus">
      <input type="hidden" name="game" value="{esc(game)}">
      <label>Region <select name="region"><option>Americas &amp; Oceania</option><option>Europe</option><option>Korea</option><option>Taiwan</option></select></label>
      <label>Locale <select name="locale"><option>All</option><option>English</option></select></label>
      <label>Search <input name="q" value="{esc(query)}" placeholder="Realm Name"></label>
      <button type="submit">Search</button>
    </form>
  </div>
  <table class="sl-realm-table">
    <thead><tr><th>Status</th><th>Realm Name</th><th>Type</th><th>Population</th><th>Timezone</th><th>Locale</th></tr></thead>
    <tbody>{row}</tbody>
  </table>
</section>"""


def _classic_promo() -> str:
    return f"""<section class="sl-tbc">
  <div class="sl-tbc-copy">
    <p class="sl-tbc-logo"><span>World of Warcraft</span> Burning Crusade <em>Classic</em></p>
    <h1>The Dark Portal Reopens Soon</h1>
    <p>Play WoW® Classic and Get Ready Now</p>
  </div>
</section>"""


def _trial() -> str:
    return """<section class="sl-trial" data-bar="2021">
  <h1>World of Warcraft® Free Trial</h1>
  <p class="sl-trial-lead">Begin your journey and play FREE up to Level 20!</p>
  <p>Welcome to Azeroth, a world of magic and limitless adventure. Experience the ever-expanding fantasy of World of Warcraft for FREE today.</p>
  <p><a class="sl-download" href="/account/create">Download WoW</a></p>
</section>"""


def character_profile(exp, char: dict) -> str:
    equipped = {}
    for item in char.get("equipment") or []:
        slot = str(item.get("slot") or "")
        if slot:
            equipped[slot] = item

    def cell(slot: str) -> str:
        item = equipped.get(slot)
        if not item or not item.get("item_id"):
            return f'<li class="sl-slot sl-slot-empty"><span>{esc(slot)}</span></li>'
        icon = _icon(assets.display_icon(exp, item.get("display_id")), "")
        name = item.get("name") or f"Item {item.get('item_id')}"
        return (
            f'<li class="sl-slot"><a href="/armory/item/{esc(item.get("item_id"))}">'
            f"{icon}<span>{esc(name)}</span></a></li>"
        )

    left = "".join(cell(slot) for slot in _LEFT_SLOTS)
    right = "".join(cell(slot) for slot in _RIGHT_SLOTS)
    weapons = "".join(cell(slot) for slot in _WEAPON_SLOTS)
    tabs = []
    for key, label in _PROFILE_TABS:
        mark = " sl-ptab-on" if key == "character" else ""
        tabs.append(f'<a class="sl-ptab{mark}" href="#{esc(key)}">{esc(label)}</a>')
    achievements = char.get("achievements", 0)
    kills = char.get("honorable_kills", "")
    pvp = f"<p>Honorable kills: {esc(kills)}</p>" if kills not in (None, "") else "<p>No honor recorded on this profile.</p>"
    guild = ""
    if char.get("guild") and isinstance(char["guild"], dict) and char["guild"].get("name"):
        guild = f"<p>Guild: {esc(char['guild']['name'])}</p>"
    return f"""<section class="sl-profile">
  <header class="sl-profile-head">
    <h1>{esc(char.get("name"))}</h1>
    <p>{esc(char.get("level"))} {esc(char.get("race"))} {esc(char.get("class"))}</p>
    {guild}
  </header>
  <nav class="sl-ptabs" aria-label="Profile">{"".join(tabs)}</nav>
  <div class="sl-doll" id="character">
    <ul class="sl-doll-col">{left}</ul>
    <div class="sl-doll-mid"><p>{esc(char.get("realm") or getattr(exp, "realm_name", ""))}</p></div>
    <ul class="sl-doll-col">{right}</ul>
  </div>
  <ul class="sl-weapons">{weapons}</ul>
  <section id="achievements"><h2>Achievements</h2><p>{esc(achievements)}</p></section>
  <section id="collections"><h2>Collections</h2><p>Collections are not on this profile.</p></section>
  <section id="dungeons"><h2>Dungeons &amp; Raids</h2><p>Dungeon and raid progress is not on this profile.</p></section>
  <section id="pvp"><h2>Player vs Player</h2>{pvp}</section>
  <section id="reputation"><h2>Reputation</h2><p>Reputation is not on this profile.</p></section>
</section>"""


def _take_character(path: str, ctx: dict):
    name = path.rsplit("/", 1)[-1]
    cfg = ctx.get("labcfg")
    if not name or cfg is None:
        return None
    char = armory.get_character(cfg, ctx["exp"], name)
    if not char:
        return None
    return (str(char.get("name") or name), character_profile(ctx["exp"], char))


def take(path: str, ctx: dict):
    exp = ctx["exp"]
    if path == "/wow/news":
        return ("News", _news_index(exp))
    if path.startswith("/wow/news/"):
        tail = path[len("/wow/news/"):]
        if not tail.isdigit():
            return None
        news = content.news_for(exp)
        idx = int(tail)
        if idx < 0 or idx >= len(news):
            return None
        title, date, body = news[idx]
        return (title, _article(title, date, body, idx))
    if path == "/wow/info" or path.startswith("/wow/info/"):
        return _take_info(path, ctx)
    if path == "/wow/realmstatus":
        return ("Realm Status", _realm_page(ctx))
    if path == "/classic":
        return ("WoW Classic", _classic_promo())
    if path == "/trial":
        return ("Free Trial", _trial())
    if path.startswith("/armory/character/"):
        return _take_character(path, ctx)
    return None


def _forum_nav(user: str | None) -> str:
    who = esc(user) if user else "My Account"
    return f"""<header class="sl-fnav">
  <a class="sl-blizz" href="/wow/">Blizzard</a>
  <nav aria-label="Battle.net">
    <a href="/wow/">Games</a>
    <a href="/shop">Shop</a>
    <a href="/wow/news">News</a>
    <a href="/esports">Esports</a>
  </nav>
  <nav class="sl-fnav-right" aria-label="Account and support">
    <a href="/support/">Support</a>
    <a href="/account/">{who}</a>
    <a class="sl-search" href="/wow/search">Search</a>
  </nav>
</header>"""


def _board_map(exp) -> dict[str, str]:
    return {slug: title for slug, title in forums.boards_for(exp) if slug != "evoker"}


def _gather_threads(conn, exp) -> list[dict]:
    found = []
    for slug, title in forums.boards_for(exp):
        if slug == "evoker":
            continue
        for thread in forums.list_threads(conn, exp, slug):
            row = dict(thread)
            row["board"] = slug
            row["board_title"] = title
            found.append(row)
    return found


def _thread_rows(threads: list[dict], slug_key: str = "board") -> str:
    if not threads:
        return '<tr class="sl-empty"><td colspan="5">No topics yet.</td></tr>'
    rows = []
    for thread in threads:
        board = thread.get(slug_key) or thread.get("board") or ""
        replies = thread.get("replies") or 0
        rows.append(
            "<tr>"
            f'<td class="sl-topic"><a href="/forums/{esc(board)}/{esc(thread.get("id"))}">{esc(thread.get("title"))}</a></td>'
            f'<td>{esc(thread.get("author"))}</td>'
            f'<td class="sl-num">{esc(replies)}</td>'
            '<td class="sl-num">0</td>'
            f'<td class="sl-num">{esc(_ago(thread.get("last") or thread.get("created")))}</td>'
            "</tr>"
        )
    return "".join(rows)


def _forum_index(exp, conn, user, view: str) -> str:
    boards = _board_map(exp)
    classes = []
    for slug in _CLASS_FORUMS:
        title = boards.get(slug)
        if not title:
            continue
        classes.append(
            f'<a href="/forums/{esc(slug)}">{_icon(assets.class_icon(exp.id, slug), title)}'
            f"<span>{esc(title)}</span></a>"
        )
    if view == "categories":
        body = f"""<div class="sl-cats">
  <section class="sl-cat" id="community">
    <h2>Community</h2>
    <p>Discuss World of Warcraft.</p>
    <p class="sl-cat-links"><a href="/forums/general">General Discussion</a>
    <a href="/forums/guilds">Guild Recruitment</a></p>
  </section>
  <section class="sl-cat" id="classes">
    <h2>Classes</h2>
    <p>For all your class discussion needs.</p>
    <div class="sl-class-links">{"".join(classes)}</div>
  </section>
  <section class="sl-cat" id="world">
    <h2>World of Warcraft</h2>
    <p class="sl-cat-links">
      <a href="/forums/pvp">PvP</a>
      <a href="/forums/dungeons">Dungeons &amp; Raids</a>
      <a href="/forums/covenants">Covenants</a>
      <a href="/forums/professions">Professions</a>
      <a href="/forums/ui">UI &amp; Macros</a>
      <a href="/forums/realm">Realm Forum</a>
    </p>
  </section>
  <section class="sl-cat" id="support">
    <h2>Support</h2>
    <p class="sl-cat-links"><a href="/forums/bugs">Bug Report</a></p>
  </section>
</div>"""
    else:
        threads = _gather_threads(conn, exp)
        if view == "top":
            threads.sort(key=lambda row: int(row.get("replies") or 0), reverse=True)
        elif view == "blizz":
            threads = [row for row in threads if "blizzard" in str(row.get("author") or "").lower()]
        else:
            threads.sort(key=lambda row: int(row.get("last") or row.get("created") or 0), reverse=True)
        body = (
            '<table class="sl-topics"><thead><tr>'
            "<th>Topic</th><th>Author</th><th>Replies</th><th>Views</th><th>Activity</th>"
            f"</tr></thead><tbody>{_thread_rows(threads)}</tbody></table>"
        )
    tabs = (
        ("categories", "Categories"),
        ("top", "Top"),
        ("new", "New"),
        ("unread", "Unread"),
        ("latest", "Latest"),
        ("blizz", "Blizz Tracker"),
    )
    tab_html = []
    for key, label in tabs:
        mark = " sl-ftab-on" if key == view else ""
        href = "/forums" if key == "categories" else f"/forums?view={key}"
        tab_html.append(f'<a class="sl-ftab{mark}" href="{href}">{label}</a>')
    new_href = "/forums/general#new" if user else "/account/login"
    return f"""{_forum_nav(user)}
<div class="sl-jailer"></div>
<main class="sl-fmain">
  <p class="sl-crumb"><a href="/forums">Forums</a></p>
  <div class="sl-fhead"><h1>All Categories</h1><a class="sl-newtopic" href="{new_href}">+ New Topic</a></div>
  <nav class="sl-ftabs" aria-label="Forum views">{"".join(tab_html)}</nav>
  {body}
</main>"""


def _forum_board(exp, conn, slug: str, user, view: str, page: int) -> str | None:
    title = forums.board_title(exp, slug)
    if not title or slug == "evoker":
        return None
    threads = forums.list_threads(conn, exp, slug)
    for thread in threads:
        thread["board"] = slug
    if view == "top":
        threads = sorted(threads, key=lambda row: int(row.get("replies") or 0), reverse=True)
    elif view == "blizz":
        threads = [row for row in threads if "blizzard" in str(row.get("author") or "").lower()]
    page_size = 20
    pages = max(1, (len(threads) + page_size - 1) // page_size)
    page_n = min(max(page, 1), pages)
    window = threads[(page_n - 1) * page_size : page_n * page_size]
    if slug == "bugs":
        heading = '<h1><a href="/forums#support">Support</a> <span aria-hidden="true">›</span> Bug Report</h1>'
        crumb = '<a href="/forums">Forums</a> <span>Support</span> <span>Bug Report</span>'
    else:
        heading = f"<h1>{esc(title)}</h1>"
        crumb = f'<a href="/forums">Forums</a> <span>{esc(title)}</span>'
    tabs = (("top", "Top"), ("latest", "Latest"), ("blizz", "Blizz Tracker"))
    tab_html = []
    for key, label in tabs:
        mark = " sl-ftab-on" if key == view else ""
        tab_html.append(f'<a class="sl-ftab{mark}" href="/forums/{esc(slug)}?view={key}">{label}</a>')
    if user:
        form = f"""<form id="new" class="sl-post" method="post" action="/forums/{esc(slug)}/new">
  <label>Title <input name="title" required maxlength="120"></label>
  <label>Body <textarea name="body" required rows="6"></textarea></label>
  <button type="submit">Post</button>
</form>"""
        new_href = "#new"
    else:
        form = '<p class="sl-signin"><a href="/account/login">Log In</a> to start a topic.</p>'
        new_href = "/account/login"
    pager = ""
    if pages > 1:
        links = []
        for number in range(1, pages + 1):
            mark = " sl-ftab-on" if number == page_n else ""
            links.append(f'<a class="{mark}" href="/forums/{esc(slug)}?view={esc(view)}&page={number}">{number}</a>')
        pager = f'<nav class="sl-pager">{"".join(links)}</nav>'
    return f"""{_forum_nav(user)}
<main class="sl-fmain sl-fboard">
  <p class="sl-crumb">{crumb}</p>
  <div class="sl-fhead">{heading}<a class="sl-newtopic" href="{new_href}">+ New Topic</a></div>
  <nav class="sl-ftabs" aria-label="Topics">{"".join(tab_html)}</nav>
  <table class="sl-topics"><thead><tr>
    <th>Topic</th><th>Author</th><th>Replies</th><th>Views</th><th>Activity</th>
  </tr></thead><tbody>{_thread_rows(window, "board")}</tbody></table>
  {pager}
  {form}
</main>"""


def _forum_thread(exp, conn, slug: str, tid: int, user) -> str | None:
    if forums.board_title(exp, slug) is None or slug == "evoker":
        return None
    thread = forums.get_thread(conn, exp, tid)
    if not thread:
        return None
    posts = []
    for post in thread.get("posts") or []:
        posts.append(
            "<article class=\"sl-post-card\">"
            f"<header>{esc(post.get('author'))} · {esc(_stamp(post.get('created')))}</header>"
            f"<p>{esc(post.get('body'))}</p></article>"
        )
    if user:
        form = f"""<form class="sl-post" method="post" action="/forums/{esc(slug)}/{int(tid)}/reply">
  <label>Reply <textarea name="body" required rows="5"></textarea></label>
  <button type="submit">Reply</button>
</form>"""
    else:
        form = '<p class="sl-signin"><a href="/account/login">Log In</a> to reply.</p>'
    title = forums.board_title(exp, slug) or slug
    return f"""{_forum_nav(user)}
<main class="sl-fmain sl-fboard">
  <p class="sl-crumb"><a href="/forums">Forums</a> <a href="/forums/{esc(slug)}">{esc(title)}</a> <span>{esc(thread.get("title"))}</span></p>
  <h1>{esc(thread.get("title"))}</h1>
  {"".join(posts)}
  {form}
</main>"""


def _forums_document(path: str, ctx: dict) -> str | None:
    exp = ctx["exp"]
    data_dir = ctx.get("data_dir")
    if data_dir is None:
        return None
    parts = [part for part in path.split("/") if part]
    if not parts or parts[0] != "forums":
        return None
    qs = ctx.get("qs") or {}
    view = ((qs.get("view") or ["categories"])[0] or "categories").lower()
    try:
        page = int((qs.get("page") or ["1"])[0])
    except ValueError:
        page = 1
    user = ctx.get("user")
    conn = forums.connect(data_dir)
    try:
        forums.seed_if_empty(conn, exp)
        if len(parts) == 1:
            if view not in ("categories", "top", "new", "unread", "latest", "blizz"):
                view = "categories"
            inner = _forum_index(exp, conn, user, view)
            title = "Forums"
        elif len(parts) == 2:
            if view not in ("top", "latest", "blizz"):
                view = "latest"
            inner = _forum_board(exp, conn, parts[1], user, view, page)
            if inner is None:
                return None
            title = forums.board_title(exp, parts[1]) or "Forums"
        elif len(parts) == 3 and parts[2].isdigit():
            inner = _forum_thread(exp, conn, parts[1], int(parts[2]), user)
            if inner is None:
                return None
            title = "Forums"
        else:
            return None
    finally:
        conn.close()
    return document(
        f"{title} — Forums",
        styles("shadowlands"),
        "era-shadowlands sl-forums",
        inner,
        dev_note_text=dev_note(exp, bool(ctx.get("dev"))),
    )


def _shop_document(exp, dev: bool) -> str:
    inner = """<header class="bn-top">
  <a class="bn-logo" href="/shop">Battle.net</a>
  <nav aria-label="Shop">
    <a href="/wow/">Games</a>
    <a href="/account/services">Services</a>
    <a href="/shop">Blizzard Gear</a>
  </nav>
  <form class="bn-search" method="get" action="/wow/search"><input name="q" placeholder="Search Shop" aria-label="Search Shop"></form>
  <nav class="bn-top-right" aria-label="Account">
    <a href="/wow/">Download Battle.net</a>
    <a href="/support/">Support</a>
    <a href="/account/">My Account</a>
  </nav>
</header>
<section class="bn-hero" id="cold-war">
  <p class="bn-kicker">Activision</p>
  <h1>Call of Duty<br>Black Ops<br>Cold War</h1>
  <p>Up to 50% off. Sale ends August 2</p>
  <a class="bn-buy" href="/shop#cold-war">Buy Now</a>
</section>
<section class="bn-shelf">
  <h2>Recommended</h2>
  <div class="bn-grid">
    <article><h3>World of Warcraft®: Special Subscription Offer</h3><p>Includes access to World of Warcraft.</p></article>
    <article><h3>Call of Duty®: Warzone</h3><p>Free for everyone. Action Shooter.</p></article>
    <article><h3>WoW®: Burning Crusade Classic™ Deluxe Edition</h3><p>Burning Crusade Classic is ready when the Dark Portal reopens.</p></article>
    <article><h3>Call of Duty®: Black Ops Cold War - Ultimate Edition</h3><p>Get the Captain Price operator.</p></article>
    <article><h3>Diablo® II: Resurrected™</h3><p>Pre-Purchase Now. Action RPG.</p></article>
  </div>
</section>"""
    return document(
        "Shop — Battle.net",
        styles("shadowlands"),
        "era-shadowlands sl-shop",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def _services_gate(exp, dev: bool) -> str:
    inner = """<main class="sl-services-gate">
  <h1>Character Services</h1>
  <p>Sign in to use character services on this account.</p>
  <p><a href="/account/login">Log In</a></p>
</main>"""
    return document(
        "Character Services — World of Warcraft",
        styles("shadowlands"),
        "era-shadowlands sl-account sl-account-gate",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def full(path: str, ctx: dict) -> str | None:
    exp = ctx["exp"]
    dev = bool(ctx.get("dev"))
    if path == "/shop":
        return _shop_document(exp, dev)
    if path == "/account/services" and not ctx.get("user"):
        return _services_gate(exp, dev)
    if path == "/forums" or path.startswith("/forums/"):
        return _forums_document(path, ctx)
    return None
