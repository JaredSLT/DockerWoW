"""Dragonflight community site.

Home, forums, realm status, shop, and account follow the 2022–2023 references.
News index, game guide, the general forum board, and the character profile
have no own reference; they use this masthead and live realm data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .common import dev_note, document, esc, styles

# Home cards are the 20–27 June 2023 reference. news_for() is the later archive.
_JUNE = (
    (
        "june-27",
        "27 June 2023",
        "Get Hot Summer Rewards in the July Trading Post",
        "news-trading.jpg",
        "Hot summer rewards are in the July Trading Post.",
    ),
    (
        "june-26",
        "26 June 2023",
        "This Week in WoW: 26 June 2023",
        "news-week.jpg",
        "A weekly look at what is live in World of Warcraft.",
    ),
    (
        "june-22",
        "22 June 2023",
        "Heed the Call of the Crusade—Raid Dungeons Now Live!",
        "news-crusade.jpg",
        "Call of the Crusade raid dungeons are open.",
    ),
    (
        "june-20",
        "20 June 2023",
        "The WoW Summer Sale is here!",
        "news-sale.jpg",
        "The summer sale is open in the shop.",
    ),
)

_MOUNTS = (
    ("Wondrous Wavewhisker", "mount-wave.jpg"),
    ("Dread Raven", "mount-raven.jpg"),
    ("Enchanted Fey Dragon", "mount-fey.jpg"),
    ("Ensorcelled Everwyrm", "mount-wyrm.jpg"),
    ("Heart of the Aspects", "mount-heart.jpg"),
    ("Hogrus, Swine of Good Fortune", "mount-hogrus.jpg"),
    ("Imperial Quilen", "mount-quilen.jpg"),
    ("Jade, Bright Foreseer", "mount-jade.jpg"),
)

# Visible rows on the November 2022 realm-status reference.
_RETAIL_ROWS = (
    ("Aegwynn", "Normal", "New Players", "CST", "United States"),
    ("Aerie Peak", "Normal", "Medium", "PST", "United States"),
    ("Agamaggan", "Normal", "High", "CST", "United States"),
    ("Aggramar", "Normal", "Full", "CST", "United States"),
    ("Akama", "Normal", "High", "PST", "United States"),
    ("Alexstrasza", "Normal", "Low", "CST", "United States"),
)

_CLASSIC_NAMES = (
    "Atiesh",
    "Benediction",
    "Faerlina",
    "Mankrik",
    "Pagle",
    "Whitemane",
    "Grobbulus",
    "Ashkandi",
)
_WOTLK_NAMES = (
    "Benediction",
    "Faerlina",
    "Mankrik",
    "Pagle",
    "Grobbulus",
    "Earthfury",
)

_CLASS_ORDER = (
    ("deathknight", "Death Knight"),
    ("demonhunter", "Demon Hunter"),
    ("druid", "Druid"),
    ("evoker", "Evoker"),
    ("hunter", "Hunter"),
    ("mage", "Mage"),
    ("monk", "Monk"),
    ("paladin", "Paladin"),
    ("priest", "Priest"),
    ("rogue", "Rogue"),
    ("shaman", "Shaman"),
    ("warlock", "Warlock"),
    ("warrior", "Warrior"),
)

_ZONES = (
    ("The Waking Shores", "Red dragons and the first shore of the Dragon Isles."),
    ("Ohn'ahran Plains", "The green flight's wide hunting grounds."),
    ("The Azure Span", "Blue-dragon tundra and the tuskarr."),
    ("Thaldraszus", "The bronze seat and the towers of Valdrakken."),
    ("Zaralek Cavern", "Neltharion's laboratory under the isles."),
    ("The Emerald Dream", "The green flight's dream, opened in the last season."),
)


def _q(qs: dict | None, key: str, default: str = "") -> str:
    if not qs:
        return default
    val = qs.get(key)
    if isinstance(val, list):
        return val[0] if val else default
    if val is None:
        return default
    return str(val)


def _doc(exp, title: str, inner: str, dev: bool, extra: str = "") -> str:
    kind = "era-dragonflight" + (f" {extra}" if extra else "")
    return document(
        title,
        styles("dragonflight"),
        kind,
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def _menu(links: tuple[tuple[str, str], ...]) -> str:
    return "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in links)


def _drop(href: str, label: str, links: tuple[tuple[str, str], ...]) -> str:
    return (
        f'<div class="df-drop"><a href="{esc(href)}">{esc(label)}</a>'
        f'<div class="df-menu">{_menu(links)}</div></div>'
    )


def _bar(user: str | None) -> str:
    account = (
        (
            ("/account/", "Overview"),
            ("/account/services", "Services"),
            ("/account/logout", "Log Out"),
        )
        if user
        else (
            ("/account/login", "Log In"),
            ("/account/create", "Create Account"),
            ("/account/", "Overview"),
            ("/account/services", "Services"),
        )
    )
    who = f'<p class="df-who">Signed in as {esc(user)}</p>' if user else ""
    return f"""<header class="df-bar">
  <a class="df-blizz" href="/wow/">Blizzard</a>
  <a class="df-wmark" href="/wow/" aria-label="World of Warcraft"><span>W</span></a>
  <nav class="df-links" aria-label="World of Warcraft">
    {_drop("/wow/info", "Game Info", (
        ("/wow/info", "Game Guide"),
        ("/wow/info/classes", "Classes"),
        ("/wow/info/races", "Races"),
        ("/wow/realmstatus", "Realm Status"),
        ("/wow/info/professions", "Professions"),
    ))}
    {_drop("/classic", "Expansions", (
        ("/wow/", "Dragonflight"),
        ("/classic", "WoW Classic"),
        ("/story", "Story"),
    ))}
    {_drop("/wow/news", "News", (("/wow/news", "All News"), ("/wow/", "Home")))}
    {_drop("/forums", "Community", (
        ("/forums", "Forums"),
        ("/forums/general", "General Discussion"),
        ("/esports", "Esports"),
        ("/support", "Support"),
        ("/armory", "Armory"),
    ))}
    {_drop("/shop", "Shop", (("/shop", "Mounts"), ("/shop", "Shop")))}
  </nav>
  <a class="df-search" href="/wow/search" aria-label="Search">Search</a>
  <div class="df-drop df-account">
    <a href="/account/">Account</a>
    <div class="df-menu">{who}{_menu(account)}</div>
  </div>
  <a class="df-try" href="/account/create">Try Free</a>
  <a class="df-sub" href="/shop">Subscribe Now</a>
