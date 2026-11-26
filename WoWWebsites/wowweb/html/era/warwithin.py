"""The War Within community site, March 2025 through early 2026.

The English home keeps the Undermine hero. The November 2025 French home
is the same masthead, with Expansions marked NEW. It is not the copy.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from wowweb import armory, assets, content, forums, lab, talents
from wowweb.html.era.common import dev_note, document, esc, styles

_IMG = "/static/img/warwithin"
_HERO = f"{_IMG}/undermine-hero.jpg"
_NEWS_ART = [f"{_IMG}/news-{i}.jpg" for i in range(1, 5)]
# Rows visible in the October 2024 status crop. The lab realm is appended if it is not already listed.
_STATUS_ROWS = (
    "Aegwynn",
    "Aerie Peak",
    "Agamaggan",
    "Aggramar",
    "Akama",
    "Alexstrasza",
    "Alleria",
    "Altar of Storms",
    "Alterac Mountains",
    "Aman'Thul",
    "Andorhal",
    "Anetheron",
    "Antonidas",
)

_HORDE = {2, 5, 6, 8, 9, 10, 26, 27, 28, 31, 35, 36}
_ALLIANCE = {1, 3, 4, 7, 11, 22, 25, 29, 30, 32, 34, 37}
_LEFT = ("Head", "Neck", "Shoulders", "Back", "Chest", "Wrists")
_RIGHT = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEAPONS = ("Main Hand", "Off Hand")
_TABS = (
    ("character", "CHARACTER"),
    ("achievements", "ACHIEVEMENTS"),
    ("collections", "COLLECTIONS"),
    ("dungeons", "DUNGEONS & RAIDS"),
    ("pvp", "PLAYER VS PLAYER"),
    ("reputation", "REPUTATION"),
)
_CLASS_SLUGS = {
    "warrior",
    "paladin",
    "hunter",
    "rogue",
    "priest",
    "deathknight",
    "shaman",
    "mage",
    "warlock",
    "monk",
    "druid",
    "demonhunter",
    "evoker",
}
_HERO_COPY = (
    "Travel deep into the goblin city of Undermine and learn to D.R.I.V.E., "
    "Join a cartel, adventure in two new delves, a new dungeon: Operation Floodgate, "
    "face Gallywix in the Liberation of Undermine raid, battle in a new PvP Arena — and more!"
)


def _drop(label: str, href: str, items: list[tuple[str, str]], badge: bool = False) -> str:
    links = "".join(f'<a href="{esc(h)}">{esc(text)}</a>' for h, text in items)
    mark = '<span class="tww-new">NEW</span> ' if badge else ""
    return (
        f'<div class="tww-item"><a class="tww-top" href="{esc(href)}">{mark}{esc(label)}</a>'
        f'<div class="tww-sub">{links}</div></div>'
    )


def _sections() -> str:
    return (
        _drop(
            "Game Info",
            "/wow/info",
            [
                ("/wow/info", "Game Guide"),
                ("/wow/info/classes", "Classes"),
                ("/wow/info/races", "Races"),
                ("/wow/realmstatus", "Realm Status"),
                ("/armory", "Armory"),
            ],
        )
        + _drop(
            "Expansions",
            "/wow/",
            [
                ("/wow/", "The War Within"),
                ("/story", "Story"),
                ("/classic", "WoW Classic"),
            ],
            badge=True,
        )
        + '<a class="tww-top" href="/wow/news">News</a>'
        + _drop(
            "Community",
            "/forums",
            [
                ("/forums", "Forums"),
                ("/forums/general", "General"),
                ("/support/", "Support"),
            ],
        )
        + _drop("Shop", "/shop", [("/shop", "Shop")])
    )


def _flat_sections() -> str:
    rows = [
        ("/wow/info", "Game Info", False),
        ("/wow/info/classes", "Classes", False),
        ("/wow/info/races", "Races", False),
        ("/wow/realmstatus", "Realm Status", False),
        ("/armory", "Armory", False),
        ("/wow/", "Expansions", True),
        ("/story", "Story", False),
        ("/wow/news", "News", False),
        ("/forums", "Community", False),
        ("/forums/general", "General", False),
        ("/support/", "Support", False),
        ("/shop", "Shop", False),
    ]
    bits = []
    for href, label, badge in rows:
        mark = '<span class="tww-new">NEW</span> ' if badge else ""
        bits.append(f'<a href="{esc(href)}">{mark}{esc(label)}</a>')
    return "".join(bits)


def _account_menu(user: str | None) -> str:
    if user:
        label = esc(user)
        extra = '<a href="/account/logout">Log Out</a>'
    else:
        label = "Account"
        extra = '<a href="/account/login">Log In</a><a href="/account/create">Create Account</a>'
    return (
        f'<div class="tww-item tww-account"><a class="tww-top" href="/account/">{label}</a>'
        f'<div class="tww-sub"><a href="/account/">Account</a>{extra}'
        f'<a href="/account/services">Character Services</a></div></div>'
    )


def _mast(user: str | None, collapsed: bool) -> str:
    logo = f'<img src="{_IMG}/logo-blizzard.png" alt="Blizzard">'
    mark = f'<img src="{_IMG}/logo-w.png" alt="">'
    if collapsed:
        sections = (
            '<details class="tww-ellipsis"><summary aria-label="Sections">…</summary>'
            f'<div class="tww-sub">{_flat_sections()}</div></details>'
        )
        actions = ""
    else:
        sections = f'<div class="tww-links">{_sections()}</div>'
        actions = (
            '<a class="tww-try" href="/account/create">Try Free</a>'
            '<a class="tww-subnow" href="/shop">Subscribe Now</a>'
        )
    return f"""<a class="tww-skip" href="#main">Skip to main content</a>
