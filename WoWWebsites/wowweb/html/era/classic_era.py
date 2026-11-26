"""Classic Era community pages (client 1.15.x), not the 2006 community site.

Chrome is the November 2023 realm-status page and the May 2023 forum
category cards: one nebula field, gold tabs, and the same table treatment.
"""

from __future__ import annotations

from urllib.parse import urlencode

from .common import dev_note, document, esc, signed_in, styles

_CLASS_SLUGS = (
    "warrior",
    "paladin",
    "hunter",
    "rogue",
    "priest",
    "shaman",
    "mage",
    "warlock",
    "druid",
    "deathknight",
    "monk",
    "demonhunter",
    "evoker",
)

# English labels for the May 2023 WoW Classic category card.
# Wrath has no board of its own on this realm, so that row opens Quests.
_CLASSIC_LINES = (
    (("quests", "Wrath of the Lich King Classic - General", "helm"),),
    (
        ("general", "WoW Classic – General", "shield"),
        ("classes", "WoW Classic – Classes", "hammers"),
    ),
    (("professions", "WoW Classic – Professions", "anvil"),),
    (("guilds", "WoW Classic – Player & Guild Search", "swirl"),),
    (("guildrelations", "Player & Guild Registry 2004-2006", "swirl"),),
)
_COMMUNITY_LINKS = (
    ("suggestions", "General", "helm"),
    ("rp", "Fan Creations and Events", "frame"),
)
_SUPPORT_LINKS = (
    ("realm", "Service Status", "help"),
    ("support", "Customer Service", "help"),
    ("bugs", "Bug Report", "help"),
)


def _svg(name: str) -> str:
    paths = {
        "laurel": (
            '<path d="M12 2.2l6.2 2.4v5.6c0 4.4-2.5 7.4-6.2 9.8-3.7-2.4-6.2-5.4-6.2-9.8V4.6z"/>'
            '<path d="M3.2 8.2c1.6 1.2 2.4 3 2.2 5.2M20.8 8.2c-1.6 1.2-2.4 3-2.2 5.2" fill="none" stroke="currentColor" stroke-width="1.4"/>'
        ),
        "helm": '<path d="M6 11.5c0-3.6 2.2-6.5 6-7.5 3.8 1 6 3.9 6 7.5V16H6zM4.2 8.2l2.2 2.6M19.8 8.2l-2.2 2.6M8 16h8v2.2H8z"/>',
        "shield": '<path d="M12 2.4l7 2.6v6.2c0 4.6-2.8 7.8-7 10.2-4.2-2.4-7-5.6-7-10.2V5z"/>',
        "swords": '<path d="M5 4l8 8-1.6 1.6L3.4 5.6zM19 4l-8 8 1.6 1.6 8-8zM8.2 15.2l-2.4 4.2 1.6.8 2.2-4.2zM15.8 15.2l2.4 4.2-1.6.8-2.2-4.2z"/>',
        "hammers": '<path d="M3.2 7.4 8.6 4.2l1.5 2.4-5.4 3.2zM14 3.6l6.2 3.4-1.4 2.4-6.2-3.4zM8.4 8.2l6.2 10.4-2.2 1.2L6.2 9.4zM15.6 8.2l-6.2 10.4 2.2 1.2 6.2-10.4z"/>',
        "anvil": '<path d="M4 14h16v2.2H4zM6 11.2h12V14H6zM8.2 8h7.6l1.2 3.2H7z"/>',
        "swirl": '<path d="M12 4a6 6 0 0 1 4.2 10.2A6 6 0 1 1 7.2 7.2 3.2 3.2 0 1 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8"/>',
        "help": '<path d="M12 4a8 8 0 1 0 .01 16.01A8 8 0 0 0 12 4zm0 12.2a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm1.6-4.6c-.4.3-.8.6-.8 1.2h-1.6c0-1.4.6-2 1.4-2.5.6-.4.8-.6.8-1.1 0-.6-.5-1-1.2-1s-1.2.4-1.2 1.1H9.4C9.4 8 10.5 7 12.2 7c1.6 0 2.8 1 2.8 2.4 0 1-.6 1.6-1.4 2.2z"/>',
        "frame": '<path d="M5 6h14v12H5z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8 15l2.2-2.6 1.6 1.6L15 10l2 5z"/>',
        "search": '<circle cx="10" cy="10" r="5.2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M14.2 14.2L19 19" fill="none" stroke="currentColor" stroke-width="2"/>',
    }
    inner = paths.get(name, paths["shield"])
    return f'<svg class="ce-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{inner}</svg>'


