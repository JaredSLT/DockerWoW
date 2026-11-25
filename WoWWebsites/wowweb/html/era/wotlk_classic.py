"""May 2022 Wrath of the Lich King Classic product site, not the 2010 community site."""

from __future__ import annotations

from urllib.parse import unquote

from .common import dev_note, document, esc, styles

_IMG = "/static/img/wotlk-classic"


_SUB = (
    ("/wow/", "Overview", "overview"),
    ("/story", "The Lich King", "lich"),
    ("/wow/info/features", "Features", "features"),
    ("/wow/info/basics", "Getting Started", "start"),
    ("/wow/media/screenshots", "Media", "media"),
)

_SHOP = (
    ("Level 70 Character Boost", True, True),
    ("Expert Riding Skill for Boosted Character", True, True),
    ("Appropriate Gear for the Boosted Character, a Mount, and Starting Gold", True, True),
    ("Pebble, a penguin pet", True, True),
    ("Fishspeaker's Lucky Lure, a toy to summon your very own tuskarr fishing companion", True, True),
    ("Kalu'ak Whalebone Glider, a flying mount for your Classic characters", False, True),
    ("Tuskarr Shoreglider, a flying mount for your Non-Classic Characters", False, True),
    ("30 Days of Game Time", False, True),
)

_REGIONS = ("Americas & Oceania", "Europe", "Korea", "Taiwan", "China")
_LOCALES = ("All", "United States", "Oceania", "Europe", "Korea")


def _q(qs: dict | None, key: str, default: str = "") -> str:
    if not qs:
        return default
    raw = qs.get(key)
    if isinstance(raw, list):
        return raw[0] if raw else default
    if raw is None:
        return default
    return str(raw)


def _kind(body: str) -> str:
    if 'class="wc-home"' in body:
        return "home"
    if 'class="wc-shop"' in body:
        return "shop"
    if 'class="wc-realms"' in body:
        return "realms"
    return "page"


def _current(crumb: str, title: str) -> str:
    crumb_l = (crumb or "").strip().lower()
    title_l = (title or "").strip().lower()
    blob = f"{crumb_l} {title_l}"
    if crumb_l in {"world of warcraft community site", "the lich king returns"} or title_l in {
        "world of warcraft community site",
        "the lich king returns",
    }:
        return "overview"
    if "lich king" in blob and "returns" not in blob:
        return "lich"
    if "feature" in blob:
        return "features"
    if "getting started" in blob or "new player" in blob:
        return "start"
    if any(word in blob for word in ("screenshot", "wallpaper", "media")):
        return "media"
    return ""


def _drop(summary: str, links: tuple[tuple[str, str], ...]) -> str:
    rows = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in links)
    return (
        f'<details class="wc-drop"><summary>{esc(summary)}</summary>'
        f'<div class="wc-drop-menu">{rows}</div></details>'
    )


def _account_slot(user: str | None) -> str:
    if user:
        return (
            '<details class="wc-drop wc-user">'
            f"<summary>{esc(user)}</summary>"
            '<div class="wc-drop-menu">'
            '<a href="/account/">Account</a>'
            '<a href="/account/services">Character Services</a>'
            '<a href="/account/logout">Log Out</a>'
            "</div></details>"
        )
    return '<a class="wc-login" href="/account/login">Log In</a>'


def _subnav(current: str) -> str:
    links = []
    for href, label, key in _SUB:
        mark = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{esc(href)}"{mark}>{esc(label)}</a>')
    return (
        '<div class="wc-sub">'
        '<a class="wc-brand" href="/wow/"><span class="wc-w">W</span><span class="wc-brand-sub">CLASSIC</span></a>'
        f'<nav class="wc-subnav" aria-label="Wrath of the Lich King Classic">{"".join(links)}</nav>'
        '<a class="wc-sub-cta" href="/shop">SUBSCRIBE NOW</a>'
        "</div>"
    )