<header class="tww-mast">
  <a class="tww-blizz" href="/wow/">{logo}</a>
  <a class="tww-wmark" href="/wow/" aria-label="World of Warcraft">{mark}</a>
  <nav class="tww-nav" aria-label="World of Warcraft">{sections}</nav>
  <form class="tww-search" action="/wow/search" method="get" role="search">
    <input type="search" name="q" aria-label="Search" placeholder="Search">
    <button type="submit" aria-label="Search"><span class="tww-glass"></span></button>
  </form>
  {_account_menu(user)}
  {actions}
</header>"""


def _footer(exp) -> str:
    links = (
        ("/wow/", "Home"),
        ("/wow/news", "News"),
        ("/wow/info", "Game Guide"),
        ("/wow/info/classes", "Classes"),
        ("/wow/info/races", "Races"),
        ("/wow/realmstatus", "Realm Status"),
        ("/forums", "Forums"),
        ("/forums/general", "General"),
        ("/shop", "Shop"),
        ("/account/login", "Log In"),
        ("/account/create", "Create Account"),
        ("/account/", "Account"),
        ("/account/services", "Character Services"),
        ("/support/", "Support"),
        ("/armory", "Armory"),
    )
    items = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in links)
    return (
        f'<footer class="tww-foot"><nav aria-label="Footer">{items}</nav>'
        f"<p>© {esc(exp.year)} Blizzard Entertainment, Inc. All rights reserved.</p></footer>"
    )


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online, login_error
    gate = 'data-chrome="bnet-gate"' in body
    overview = 'data-chrome="bnet-overview"' in body
    collapsed = 'data-nav="ellipsis"' in body
    bare = 'data-bare="1"' in body or gate or overview
    if gate:
        inner = body
        klass = "era-warwithin warwithin tww-gate"
    elif overview:
        inner = body
        klass = "era-warwithin warwithin tww-account"
    else:
        if bare:
            main = body
        else:
            main = f'<div class="tww-panel"><h1>{esc(crumb or title)}</h1>{body}</div>'
        inner = _mast(user, collapsed) + f'<main class="tww-main" id="main">{main}</main>' + _footer(exp)
        klass = "era-warwithin warwithin"
        if collapsed:
            klass += " tww-forums"
        if 'class="tww-status"' in body:
            klass += " tww-status-page"
        if 'class="tww-home"' in body:
            klass += " tww-home"
        if 'class="tww-profile"' in body:
            klass += " tww-profile-page"
    css = styles("warwithin") + ["/static/css/forums.css", "/static/css/armory.css"]
    return document(
        f"{title} — World of Warcraft",
        css,
        klass,
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _cards(items: list[tuple[str, str, str]], limit: int | None = None) -> str:
    rows = list(items if limit is None else items[:limit])
    cards = []
    for index, (title, date, _body) in enumerate(rows):
        src = _NEWS_ART[index % len(_NEWS_ART)]
        cards.append(
            f'<a class="tww-card" href="/wow/news/{index}">'
            f'<img src="{esc(src)}" alt="">'
            f"<strong>{esc(title)}</strong><time>{esc(date)}</time></a>"
        )
    return "".join(cards)


def home_body(exp, news, realm, user) -> str:
    _ = exp, realm, user
    items = list(news or [])
    return f"""<div class="tww-home" data-bare="1">
  <section class="tww-hero">
    <img class="tww-hero-img" src="{_HERO}" alt="">
    <div class="tww-sr">
      <h1>THE UNDERMINE(D) CONTENT UPDATE IS NOW LIVE!</h1>
      <p>{_HERO_COPY}</p>
    </div>
    <a class="tww-hit tww-hit-sub" href="/shop">SUBSCRIBE TODAY</a>
    <a class="tww-hit tww-hit-learn" href="/wow/news">LEARN MORE</a>
  </section>
  <section class="tww-latest">
    <div class="tww-latest-head">
      <h2>Latest News &amp; Updates</h2>
      <a class="tww-all" href="/wow/news">VIEW ALL NEWS</a>
    </div>
    <div class="tww-cards">{_cards(items, 4)}</div>
  </section>