def _qs_one(qs: dict | None, key: str, default: str = "") -> str:
    if not qs:
        return default
    raw = qs.get(key, default)
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else default
    if raw is None:
        return default
    return str(raw)


def _population(value, up: bool) -> str:
    if value is None or value == "":
        return "Low" if up else "—"
    text = str(value).strip()
    known = {"low": "Low", "medium": "Medium", "high": "High", "full": "Full"}
    if text.lower() in known:
        return known[text.lower()]
    try:
        number = float(text)
    except ValueError:
        return text
    if "." in text and number <= 3:
        if number < 0.5:
            return "Low"
        if number < 1.5:
            return "Medium"
        if number < 2.5:
            return "High"
        return "Full"
    count = int(number)
    if count < 50:
        return "Low"
    if count < 200:
        return "Medium"
    if count < 400:
        return "High"
    return "Full"


def _nav(title: str, user: str | None) -> str:
    low = (title or "").lower()
    if title == "World of Warcraft Community Site":
        low = "home"
    items = (
        ("/wow/info/", "Game", ("game guide", "races", "classes", "profession", "talent", "new player", "world map", "patch", "feature")),
        ("/wow/news", "News", ("news", "archived")),
        ("/forums/", "Forums", ("forum", "categor", "general discussion", "guild")),
        ("/wow/realmstatus", "Realm Status", ("realm",)),
        ("/armory/", "Armory", ("armory", "character")),
        ("/shop", "Shop", ("shop",)),
        ("/account/", "Account", ("account", "log in", "create account", "change password", "character services")),
        ("/support/", "Support", ("support", "stuck", "addon", "honor")),
    )

    def on(keys: tuple[str, ...]) -> str:
        return " is-on" if any(key in low for key in keys) else ""

    links = "".join(
        f'<a class="ce-tab{on(keys)}" href="{esc(href)}">{esc(label)}</a>'
        for href, label, keys in items
    )
    return (
        '<header class="ce-mast">'
        '<a class="ce-brand" href="/wow/">World of Warcraft Classic</a>'
        f'<nav class="ce-nav" aria-label="World of Warcraft">{links}</nav>'
        f'<div class="ce-who">{signed_in(user)}</div>'
        "</header>"
    )


