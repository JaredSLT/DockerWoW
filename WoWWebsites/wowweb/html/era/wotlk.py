"""March 2010 community site, plus the Armory, forums, and expansion splash.

The community shell is the sharp March 2010 home. Forums, the Armory, the
Battle.net account, and the 2008 product splash are their own documents.
"""

from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import quote, unquote

from .common import dev_note, document, esc, styles

_PAGE = 20

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
    "druid",
    "monk",
    "demonhunter",
    "evoker",
}

_ALLIANCE = {"Human", "Dwarf", "Night Elf", "Gnome", "Draenei"}
_HORDE = {"Orc", "Undead", "Tauren", "Troll", "Blood Elf"}

_CLASS_COLOR = {
    "Warrior": "#c69b6d",
    "Paladin": "#f48cba",
    "Hunter": "#aad372",
    "Rogue": "#fff468",
    "Priest": "#ffffff",
    "Death Knight": "#c41e3a",
    "Shaman": "#0070dd",
    "Mage": "#3fc7eb",
    "Warlock": "#8788ee",
    "Druid": "#ff7c0a",
}

_LEFT_SLOTS = ("Head", "Neck", "Shoulders", "Back", "Chest", "Shirt", "Tabard", "Wrists")
_RIGHT_SLOTS = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEAPON_SLOTS = ("Main Hand", "Off Hand", "Ranged")

_BASE_STATS = ("Strength", "Agility", "Stamina", "Intellect", "Spirit", "Armor")
_MELEE_STATS = ("Damage", "Speed", "Power", "Hit Rating", "Crit", "Expertise")
_RANGED_STATS = ("Damage", "Speed", "Power", "Hit Rating", "Crit")
_SPELL_STATS = ("Power", "Hit Rating", "Crit", "Haste", "Mana Regen")
_DEF_STATS = ("Armor", "Defense", "Dodge", "Parry", "Block", "Resilience")
_RES_STATS = ("Arcane", "Fire", "Nature", "Frost", "Shadow")


def _mdy(iso: str) -> str:
    parts = (iso or "").split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = parts
        return f"{int(month)}-{int(day)}-{year[2:]}"
    return iso or ""


def _stamp(value) -> str:
    try:
        when = datetime.fromtimestamp(int(value or 0), UTC)
    except (TypeError, ValueError, OSError):
        return ""
    return when.strftime("%m/%d/%y")


def _class_slug(name: str) -> str:
    return (name or "").lower().replace(" ", "").replace("-", "")


def _faction(race: str) -> str:
    if race in _HORDE:
        return "Horde"
    if race in _ALLIANCE:
        return "Alliance"
    return "—"


def _safe_store(message: str) -> str:
    text = message or ""
    low = text.lower()
    if "mariadb" in low or "mysql" in low or "private server" in low:
        return "The realm database is not reachable."
    return text


def _up(realm) -> tuple[str, str]:
    if not isinstance(realm, dict):
        return "Down", ""
    flag = "Up" if realm.get("up") else "Down"
    name = realm.get("name") or ""
    return flag, name


def _sec(key: str, label: str, links, open_: bool) -> str:
    opened = " open" if open_ else ""
    rows = "".join(f'<a href="{esc(href)}">{esc(text)}</a>' for href, text in links)
    return (
        f'<details class="wlk-sec wlk-sec-{key}"{opened}>'
        f"<summary><span>{esc(label)}</span><i></i></summary>"
        f'<div class="wlk-sub">{rows}</div></details>'
    )


def _menu() -> str:
    news = (
        ("/wow/", "Current News"),
        ("/wow/news", "Archived News"),
    )
    account = (
        ("/account/create", "Create Account"),
        ("/account/", "Manage Account"),
        ("/account/services", "Character Services"),
        ("/account/retrieve", "Retrieve Password"),
        ("/wow/realmstatus", "Realm Status"),
        ("/bnet", "Battle.net"),
    )
    guide = (
        ("/wow/info/", "Game Guide"),
        ("/wow/info/introduction", "Introduction"),
        ("/wow/info/basics", "Getting Started"),
        ("/wow/info/races", "Character"),
        ("/wow/info/", "Reputations"),
        ("/wow/info/", "Items"),
        ("/wow/info/basics/map", "The World"),
        ("/wow/info/", "Transportation"),
        ("/wow/info/", "Player Interaction"),
        ("/wow/pvp/rankings", "Player vs Player"),
        ("/support/", "FAQ"),
        ("/story", "Story"),
        ("/wow/news", "Cataclysm"),
        ("/wrath", "Wrath of Lich King"),
        ("/wow/info/", "Burning Crusade"),
        ("/wow/info/patches", "Under Development"),
        ("/wow/info/patches", "Previous Patches"),
    )
    workshop = (
        ("/armory/", "Armory"),
        ("/armory/arena", "Arena"),
        ("/wow/info/classes/", "Talent Calculators"),
        ("/wow/info/", "Events Calendar"),
        ("/wow/info/", "Armor Sets"),
        ("/wow/info/basics/map", "Maps"),
        ("/wow/pvp/rankings", "Battlegroups"),
        ("/wow/pvp/rankings", "Toplist"),
    )
    media = (
        ("/wow/media/screenshots", "Screenshots"),
        ("/wow/media/wallpapers", "Wallpapers"),
        ("/wow/media/screenshots", "Movies"),
    )
    forums = (
        ("/forums/", "Index"),
        ("/forums/", "Blizz Tracker"),
        ("/forums/general", "General"),
    )
    community = (
        ("/wow/", "Overview"),
        ("/wow/news", "Contests"),
        ("/forums/", "Forums"),
    )
    support = (
        ("/support/", "Customer Support"),
        ("/wow/realmstatus", "Realm Status"),
    )
    return (
        _sec("news", "News", news, False)
        + _sec("account", "Account", account, False)
        + _sec("guide", "Game Guide", guide, True)
        + _sec("workshop", "Workshop", workshop, True)
        + _sec("media", "Media", media, False)
        + _sec("forums", "Forums", forums, True)
        + _sec("community", "Community", community, False)
        + _sec("support", "Support", support, False)
    )