</div>"""


def _guide(exp) -> str:
    races = []
    for slug in content.races_for(exp):
        name, faction, city, _blurb = content.race_facts(exp, slug)
        races.append(
            f'<li><a href="/wow/info/races/{esc(slug)}">{esc(name)}</a>'
            f" — {esc(faction)}, {esc(city)}</li>"
        )
    classes = []
    for slug in content.classes_for(exp):
        name, armor, specs, _blurb = content.class_facts(exp, slug)
        talent = ""
        if talents.trees_for(exp, slug):
            talent = f' · <a href="/wow/info/classes/{esc(slug)}/talents.html">Talents</a>'
        classes.append(
            f'<li><a href="/wow/info/classes/{esc(slug)}">{esc(name)}</a>'
            f" — {esc(armor)}; {esc(specs)}{talent}</li>"
        )
    features = "".join(f"<li>{esc(feature)}</li>" for feature in content.features_for(exp))
    return (
        f"<p>{esc(content.intro_blurb(exp))}</p>"
        f"<h2>Features</h2><ul>{features}</ul>"
        f"<h2>Races</h2><ul>{''.join(races)}</ul>"
        f"<h2>Classes</h2><ul>{''.join(classes)}</ul>"
        f'<p><a href="/wow/info/professions">Professions</a>'
        f' · <a href="/wow/info/basics">New Players</a>'
        f' · <a href="/wow/info/basics/map">World Map</a></p>'
    )


def _class_index(exp) -> str:
    rows = []
    for slug in content.classes_for(exp):
        name, _armor, specs, blurb = content.class_facts(exp, slug)
        talent = ""
        if talents.trees_for(exp, slug):
            points = talents.points_available(exp)
            note = f" · {points} points" if points else ""
            talent = f'<a href="/wow/info/classes/{esc(slug)}/talents.html">Talents</a>{note}'
        rows.append(
            f"<li><a href=\"/wow/info/classes/{esc(slug)}\">{esc(name)}</a> — {esc(specs)}. "
            f"{esc(blurb)} {talent}</li>"
        )
    return f"<ul>{''.join(rows)}</ul>"


def _race_index(exp) -> str:
    rows = []
    for slug in content.races_for(exp):
        name, faction, city, blurb = content.race_facts(exp, slug)
        rows.append(
            f'<li><a href="/wow/info/races/{esc(slug)}">{esc(name)}</a>'
            f" — {esc(faction)}, {esc(city)}. {esc(blurb)}</li>"
        )
    return f"<ul>{''.join(rows)}</ul>"


def _news_index(exp, _ctx) -> str:
    _ = _ctx
    items = content.news_for(exp)
    return (
        '<div class="tww-latest" data-bare="1"><div class="tww-latest-head"><h1>News</h1></div>'
        f'<div class="tww-cards">{_cards(items)}</div></div>'
    )


def _realm_body(realm: dict, dev: bool) -> str:
    note = ""
    if dev and realm.get("error"):
        note = f'<p class="tww-warn">{esc(realm.get("error"))}</p>'
    rows = [(name, True, "Normal") for name in _STATUS_ROWS]
    lab_name = str(realm.get("name") or "")
    if lab_name and lab_name.casefold() not in {name.casefold() for name in _STATUS_ROWS}:
        rows.append((lab_name, bool(realm.get("up")), str(realm.get("type") or "Normal")))
    body = []
    for name, up, kind in rows:
        flag = "up" if up else "down"
        mark = "✓" if up else "✕"
        label = "Up" if up else "Down"
        body.append(
            "<tr>"
            f'<td><span class="tww-dot tww-dot-{flag}" aria-label="{label}">{mark}</span></td>'
            f"<td>{esc(name)}</td>"
            f"<td>{esc(kind)}</td>"
            "</tr>"
        )
    return f"""<div class="tww-status" data-bare="1">
  {note}
  <table>
    <thead><tr><th>Status</th><th>Realm Name</th><th>Type</th></tr></thead>
    <tbody>{''.join(body)}</tbody>
  </table>