def _shown_title(title: str) -> tuple[str, str]:
    if title == "World of Warcraft Community Site":
        return "World of Warcraft Classic", "home"
    if title == "Realm Status":
        return title, "realm"
    if title == "All Categories":
        return title, "board"
    return title, "page"


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = crumb, online, login_error
    shown, kind = _shown_title(title or "")
    body_class = "era-classic-era"
    if body and "ce-shot-realm" in body:
        body_class += " ce-is-realm"
    elif body and "ce-shot-forums" in body:
        body_class += " ce-is-forums"
    inner = (
        '<div class="ce-site">'
        f"{_nav(title or '', user)}"
        f'<main class="ce-main ce-main-{kind}">'
        f'<h1 class="ce-title">{esc(shown)}</h1>'
        f"{body}"
        "</main></div>"
    )
    return document(
        f"{shown} — World of Warcraft",
        styles(exp.id) if exp is not None else styles("classic-era"),
        body_class,
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    _ = user
    from wowweb import talents

    rows = []
    for i, item in enumerate(news or []):
        title, date, body = item[0], item[1], item[2] if len(item) > 2 else ""
        rows.append(
            "<tr>"
            f'<td><a href="/wow/news/{i}">{esc(title)}</a>'
            f'<p class="ce-news-body">{esc(body)}</p></td>'
            f"<td>{esc(date)}</td>"
            "</tr>"
        )
    if not rows:
        rows.append('<tr><td colspan="2">No news posted.</td></tr>')
    up = "Up" if realm and realm.get("up") else "Down"
    name = (realm or {}).get("name") or getattr(exp, "realm_name", "") or "Classic Era"
    pop = _population((realm or {}).get("population"), bool(realm and realm.get("up")))
    points = talents.points_available(exp)
    return (
        '<div class="ce-home">'
        f'<p class="ce-kicker">Patch {esc(getattr(exp, "last_patch", ""))}</p>'
        '<table class="ce-realms ce-news">'
        "<thead><tr><th>News</th><th>Date</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        '<p class="ce-realmchip">Realm '
        f'<a href="/wow/realmstatus">{esc(name)}</a> is {esc(up)}'
        f" · Population {esc(pop)}.</p>"
        f'<p class="ce-realmchip">Talent calculators use {esc(points)} points. '
        '<a href="/wow/info/classes/">Open a class</a> · '
        '<a href="/forums/">Forums</a> · '
        '<a href="/armory/">Character profile</a></p>'
        "</div>"
    )


def _realm_href(game: str, region: str, locale: str, query: str) -> str:
    params = {"game": game, "region": region, "locale": locale}
    if query:
        params["q"] = query
    return "/wow/realmstatus?" + urlencode(params)


def _realm_body(ctx: dict) -> str:
    from wowweb import lab

    exp = ctx["exp"]
    qs = ctx.get("qs") or {}
    game = _qs_one(qs, "game", "classic")
    if game not in ("retail", "classic", "wotlk"):
        game = "classic"
    region = _qs_one(qs, "region", "us")
    if region not in ("us", "eu", "kr", "tw"):
        region = "us"
    locale = _qs_one(qs, "locale", "all")
    if locale not in ("all", "era"):
        locale = "all"
    query = _qs_one(qs, "q", "").strip()
    realm = lab.realm_status(ctx["labcfg"], exp)
    show = game == "classic" and region == "us" and locale in ("all", "era")
    name = str(realm.get("name") or getattr(exp, "realm_name", "") or "Classic Era")
    if show and query and query.lower() not in name.lower():
        show = False
    tabs = (
        ("retail", "World of Warcraft"),
        ("classic", "World of Warcraft Classic"),
        ("wotlk", "Wrath of the Lich King Classic"),
    )
    tab_html = "".join(
        f'<a href="{esc(_realm_href(key, region, locale, query))}"'
        + (' class="is-selected" aria-current="page"' if key == game else "")
        + f">{esc(label)}</a>"
        for key, label in tabs
    )
    regions = (
        ("us", "Americas &amp; Oceania"),
        ("eu", "Europe"),
        ("kr", "Korea"),
        ("tw", "Taiwan"),
    )
    region_opts = "".join(
        f'<option value="{key}"' + (" selected" if key == region else "") + f">{label}</option>"
        for key, label in regions
    )
    locales = (("all", "All"), ("era", "Classic Era"))
    locale_opts = "".join(
        f'<option value="{key}"' + (" selected" if key == locale else "") + f">{esc(label)}</option>"
        for key, label in locales
    )
    if show:
        up = bool(realm.get("up"))
        dot = "ce-dot ce-dot-up" if up else "ce-dot ce-dot-down"
        label = "Up" if up else "Down"
        kind = realm.get("type") or "—"
        row = (
            "<tr>"
            f'<td class="ce-status"><span class="{dot}" role="img" aria-label="{label}"></span></td>'
            f"<td>{esc(name)}</td>"
            f"<td>{esc(kind)}</td>"
            f"<td>{esc(_population(realm.get('population'), up))}</td>"
            f"<td>{esc(realm.get('timezone') or 'PST')}</td>"
            "<td>Classic Era</td>"
            "</tr>"
        )
    else:
        row = '<tr class="ce-empty"><td colspan="6">No realms match these filters.</td></tr>'
    return (
        '<div class="ce-shot ce-shot-realm">'
        '<p class="ce-lead">This page lists all available World of Warcraft realms and has information '
        "on whether or not a realm is up or down. You can find more information about realm status and "
        'scheduled maintenances in the <a href="/forums/realm">Service Status Forum</a>. If your realm '
        "is listed as down, rest assured that we're aware of it and working diligently to bring it back "
        "online as quickly as possible.</p>"
        f'<nav class="ce-games" aria-label="Games">{tab_html}</nav>'
        '<form class="ce-filters" method="get" action="/wow/realmstatus">'
        f'<input type="hidden" name="game" value="{esc(game)}">'
        '<label class="ce-field"><span>Region</span>'
        f'<select name="region" onchange="this.form.submit()">{region_opts}</select></label>'
        '<label class="ce-field"><span>Locale</span>'
        f'<select name="locale" onchange="this.form.submit()">{locale_opts}</select></label>'
        '<label class="ce-field"><span>Search</span><span class="ce-search">'
        f'<input name="q" value="{esc(query)}" placeholder="Realm Name" aria-label="Realm Name">'
        f'<button type="submit" aria-label="Search">{_svg("search")}</button>'
        "</span></label></form>"
        '<hr class="ce-rule">'
        '<table class="ce-realms ce-status-table">'
        "<thead><tr>"
        "<th>Status</th>"
        '<th class="ce-col-name">Realm Name <span class="ce-caret" aria-hidden="true"></span></th>'
        "<th>Type</th><th>Population</th><th>Timezone</th><th>Locale</th>"
        "</tr></thead>"
        f"<tbody>{row}</tbody></table></div>"
    )


def _blink(href: str, label: str, icon: str) -> str:
    return (
        f'<a class="ce-blink" href="{esc(href)}">{_svg(icon)}'
        f"<span>{esc(label)}</span></a>"
    )


def _card(icon: str, title: str, desc: str, links: str, extra: str = "", klass: str = "") -> str:
    ident = f' id="{extra}"' if extra else ""
    class_attr = "ce-card" + (f" {klass}" if klass else "")
    return (
        f'<article class="{class_attr}"{ident}>'
        f'<div class="ce-card-h">{_svg(icon)}<h2>{esc(title)}</h2></div>'
        f'<p class="ce-desc">{esc(desc)}</p>'
        f'<div class="ce-links">{links}</div></article>'
    )


def _classic_block(by_slug: dict[str, str], used: set[str]) -> str:
    lines = []
    for line in _CLASSIC_LINES:
        bits = []
        for slug, label, icon in line:
            if slug == "classes":
                if any(name in by_slug for name in _CLASS_SLUGS):
                    bits.append(_blink("#ce-classes", label, icon))
                continue
            if slug not in by_slug or slug in used:
                continue
            used.add(slug)
            bits.append(_blink(f"/forums/{slug}", label, icon))
        if bits:
            lines.append(f'<div class="ce-line">{"".join(bits)}</div>')
    return "".join(lines)


def _linked(by_slug: dict[str, str], spec: tuple, used: set[str]) -> str:
    bits = []
    for slug, label, icon in spec:
        if slug not in by_slug or slug in used:
            continue
        used.add(slug)
        bits.append(_blink(f"/forums/{slug}", label, icon))
    return "".join(bits)


def _forum_threads(ctx: dict) -> list[dict]:
    from wowweb import forums as forum_api

    exp = ctx["exp"]
    conn = forum_api.connect(ctx["data_dir"])
    try:
        forum_api.seed_if_empty(conn, exp)
        rows = conn.execute(
            """
            SELECT t.id, t.board, t.title, t.author, t.created,
                   (SELECT COUNT(*) FROM posts p WHERE p.thread_id = t.id) AS replies,
                   (SELECT MAX(created) FROM posts p WHERE p.thread_id = t.id) AS last
            FROM threads t
            WHERE t.expansion = ?
            """,
            (exp.id,),
        ).fetchall()
    finally:
        conn.close()
    items = []
    for row in rows:
        last = row["last"] or row["created"] or 0
        items.append(
            {
                "id": row["id"],
                "board": row["board"],
                "title": row["title"],
                "author": row["author"],
                "created": row["created"] or 0,
                "replies": row["replies"] or 0,
                "last": last,
            }
        )
    return items


def _forum_body(ctx: dict) -> str:
    from wowweb import forums as forum_api

    exp = ctx["exp"]
    boards = forum_api.boards_for(exp)
    by_slug = {slug: title for slug, title in boards}
    view = _qs_one(ctx.get("qs"), "view", "categories")
    if view not in ("categories", "top", "new", "unread", "latest"):
        view = "categories"
    threads = _forum_threads(ctx)
    count = len(threads)
    tabs = (
        ("categories", "Categories"),
        ("top", "Top"),
        ("new", f"New ({count})"),
        ("unread", f"Unread ({count})"),
        ("latest", "Latest"),
    )
    tab_html = "".join(
        f'<a href="/forums?view={key}"' + (' class="is-on" aria-current="page"' if key == view else "") + f">{esc(label)}</a>"
        for key, label in tabs
    )
    tab_html += '<a class="ce-blizz" href="/wow/">Blizzard</a>'
    bar = f'<nav class="ce-ftabs" aria-label="Forum views">{tab_html}</nav>'
    if view != "categories":
        order = {
            "top": lambda item: (-int(item["replies"]), -int(item["last"])),
            "new": lambda item: -int(item["created"]),
            "unread": lambda item: -int(item["created"]),
            "latest": lambda item: -int(item["last"]),
        }[view]
        ranked = sorted(threads, key=order)
        import time

        body_rows = []
        for item in ranked:
            when = time.strftime("%Y-%m-%d %H:%M", time.gmtime(int(item["last"] or 0)))
            board_name = by_slug.get(item["board"]) or item["board"]
            if item["board"] == "realm":
                titled = forum_api.board_title(exp, "realm")
                if titled:
                    board_name = titled
            body_rows.append(
                "<tr>"
                f'<td><a href="/forums/{esc(item["board"])}/{int(item["id"])}">{esc(item["title"])}</a></td>'
                f'<td><a href="/forums/{esc(item["board"])}">{esc(board_name)}</a></td>'
                f'<td>{esc(item["author"])}</td>'
                f'<td>{esc(item["replies"])}</td>'
                f"<td>{esc(when)}</td>"
                "</tr>"
            )
        if not body_rows:
            body_rows.append('<tr class="ce-empty"><td colspan="5">No threads yet.</td></tr>')
        note = ""
        if view == "unread":
            note = '<p class="ce-desc">Every thread is listed. This board does not keep a read mark.</p>'
        return (
            bar
            + note
            + '<table class="ce-realms"><thead><tr>'
            "<th>Subject</th><th>Board</th><th>Author</th><th>Replies</th><th>Last Post</th>"
            f"</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
        )
    used: set[str] = set()
    community = _linked(by_slug, _COMMUNITY_LINKS, used)
    classic = _classic_block(by_slug, used)
    support = _linked(by_slug, _SUPPORT_LINKS, used)
    class_links = []
    for slug, title in boards:
        if slug in _CLASS_SLUGS and slug not in used:
            used.add(slug)
            class_links.append(_blink(f"/forums/{slug}", title, "swords"))
    leftover = []
    for slug, title in boards:
        if slug not in used:
            used.add(slug)
            leftover.append(_blink(f"/forums/{slug}", title, "shield"))
    cards = [
        _card(
            "helm",
            "Community",
            "Talk about general WoW topics and the community, and show off fan creations, events, and more.",
            community,
        ),
        _card(
            "swords",
            "Classes",
            "Class boards for World of Warcraft Classic.",
            "".join(class_links),
            "ce-classes",
        ),
        _card(
            "laurel",
            "WoW Classic",
            "Everything about World of Warcraft Classic belongs in these forums.",
            classic,
            klass="ce-classic",
        ),
        _card(
            "help",
            "Guides",
            "Walkthroughs and answers for World of Warcraft Classic.",
            _blink("/wow/info/", "Game Guide", "help")
            + _blink("/wow/info/basics", "Getting Started", "help")
            + _blink("/support/", "Support Articles", "help"),
        ),
        _card(
            "help",
            "Support",
            "Technical problems and realm status notes belong in these forums.",
            support,
        ),
    ]
    if leftover:
        cards.append(_card("shield", "Other", "The rest of the boards on this realm.", "".join(leftover)))
    return (
        '<div class="ce-shot ce-shot-forums">'
        + bar
        + f'<div class="ce-grid">{"".join(cards)}</div></div>'
    )


def _services_guest() -> str:
    return (
        '<section class="acct-ce"><h2>Account Management</h2>'
        "<p>Sign in to change a character name and use the other services on this realm.</p>"
        '<p><a href="/account/login">Log In</a></p></section>'
    )


def full(path: str, ctx: dict) -> str | None:
    _ = path, ctx
    return None


def take(path: str, ctx: dict) -> tuple[str, str] | None:
    if path == "/wow/realmstatus":
        return "Realm Status", _realm_body(ctx)
    if path == "/forums":
        return "All Categories", _forum_body(ctx)
    if path == "/account/services" and not ctx.get("user"):
        return "Character Services", _services_guest()
    return None