def _chrome(user: str | None, current: str) -> str:
    games = _drop("GAMES", (("/wow/", "Wrath of the Lich King Classic"),))
    esports = _drop("ESPORTS", (("/esports", "Esports"), ("/wow/pvp/rankings", "Rankings")))
    return f"""<header class="wc-blizz">
  <a class="wc-logo" href="/wow/">BLIZZARD</a>
  <nav class="wc-blizz-nav" aria-label="Blizzard">
    {games}
    <a href="/shop">SHOP</a>
    <a href="/wow/news">NEWS</a>
    {esports}
  </nav>
  <div class="wc-blizz-right">
    <a href="/support/">Support</a>
    {_account_slot(user)}
  </div>
</header>
{_subnav(current)}"""


def _footer(exp) -> str:
    year = esc(getattr(exp, "year", "") or "2022")
    return f"""<footer class="wc-foot">
  <nav aria-label="Footer">
    <a href="/support/">Support</a>
    <a href="/wow/realmstatus">Realm Status</a>
    <a href="/forums/">Forums</a>
    <a href="/wow/news">News</a>
    <a href="/account/">Account</a>
  </nav>
  <p>©{year} Blizzard Entertainment, Inc. All rights reserved.</p>
</footer>"""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online, login_error
    kind = _kind(body)
    current = _current(crumb or "", title or "")
    if kind in {"home", "shop", "realms"}:
        content = body
    else:
        content = f'<main class="wc-panel"><h1>{esc(crumb or title)}</h1>{body}</main>'
    inner = f"""<div class="wc-site">
{_chrome(user, current)}
{content}
{_footer(exp)}
</div>"""
    shown = "The Lich King Returns" if kind == "home" else title
    return document(
        f"{shown} — World of Warcraft",
        styles(exp.id),
        f"era-wotlk-classic wc-kind-{kind}",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    _ = user
    name = (realm or {}).get("name") or getattr(exp, "realm_name", "") or "Wrath Classic"
    flag = "Up" if (realm or {}).get("up") else "Down"
    cards = []
    for index, item in enumerate(news or []):
        if index >= 4:
            break
        headline, when, _body = item
        cards.append(
            "<li>"
            f'<a href="/wow/news/{index}">{esc(headline)}</a>'
            f'<span class="wc-when">{esc(when)}</span>'
            "</li>"
        )
    band = ""
    if cards:
        band = (
            '<section class="wc-newsband">'
            "<h2>News</h2>"
            f'<ul>{"".join(cards)}</ul>'
            '<p><a href="/wow/news">All news</a></p>'
            "</section>"
        )
    return f"""<div class="wc-home">
  <img class="wc-hero-bg" src="{_IMG}/hero.jpg" alt="">
  <div class="wc-hero-copy">
    <p class="wc-wow">WORLD<br>OF<br>WARCRAFT</p>
    <p class="wc-wrath"><span>WRATH</span> <em>of the</em> <span>LICH KING</span></p>
    <p class="wc-classic-line"><span></span> CLASSIC <span></span></p>
    <h1>The Lich King Returns</h1>
    <p class="wc-tag">Play Burning Crusade Classic™ today and face the Lich King in 2022</p>
    <div class="wc-ctas">
      <a class="wc-btn" href="/shop">SUBSCRIBE NOW</a>
      <details class="wc-beta">
        <summary class="wc-btn">BETA OPT-IN</summary>
        <div class="wc-beta-menu">
          <a href="/account/">Account</a>
          <a href="/account/create">Create Account</a>
        </div>
      </details>
    </div>
    <p class="wc-avail">Available on Windows/Mac</p>
    <p class="wc-bnet">BATTLE.NET</p>
    <p class="wc-realmchip"><a href="/wow/realmstatus">{esc(name)} is {esc(flag)}</a></p>
  </div>
</div>
{band}"""


def _noref() -> str:
    return ""


def _tick(on: bool) -> str:
    if not on:
        return '<span class="wc-tick"></span>'
    return '<span class="wc-tick" aria-label="Included">✓</span>'


def _shop() -> str:
    rows = []
    for text, heroic, epic in _SHOP:
        rows.append(
            '<div class="wc-feature">'
            f"<p>{esc(text)}</p>"
            f"{_tick(heroic)}{_tick(epic)}"
            "</div>"
        )
    return f"""<main class="wc-shop">
  <div class="wc-compare">
    <div class="wc-offer-spacer"></div>
    <article class="wc-offer">
      <img src="{_IMG}/shop-heroic.jpg" alt="Northrend Heroic Upgrade">
      <h2>Northrend Heroic Upgrade</h2>
      <p class="wc-price">$49.99</p>
      <button type="button" class="wc-buy">Buy Now</button>
    </article>
    <article class="wc-offer">
      <img src="{_IMG}/shop-epic.jpg" alt="Northrend Epic Upgrade">
      <h2>Northrend Epic Upgrade</h2>
      <p class="wc-price">$79.99</p>
      <button type="button" class="wc-buy">Buy Now</button>
    </article>
    {"".join(rows)}
  </div>
  <p class="wc-shop-note">Nothing here is charged.</p>
</main>"""


def _population(value) -> str:
    text = "" if value is None else str(value).strip()
    labels = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "full": "Full",
        "new": "New Players",
        "new players": "New Players",
    }
    if text.lower() in labels:
        return labels[text.lower()]
    try:
        count = int(float(text))
    except ValueError:
        return text or "Low"
    if count < 80:
        return "Low"
    if count < 200:
        return "Medium"
    if count < 400:
        return "High"
    return "Full"