</header>"""


def _foot() -> str:
    return """<footer class="df-foot">
  <nav>
    <a href="/support">Support</a>
    <a href="/wow/realmstatus">Realm Status</a>
    <a href="/forums">Forums</a>
    <a href="/shop">Shop</a>
    <a href="/account/">Account</a>
  </nav>
  <p>©2023 Blizzard Entertainment, Inc. All rights reserved.</p>
</footer>"""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online, login_error
    home = "df-home" in (body or "")
    if home:
        main = body
        site = "df-site df-site-home"
        shown = "World of Warcraft"
        extra = "era-df-home"
    else:
        heading = ""
        if "df-self" not in body and "acct-df" not in body:
            heading = f'<h1 class="df-crumb">{esc(crumb or title)}</h1>'
        main = f'<main class="df-main">{heading}<div class="df-sheet">{body}</div></main>'
        site = "df-site df-site-page"
        shown = title
        extra = ""
    inner = f'<div class="{site}">{_bar(user)}{main}{_foot()}</div>'
    return document(
        f"{shown} — World of Warcraft",
        styles("dragonflight"),
        "era-dragonflight" + (f" {extra}" if extra else ""),
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    _ = exp, news, realm, user
    # Cards sit on the June 2023 stage. The photograph already paints the
    # captions, so the link text is real and transparent over each card.
    cards = []
    for index, (slug, date, title, _image, _blurb) in enumerate(_JUNE, start=1):
        cards.append(
            f'<a class="df-hit df-hit-card df-hit-card-{index}" href="/wow/news#{esc(slug)}">'
            f'<span class="df-card-date">{esc(date)}</span>'
            f'<span class="df-card-title">{esc(title)}</span>'
            "</a>"
        )
    return f"""<div class="df-home">
  <h1 class="df-sr">DRAGONFLIGHT SEASON 2 NOW LIVE!</h1>
  <p class="df-sr">Breach Neltharion's secret laboratory to thwart Scalecommander Sarkareth, whose forces seek to claim the legacy of the dracthyr. Dragonflight Season 2 brings a new raid, an updated rotation of Mythic+ dungeons, a new PvP Season, and more.</p>
  <a class="df-hit df-hit-explore" href="/wow/info">Explore Dragonflight</a>
  <a class="df-hit df-hit-buy" href="/shop">BUY DRAGONFLIGHT</a>
  <a class="df-hit df-hit-learn" href="/wow/info">LEARN MORE</a>
  <h2 class="df-sr">Latest News &amp; Updates</h2>
  <a class="df-hit df-hit-all" href="/wow/news">View all news</a>
  {''.join(cards)}
  <p class="df-sr">By clicking “Accept All Cookies”, you agree to the storing of cookies on your device to enhance site navigation, analyze site usage, and assist in our marketing efforts. <a href="/support">Cookie Policy</a> <a href="/support">Cookies Settings</a></p>
  <a class="df-hit df-hit-reject" href="/wow/">Reject All</a>
  <a class="df-hit df-hit-accept" href="/wow/">Accept All Cookies</a>