</div>"""


def _activity(stamp) -> str:
    try:
        when = int(stamp or 0)
    except (TypeError, ValueError):
        return ""
    if when <= 0:
        return ""
    delta = max(0, int(time.time()) - when)
    if delta < 3600:
        return f"{max(1, delta // 60)}m"
    if delta < 86400:
        return f"{max(1, delta // 3600)}h"
    if delta < 86400 * 14:
        return f"{max(1, delta // 86400)}d"
    return datetime.fromtimestamp(when, timezone.utc).strftime("%b %Y")


def _forum_group(slug: str) -> str:
    if slug in {"bugs", "support"}:
        return "Support"
    if slug in {"guilds", "realm", "ui"}:
        return "Community"
    if slug in _CLASS_SLUGS:
        return "Classes"
    return "Game"


def _board_names(slug: str, title: str) -> tuple[str, str]:
    if slug == "bugs":
        return "Support", "Website Bug Report"
    return _forum_group(slug), title


def _forum_index(exp) -> str:
    groups: dict[str, list[str]] = {}
    for slug, title in forums.boards_for(exp):
        group, label = _board_names(slug, title)
        groups.setdefault(group, []).append(
            f'<li><a href="/forums/{esc(slug)}">{esc(label)}</a></li>'
        )
    blocks = []
    for group, rows in groups.items():
        blocks.append(f"<section><h2>{esc(group)}</h2><ul>{''.join(rows)}</ul></section>")
    return (
        '<div class="tww-board" data-bare="1" data-nav="ellipsis">'
        "<h1>Forums</h1>"
        + "".join(blocks)
        + "</div>"
    )


def _forum_board(exp, slug: str, title: str, ctx: dict) -> str:
    group, label = _board_names(slug, title)
    conn = forums.connect(ctx["data_dir"])
    forums.seed_if_empty(conn, exp)
    threads = forums.list_threads(conn, exp, slug)
    conn.close()
    rows = []
    for thread in threads:
        replies = thread.get("replies") or 0
        try:
            shown = max(0, int(replies) - 1)
        except (TypeError, ValueError):
            shown = 0
        when = _activity(thread.get("last") or thread.get("created"))
        rows.append(
            "<tr>"
            f'<td class="tww-topic"><a href="/forums/{esc(slug)}/{int(thread["id"])}">{esc(thread.get("title"))}</a></td>'
            f"<td>{esc(thread.get('author'))}</td>"
            f"<td>{shown}</td>"
            f"<td>—</td>"
            f"<td>{esc(when)}</td>"
            "</tr>"
        )
    body = "".join(rows) or '<tr class="tww-empty"><td colspan="5">No topics yet.</td></tr>'
    if group == "Support":
        group_html = f'<a href="/support/">{esc(group)}</a>'
    else:
        group_html = esc(group)
    user = ctx.get("user")
    if user:
        form = f"""<form class="tww-post" id="new-topic" method="post" action="/forums/{esc(slug)}/new">
  <h2>New Topic</h2>
  <label>Title <input name="title" required maxlength="120"></label>
  <label>Body <textarea name="body" required rows="6"></textarea></label>
  <button type="submit">Post</button>