def _live_realm(exp, ctx: dict) -> dict:
    status = {
        "name": getattr(exp, "realm_name", "") or "Wrath Classic",
        "up": False,
        "population": "",
        "type": "",
        "timezone": "PST",
        "error": "",
    }
    labcfg = ctx.get("labcfg")
    if labcfg is None:
        return status
    from wowweb import lab

    live = lab.realm_status(labcfg, exp) or {}
    for key in ("name", "population", "type", "timezone"):
        if live.get(key) not in (None, ""):
            status[key] = live.get(key)
    status["up"] = bool(live.get("up"))
    if ctx.get("dev"):
        status["error"] = live.get("error") or ""
    return status


def _options(choices: tuple[str, ...], selected: str) -> str:
    bits = []
    for choice in choices:
        mark = " selected" if choice == selected else ""
        bits.append(f'<option value="{esc(choice)}"{mark}>{esc(choice)}</option>')
    return "".join(bits)


def _realm_page(ctx: dict) -> str:
    exp = ctx["exp"]
    qs = ctx.get("qs") or {}
    game = _q(qs, "game", "wotlk").strip().lower().replace(" ", "-")
    if game in {"wow", "retail", "world-of-warcraft"}:
        game = "retail"
    elif game in {"classic", "era", "vanilla", "wow-classic"}:
        game = "classic"
    else:
        game = "wotlk"
    region = _q(qs, "region", "Americas & Oceania") or "Americas & Oceania"
    if region not in _REGIONS:
        region = "Americas & Oceania"
    locale = _q(qs, "locale", "All") or "All"
    if locale not in _LOCALES:
        locale = "All"
    query = _q(qs, "q", "").strip()
    tabs = (
        ("retail", "World of Warcraft"),
        ("classic", "World of Warcraft Classic"),
        ("wotlk", "Wrath of the Lich King Classic"),
    )
    tab_html = []
    for key, label in tabs:
        mark = ' class="wc-tab is-on" aria-current="page"' if key == game else ' class="wc-tab"'
        tab_html.append(f'<a href="/wow/realmstatus?game={key}"{mark}>{esc(label)}</a>')
    row = ""
    note = ""
    dev_line = ""
    if game != "wotlk":
        note = (
            "<p class=\"wc-realm-empty\">This tab is not the Wrath of the Lich King Classic list. "
            "This page lists that realm.</p>"
        )
    else:
        live = _live_realm(exp, ctx)
        name = str(live.get("name") or "")
        matched = True
        if region != "Americas & Oceania":
            matched = False
        if locale not in {"All", "United States"}:
            matched = False
        if query and query.lower() not in name.lower():
            matched = False
        if matched:
            flag = "Up" if live.get("up") else "Down"
            mark = "✓" if live.get("up") else "✕"
            state = "wc-up" if live.get("up") else "wc-down"
            kind = live.get("type") or "Normal"
            dev_line = ""
            if ctx.get("dev") and live.get("error"):
                dev_line = f'<p class="wc-realm-dev">{esc(live.get("error"))}</p>'
            row = (
                "<tr>"
                f'<td><span class="{state}" aria-label="{flag}">{mark}</span></td>'
                f"<td>{esc(name)}</td>"
                f"<td>{esc(kind)}</td>"
                f"<td>{esc(_population(live.get('population')))}</td>"
                f"<td>{esc(live.get('timezone') or 'PST')}</td>"
                "<td>United States</td>"
                "</tr>"
            )
        else:
            note = '<p class="wc-realm-empty">No realms match.</p>'
    return f"""<main class="wc-realms">
  <h1>Realm Status</h1>
  <p class="wc-realm-lead">This page lists all available World of Warcraft realms and has information on whether or not a realm is up or down. You can find more information about realm status and scheduled maintenances in the <a href="/forums/realm">Service Status Forum</a>. If your realm is listed as down, rest assured that we're aware of it and working diligently to bring it back online as quickly as possible.</p>
  <div class="wc-realm-bar">
    <nav class="wc-tabs" aria-label="Game">{"".join(tab_html)}</nav>
    <form class="wc-filters" method="get" action="/wow/realmstatus">
      <input type="hidden" name="game" value="{esc(game)}">
      <label>Region <select name="region">{_options(_REGIONS, region)}</select></label>
      <label>Locale <select name="locale">{_options(_LOCALES, locale)}</select></label>
      <label>Search <span class="wc-search"><input name="q" value="{esc(query)}" placeholder="Realm Name" aria-label="Realm Name"><button type="submit">Search</button></span></label>
    </form>
  </div>
  <table class="wc-realm-table">
    <thead>
      <tr>
        <th>Status</th>
        <th>Realm Name</th>
        <th>Type</th>
        <th>Population</th>
        <th>Timezone</th>
        <th>Locale</th>
      </tr>
    </thead>
    <tbody>{row}</tbody>
  </table>
  {note}
  {dev_line}
</main>"""