</div>"""


def _june_block() -> str:
    bits = []
    for slug, date, title, image, blurb in _JUNE:
        bits.append(
            f'<article class="df-story" id="{esc(slug)}">'
            f'<img src="/static/img/dragonflight/{esc(image)}" alt="">'
            f"<p>{esc(date)}</p><h2>{esc(title)}</h2><p>{esc(blurb)}</p>"
            "</article>"
        )
    return "".join(bits)


def _news_body(exp) -> str:
    from wowweb.content import news_for

    later = []
    for i, (title, date, body) in enumerate(news_for(exp)):
        later.append(
            f'<li><a href="/wow/news/{i}">{esc(date)} — {esc(title)}</a>'
            f"<p>{esc(body)}</p></li>"
        )
    archive = "".join(later) or "<li>No later notes.</li>"
    return (
        '<div class="df-self df-newsindex">'
        "<h1>News</h1>"
        f'<div class="df-stories">{_june_block()}</div>'
        "<h2>Archive</h2>"
        f"<ul class=\"df-archive\">{archive}</ul>"
        "</div>"
    )


def _guide_body(exp) -> str:
    from wowweb.content import class_facts, classes_for, features_for, race_facts, races_for
    from wowweb import talents

    zones = "".join(f"<li><strong>{esc(name)}</strong> — {esc(text)}</li>" for name, text in _ZONES)
    feats = "".join(f"<li>{esc(item)}</li>" for item in features_for(exp))
    races = []
    for slug in races_for(exp):
        name, faction, city, _blurb = race_facts(exp, slug)
        races.append(
            f'<a class="df-pill" href="/wow/info/races/{esc(slug)}">'
            f"<strong>{esc(name)}</strong><span>{esc(faction)} · {esc(city)}</span></a>"
        )
    classes = []
    for slug in classes_for(exp):
        name, armor, specs, _blurb = class_facts(exp, slug)
        trees = talents.trees_for(exp, slug) or ()
        tree_names = ", ".join(tree.name for tree in trees)
        extra = f"<span>{esc(tree_names)}</span>" if tree_names else ""
        classes.append(
            f'<a class="df-pill" href="/wow/info/classes/{esc(slug)}">'
            f"<strong>{esc(name)}</strong><span>{esc(armor)} · {esc(specs)}</span>{extra}</a>"
        )
    return (
        '<div class="df-self df-guide">'
        "<h1>Game Guide</h1>"
        "<p>The Dragon Isles are awake. Dragonriding crosses the map, the dracthyr return as evokers, and talent trees are back.</p>"
        f"<h2>Dragon Isles</h2><ul>{zones}</ul>"
        f"<h2>Features</h2><ul>{feats}</ul>"
        f'<h2>Races</h2><div class="df-pills">{"".join(races)}</div>'
        f'<h2>Classes</h2><div class="df-pills">{"".join(classes)}</div>'
        '<p class="df-more"><a href="/wow/info/classes/evoker/talents.html">Evoker talents</a>'
        ' · <a href="/wow/info/classes">All classes</a>'
        ' · <a href="/wow/info/basics/map">World map</a>'
        ' · <a href="/wow/info/basics">New players</a></p>'
        "</div>"
    )


def _board_body(ctx, slug: str) -> tuple[str, str] | None:
    from wowweb import forums

    exp = ctx["exp"]
    title = forums.board_title(exp, slug)
    if not title:
        return None
    conn = forums.connect(ctx["data_dir"])
    try:
        forums.seed_if_empty(conn, exp)
        threads = forums.list_threads(conn, exp, slug)
    finally:
        conn.close()
    rows = []
    for thread in threads:
        when = ""
        stamp = thread.get("last") or thread.get("created")
        if stamp:
            when = datetime.fromtimestamp(int(stamp), timezone.utc).strftime("%Y-%m-%d %H:%M")
        rows.append(
            "<tr>"
            f'<td><a href="/forums/{esc(slug)}/{int(thread["id"])}">{esc(thread.get("title"))}</a></td>'
            f"<td>{esc(thread.get('author'))}</td>"
            f"<td>{esc(thread.get('replies') or 0)}</td>"
            f"<td>{esc(when)}</td>"
            "</tr>"
        )
    body_rows = "".join(rows) or "<tr><td colspan=\"4\">No threads yet.</td></tr>"
    user = ctx.get("user")
    if user:
        form = (
            f'<form class="df-post" method="post" action="/forums/{esc(slug)}/new">'
            "<label>Title <input name=\"title\" required maxlength=\"120\"></label>"
            "<label>Body <textarea name=\"body\" required rows=\"6\"></textarea></label>"
            "<button type=\"submit\">Post</button></form>"
        )
    else:
        form = '<p><a href="/account/login">Log in</a> to post.</p>'
    html = (
        '<div class="df-self df-board">'
        f"<h1>{esc(title)}</h1>"
        '<p class="df-more"><a href="/forums">All categories</a></p>'
        "<table><thead><tr><th>Subject</th><th>Author</th><th>Replies</th><th>Last post</th></tr></thead>"
        f"<tbody>{body_rows}</tbody></table>"
        f"{form}</div>"
    )
    return title, html


def profile_body(exp, char: dict) -> str:
    from wowweb import assets

    guild = ""
    g = char.get("guild")
    if isinstance(g, dict) and g.get("name"):
        guild = (
            f'<p>Guild <a href="/armory/guild/{esc(g["name"])}">{esc(g["name"])}</a></p>'
        )
    else:
        guild = "<p>No guild</p>"
    online = "Online" if char.get("online") else "Offline"
    gear = []
    for item in char.get("equipment") or []:
        if not isinstance(item, dict):
            continue
        slot = item.get("slot") or "Slot"
        name = item.get("name") or ""
        src = assets.display_icon(exp, item.get("display_id"))
        icon = f'<img src="{esc(src)}" alt="">' if src else ""
        link = name
        if item.get("item_id"):
            link = f'<a href="/armory/item/{esc(item["item_id"])}">{esc(name)}</a>'
        else:
            link = esc(name)
        gear.append(f"<li>{icon}<span>{esc(slot)}</span>{link}</li>")
    gear_html = "".join(gear) or "<li>No equipment recorded.</li>"
    money = char.get("money_text") or ""
    return (
        '<div class="df-self df-profile">'
        '<p class="df-profile-kicker">Dragonflight</p>'
        f"<h1>{esc(char.get('name'))}</h1>"
        f"<p>Level {esc(char.get('level'))} {esc(char.get('race'))} {esc(char.get('class'))}</p>"
        f"<p>{esc(char.get('realm') or getattr(exp, 'realm_name', ''))} · {esc(online)}</p>"
        f"{guild}"
        f"<p>Achievements {esc(char.get('achievements') or 0)}</p>"
        f"<p>{esc(money)}</p>"
        f"<ul class=\"df-gear\">{gear_html}</ul>"
        '<p class="df-more"><a href="/armory">Armory search</a></p>'
        "</div>"
    )


def _services_body(ctx) -> tuple[str, str]:
    user = ctx.get("user") or ""
    if not user:
        inner = (
            "<h1>Character Services</h1>"
            "<p>Sign in to change a name, appearance, race, faction, or guild.</p>"
            '<p><a href="/account/login">Log In</a></p>'
        )
    else:
        from wowweb.services.page import services_page

        inner = "<h1>Character Services</h1>" + services_page(
            ctx["labcfg"], ctx["exp"], user, ctx["data_dir"]
        )
    return "Character Services", f'<div class="df-self df-services">{inner}</div>'


def _cat(title: str, blurb: str, links: tuple[tuple[str, str], ...]) -> str:
    items = "".join(f'<li><a href="{esc(href)}">{esc(label)}</a></li>' for href, label in links)
    return (
        '<section class="df-fcat">'
        f"<h3>{esc(title)}</h3><p>{esc(blurb)}</p><ul>{items}</ul>"
        "</section>"
    )


def _forums_doc(ctx) -> str:
    from wowweb import forums

    exp = ctx["exp"]
    live = {slug: title for slug, title in forums.boards_for(exp)}
    view = _q(ctx.get("qs"), "view", "categories")
    classes = []
    for slug, label in _CLASS_ORDER:
        href = f"/forums/{slug}" if slug in live else "/forums"
        classes.append(f'<a href="{esc(href)}">{esc(label)}</a>')
    class_box = (
        '<section class="df-fcat df-fclasses"><h3>Classes</h3>'
        "<p>Pick up your class discussion needs.</p>"
        f'<p class="df-classline">{"".join(classes)}</p></section>'
    )
    left = (
        _cat("Community", "Discuss World of Warcraft.", (
            ("/forums/general", "General Discussion"),
            ("/forums/general", "Oceanic General Discussion"),
            ("/forums", "WoW Community Council"),
        ))
        + _cat("WoW Classic", "Classic discussions.", (
            ("/classic", "WoW Classic General Discussion"),
            ("/forums/general", "Wrath of the Lich King Classic Discussion"),
            ("/forums/bugs", "WoW Classic Bug Report"),
            ("/forums/guilds", "WoW Classic New Guild Listings"),
            ("/forums", "Classic Connections 2004-2019 - Find People Here"),
        ))
        + _cat("In Development", "Discuss in-development content.", (
            ("/forums/general", "Embers of Neltharion PTR Discussion"),
            ("/forums/general", "Wrath Classic: Call of the Crusade PTR"),
        ))
        + _cat("Support", "Problem installing? In-game or account issues? Reporting bugs?", (
            ("/support", "Customer Support"),
            ("/wow/realmstatus", "Service Status"),
            ("/support", "Technical Support"),
            ("/support", "Mac Technical Support"),
            ("/forums/bugs", "Bug Report"),
            ("/forums/bugs", "Website Bug Report"),
            ("/forums/bugs", "Mobile Bug Report"),
        ))
        + class_box
    )
    right = (
        _cat("PvP", "Discuss arenas and battlegrounds here with your fellow players.", (
            ("/forums/pvp", "Arenas"),
            ("/forums/pvp", "Battlegrounds"),
            ("/forums/pvp", "War Mode and World PvP"),
        ))
        + _cat("Guides", "New to World of Warcraft or returning after some time away?", (
            ("/wow/info", "New Player Help and Guides"),
            ("/wow/info", "Returning Player Help & Discussions"),
            ("/forums/ui" if "ui" in live else "/forums", "UI and Macros"),
        ))
        + _cat("Gameplay", "Gameplay discussion for World of Warcraft.", (
            ("/forums/general", "Quests"),
            ("/forums/professions" if "professions" in live else "/forums", "Professions"),
            ("/wow/info", "Pet Battles"),
            ("/forums/dungeons" if "dungeons" in live else "/forums", "Dungeons, Raids and Scenarios"),
            ("/wow/info", "Transmogrification"),
            ("/armory", "Achievements"),
        ))
        + _cat("Recruitment", "Searching for a guild or community? Or do you want to advertise yours?", (
            ("/forums/guilds", "Guild Recruitment"),
            ("/forums/guilds", "Oceanic Guild Recruitment"),
            ("/forums/guilds", "Communities Recruitment"),
        ))
        + _cat("Lore", "Discuss World of Warcraft lore or share your original fan fiction.", (
            ("/forums/general", "World's End Tavern: Role-play and Fan Fiction"),
            ("/story", "Story Forum"),
        ))
        + _cat("Off-Topic", "For all your non-Warcraft game discussions.", (
            ("/forums/general", "General, Gaming and Hardware"),
            ("/forums/general", "Movies, TV and Entertainment"),
            ("/forums/general", "Books and Comics"),
        ))
    )
    classic_names = (
        "Atiesh", "Benediction", "Faerlina", "Mankrik", "Pagle", "Whitemane",
        "Grobbulus", "Ashkandi", "Sulfuras", "Westfall", "Herod", "Earthfury",
        "Bloodsail Buccaneers", "Hydraxis", "Old Blanchy", "Pagle", "Thunderfury",
    )
    retail_names = (
        "Area 52", "Illidan", "Stormrage", "Tichondrius", "Mal'Ganis", "Sargeras",
        "Thrall", "Zul'jin", "Dalaran", "Kel'Thuzad", "Bleeding Hollow", "Burning Blade",
        "Frostmourne", "Azralon", "Ragnaros", "Proudmoore", "Moon Guard", "Wyrmrest Accord",
    )
    def realm_cols(names: tuple[str, ...] | list[str]) -> str:
        return "".join(f'<li><a href="/wow/realmstatus">{esc(name)}</a></li>' for name in names)

    extra = ""
    if view in ("latest", "top"):
        conn = forums.connect(ctx["data_dir"])
        try:
            forums.seed_if_empty(conn, exp)
            found = []
            for slug in live:
                for thread in forums.list_threads(conn, exp, slug):
                    found.append((slug, thread))
        finally:
            conn.close()
        found.sort(key=lambda item: int((item[1].get("last") or item[1].get("created") or 0)), reverse=True)
        if view == "top":
            found.sort(key=lambda item: int(item[1].get("replies") or 0), reverse=True)
        rows = []
        for slug, thread in found[:20]:
            rows.append(
                f'<li><a href="/forums/{esc(slug)}/{int(thread["id"])}">{esc(thread.get("title"))}</a>'
                f' <span>{esc(live.get(slug, slug))}</span></li>'
            )
        extra = f'<ul class="df-flat">{"".join(rows) or "<li>No threads yet.</li>"}</ul>'
    cats = "" if view in ("latest", "top") else (
        f'<div class="df-fgrid"><div class="df-fcol">{left}</div><div class="df-fcol">{right}</div></div>'
        '<section class="df-realms"><h2>All WoW Classic Realms</h2>'
        f'<ul>{realm_cols(classic_names)}</ul>'
        "<h2>All Realms</h2>"
        f"<ul>{realm_cols(retail_names)}</ul></section>"
    )
    current = {"categories": "Categories", "top": "Top", "latest": "Latest"}.get(view, "Categories")
    tools = (
        f'<a href="/forums">Categories</a>'
        f'<a href="/forums?view=top">Top</a>'
        f'<a href="/forums?view=latest">Latest</a>'
        '<span>Blizz Tracker</span>'
    )
    inner = f"""<div class="df-forums">
  <header class="df-fhead">
    <a class="df-blizz" href="/wow/">Blizzard</a>
    <nav>
      <a href="/wow/">Warcraft</a>
      <span>Diablo</span>
      <span>Overwatch</span>
      <span>StarCraft</span>
      <a href="/wow/info">About</a>
      <a href="/shop">Shop</a>
      <a href="/account/">Account</a>
    </nav>
    <a class="df-download" href="/account/create">Download Battle.net</a>
  </header>
  <div class="df-fhero">
    <p class="df-wowlogo"><span>World of</span> Warcraft</p>
  </div>
  <main class="df-fmain">
    <h1>All Categories</h1>
    <p class="df-ftools">{tools}<em>{esc(current)}</em></p>
    {cats}{extra}
  </main>
  <footer class="df-ffoot">
    <p>English (US)</p>
    <p class="df-blizz">Blizzard</p>
    <nav>
      <a href="/support">Support</a>
      <a href="/wow/info">About</a>
      <a href="/account/">Account</a>
    </nav>
    <p>©2023 Blizzard Entertainment, Inc. All rights reserved.</p>
  </footer>