</form>"""
        button = '<a class="tww-newtopic" href="#new-topic">New Topic</a>'
    else:
        form = ""
        button = '<a class="tww-newtopic" href="/account/login">New Topic</a>'
    return f"""<div class="tww-board" data-bare="1" data-nav="ellipsis">
  <p class="tww-crumb"><a class="tww-crumb-home" href="/forums" aria-label="Forums home"></a><a href="/forums">Forums</a> <span>&gt;</span> {group_html} <span>&gt;</span> {esc(label)}</p>
  <div class="tww-board-head">
    <h1>Latest topics in {esc(label)}</h1>
    {button}
  </div>
  <p class="tww-sort">Topic list, column headers with buttons are sortable.</p>
  <table class="tww-threads">
    <thead><tr>
      <th><button type="button">Topic</button></th>
      <th><button type="button">Author</button></th>
      <th><button type="button">Replies</button></th>
      <th><button type="button">Views</button></th>
      <th><button type="button">Activity</button></th>
    </tr></thead>
    <tbody>{body}</tbody>
  </table>
  {form}
</div>"""


def _forum_thread(slug: str, thread: dict, user: str | None) -> str:
    posts = []
    for post in thread.get("posts") or []:
        when = _activity(post.get("created"))
        posts.append(
            f'<article class="tww-post"><header>{esc(post.get("author"))} · {esc(when)}</header>'
            f"<pre>{esc(post.get('body'))}</pre></article>"
        )
    form = ""
    if user:
        form = (
            f'<form class="tww-post" method="post" action="/forums/{esc(slug)}/{int(thread["id"])}/reply">'
            f'<label>Reply <textarea name="body" required rows="5"></textarea></label>'
            f'<button type="submit">Reply</button></form>'
        )
    else:
        form = '<p><a href="/account/login">Log in</a> to reply.</p>'
    return (
        '<div class="tww-board" data-bare="1" data-nav="ellipsis">'
        f'<p class="tww-crumb"><a href="/forums">Forums</a> &gt; <a href="/forums/{esc(slug)}">{esc(slug)}</a></p>'
        f"<h1>{esc(thread.get('title'))}</h1>{''.join(posts)}{form}</div>"
    )


def _below_armory_level(ctx: dict, name: str) -> dict | None:
    """The shared armory hides characters under level 10. The sheet still uses lab data."""
    exp = ctx["exp"]
    cfg = ctx["labcfg"]
    db = cfg.chars_db(exp)
    safe = name.replace("\\", "\\\\").replace("'", "''")
    rows = lab.mysql_rows(
        cfg,
        f"SELECT name, race, class, level FROM `{db}`.`characters` WHERE name='{safe}' LIMIT 1;",
    )
    if not rows:
        return None
    from wowweb.armory.constants import CLASSES, RACES

    row = rows[0]
    try:
        race_id = int(row[1] or 0)
        class_id = int(row[2] or 0)
    except (TypeError, ValueError):
        race_id = class_id = 0
    return {
        "name": row[0],
        "race_id": race_id,
        "race": RACES.get(race_id, row[1]),
        "class": CLASSES.get(class_id, row[2]),
        "level": row[3],
        "realm": exp.realm_name,
        "equipment": [],
        "achievements": 0,
    }


def _faction(char: dict) -> str:
    try:
        race_id = int(char.get("race_id") or 0)
    except (TypeError, ValueError):
        race_id = 0
    if race_id in _HORDE:
        return "horde"
    if race_id in _ALLIANCE:
        return "alliance"
    return "neutral"


def _gear(char: dict, names: tuple[str, ...], exp) -> str:
    equipped = {}
    for item in char.get("equipment") or []:
        slot = str(item.get("slot") or "")
        if item.get("item_id"):
            equipped[slot] = item
    rows = []
    for name in names:
        item = equipped.get(name)
        if not item:
            continue
        icon = ""
        if exp is not None:
            src = assets.display_icon(exp, item.get("display_id"))
            if src:
                icon = f'<img src="{esc(src)}" alt="">'
        rows.append(
            f'<a class="tww-itemlink" href="/armory/item/{esc(item.get("item_id"))}">'
            f"{icon}<span><strong>{esc(item.get('name') or name)}</strong>"
            f"<em>{esc(name)}</em></span></a>"
        )
    return "".join(rows)


def character_body(char: dict, tab: str = "character", exp=None) -> str:
    key = (tab or "character").lower()
    if key not in {slug for slug, _label in _TABS}:
        key = "character"
    tabs = []
    for slug, label in _TABS:
        cls = " is-on" if slug == key else ""
        tabs.append(f'<a class="{cls.strip()}" href="?tab={slug}">{esc(label)}</a>')
    level = esc(char.get("level"))
    race = esc(char.get("race"))
    klass = esc(char.get("class"))
    spec = esc(char.get("spec") or "")
    ident = " ".join(part for part in (level, race, spec, klass) if part)
    ilvl = char.get("ilvl")
    ilvl_text = esc(ilvl) if ilvl not in (None, "") else "—"
    if key == "achievements":
        panel = f"<p>{esc(char.get('achievements') or 0)} achievement points.</p>"
    elif key == "collections":
        panel = "<p>No collections are stored for this character.</p>"
    elif key == "dungeons":
        panel = "<p>No dungeon or raid progress is stored for this character.</p>"
    elif key == "pvp":
        kills = char.get("honorable_kills")
        panel = f"<p>Honorable kills: {esc(kills if kills not in (None, '') else '—')}</p>"
    elif key == "reputation":
        panel = "<p>No reputations are stored for this character.</p>"
    else:
        left = _gear(char, _LEFT, exp)
        right = _gear(char, _RIGHT, exp)
        weapons = _gear(char, _WEAPONS, exp)
        empty = ""
        if not (left or right or weapons):
            empty = "<p>No gear recorded at last logout.</p>"
        panel = (
            f'<div class="tww-doll"><div class="tww-gear tww-gear-left">{left}</div>'
            f'<div class="tww-figure" aria-hidden="true"></div>'
            f'<div class="tww-gear tww-gear-right">{right}</div></div>'
            f'<div class="tww-weapons">{weapons}</div>{empty}'
        )
    guild = ""
    if char.get("guild") and isinstance(char.get("guild"), dict) and char["guild"].get("name"):
        guild = f'<p class="tww-guild">{esc(char["guild"]["name"])}</p>'
    title = char.get("title")
    titled = f" ({esc(title)})" if title else ""
    faction = _faction(char)
    if faction == "horde":
        crest = f'<img class="tww-crestimg" src="{_IMG}/crest-horde.png" alt="">'
    else:
        crest = f'<span class="tww-crest tww-crest-{faction}" aria-hidden="true"></span>'
    return f"""<div class="tww-profile" data-bare="1">
  <header class="tww-profile-head">
    {crest}
    <div>
      <h1>{esc(char.get("name"))}</h1>
      <p class="tww-score"><span class="tww-ach">{esc(char.get("achievements") or 0)}</span> <span class="tww-ilvl">{ilvl_text} ILVL</span></p>
      <p class="tww-ident">{ident}{titled} <span>{esc(char.get("realm") or "")}</span></p>
      {guild}
    </div>
  </header>
  <nav class="tww-tabs" aria-label="Profile">{''.join(tabs)}</nav>
  <div class="tww-panel-body">{panel}</div>