def _news_index(ctx: dict) -> str:
    from wowweb import content

    items = []
    for index, (headline, when, _body) in enumerate(content.news_for(ctx["exp"])):
        items.append(
            "<li>"
            f'<a href="/wow/news/{index}">{esc(headline)}</a>'
            f'<span class="wc-when">{esc(when)}</span>'
            "</li>"
        )
    listing = "".join(items) or "<li>No stories yet.</li>"
    return f"""{_noref()}
<ul class="wc-newslist">{listing}</ul>"""


def _news_article(path: str, ctx: dict):
    from wowweb import content

    try:
        index = int(path.rsplit("/", 1)[-1])
        headline, when, body = content.news_for(ctx["exp"])[index]
    except (ValueError, IndexError):
        return None
    return headline, f"""{_noref()}
<p class="wc-when">{esc(when)}</p>
<p>{esc(body)}</p>
<p><a href="/wow/news">All news</a></p>"""


def _guide(ctx: dict) -> str:
    from wowweb import content, talents

    exp = ctx["exp"]
    points = talents.points_available(exp)
    races = []
    for slug in content.races_for(exp):
        info = content.RACE_INFO.get(slug)
        if not info:
            continue
        races.append(
            f'<li><a href="/wow/info/races/{esc(slug)}">{esc(info[0])}</a>'
            f'<span>{esc(info[1])}</span></li>'
        )
    classes = []
    for slug in content.classes_for(exp):
        info = content.CLASS_INFO.get(slug)
        if not info:
            continue
        trees = talents.trees_for(exp, slug) or ()
        tree_names = ", ".join(tree.name for tree in trees)
        classes.append(
            "<li>"
            f'<a href="/wow/info/classes/{esc(slug)}">{esc(info[0])}</a>'
            f'<span>{esc(tree_names)}</span>'
            f'<a href="/wow/info/classes/{esc(slug)}/talents.html">Talents</a>'
            "</li>"
        )
    return f"""{_noref()}
<p class="wc-lead">Wrath of the Lich King Classic brings Northrend to the Classic client. Talent calculators on this site spend {esc(points)} points.</p>
<div class="wc-guide">
  <section><h2>Races</h2><ul class="wc-cards">{"".join(races)}</ul></section>
  <section><h2>Classes</h2><ul class="wc-cards">{"".join(classes)}</ul></section>
</div>
<p><a href="/wow/info/features">Features</a> · <a href="/wow/info/basics">Getting Started</a> · <a href="/wow/info/professions">Professions</a></p>"""