def _who(user: str | None) -> str:
    if not user:
        return ""
    return (
        f'<span class="wlk-who">Signed in as <strong>{esc(user)}</strong>'
        f' · <a href="/account/">Account</a>'
        f' · <a href="/account/logout">Log Out</a></span>'
    )


def _tools(user: str | None) -> str:
    return f"""<div class="wlk-tools">
      <form class="wlk-search" action="/wow/search" method="get">
        <input type="search" name="q" placeholder="Search World of Warcraft" aria-label="Search World of Warcraft">
        <button type="submit">Search</button>
      </form>
      <span class="wlk-lang">English (USA)</span>
      {_who(user)}
    </div>"""


def _rail() -> str:
    return """<aside class="wlk-rail">
  <a class="ad ad-trial" href="/account/create"><img src="/static/img/wotlk/ad-trial.jpg" alt="10 Day Free Trial"></a>
  <a class="ad ad-gift" href="/shop"><img src="/static/img/wotlk/ad-gift.jpg" alt="Gift World of Warcraft"></a>
  <a class="ad ad-cata" href="/wow/news"><img src="/static/img/wotlk/ad-cata.jpg" alt="World of Warcraft Cataclysm"></a>
  <a class="ad ad-raf" href="/account/create"><img src="/static/img/wotlk/ad-raf.jpg" alt="Recluta a un amigo"></a>
  <div class="ql">
    <h3>Quicklinks</h3>
    <a href="/account/">Account Management</a>
    <a href="/account/retrieve">Retrieve Password</a>
    <a href="/wow/realmstatus">Realm Status</a>
    <a href="/account/create">Account Creation</a>
  </div>
</aside>"""