</div>"""


def _forums(path: str, ctx: dict):
    exp = ctx["exp"]
    parts = [part for part in path.split("/") if part]
    if not parts or parts[0] != "forums":
        return None
    if len(parts) == 1:
        return "Forums", _forum_index(exp)
    slug = parts[1]
    title = forums.board_title(exp, slug)
    if len(parts) == 2:
        if not title:
            return None
        return _board_names(slug, title)[1], _forum_board(exp, slug, title, ctx)
    if len(parts) == 3 and parts[2].isdigit():
        conn = forums.connect(ctx["data_dir"])
        thread = forums.get_thread(conn, exp, int(parts[2]))
        conn.close()
        if not thread:
            return None
        return thread.get("title") or "Topic", _forum_thread(slug, thread, ctx.get("user"))
    return None


def _shop_cards() -> str:
    cards = (
        {
            "kicker": "CALL OF DUTY BLACK OPS 6",
            "title": "Call of Duty: Black Ops 6",
            "line": "Wreak havoc in Season 01",
            "kind": "Action Shooter",
            "price": "$69.99",
            "art": "shop-cod.jpg",
        },
        {
            "kicker": "WORLD OF WARCRAFT",
            "title": "World of Warcraft: Subscription",
            "line": (
                "Get access to World of Warcraft, now including Dragonflight, "
                "WoW Classic: 20th Anniversary Edition, Cataclysm Classic, and more!"
            ),
            "kind": "Subscriptions",
            "price": "From $12.99/month",
            "art": "shop-sub.jpg",
            "anchor": "subscription",
        },
        {
            "kicker": "WORLD OF WARCRAFT",
            "title": "World of Warcraft: The War Within",
            "line": "Now live! Get a Level 70 Boost included in all editions and get back in the fight.",
            "kind": "Massively Multiplayer RPG",
            "price": "From $49.99",
            "art": "shop-tww.jpg",
            "anchor": "war-within",
        },
        {
            "kicker": "DIABLO IV",
            "title": "Diablo IV Expansion Bundle",
            "line": "Vessel of Hatred Available Now!",
            "kind": "Action RPG",
            "price": "$69.99",
            "art": "shop-d4.jpg",
        },
        {
            "kicker": "CALL OF DUTY BLACK OPS 6",
            "title": "Call of Duty: Black Ops 6 - Vault Edition",
            "line": "Wreak havoc in Season 01",
            "kind": "Action Shooter",
            "price": "$99.99",
            "art": "shop-vault.jpg",
        },
    )
    bits = []
    for card in cards:
        anchor = card.get("anchor")
        ident = f' id="{anchor}"' if anchor else ""
        art = f'<img src="{_IMG}/{card["art"]}" alt="">'
        bits.append(
            f'<article class="bnet-card"{ident}>{art}'
            f'<div class="bnet-copy">'
            f'<p class="bnet-kicker">{esc(card["kicker"])}</p>'
            f'<h3>{esc(card["title"])}</h3>'
            f'<p class="bnet-line">{esc(card["line"])}</p>'
            f'<p class="bnet-kind">{esc(card["kind"])}</p>'
            f'<p class="bnet-price">{esc(card["price"])}</p></div></article>'
        )
    return "".join(bits)


def _shop_document(exp, dev: bool) -> str:
    inner = f"""<div class="bnet-shop">
  <header class="bnet-shop-top">
    <a class="bnet-brand" href="/shop"><img src="{_IMG}/logo-bnet.png" alt="Battle.net"></a>
    <nav aria-label="Battle.net">
      <a class="bnet-dl" href="/wow/">Download Battle.net</a>
      <a class="bnet-help" href="/support/">Support</a>
      <a class="bnet-acct" href="/account/">Account</a>
    </nav>
  </header>
  <div class="bnet-shop-nav">
    <nav aria-label="Games">
      <a class="is-on" href="/shop">Warcraft</a>
      <a href="#diablo">Diablo</a>
      <a href="#overwatch">Overwatch</a>
      <a href="#cod">Call of Duty</a>
      <a href="#more">Avowed</a>
      <a href="#more">More</a>
    </nav>
    <form action="/wow/search" method="get" role="search">
      <input type="search" name="q" aria-label="Search Shop" placeholder="Search Shop">
    </form>
    <a class="bnet-balance" href="/account/">Battle.net Balance</a>
  </div>
  <section class="bnet-promo">
    <img src="{_IMG}/shop-promo.jpg" alt="">
    <div>
      <img class="bnet-hs" src="{_IMG}/shop-hs.jpg" alt="Hearthstone Battlegrounds">
      <p>Get the new Battlegrounds Season Pass Plus now!</p>
      <a class="bnet-buy" href="#war-within">Buy Now</a>
    </div>
  </section>
  <div class="bnet-dots" aria-hidden="true"><b></b><i></i><i></i><i></i><i></i><i></i></div>
  <section class="bnet-recommended" id="recommended">
    <h2>Recommended</h2>
    <div class="bnet-grid" id="diablo">{_shop_cards()}</div>
    <img class="bnet-more" id="overwatch" src="{_IMG}/shop-more.jpg" alt="">
  </section>
  <p id="cod"></p><p id="more"></p>