</div>"""
    # The October 2023 category index is the stage. The same links stay in
    # the document, drawn clear over the photograph so the text is not doubled.
    inner = f"""<div class="df-forums df-photo">
  <img class="df-fstage" src="/static/img/dragonflight/forums-bg.png" alt="">
  <div class="df-sr">{inner}</div>
  <a class="df-hit df-f-wow" href="/wow/">Warcraft</a>
  <a class="df-hit df-f-about" href="/wow/info">About</a>
  <a class="df-hit df-f-shop" href="/shop">Shop</a>
  <a class="df-hit df-f-account" href="/account/">Account</a>
  <a class="df-hit df-f-dl" href="/account/create">Download Battle.net</a>
  <a class="df-hit df-f-embers" href="/forums/general">Embers of Neltharion PTR Discussion</a>
  <a class="df-hit df-f-evoker" href="/forums/evoker">Evoker</a>
  <a class="df-hit df-f-dk" href="/forums/deathknight">Death Knight</a>
</div>"""
    return _doc(exp, "Forums — World of Warcraft", inner, bool(ctx.get("dev")), "era-df-forums")


def _realm_rows(ctx, tab: str) -> list[tuple]:
    from wowweb import lab

    exp = ctx["exp"]
    realm = lab.realm_status(ctx["labcfg"], exp)
    rows = []
    live_name = str(realm.get("name") or exp.realm_name)
    live = (
        live_name,
        str(realm.get("type") or "Normal"),
        str(realm.get("population") or "—"),
        str(realm.get("timezone") or "PST"),
        "United States",
        bool(realm.get("up")),
    )
    if tab == "classic":
        base = [(name, "Normal", "—", "PST", "United States", True) for name in _CLASSIC_NAMES]
    elif tab == "wotlk":
        base = [(name, "Normal", "—", "CST", "United States", True) for name in _WOTLK_NAMES]
    else:
        base = [(*row, True) for row in _RETAIL_ROWS]
    seen = False
    for name, kind, pop, zone, locale, up in base:
        if name.lower() == live_name.lower():
            rows.append(live)
            seen = True
        else:
            rows.append((name, kind, pop, zone, locale, up))
    if not seen:
        rows.insert(0, live)
    q = _q(ctx.get("qs"), "q").strip().lower()
    locale = _q(ctx.get("qs"), "locale", "All")
    if q:
        rows = [row for row in rows if q in row[0].lower()]
    if locale and locale != "All":
        rows = [row for row in rows if row[4] == locale]
    return rows


def _realm_doc(ctx) -> str:
    from wowweb import lab

    exp = ctx["exp"]
    tab = _q(ctx.get("qs"), "tab", "retail")
    if tab not in ("retail", "classic", "wotlk"):
        tab = "retail"
    realm = lab.realm_status(ctx["labcfg"], exp)
    note = ""
    if ctx.get("dev") and realm.get("error"):
        note = f'<p class="df-warn">{esc(realm.get("error"))}</p>'
    tabs = (
        ("retail", "World of Warcraft"),
        ("classic", "World of Warcraft Classic"),
        ("wotlk", "Wrath of the Lich King Classic"),
    )
    tab_html = "".join(
        f'<a class="df-tab{" df-tab-on" if key == tab else ""}" href="/wow/realmstatus?tab={key}">{esc(label)}</a>'
        for key, label in tabs
    )
    body_rows = []
    for name, kind, pop, zone, locale, up in _realm_rows(ctx, tab):
        mark = "df-up" if up else "df-down"
        body_rows.append(
            "<tr>"
            f'<td class="{mark}"></td>'
            f"<td>{esc(name)}</td><td>{esc(kind)}</td>"
            f'<td class="df-pop">{esc(pop)}</td><td>{esc(zone)}</td><td>{esc(locale)}</td>'
            "</tr>"
        )
    table = "".join(body_rows) or "<tr><td colspan=\"6\">No realms match.</td></tr>"
    sheet = f"""<div class="df-rs">
  <a class="df-rs-help" href="/support" aria-label="Support">Support</a>
  <header class="df-rs-head">
    <h1>Realm Status</h1>
    <p>This page lists all available World of Warcraft realms and has information on whether or not a realm is up or down. You can find more information about realm status and scheduled maintenances in the <a href="/forums/realm">Service Status Forum</a>. If your realm is listed as down, rest assured that we're aware of it and working diligently to bring it back online as quickly as possible.</p>
  </header>
  {note}
  <nav class="df-tabs" aria-label="Games">{tab_html}</nav>
  <form class="df-filters" method="get" action="/wow/realmstatus">
    <input type="hidden" name="tab" value="{esc(tab)}">
    <label>Region <select name="region"><option>Americas &amp; Oceania</option></select></label>
    <label>Locale <select name="locale"><option>All</option><option>United States</option></select></label>
    <label>Search <input name="q" value="{esc(_q(ctx.get('qs'), 'q'))}" placeholder="Realm Name"></label>
  </form>
  <table class="df-rs-table">
    <thead><tr><th>Status</th><th>Realm Name</th><th>Type</th><th>Population</th><th>Timezone</th><th>Locale</th></tr></thead>
    <tbody>{table}</tbody>
  </table>
  <footer class="df-rs-foot">
    <p><strong>DRAGONFLIGHT</strong> AVAILABLE NOW</p>
    <a href="/shop">BUY NOW</a>
  </footer>