def _community(exp, title, body, user, crumb, dev, extra_js) -> str:
    home = "wlk-home" in body
    banner = "" if home else f'<h1 class="wlk-banner">{esc(crumb or title)}</h1>'
    inner = f"""<div class="wlk-top"><div class="wlk-top-inner">
  <a href="/wow/">WorldofWarcraft.com</a>
  <span>|</span>
  <a href="/armory/">The Armory</a>
  <span>|</span>
  <a href="/forums/">Forums</a>
</div></div>
<div class="wlk">
  <div class="wlk-chain">
    <a class="wlk-logo" href="/wow/"><img src="/static/img/wotlk/logo.jpg" alt="World of Warcraft Wrath of the Lich King"></a>
    {_tools(user)}
  </div>
  <div class="wlk-cols">
    <nav class="wlk-menu" aria-label="Community">{_menu()}</nav>
    <div class="wlk-center"><div class="wlk-parch">{banner}{body}</div></div>
    {_rail()}
  </div>
  <p class="wlk-legal">©2010 Blizzard Entertainment. All rights reserved.</p>
</div>"""
    return document(
        f"{title} — World of Warcraft",
        styles("wotlk"),
        "era-wotlk",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _signup_doc(exp, title, body, dev, extra_js) -> str:
    inner = f"""<div class="su-page">
  <div class="su-sheet">
    <p class="su-mark">World of Warcraft</p>
    {body}
  </div>
  <p class="su-legal">©2009 Blizzard Entertainment. All rights reserved.</p>
</div>"""
    return document(
        f"{title} — World of Warcraft",
        styles("wotlk"),
        "era-wotlk era-wotlk-signup",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _account_doc(exp, title, body, user, dev, extra_js) -> str:
    if user:
        welcome = (
            f'<p class="bn-welcome">Welcome, {esc(user)}</p>'
            f'<p class="bn-lang"><a href="/account/logout">Log Out</a></p>'
        )
    else:
        welcome = '<p class="bn-lang">Language: English (US)</p>'
    inner = f"""<div class="bn">
  <header class="bn-bar">
    <a class="bn-logo" href="/bnet"><img src="/static/img/wotlk/bnet-sky.jpg" alt="Battle.net"></a>
    <div class="bn-user">{welcome}</div>
  </header>
  <div class="bn-panel">{body}</div>
  <footer class="bn-foot">
    <a href="/bnet">What is the Battle.net Account?</a>
    <a href="/account/retrieve">Password Retrieval</a>
    <a href="/support/">Support Site</a>
    <a href="/wow/">World of Warcraft</a>
    <a href="/forums/">Forums</a>
    <p>©2009 Blizzard Entertainment, Inc. All rights reserved.</p>
  </footer>
</div>"""
    return document(
        f"{title} — Battle.net",
        styles("wotlk"),
        "era-wotlk era-wotlk-account",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online, login_error
    if "acct-mode-create" in body:
        return _signup_doc(exp, title, body, dev, extra_js)
    if "acct-wotlk" in body:
        return _account_doc(exp, title, body, user, dev, extra_js)
    return _community(exp, title, body, user, crumb, dev, extra_js)


def home_body(exp, news, realm, user) -> str:
    _ = user
    from wowweb.content.news import news_for

    stories = list(news) if news else news_for(exp)
    flag, name = _up(realm)
    realm_name = name or getattr(exp, "realm_name", "")
    rows = []
    for index, (title, date, _body) in enumerate(stories):
        rows.append(
            f'<li><span>{esc(_mdy(date))}</span> '
            f'<a href="/wow/news/{index}">{esc(title)}</a></li>'
        )
    more = "".join(rows)
    return f"""<div class="wlk-home">
  <div class="wlk-hero">
    <a class="slide-gift" href="/shop">
      <img src="/static/img/wotlk/hero-gift.jpg" alt="Gift World of Warcraft">
      <span class="off">Gift World of Warcraft</span>
    </a>
    <a class="slide-fall" href="/wrath"><span class="off">Fall of the Lich King</span></a>
  </div>
  <div class="wlk-poll" aria-hidden="true">
    <span class="bar"><span>100%</span></span>
    <span class="poll-name">BattleCry</span>
  </div>
  <article class="wlk-story">
    <h2>PrintWarcraft.com Custom Poster Contest Week Three</h2>
    <p class="by">Posted by: Nebu | 3-5-10</p>
    <p>Week three of the PrintWarcraft.com custom poster contest has come to an end, and after thousands of entries, we've chosen our third winner, Severedsoul of Spinebreaker. Be sure to check out the week three winner's entry, as well as some other great entries <a href="/wow/news">here</a> in the gallery.</p>
    <p>Week four has just concluded, and we will announce the next round of winners out soon. This week we'll be choosing one entry each as our grand prize, second place, and third place winners for even more prizes. Find out more on our <a href="/wow/news">contest page</a>.</p>
  </article>
  <section class="wlk-more">
    <h3>Current News</h3>
    <ul>{more}</ul>
    <p class="wlk-realm">Realm {esc(realm_name)} is {esc(flag)}.</p>
  </section>
</div>"""


def _news_page(exp) -> tuple[str, str]:
    from wowweb.content.news import news_for

    rows = []
    for index, (title, date, body) in enumerate(news_for(exp)):
        rows.append(
            "<tr>"
            f"<td>{esc(_mdy(date))}</td>"
            f"<td><a href=\"/wow/news/{index}\">{esc(title)}</a><p>{esc(body)}</p></td>"
            "</tr>"
        )
    html = (
        "<table class=\"grid news\">"
        "<thead><tr><th>Date</th><th>News</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )
    return "Archived News", html


def _news_story(exp, path: str):
    from wowweb.content.news import news_for

    tail = path.rsplit("/", 1)[-1]
    if not tail.isdigit():
        return None
    stories = news_for(exp)
    index = int(tail)
    if index < 0 or index >= len(stories):
        return None
    title, date, body = stories[index]
    html = (
        f'<article class="wlk-article"><p class="by">{esc(_mdy(date))}</p>'
        f"<h2>{esc(title)}</h2><p>{esc(body)}</p>"
        '<p><a href="/wow/news">Archived News</a></p></article>'
    )
    return title, html


def _realm_page(exp, cfg) -> tuple[str, str]:
    from wowweb.lab import realm_status

    status = realm_status(cfg, exp) if cfg is not None else {"up": False, "name": exp.realm_name}
    flag, name = _up(status)
    realm_name = name or exp.realm_name
    unread = bool(status.get("error")) and not status.get("type") and not status.get("population")
    note = ""
    if unread:
        note = "<p>The realm database is not reachable. Status is the world port only.</p>"
    type_cell = status.get("type") or "—"
    pop = status.get("population")
    pop_cell = pop if pop not in (None, "") else "—"
    html = (
        "<h2>Realm Status</h2>"
        f"<p>Realm status for {esc(exp.name)}.</p>"
        f"{note}"
        "<table class=\"grid\">"
        "<tr><th>Realm</th><th>Type</th><th>Population</th><th>Status</th></tr>"
        f"<tr><td>{esc(realm_name)}</td><td>{esc(type_cell)}</td>"
        f"<td>{esc(pop_cell)}</td><td class=\"{flag.lower()}\">{esc(flag)}</td></tr>"
        "</table>"
        '<p>Messages about a realm belong on the <a href="/forums/realm">Realm Forum</a>.</p>'
    )
    return "Realm Status", html


def take(path: str, ctx: dict):
    exp = ctx["exp"]
    if path == "/wow/news":
        return _news_page(exp)
    if path.startswith("/wow/news/"):
        return _news_story(exp, path)
    if path == "/wow/realmstatus":
        return _realm_page(exp, ctx.get("labcfg"))
    if path == "/account/services" and not ctx.get("user"):
        body = (
            "<h2>Character Services</h2>"
            "<p>Log in to use character services on this account. These services are free. "
            "Log out of the game before you use one.</p>"
            '<p><a href="/account/login">Log In</a></p>'
        )
        return "Character Services", body
    return None


def _top_links(forum: bool = False) -> str:
    home = "WoW-Europe.com" if forum else "WorldofWarcraft.com"
    armory = "Armory" if forum else "The Armory"
    store = '<a href="/shop">Blizzard Store</a>' if forum else ""
    return (
        '<nav class="site-links">'
        f'<a href="/wow/">{home}</a>'
        f'<a href="/armory/">{armory}</a>'
        '<a href="/forums/">Forums</a>'
        f"{store}</nav>"
    )


def _forum_index(exp) -> str:
    from wowweb import forums

    boards = forums.boards_for(exp)
    by_slug = {slug: title for slug, title in boards}
    left = (
        ("/armory/arena", "Arena Pass", "Discuss all aspects of the Arena Pass with your fellow players."),
        ("/support/", "In-Game Customer Support", "GM moderated forum to discuss in-game issues."),
        ("/forums/", "Website and Forums", "Discussions, suggestions and error reports for the forums and website."),
        ("/wow/news", "Cataclysm", "With new Goblin and Worgen allies at your side. Cataclysm is still upcoming."),
        ("/story", "Warcraft Story", "We invite you to discuss the Warcraft Universe and storylines of Azeroth here."),
        ("/forums/quests", by_slug.get("quests", "Quests"), "Talk about and get help with the countless quests in World of Warcraft."),
        ("/forums/ui", by_slug.get("ui", "Interface and Macros"), "Work with other players to create your own custom interface and macros."),
        ("/forums/dungeons", by_slug.get("dungeons", "Raid & Dungeons"), "Share your victories and discuss tactics, encounters and group composition."),
        ("/forums/guilds", by_slug.get("guilds", "Guild Management"), "Step in and share ideas and experiences on in-guild and inter-guild relationships."),
        ("/forums/guilds", "Looking for Alliance players", "If you are looking for a guild, guild members or leveling partners among the Alliance."),
        ("/forums/general", "Suggestions", "Have a suggestion for World of Warcraft?"),
        ("/shop", "Trading Card Game", "Discuss the World of Warcraft Trading Card Game."),
        ("/wow/news", "Diablo III", "Discuss Blizzard's upcoming Action RPG title, Diablo III."),
    )
    right = (
        ("/wow/news", "Blizzard Archive", "A collection of important messages and announcements, including the extended forum guidelines."),
        ("/support/", "Technical Support", "If you're experiencing technical problems playing World of Warcraft, post here for assistance."),
        ("/wow/info/basics", "Newcomers", "Newcomers of all levels are welcomed with their questions."),
        ("/forums/general", by_slug.get("general", "General Discussion"), "The place for World of Warcraft discussions that don't fit into any other forum."),
        ("/forums/professions", by_slug.get("professions", "Professions"), "The place for discussions, as well as hints and tips, about gathering and crafting."),
        ("/armory/", "Achievements", "Discussion forum for the many World of Warcraft Achievements."),
        ("/forums/pvp", by_slug.get("pvp", "Player vs. Player"), "Discuss Player versus Player mechanics and tactics."),
        ("/forums/general", "Roleplaying", "Pull up a chair, drink a mug of ale, meet new friends, tell stories, and role-play in this forum."),
        ("/wow/news", "Events and Fan Creations", "Promote, share and read about in-game and out-of-game events and creations."),
        ("/forums/guilds", "Looking for Horde players", "If you are looking for a guild, guild members or leveling partners among the Horde."),
        ("/wow/info/patches", "Public Test Realm", "Participate in the testing of upcoming changes and features."),
        ("/forums/general", "Off-Topic", "Off-topic posts of interest to the World of Warcraft community."),
        ("/wow/news", "BlizzCon", "The BlizzCon discussion forum."),
    )

    def cell(href: str, title: str, blurb: str) -> str:
        return (
            f'<a class="fi-board" href="{esc(href)}">'
            f"<strong>{esc(title)}</strong><span>{esc(blurb)}</span></a>"
        )

    classes = [(slug, title) for slug, title in boards if slug in _CLASS_SLUGS]
    class_rows = "".join(
        f'<a href="/forums/{esc(slug)}">{esc(title)}</a>' for slug, title in classes
    )
    linked = {slug for slug, _title in classes}
    linked.update({"general", "pvp", "quests", "dungeons", "professions", "ui", "guilds", "realm", "bugs"})
    extra = "".join(
        f'<a href="/forums/{esc(slug)}">{esc(title)}</a>'
        for slug, title in boards
        if slug not in linked
    )
    extra_block = f'<div class="fi-extra">{extra}</div>' if extra else ""
    realm_title = by_slug.get("realm", "Realm Forum")
    return f"""<div class="fi">
  {_top_links(forum=True)}
  <header class="fi-logo">
    <a href="/wow/"><img src="/static/img/wotlk/forums-logo.jpg" alt="World of Warcraft Wrath of the Lich King"></a>
  </header>
  <p class="fi-lang">Select Language: World of Warcraft (en)</p>
  <div class="fi-sheet">
    <div class="fi-intro">
      <div>
        <h1>Forums Index</h1>
        <p class="fi-welcome">Welcome to the official World of Warcraft forums!</p>
        <p class="fi-lead">Blizzard provides the World of Warcraft community forums for its players to chat, exchange ideas, and submit feedback. Posting requires an account on this realm. Anyone may read. Follow the <a href="/support/">Forum Guidelines</a>.</p>
      </div>
      <a class="fi-poster" href="/shop"><img src="/static/img/wotlk/forums-poster.jpg" alt="Original art posters. Available now."></a>
    </div>
    <div class="fi-cols">
      <div>{''.join(cell(*row) for row in left)}</div>
      <div>{''.join(cell(*row) for row in right)}</div>
    </div>
    {extra_block}
    <details class="fi-fold">
      <summary>Classes</summary>
      <p>Discuss your favorite class.</p>
      <div class="fi-links">{class_rows}</div>
    </details>
    <details class="fi-fold">
      <summary>Class Roles</summary>
      <p>Tank, healer, and damage discussion lives on the class boards.</p>
      <div class="fi-links"><a href="/wow/info/classes/">Talent Calculators</a></div>
    </details>
    <details class="fi-fold">
      <summary>Realm Forums</summary>
      <p>Players on your realm. Trade, groups, and realm talk.</p>
      <div class="fi-links"><a href="/forums/realm">{esc(realm_title)}</a></div>
    </details>
    <details class="fi-fold">
      <summary>Battlegroup Forums</summary>
      <p>Battleground and arena talk. <a href="/wow/pvp/rankings">See the rankings</a>.</p>
    </details>
    <p class="fi-legal"><a href="/support/">Online Privacy Policy</a><br>©2009 Blizzard Entertainment. All rights reserved.</p>
  </div>
</div>"""


def _thread_rows(slug: str, threads: list[dict], page: int) -> tuple[str, str]:
    pages = max(1, (len(threads) + _PAGE - 1) // _PAGE)
    page_n = min(max(page, 1), pages)
    start = (page_n - 1) * _PAGE
    rows = []
    for thread in threads[start : start + _PAGE]:
        author = thread.get("author") or ""
        kind = " blizz" if "Blizzard" in author else ""
        rows.append(
            "<tr>"
            f'<td class="subj"><a href="/forums/{esc(slug)}/{int(thread["id"])}">{esc(thread.get("title"))}</a></td>'
            f'<td class="who{kind}">{esc(author)}</td>'
            f'<td class="num">{esc(thread.get("replies") or 0)}</td>'
            f'<td class="num">{esc(thread.get("views") or 0)}</td>'
            f'<td class="when">{esc(_stamp(thread.get("last") or thread.get("created")))}</td>'
            "</tr>"
        )
    body = "".join(rows) or '<tr><td class="empty" colspan="5">No threads on this board yet.</td></tr>'
    if pages < 2:
        pager = ""
    else:
        links = "".join(
            f'<a href="?page={number}"' + (' class="on"' if number == page_n else "") + f">{number}</a>"
            for number in range(1, pages + 1)
        )
        pager = f'<p class="pager">{links}</p>'
    return body, pager


def _board_page(exp, slug: str, user, page: int, data_dir) -> str | None:
    from wowweb import forums

    title = forums.board_title(exp, slug)
    if not title:
        return None
    threads: list[dict] = []
    if data_dir is not None:
        conn = forums.connect(data_dir)
        forums.seed_if_empty(conn, exp)
        threads = forums.list_threads(conn, exp, slug)
        conn.close()
    rows, pager = _thread_rows(slug, threads, page)
    if user:
        form = (
            f'<form id="new-topic" class="fi-post" method="post" action="/forums/{esc(slug)}/new">'
            '<label>Title <input name="title" required maxlength="120"></label>'
            '<label>Body <textarea name="body" required rows="6"></textarea></label>'
            '<button type="submit">Post</button></form>'
        )
    else:
        form = '<p class="fi-post"><a href="/account/login">Log in</a> with a realm account to post.</p>'
    return f"""<div class="fi fi-page">
  {_top_links(forum=True)}
  <a class="eu-banner" href="/forums/"><img src="/static/img/wotlk/forums-eu-head.jpg" alt="World of Warcraft Forums"></a>
  <div class="fi-sheet">
    <p class="crumb"><a href="/forums/">Forums</a> · {esc(title)}</p>
    <h1>{esc(title)}</h1>
    <p class="board-tools"><a href="#new-topic">New Topic</a> <span>Sort by Latest Reply</span></p>
    <form class="quick" action="/wow/search" method="get">
      <input type="search" name="q" aria-label="Quick Search">
      <button type="submit">Search</button>
    </form>
    <table class="threads">
      <thead><tr><th>Subject</th><th>Author</th><th>Replies</th><th>Views</th><th>Last Post</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    {pager}
    {form}
    <aside class="board-side"><p>Posting on these forums requires an account. Anyone may read.</p></aside>
    <p class="fi-legal">©2009 Blizzard Entertainment. All rights reserved.</p>
  </div>
</div>"""


def _thread_page(exp, slug: str, thread_id: int, user, data_dir) -> str | None:
    from wowweb import forums

    if forums.board_title(exp, slug) is None or data_dir is None:
        return None
    conn = forums.connect(data_dir)
    thread = forums.get_thread(conn, exp, thread_id)
    conn.close()
    if not thread:
        return None
    posts = []
    for post in thread.get("posts") or []:
        when = _stamp(post.get("created"))
        posts.append(
            f'<article class="post"><header>{esc(post.get("author"))} · {esc(when)}</header>'
            f"<pre>{esc(post.get('body'))}</pre></article>"
        )
    if user:
        form = (
            f'<form class="fi-post" method="post" action="/forums/{esc(slug)}/{int(thread["id"])}/reply">'
            '<label>Reply <textarea name="body" required rows="5"></textarea></label>'
            '<button type="submit">Reply</button></form>'
        )
    else:
        form = '<p><a href="/account/login">Log in</a> to reply.</p>'
    return f"""<div class="fi fi-thread">
  {_top_links(forum=True)}
  <div class="fi-sheet">
    <p class="crumb"><a href="/forums/">Forums</a> · <a href="/forums/{esc(slug)}">{esc(slug)}</a></p>
    <h1>{esc(thread.get("title"))}</h1>
    {''.join(posts)}
    {form}
  </div>
</div>"""


def _forums_doc(path: str, ctx: dict) -> str | None:
    exp = ctx["exp"]
    parts = [part for part in path.split("/") if part]
    if not parts or parts[0] != "forums":
        return None
    if len(parts) == 1:
        html = _forum_index(exp)
        title = "Forums Index"
    elif len(parts) == 2:
        try:
            page = int((ctx.get("qs") or {}).get("page", ["1"])[0])
        except ValueError:
            page = 1
        html = _board_page(exp, parts[1], ctx.get("user"), page, ctx.get("data_dir"))
        title = parts[1]
    elif len(parts) == 3 and parts[2].isdigit():
        html = _thread_page(exp, parts[1], int(parts[2]), ctx.get("user"), ctx.get("data_dir"))
        title = "Forums"
    else:
        return None
    if not html:
        return None
    return document(
        f"{title} — Forums",
        styles("wotlk"),
        "era-wotlk era-wotlk-forums",
        html,
        dev_note_text=dev_note(exp, bool(ctx.get("dev"))),
    )


def _arm_login(user) -> str:
    if user:
        return '<a class="arm-login" href="/account/logout">Log Out</a>'
    return '<a class="arm-login" href="/account/login">Login</a>'


def _arm_bar(user, tab: str, field: str = "") -> str:
    tabs = (
        ("items", "/armory/?kind=items", "Items"),
        ("arena", "/armory/arena", "Arena"),
        ("info", "/armory/?kind=info", "Info"),
        ("tools", "/armory/?kind=tools", "Tools"),
    )
    links = "".join(
        f'<a href="{esc(href)}"' + (' class="on"' if key == tab else "") + f">{esc(label)}</a>"
        for key, href, label in tabs
    )
    return f"""<div class="arm-top">{_top_links()}</div>
<header class="arm-head">
  <a class="arm-logo" href="/armory/"><img src="/static/img/wotlk/armory-logo.jpg" alt="World of Warcraft The Armory"></a>
  <a class="arm-raf" href="/account/create"><img src="/static/img/wotlk/armory-raf.jpg" alt="Recruit a Friend"></a>
  {_arm_login(user)}
</header>
<div class="arm-toolbar">{field}<nav class="arm-tabs">{links}</nav></div>"""


def _icon(exp, display_id) -> str:
    from wowweb import assets

    src = assets.display_icon(exp, display_id)
    if not src:
        return ""
    return f'<img class="item-icon" src="{esc(src)}" alt="">'


def character_markup(exp, char: dict) -> str:
    """Desktop profile sheet. Stats we do not have are left blank, not invented."""
    from wowweb import talents

    name = char.get("name") or ""
    slug = _class_slug(str(char.get("class") or ""))
    trees = talents.trees_for(exp, slug) or ()
    tree_links = " ".join(
        f'<a href="/wow/info/classes/{esc(slug)}/talents.html">{esc(tree.name)}</a>'
        for tree in trees
    ) or "—"
    guild = char.get("guild") or {}
    guild_name = guild.get("name") if isinstance(guild, dict) else ""
    if guild_name:
        guild_html = f'<a href="/armory/guild/{quote(str(guild_name))}">{esc(guild_name)}</a>'
        guild_btn = f'<a class="arm-btn" href="/armory/guild/{quote(str(guild_name))}">Guild</a>'
    else:
        guild_html = "—"
        guild_btn = '<span class="arm-btn off">Guild</span>'
    equipped = {}
    for item in char.get("equipment") or []:
        slot = str(item.get("slot") or "")
        if slot:
            equipped[slot] = item

    def slot_html(slot: str) -> str:
        item = equipped.get(slot)
        if not item or not item.get("item_id"):
            return f'<div class="slot"><span class="socket"></span><span>{esc(slot)}</span></div>'
        icon = _icon(exp, item.get("display_id"))
        return (
            f'<div class="slot"><a href="/armory/item/{esc(item.get("item_id"))}">'
            f"{icon}<span>{esc(item.get('name') or slot)}</span></a></div>"
        )

    color = _CLASS_COLOR.get(str(char.get("class") or ""), "#8aa0b8")
    def stat_rows(labels) -> str:
        return "".join(f"<tr><th>{esc(label)}</th><td>—</td></tr>" for label in labels)

    base = stat_rows(_BASE_STATS)
    melee = stat_rows(_MELEE_STATS)
    ranged = stat_rows(_RANGED_STATS)
    spell = stat_rows(_SPELL_STATS)
    defense = stat_rows(_DEF_STATS)
    resist = stat_rows(_RES_STATS)
    talents_href = f"/wow/info/classes/{esc(slug)}/talents.html" if slug else "/wow/info/classes/"
    return f"""<div class="sheet" id="profile">
  <p class="sheet-btns"><span class="arm-btn on">Character</span>{guild_btn}</p>
  <nav class="sheet-tabs">
    <span class="on">Profile</span>
    <a href="{talents_href}">Talents and Glyphs</a>
    <a href="#reputation">Reputation</a>
    <a href="#calendar">Calendar</a>
    <a href="#achievements">Achievements</a>
    <a href="#statistics">Statistics</a>
    <a href="#activity">Activity Feed</a>
  </nav>
  <header class="sheet-id">
    <p class="lvl">{esc(char.get("level"))}</p>
    <div>
      <h2>{esc(name)}</h2>
      <p>{esc(char.get("race"))} {esc(char.get("class"))}</p>
      <p>{guild_html}</p>
      <p>{esc(char.get("realm") or getattr(exp, "realm_name", ""))}</p>
    </div>
    <p class="score"><span>Achievement Points</span><strong>{esc(char.get("achievements") or 0)}</strong></p>
  </header>
  <div class="doll">
    <div class="col">{''.join(slot_html(slot) for slot in _LEFT_SLOTS)}</div>
    <div class="model" style="background:{esc(color)}">
      <span>{esc(char.get("race"))}</span>
      <strong>{esc(char.get("class"))}</strong>
    </div>
    <div class="col">{''.join(slot_html(slot) for slot in _RIGHT_SLOTS)}</div>
    <aside class="side">
      <h3>Talent Specialization</h3>
      <p>{tree_links}</p>
      <h3>Primary Professions</h3>
      <p>—</p>
      <h3 id="activity">Recent Activity</h3>
      <p>Achievements recorded: {esc(char.get("achievements") or 0)}.</p>
      <p>Activity is recorded at logout.</p>
    </aside>
  </div>
  <div class="weapons">{''.join(slot_html(slot) for slot in _WEAPON_SLOTS)}</div>
  <div class="stats" id="statistics">
    <div><h3>Base Stats</h3><table>{base}</table></div>
    <div><h3>Melee</h3><table>{melee}</table></div>
    <div><h3>Ranged</h3><table>{ranged}</table></div>
    <div><h3>Spell</h3><table>{spell}</table></div>
    <div><h3>Defense</h3><table>{defense}</table></div>
    <div><h3>Resistances</h3><table>{resist}</table></div>
    <p class="updated">Last Updated at last logout.</p>
  </div>
  <section id="reputation"><h3>Reputation</h3><p>Faction standings are not on this profile.</p></section>
  <section id="calendar"><h3>Calendar</h3><p>The calendar is not on this profile.</p></section>
  <section id="achievements"><h3>Achievements</h3><p>{esc(char.get("achievements") or 0)} achievement points.</p></section>
</div>"""


def _results_table(exp, rows: list[dict], query: str, error: str) -> str:
    from wowweb import assets

    body = []
    for row in rows:
        slug = _class_slug(str(row.get("class") or ""))
        icon = assets.class_icon(exp.id, slug) if slug else None
        img = f'<img class="item-icon" src="{esc(icon)}" alt="">' if icon else ""
        exact = str(row.get("name") or "").lower() == query.strip().lower()
        width = 100 if exact else 62
        body.append(
            "<tr>"
            f'<td>{img}<a href="/armory/character/{quote(str(row.get("name") or ""))}">{esc(row.get("name"))}</a></td>'
            f'<td>{esc(row.get("level"))}</td>'
            f'<td>{esc(row.get("race"))}</td>'
            f'<td>{esc(row.get("class"))}</td>'
            f'<td>{esc(_faction(str(row.get("race") or "")))}</td>'
            "<td>—</td>"
            f'<td>{esc(row.get("realm") or exp.realm_name)}</td>'
            "<td>—</td>"
            f'<td><span class="rel"><span style="width:{width}%"></span></span></td>'
            "</tr>"
        )
    if error:
        listed = f'<tr><td class="empty" colspan="9">{esc(_safe_store(error))}</td></tr>'
    elif not body:
        listed = '<tr><td class="empty" colspan="9">No characters found.</td></tr>'
    else:
        listed = "".join(body)
    count = len(rows)
    return f"""<div class="results">
  <p class="count">Characters ({count})</p>
  <table>
    <thead><tr>
      <th>Character Name</th><th>Level</th><th>Race</th><th>Class</th>
      <th>Faction</th><th>Guild</th><th>Realm</th><th>Battlegroup</th><th>Relevance</th>
    </tr></thead>
    <tbody>{listed}</tbody>
  </table>
</div>"""


def _armory_doc(exp, user, dev, main: str, tab: str, search: str = "") -> str:
    field = (
        f'<form class="arm-q" action="/armory/" method="get">'
        f'<input name="q" value="{esc(search)}" aria-label="Character name">'
        f'<button type="submit">Search</button></form>'
        if tab != "home"
        else ""
    )
    if tab == "home":
        bar = f'<div class="arm-top">{_top_links()}</div>'
        field = ""
    else:
        bar = _arm_bar(user, tab, field)
        field = ""
    html = f'<div class="arm">{bar}{field}{main}</div>'
    return document(
        "The Armory — World of Warcraft",
        styles("wotlk"),
        "era-wotlk era-wotlk-armory",
        html,
        dev_note_text=dev_note(exp, dev),
    )


def _armory(path: str, ctx: dict) -> str | None:
    from wowweb import armory

    exp = ctx["exp"]
    user = ctx.get("user")
    dev = bool(ctx.get("dev"))
    cfg = ctx.get("labcfg")
    qs = ctx.get("qs") or {}
    if path == "/armory":
        query = (qs.get("q") or [""])[0]
        kind = (qs.get("kind") or [""])[0]
        if kind == "items" and not query:
            rows = armory.auctions(cfg, exp) if cfg is not None else []
            listed = "".join(
                f'<li><a href="/armory/item/{esc(row.get("item_id"))}">{esc(row.get("name"))}</a>'
                f' <span>{esc(row.get("buyout"))}</span></li>'
                for row in rows
            ) or "<li>The auction house has no rows to list.</li>"
            main = (
                "<div class=\"arm-block\"><h1>The Armory</h1><h2>Items</h2>"
                "<p>This tab lists auction-house rows. An item page opens from a name.</p>"
                f"<ul>{listed}</ul></div>"
            )
            return _armory_doc(exp, user, dev, main, "items")
        if kind == "info" and not query:
            main = (
                "<div class=\"arm-block\"><h1>The Armory</h1><h2>Info</h2>"
                "<p>What is the Armory? Profiles, guilds, and arena teams from the last logout on this realm.</p>"
                "<p>Character profiles now feature a 3D-style sheet. 1/13/2010.</p></div>"
            )
            return _armory_doc(exp, user, dev, main, "info")
        if kind == "tools" and not query:
            main = (
                "<div class=\"arm-block\"><h1>The Armory</h1><h2>Tools</h2>"
                '<p><a href="/wow/info/classes/">Talent Calculators</a></p>'
                '<p><a href="/wow/pvp/rankings">PvP Rankings</a></p>'
                '<p><a href="/wow/realmstatus">Realm Status</a></p></div>'
            )
            return _armory_doc(exp, user, dev, main, "tools")
        if query:
            if cfg is None:
                rows, error = [], ""
            else:
                rows, error = armory.search_with_status(cfg, exp, query)
            main = _results_table(exp, rows, query, error)
            return _armory_doc(exp, user, dev, main, "search", query)
        error = _safe_store(armory.character_store(cfg, exp)) if cfg is not None else ""
        note = f'<p class="arm-err">{esc(error)}</p>' if error else ""
        main = f"""<div class="arm-home">
  <div class="arm-frame">
    <a class="arm-logo" href="/armory/"><img src="/static/img/wotlk/armory-logo.jpg" alt="World of Warcraft The Armory"></a>
    {_arm_login(user)}
    <form action="/armory/" method="get">
      <input name="q" aria-label="Character name">
      <button type="submit">Search</button>
    </form>
    {note}
  </div>
  <div class="arm-split">
    <div class="arm-news">
      <h2>News</h2>
      <p><a href="/armory/?kind=info"><strong>Character Profiles Now Feature a 3D Model</strong></a> <span>1/13/2010</span></p>
      <p>The character profile has been updated. Profiles now feature a 3D model viewer, based on the gear worn at last logout.</p>
      <h2>Frequently Asked Questions</h2>
      <ul>
        <li>What is the Armory? A profile read from this realm at logout.</li>
        <li>How often does it update? The next time that character logs out.</li>
        <li>What information can be accessed? The gear, guild, and achievement score from the last logout.</li>
        <li>Where do I find my character? Search the name above.</li>
      </ul>
    </div>
    <a class="arm-mobile" href="/armory/?kind=info"><img src="/static/img/wotlk/armory-mobile.jpg" alt="World of Warcraft Armory"></a>
  </div>
</div>"""
        return _armory_doc(exp, user, dev, main, "home")
    if path == "/armory/arena":
        rows = armory.arena_ladder(cfg, exp) if cfg is not None else []
        body = "".join(
            f"<tr><td>{esc(row.get('name'))}</td><td>{esc(row.get('rating'))}</td><td>{esc(row.get('type'))}</td></tr>"
            for row in rows
        ) or '<tr><td colspan="3">No arena teams on this realm.</td></tr>'
        main = (
            "<div class=\"arm-block\"><h1>The Armory</h1><h2>Arena</h2>"
            "<table class=\"grid\"><tr><th>Team</th><th>Rating</th><th>Type</th></tr>"
            f"{body}</table></div>"
        )
        return _armory_doc(exp, user, dev, main, "arena")
    if path.startswith("/armory/character/"):
        name = unquote(path.rsplit("/", 1)[-1]).strip()
        if not name or cfg is None:
            return None
        char = armory.get_character(cfg, exp, name)
        if not char:
            return None
        return _armory_doc(exp, user, dev, character_markup(exp, char), "search", name)
    return None


def _wrath_doc(exp, dev: bool) -> str:
    inner = """<div class="wr">
  <img class="wr-art" src="/static/img/wotlk/expansion.jpg" alt="">
  <nav class="wr-nav">
    <a href="/wrath">Home</a>
    <a href="#features">Features</a>
    <a href="/wow/media/screenshots">Screenshots</a>
    <a href="/wow/media/wallpapers">Artwork</a>
    <a href="/wow/media/wallpapers">Downloads</a>
    <a href="/wow/media/screenshots">Movies</a>
    <a href="/support/">FAQ</a>
    <a href="/forums/">Forum</a>
  </nav>
  <a class="wr-trailer" href="/wow/media/screenshots">Watch Video Trailer</a>
  <a class="wr-pill wr-cine" href="/wow/media/screenshots">Cinematic Trailer</a>
  <a class="wr-pill wr-calc" href="/wow/info/classes/deathknight/talents.html">Talent Calculator</a>
  <a class="wr-pill wr-ach" href="/armory/">Achievements</a>
  <a class="wr-back" href="/wow/">Return to WoW-Europe.com</a>
  <div class="wr-copy" id="features">
    <h1>In the cold, harsh northlands...</h1>
    <p>The Lich King Arthas has set in motion events that could lead to the extinction of all life on Azeroth. Heroes sail for Northrend.</p>
    <h2>Features</h2>
    <ul>
      <li>Master the necromantic powers of the Death Knight, World of Warcraft's first hero class.</li>
      <li>Quest to level 80, gaining potent new abilities and talents along the way.</li>
      <li>Learn the craft of spell augmentation with the new Inscription profession.</li>
      <li>Brave the harsh new continent of Northrend, the icy domain of the Lich King.</li>
      <li>Engage in epic siege warfare, deploying mighty siege engines.</li>
      <li>Explore perilous new dungeons on Azeroth's north.</li>
    </ul>
    <p class="wr-legal">©2008 Blizzard Entertainment. All rights reserved.</p>
  </div>
</div>"""
    return document(
        "Wrath of the Lich King",
        styles("wotlk"),
        "era-wotlk era-wotlk-wrath",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def _portal_doc(exp, dev: bool) -> str:
    inner = """<div class="portal">
  <img class="portal-art" src="/static/img/wotlk/bnet-portal.jpg" alt="">
  <a class="hit hit-create" href="/account/">Create or Manage a Battle.net Account</a>
  <a class="hit hit-learn" href="/account/create">learn more</a>
  <a class="hit hit-wow" href="/wow/">Classic Community Site</a>
  <a class="hit hit-forums" href="/forums/">Classic Forums</a>
  <a class="hit hit-support" href="/support/">Support Site</a>
  <p class="portal-copy">Introducing the new Battle.net Account. Beginning with World of Warcraft. ©2009 Blizzard Entertainment, Inc. All rights reserved.</p>
</div>"""
    return document(
        "Battle.net",
        styles("wotlk"),
        "era-wotlk era-wotlk-portal",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def full(path: str, ctx: dict) -> str | None:
    exp = ctx["exp"]
    dev = bool(ctx.get("dev"))
    if path == "/wrath":
        return _wrath_doc(exp, dev)
    if path == "/bnet":
        return _portal_doc(exp, dev)
    if path == "/forums" or path.startswith("/forums/"):
        return _forums_doc(path, ctx)
    if path == "/armory" or path.startswith("/armory/"):
        return _armory(path, ctx)
    return None