</div>"""
    return document(
        "Shop — Battle.net",
        styles("warwithin"),
        "era-warwithin warwithin tww-shop",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def full(path: str, ctx: dict) -> str | None:
    exp = ctx["exp"]
    dev = bool(ctx.get("dev"))
    if path == "/shop":
        return _shop_document(exp, dev)
    if path == "/account/services":
        from wowweb.services.page import services_page

        user = ctx.get("user") or ""
        body = services_page(ctx["labcfg"], exp, user, ctx["data_dir"])
        if not user:
            body = '<p><a href="/account/login">Log in</a> to use character services.</p>' + body
        return shell(exp, "Character Services", body, ctx.get("user"), "Character Services", dev)
    return None


def take(path: str, ctx: dict):
    exp = ctx["exp"]
    if path == "/wow/news":
        return "News", _news_index(exp, ctx)
    if path in ("/wow/info", "/wow/info/introduction"):
        return "Game Guide", _guide(exp)
    if path == "/wow/info/classes":
        return "Classes", _class_index(exp)
    if path == "/wow/info/races":
        return "Races", _race_index(exp)
    if path == "/wow/realmstatus":
        realm = lab.realm_status(ctx["labcfg"], exp)
        if not ctx.get("dev"):
            realm = dict(realm)
            realm["error"] = ""
        return "Realm Status", _realm_body(realm, bool(ctx.get("dev")))
    if path.startswith("/armory/character/"):
        name = path.rsplit("/", 1)[-1]
        if not name:
            return None
        char = armory.get_character(ctx["labcfg"], exp, name)
        if not char:
            char = _below_armory_level(ctx, name)
        if not char:
            return None
        raw = (ctx.get("qs") or {}).get("tab") or ["character"]
        tab = raw[0] if isinstance(raw, list) else str(raw)
        return char.get("name") or name, character_body(char, tab, exp)
    if path == "/forums" or path.startswith("/forums/"):
        return _forums(path, ctx)
    return None