</div>"""
    locale = _q(ctx.get("qs"), "locale", "All")
    photo = tab == "retail" and not _q(ctx.get("qs"), "q").strip() and locale in ("", "All")
    if photo:
        # November 2022 retail list. Other tabs and a search use the live table.
        inner = f"""<div class="df-rs df-photo">
  <img class="df-rstage" src="/static/img/dragonflight/realm-bg.jpg" alt="">
  <a class="df-hit df-hit-help" href="/support">Support</a>
  <a class="df-tab df-tab-on df-hit df-hit-tab1" href="/wow/realmstatus?tab=retail">World of Warcraft</a>
  <a class="df-tab df-hit df-hit-tab2" href="/wow/realmstatus?tab=classic">World of Warcraft Classic</a>
  <a class="df-tab df-hit df-hit-tab3" href="/wow/realmstatus?tab=wotlk">Wrath of the Lich King Classic</a>
  <a class="df-hit df-hit-forum" href="/forums/realm">Service Status Forum</a>
  <a class="df-hit df-hit-buy" href="/shop">BUY NOW</a>
  <form class="df-filters df-hit df-hit-find" method="get" action="/wow/realmstatus">
    <input type="hidden" name="tab" value="retail">
    <input name="q" aria-label="Search" placeholder="Realm Name">
  </form>
  <div class="df-sr">{sheet}</div>