def _features(ctx: dict) -> str:
    from wowweb import content

    items = "".join(f"<li>{esc(line)}</li>" for line in content.features_for(ctx["exp"]))
    return f"""<p class="wc-lead">What comes with Wrath of the Lich King Classic.</p>
<ul class="wc-cards">{items}</ul>
<p><a href="/story">The Lich King</a> · <a href="/wow/info">Game Guide</a></p>"""


def _started(ctx: dict) -> str:
    from wowweb import talents

    points = talents.points_available(ctx["exp"])
    return f"""<ol class="wc-steps">
  <li><a href="/account/create">Create an account</a> and sign in.</li>
  <li><a href="/shop">Subscribe</a> for Northrend Heroic or Northrend Epic, or use Beta Opt-in on the account page.</li>
  <li>Check <a href="/wow/realmstatus">realm status</a> before you log in.</li>
  <li>Read the <a href="/wow/info">game guide</a> and spend {esc(points)} talent points in the <a href="/wow/info/classes/">calculators</a>.</li>
</ol>"""


def _lich() -> str:
    return """<p class="wc-lead">The Lich King sits the Frozen Throne. In 2022, Classic sails north.</p>
<p>Arthas Menethil took Frostmourne, raised a kingdom of the dead, and waited in Icecrown. Wrath of the Lich King Classic is that war on the Classic client: ships in Borean Tundra and Howling Fjord, death knights out of Acherus, and the long road through Dragonblight to the Citadel.</p>
<p>Play Burning Crusade Classic now. Northrend opens when the Lich King returns.</p>
<p><a href="/wow/info/features">Features</a> · <a href="/wow/info/basics">Getting Started</a> · <a href="/shop">Subscribe</a></p>"""


def _media(ctx: dict) -> str:
    from wowweb import assets

    shots = assets.screenshots(ctx["exp"].id)
    if not shots:
        return "<p>No screenshots are in the gallery yet.</p>"
    cards = []
    for url, caption in shots:
        cards.append(
            f'<a class="wc-shot" href="{esc(url)}"><img src="{esc(url)}" alt="{esc(caption)}"><span>{esc(caption)}</span></a>'
        )
    return f'<div class="wc-shots">{"".join(cards)}</div>'


def _boards(exp):
    from wowweb import forums

    return forums.boards_for(exp)


def _forum_index(ctx: dict) -> str:
    links = []
    for slug, title in _boards(ctx["exp"]):
        links.append(f'<li><a href="/forums/{esc(slug)}">{esc(title)}</a></li>')
    return f"""{_noref()}
<p class="wc-lead">Boards for Wrath of the Lich King Classic. Read without an account. Posting needs a sign-in.</p>
<ul class="wc-boards">{"".join(links)}</ul>"""


def _thread_rows(slug: str, threads: list[dict], page: int) -> tuple[str, str]:
    from datetime import UTC, datetime

    size = 20
    pages = max(1, (len(threads) + size - 1) // size)
    page_n = min(max(page, 1), pages)
    start = (page_n - 1) * size
    rows = []
    for thread in threads[start : start + size]:
        last = thread.get("last") or thread.get("created") or 0
        try:
            when = datetime.fromtimestamp(int(last), UTC).strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError, OSError):
            when = ""
        rows.append(
            "<tr>"
            f'<td><a href="/forums/{esc(slug)}/{esc(thread.get("id"))}">{esc(thread.get("title"))}</a></td>'
            f'<td>{esc(thread.get("author"))}</td>'
            f'<td>{esc(thread.get("replies"))}</td>'
            f'<td>{esc(when)}</td>'
            "</tr>"
        )
    body = "".join(rows) or '<tr><td colspan="4">No threads yet.</td></tr>'
    pager = ""
    if pages > 1:
        links = "".join(f'<a href="?page={number}">{number}</a>' for number in range(1, pages + 1))
        pager = f'<nav class="wc-pager" aria-label="Pages">{links}</nav>'
    return body, pager


def _post_form(slug: str, user: str | None) -> str:
    if not user:
        return '<p><a href="/account/login">Log in</a> to post.</p>'
    return f"""<form class="acct-form" method="post" action="/forums/{esc(slug)}/new">
  <label>Title <input name="title" required maxlength="120"></label>
  <label>Body <textarea name="body" required rows="6"></textarea></label>
  <button type="submit">Post</button>
</form>"""


def _forum_board(ctx: dict, slug: str, title: str):
    from wowweb import forums

    threads: list[dict] = []
    data_dir = ctx.get("data_dir")
    if data_dir is not None:
        conn = forums.connect(data_dir)
        try:
            forums.seed_if_empty(conn, ctx["exp"])
            threads = forums.list_threads(conn, ctx["exp"], slug)
        finally:
            conn.close()
    try:
        page = int(_q(ctx.get("qs"), "page", "1") or "1")
    except ValueError:
        page = 1
    rows, pager = _thread_rows(slug, threads, page)
    body = f"""{_noref()}
<p><a href="/forums/">All boards</a></p>
<table class="wc-threads">
  <thead><tr><th>Subject</th><th>Author</th><th>Replies</th><th>Last Post</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
{pager}
{_post_form(slug, ctx.get("user"))}"""
    return title, body


def _forum_thread(ctx: dict, slug: str, tid: int):
    from datetime import UTC, datetime

    from wowweb import forums

    data_dir = ctx.get("data_dir")
    if data_dir is None:
        return None
    conn = forums.connect(data_dir)
    try:
        thread = forums.get_thread(conn, ctx["exp"], tid)
    finally:
        conn.close()
    if not thread:
        return None
    posts = []
    for post in thread.get("posts") or []:
        try:
            when = datetime.fromtimestamp(int(post.get("created") or 0), UTC).strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError, OSError):
            when = ""
        posts.append(
            "<article class=\"wc-post\">"
            f"<header>{esc(post.get('author'))} · {esc(when)}</header>"
            f"<pre>{esc(post.get('body'))}</pre>"
            "</article>"
        )
    form = ""
    user = ctx.get("user")
    if user:
        form = f"""<form class="acct-form" method="post" action="/forums/{esc(slug)}/{int(tid)}/reply">
  <label>Reply <textarea name="body" required rows="5"></textarea></label>
  <button type="submit">Reply</button>
</form>"""
    else:
        form = '<p><a href="/account/login">Log in</a> to reply.</p>'
    body = f"""{_noref()}
<p><a href="/forums/{esc(slug)}">Back to board</a></p>
{"".join(posts)}
{form}"""
    return thread.get("title") or "Thread", body