</div>"""
    else:
        inner = sheet
    return _doc(exp, "Realm Status — World of Warcraft", inner, bool(ctx.get("dev")), "era-df-realms")


def _shop_doc(ctx) -> str:
    exp = ctx["exp"]
    q = _q(ctx.get("qs"), "q").strip().lower()
    cards = []
    for name, image in _MOUNTS:
        if q and q not in name.lower():
            continue
        cards.append(
            '<article class="df-mount">'
            f'<div class="df-art" style="background-image:url(\'/static/img/dragonflight/{esc(image)}\')"></div>'
            '<p class="df-game">World of Warcraft</p>'
            f"<h3>{esc(name)}</h3><p>Mounts</p><p class=\"df-price\">$25.00</p>"
            "</article>"
        )
    grid = "".join(cards) or "<p>No mounts match.</p>"
    sheet = f"""<div class="df-shophome">
  <header class="df-shopbar">
    <nav>
      <a href="/wow/">Warcraft</a>
      <span>Call of Duty</span>
      <span>Diablo</span>
      <span>Overwatch</span>
      <span>StarCraft</span>
      <span>More</span>
    </nav>
    <form class="df-shopsearch" method="get" action="/shop">
      <input name="q" value="{esc(_q(ctx.get('qs'), 'q'))}" placeholder="Search Shop" aria-label="Search Shop">
    </form>
    <a class="df-balance" href="/account/">Battle.net Balance</a>
  </header>
  <p class="df-shopcrumb"><a href="/shop">Shop</a> <span>›</span> World of Warcraft</p>
  <div class="df-shoplayout">
    <aside>
      <h1>Mounts</h1>
      <p>Saddle up, because your mount will travel as fast as your riding skill will take you.</p>
    </aside>
    <div class="df-mounts">{grid}</div>
  </div>
  <p class="df-shop-note">This shelf is a display. Nothing here is charged.</p>