def _profile(path: str, ctx: dict):
    name = unquote(path.rsplit("/", 1)[-1]).strip()
    if not name:
        return None
    labcfg = ctx.get("labcfg")
    if labcfg is None:
        return name, f"""{_noref()}
<p>No character sheet for {esc(name)} until the realm can be read.</p>"""
    from wowweb import armory

    char = armory.get_character(labcfg, ctx["exp"], name)
    if not char:
        return None
    guild = char.get("guild") or {}
    if guild.get("name"):
        guild_html = (
            f'<p>Guild <a href="/armory/guild/{esc(guild.get("name"))}">{esc(guild.get("name"))}</a></p>'
        )
    else:
        guild_html = "<p>No guild</p>"
    gear = []
    for item in char.get("equipment") or []:
        if not item.get("item_id"):
            continue
        label = item.get("name") or f"Item {item.get('item_id')}"
        gear.append(
            "<li>"
            f'<span>{esc(item.get("slot"))}</span>'
            f'<a href="/armory/item/{esc(item.get("item_id"))}">{esc(label)}</a>'
            "</li>"
        )
    gear_html = "".join(gear) or "<li>No equipment recorded.</li>"
    state = "Online" if char.get("online") else "Offline"
    body = f"""{_noref()}
<p class="wc-lead">Level {esc(char.get("level"))} {esc(char.get("race"))} {esc(char.get("class"))}</p>
<p>{esc(state)} · {esc(char.get("realm"))}</p>
{guild_html}
<p>Achievements: {esc(char.get("achievements") or 0)}</p>
<p>{esc(char.get("money_text") or "")}</p>
<ul class="wc-gear">{gear_html}</ul>"""
    return char.get("name") or name, body


def _services_gate() -> str:
    return f"""{_noref()}
<p class="wc-lead">Sign in to change a name, an appearance, a race, or a faction.</p>
<p><a href="/account/login">Log In</a> · <a href="/account/create">Create Account</a></p>"""


def full(path: str, ctx: dict) -> str | None:
    _ = path, ctx
    return None


def take(path: str, ctx: dict):
    if path == "/shop":
        return "Shop", _shop()
    if path == "/wow/realmstatus":
        return "Realm Status", _realm_page(ctx)
    if path == "/wow/news":
        return "News", _news_index(ctx)
    if path.startswith("/wow/news/"):
        return _news_article(path, ctx)
    if path in {"/wow/info", "/wow/info/introduction"}:
        return "Game Guide", _guide(ctx)
    if path == "/wow/info/features":
        return "Features", _features(ctx)
    if path in {"/wow/info/basics", "/wow/info/beginners"}:
        return "Getting Started", _started(ctx)
    if path == "/story":
        return "The Lich King", _lich()
    if path == "/wow/media/screenshots":
        return "Media", _media(ctx)
    if path == "/forums":
        return "Forums", _forum_index(ctx)
    if path.startswith("/forums/"):
        parts = [part for part in path.split("/") if part]
        if len(parts) == 2:
            from wowweb import forums

            title = forums.board_title(ctx["exp"], parts[1])
            if not title:
                return None
            return _forum_board(ctx, parts[1], title)
        if len(parts) == 3 and parts[2].isdigit():
            from wowweb import forums

            if not forums.board_title(ctx["exp"], parts[1]):
                return None
            return _forum_thread(ctx, parts[1], int(parts[2]))
        return None
    if path.startswith("/armory/character/"):
        return _profile(path, ctx)
    if path == "/account/services" and not ctx.get("user"):
        return "Character Services", _services_gate()
    return None