</div>"""
    if not q:
        inner = f"""<div class="df-shophome df-photo">
  <img class="df-sstage" src="/static/img/dragonflight/shop-bg.jpg" alt="">
  <a class="df-hit df-s-wow" href="/wow/">Warcraft</a>
  <a class="df-hit df-s-balance" href="/account/">Battle.net Balance</a>
  <form class="df-shopsearch df-hit df-s-find" method="get" action="/shop">
    <input name="q" placeholder="Search Shop" aria-label="Search Shop">
  </form>
  <div class="df-sr">{sheet}</div>
</div>"""
    else:
        inner = sheet
    return _doc(exp, "Shop — World of Warcraft", inner, bool(ctx.get("dev")), "era-df-shop")


def _account_doc(ctx, mode: str) -> str:
    from wowweb import accounts
    from wowweb.account_ui import render_account

    exp = ctx["exp"]
    user = ctx.get("user") or ""
    summary = (
        accounts.account_summary(ctx["labcfg"], exp, user)
        if user
        else {"email": "", "characters": []}
    )
    body = render_account(
        exp,
        user=user,
        error="",
        notice="",
        mode=mode,
        email=summary.get("email") or "",
        characters=summary.get("characters") or [],
        login_kind="email" if accounts.email_login(exp) else "account",
        separate_game_name=exp.proto == "bnet",
    )
    titles = {
        "summary": "Account Overview",
        "login": "Log In",
        "create": "Create Account",
        "password": "Security",
    }
    return _doc(
        exp,
        f"{titles.get(mode, 'Account')} — Blizzard Account",
        body,
        bool(ctx.get("dev")),
        "era-df-account",
    )


def full(path: str, ctx: dict) -> str | None:
    if path in ("/account", "/account/login"):
        mode = "summary" if path == "/account" and ctx.get("user") else "login"
        return _account_doc(ctx, mode)
    if path == "/account/create":
        return _account_doc(ctx, "create")
    if path == "/account/password":
        if not ctx.get("user"):
            return None
        return _account_doc(ctx, "password")
    if path == "/shop":
        return _shop_doc(ctx)
    if path == "/forums":
        return _forums_doc(ctx)
    if path == "/wow/realmstatus":
        return _realm_doc(ctx)
    return None


def take(path: str, ctx: dict) -> tuple[str, str] | None:
    if path == "/wow/news":
        return "News", _news_body(ctx["exp"])
    if path in ("/wow/info", "/wow/info/introduction"):
        return "Game Guide", _guide_body(ctx["exp"])
    if path == "/forums/general":
        return _board_body(ctx, "general")
    if path == "/account/services":
        return _services_body(ctx)
    if path.startswith("/armory/character/"):
        name = path.rsplit("/", 1)[-1]
        if not name:
            return None
        from wowweb import armory

        char = armory.get_character(ctx["labcfg"], ctx["exp"], name)
        if not char:
            return None
        return str(char.get("name") or name), profile_body(ctx["exp"], char)
    return None
