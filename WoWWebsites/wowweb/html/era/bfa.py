"""July 2019 Battle for Azeroth community site (Rise of Azshara).

Home, forums index, and shop follow the accepted screenshots.
News, the game guide, realm status, and the armory profile use this shell.
There is no account screenshot. Character profiles are /armory/character/<name>
and are unreferenced.
"""

from __future__ import annotations

from .common import dev_note, document, esc, styles

_IMG = "/static/img/bfa"

# Copy under the hero on references/screenshots/bfa/home-2019-07.jpg.
_HERO = (
    "Battle for Azeroth's latest content update is here! Explore Nazjatar—home turf of "
    "the naga—and collect powerful Benthic gear. Travel to the lost isle of Mechagon "
    "and join the Rustbolt Resistance. Earn new Heritage Armor sets for tauren and "
    "gnomes, mount equipment, and more!"
)

# Frozen on that same capture, not a live clock.
_COUNTDOWN = (("52", "Days"), ("03", "Hours"), ("35", "Mins"), ("27", "Secs"))

_GAME = (
    ("/wow/info", "Game Guide"),
    ("/wow/info/classes", "Classes"),
    ("/wow/info/races", "Races"),
    ("/wow/info/professions", "Professions"),
    ("/wow/info/basics", "New Players"),
    ("/wow/realmstatus", "Realm Status"),
    ("/armory", "Armory"),
    ("/wow/info/patches", "Patch Notes"),
    ("/wow/pvp/rankings", "PvP Rankings"),
)

_ESPORTS = (
    ("/esports", "Arena World Championship"),
    ("/esports", "Mythic Dungeon International"),
)

_CLASSES = (
    ("deathknight", "Death Knight"),
    ("demonhunter", "Demon Hunter"),
    ("druid", "Druid"),
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

# Connected-realm names from the 2019 category index. The local realm is added first.
_REALMS = (
    "Aerie Peak", "Aman'Thul", "Antonidas", "Anvilmar",
    "Arathor", "Area 52", "Argent Dawn", "Arthas",
    "Azjol-Nerub", "Azshara", "Baelgun", "Barthilas",
    "Blackhand", "Blackrock", "Blackwing Lair", "Bleeding Hollow",
    "Bloodhoof", "Bonechewer", "Boulderfist", "Bronzebeard",
    "Burning Blade", "Burning Legion", "Cenarius", "Dalaran",
    "Darkspear", "Deathwing", "Demon Soul", "Detheroc",
    "Doomhammer", "Draenor", "Dragonblight", "Dragonmaw",
    "Durotan", "Earthen Ring", "Echo Isles", "Emerald Dream",
    "Eonar", "Eredar", "Executus", "Exodar",
    "Farstriders", "Feathermoon", "Frostwolf", "Garona",
    "Garrosh", "Gilneas", "Gnomeregan", "Gorefiend",
    "Greymane", "Grizzly Hills", "Gul'dan", "Hakkar",
    "Haomarush", "Hellscream", "Hyjal", "Icecrown",
    "Illidan", "Kael'thas", "Kalecgos", "Kel'Thuzad",
    "Khadgar", "Kil'jaeden", "Kilrogg", "Kirin Tor",
    "Lightbringer", "Lightning's Blade", "Llane", "Lothar",
    "Madoran", "Maelstrom", "Magtheridon", "Malfurion",
    "Mal'Ganis", "Malygos", "Mannoroth", "Medivh",
    "Moon Guard", "Mug'thol", "Nagrand", "Nazgrel",
    "Ner'zhul", "Nesingwary", "Nordrassil", "Onyxia",
    "Proudmoore", "Quel'Thalas", "Ragnaros", "Ravencrest",
    "Ravenholdt", "Rexxar", "Runetotem and Uther", "Sargeras",
    "Saurfang", "Scarlet Crusade", "Sen'jin", "Shadow Council",
    "Shattered Hand", "Silvermoon", "Skullcrusher", "Skywall",
    "Spirestone", "Staghelm", "Steamwheedle Cartel", "Stormrage",
    "Stormreaver", "Suramar", "Terenas", "Terokkar",
    "The Venture Co", "Thrall", "Thunderhorn", "Tichondrius",
    "Trollbane", "Turalyon", "Uldaman", "Uldum",
    "Vashj", "Vek'nilash", "Whisperwind", "Wildhammer",
    "Windrunner", "Wyrmrest Accord", "Ysera", "Zul'jin",
    "Zuluhed", "Aggramar",
)


def _menu(rows) -> str:
    return "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in rows)


def _drop(label: str, rows, css: str = "bfa-drop") -> str:
    return (
        f'<details class="{css}">'
        f"<summary>{esc(label)}</summary>"
        f'<div class="bfa-menu">{_menu(rows)}</div>'
        "</details>"
    )


def _account(user: str | None) -> str:
    if user:
        return (
            '<details class="bfa-user">'
            '<summary aria-label="Account"><span class="bfa-avatar"></span></summary>'
            '<div class="bfa-user-menu">'
            f'<p>Signed in as <strong>{esc(user)}</strong></p>'
            '<a href="/account/">Account</a>'
            '<a href="/account/logout">Log out</a>'
            "</div></details>"
        )
    return '<a class="bfa-login" href="/account/login">Log In</a>'


def _search() -> str:
    return (
        '<form class="bfa-search" action="/wow/search" method="get">'
        '<input type="search" name="q" aria-label="Search">'
        '<button type="submit" aria-label="Search"></button>'
        "</form>"
    )


def _blizz(user: str | None) -> str:
    games = (
        ("/wow/", "World of Warcraft"),
        ("/classic", "WoW Classic"),
    )
    esports = (
        ("/esports", "Esports"),
        ("/wow/pvp/rankings", "PvP Rankings"),
    )
    who = (
        f'<a href="/account/">My Account</a>'
        if user
        else '<a href="/account/login">Log In</a>'
    )
    return (
        '<div class="bfa-blizz">'
        '<a class="bfa-bmark" href="/wow/">Blizzard</a>'
        '<nav class="bfa-blizz-nav" aria-label="Blizzard">'
        f"{_drop('Games', games, 'bfa-drop bfa-drop-lite')}"
        '<a href="/shop">Shop</a>'
        '<a href="/wow/news">News</a>'
        f"{_drop('Esports', esports, 'bfa-drop bfa-drop-lite')}"
        "</nav>"
        '<nav class="bfa-blizz-right" aria-label="Support">'
        '<a href="/support/">Support</a>'
        f"{who}"
        "</nav></div>"
    )


def _subnav(user: str | None) -> str:
    # July 2019 bar: Game, News, Forums, Shop, Esports, WoW Classic. No Subscribe.
    return (
        '<div class="bfa-sub">'
        f'<a class="bfa-logo" href="/wow/"><img src="{_IMG}/logo.png" alt="World of Warcraft"></a>'
        '<nav class="bfa-subnav" aria-label="World of Warcraft">'
        f"{_drop('Game', _GAME)}"
        '<a href="/wow/news">News</a>'
        '<a href="/forums">Forums</a>'
        '<a href="/shop">Shop</a>'
        f"{_drop('Esports', _ESPORTS)}"
        '<a href="/classic">WoW Classic</a>'
        "</nav>"
        f"{_search()}"
        f"{_account(user)}"
        "</div>"
    )


def _legal() -> str:
    return '<footer class="bfa-legal">©2019 Blizzard Entertainment, Inc. All rights reserved.</footer>'


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online, login_error, crumb
    home = "bfa-home" in body
    doc_title = "World of Warcraft" if home else f"{title} — World of Warcraft"
    stage = body if home else f'<main class="bfa-sheet">{body}</main>'
    inner = f'<div class="bfa-site">{_blizz(user)}{_subnav(user)}{stage}{_legal()}</div>'
    return document(
        doc_title,
        styles("bfa"),
        "era-bfa era-bfa-home" if home else "era-bfa",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _news_list(news) -> str:
    rows = []
    for i, item in enumerate(news or []):
        title, date, body = item[0], item[1], item[2] if len(item) > 2 else ""
        copy = f"<p>{esc(body)}</p>" if body else ""
        rows.append(
            '<article class="bfa-news-item">'
            f'<time datetime="{esc(date)}">{esc(date)}</time>'
            f'<h3><a href="/wow/news/{i}">{esc(title)}</a></h3>'
            f"{copy}</article>"
        )
    if not rows:
        return "<p>No news posts yet.</p>"
    return "".join(rows)


def home_body(exp, news, realm, user) -> str:
    _ = user
    realm = realm or {}
    status = "Up" if realm.get("up") else "Down"
    name = realm.get("name") or getattr(exp, "realm_name", "")
    ticks = "".join(
        f"<li><b>{esc(num)}</b><span>{esc(label)}</span></li>" for num, label in _COUNTDOWN
    )
    return f"""<div class="bfa-home">
<section class="bfa-hero">
  <div class="bfa-hero-copy">
    <h1>RISE OF AZSHARA NOW LIVE!</h1>
    <p>{esc(_HERO)}</p>
    <p><a class="bfa-explore" href="/wow/info">Explore Battle for Azeroth</a></p>
    <p class="bfa-ctas">
      <a class="bfa-buy" href="/shop">Buy Now</a>
      <a class="bfa-trailer" href="/wow/media/screenshots">Launch Trailer</a>
    </p>
  </div>
</section>
<div class="bfa-rivets" aria-hidden="true"></div>
<section class="bfa-countdown" aria-label="WoW Classic global release">
  <p class="bfa-count-label"><strong>WoW Classic</strong><span>Global release in</span></p>
  <ol>{ticks}</ol>
</section>
<section class="bfa-latest">
  <h2>Latest News</h2>
  <p class="bfa-realm">Realm {esc(name)} is {esc(status)}.</p>
  {_news_list(news)}
</section>
</div>"""


def _board(boards: dict, used: set, slug: str, label: str) -> str:
    if slug in boards:
        used.add(slug)
        return f'<a href="/forums/{esc(slug)}">{esc(label)}</a>'
    return f"<span>{esc(label)}</span>"


def _goto(href: str, label: str) -> str:
    return f'<a href="{esc(href)}">{esc(label)}</a>'


def _fcard(title: str, blurb: str, links: str) -> str:
    text = f"<p>{esc(blurb)}</p>" if blurb else ""
    return (
        '<section class="bfa-fcard">'
        f"<h2>{esc(title)}</h2>{text}"
        f'<p class="bfa-flinks">{links}</p>'
        "</section>"
    )


def _forums_document(exp, user, dev: bool) -> str:
    from wowweb.forums import boards_for

    boards = dict(boards_for(exp))
    used: set[str] = set()

    def b(slug: str, label: str) -> str:
        return _board(boards, used, slug, label)

    classes = "".join(b(slug, label) for slug, label in _CLASSES)
    cards = [
        _fcard(
            "Community",
            "Discuss World of Warcraft",
            b("general", "General Discussion") + "<span>Oceanic General Discussion</span>",
        ),
        _fcard("Classes", "For all your class discussion needs.", classes),
        _fcard(
            "WoW Classic",
            "",
            "<span>WoW Classic General Discussion</span>"
            "<span>WoW Classic Support and Bug Report</span>"
            + b("guilds", "WoW Classic New Guild Listings")
            + "<span>Classic Connections 2004-2006 - Find People Here</span>",
        ),
        _fcard(
            "Guides",
            "New to World of Warcraft or returning after some time away? Come and join us.",
            _goto("/wow/info/basics", "New Player Help and Guides")
            + _goto("/wow/info", "Returning Player Help & Discussions")
            + b("ui", "UI and Macro"),
        ),
        _fcard(
            "Support",
            "Problem installing? In-game or account issues? Reporting bugs? Come and join us here in Support.",
            _goto("/support/", "Customer Support")
            + _goto("/wow/realmstatus", "Service Status")
            + _goto("/support/", "Technical Support")
            + "<span>Mac Technical Support</span>"
            + b("bugs", "Bug Report")
            + "<span>Website Bug Report</span>"
            + "<span>Mobile Bug Report</span>",
        ),
        _fcard(
            "Gameplay",
            "Gameplay discussion for World of Warcraft.",
            b("general", "Quests")
            + b("professions", "Professions")
            + "<span>Pet Battles</span>"
            + b("dungeons", "Dungeons, Raids and Scenarios")
            + "<span>Transmogrification</span>"
            + "<span>Achievements</span>",
        ),
        _fcard(
            "PvP",
            "Discuss Arenas and Battleground here with your fellow players.",
            b("pvp", "Arenas") + b("pvp", "Battlegrounds") + b("pvp", "War Mode and World PvP"),
        ),
        _fcard(
            "Recruitment",
            "Searching for a guild or community? Or do you want to advertise yours? Come on in!",
            b("guilds", "Guild Recruitment")
            + "<span>Oceanic Guild Recruitment</span>"
            + "<span>Communities Recruitment</span>",
        ),
        _fcard(
            "In Development",
            "Discuss our in-development content.",
            "<span>8.2.5 PTR General Discussion</span>"
            + "<span>8.2.5 Bug Report</span>"
            + _goto("/wow/info/classes", "BFA Items and Classes")
            + b("islands", "BFA Dungeons, Island Expeditions, and Raids")
            + _goto("/classic", "WoW Classic Beta Test"),
        ),
        _fcard(
            "Lore",
            "Discuss World of Warcraft Lore or share your original fan fiction, or role-play.",
            b("general", "World's End Tavern: Role-play and Fan Fiction")
            + b("general", "Story Forum"),
        ),
        _fcard(
            "Off-Topic",
            "For all your non-Blizzard game discussions.",
            "<span>Games, Gaming and Hardware</span>"
            + "<span>Movies, TV and Entertainment</span>"
            + "<span>Books and Comics</span>",
        ),
    ]
    leftover = "".join(
        _goto(f"/forums/{slug}", title) for slug, title in boards.items() if slug not in used
    )
    if leftover:
        cards.append(_fcard("This Realm", "Boards open on this realm.", leftover))
    names = [exp.realm_name] + [name for name in _REALMS if name != exp.realm_name]
    realms = "".join(f'<li><a href="/forums/realm">{esc(name)}</a></li>' for name in names)
    who = f'<a href="/account/">My Account</a>' if user else '<a href="/account/login">My Account</a>'
    inner = f"""<div class="bfa-forums">
<header class="bfa-fbar">
  <a class="bfa-bmark" href="/wow/">Blizzard</a>
  <nav aria-label="Blizzard">
    {_drop("Games", (("/wow/", "World of Warcraft"), ("/classic", "WoW Classic")), "bfa-drop bfa-drop-lite")}
    <a href="/shop">Shop</a>
    <a href="/wow/news">News</a>
    {_drop("Esports", _ESPORTS, "bfa-drop bfa-drop-lite")}
  </nav>
  <nav class="bfa-fbar-right" aria-label="Account">
    <a href="/support/">Support</a>
    {who}
  </nav>
</header>
<div class="bfa-fhero">
  <p class="bfa-fcrumb"><a href="/wow/">Home</a> <span>Forums</span></p>
  <a class="bfa-fhero-hit" href="/wow/">World of Warcraft</a>
</div>
<main class="bfa-fmain">
  <h1>All Categories</h1>
  <nav class="bfa-ftabs" aria-label="Forum views">
    <a class="on" href="/forums">Categories</a>
    <a href="/forums/general">Top</a>
    <a href="/forums/general">Latest</a>
    <a href="/wow/news">Blizz Tracker</a>
  </nav>
  <div class="bfa-fcats">{''.join(cards)}</div>
  <section class="bfa-realms">
    <h2>All Realms</h2>
    <ul>{realms}</ul>
  </section>
</main>
<footer class="bfa-ffoot">
  <p>English (US)</p>
  <p class="bfa-fblizz">Blizzard Entertainment</p>
  <p class="bfa-fmeta">
    <span>Careers</span> | <span>About</span> | <a href="/support/">Support</a> |
    <span>Contact Us</span> | <span>Press</span> | <span>API</span>
  </p>
  <p>©2019 Blizzard Entertainment, Inc. All rights reserved.</p>
  <p>All trademarks referenced herein are the properties of their respective owners.</p>
  <p class="bfa-fmeta"><span>Privacy</span> | <span>Terms</span> | <span>Cookies</span></p>
  <p class="bfa-frating"><strong>T</strong> Teen</p>
  <ul>
    <li>Blood and Gore</li><li>Crude Humor</li><li>Suggestive Themes</li>
    <li>Use of Alcohol</li><li>Violence</li><li>Mild Language</li>
    <li>Users Interact</li><li>In-Game Purchases</li>
  </ul>
</footer>
</div>"""
    return document(
        "Forums — World of Warcraft",
        styles("bfa"),
        "era-bfa era-bfa-forums",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def _shop_document(exp, user, dev: bool) -> str:
    _ = exp
    who = "My Account" if user else "Log In"
    who_href = "/account/" if user else "/account/login"
    inner = f"""<div class="bfa-shop">
<header class="bfa-shop-bar">
  <nav aria-label="Shop">
    <a href="/wow/">Home</a>
    <a href="/wow/">Games</a>
    <a href="/account/services">Services</a>
    <a href="/shop">Blizzard Gear</a>
  </nav>
  <form action="/wow/search" method="get">
    <input type="search" name="q" aria-label="Search the shop" placeholder="Search the shop">
  </form>
  <nav class="bfa-shop-right" aria-label="Account">
    <a href="/account/">Wishlist</a>
    <a href="{esc(who_href)}">{esc(who)}</a>
  </nav>
</header>
<div class="bfa-shop-banner">
  <img src="{_IMG}/shop-banner.jpg" alt="Battle for Azeroth">
</div>
<nav class="bfa-shop-filters" aria-label="Browse">
  <a href="/shop">Great for new players</a>
  <a href="/shop">Games</a>
  <a href="/shop">Mounts</a>
  <a href="/shop">Pets</a>
  <a href="/shop">Toys</a>
  <a href="/shop">Packs</a>
  <a href="/account/services">Game Services</a>
  <a href="/shop">Gear</a>
  <span>Group by Categories</span>
  <span>Sort by Featured products</span>
</nav>
<section class="bfa-shop-grid">
  <header>
    <h1>Great for new players</h1>
    <p>Just arrived in World of Warcraft? Start here.</p>
  </header>
  <article class="bfa-sku">
    <img src="{_IMG}/card-wow.jpg" alt="">
    <p class="bfa-sku-mark">W</p>
    <h2>World of Warcraft®</h2>
    <p class="bfa-sku-lead">Begin your adventure in Azeroth today.</p>
    <p class="bfa-sku-kind">(MMORPG) Massively multiplayer online role-playing game</p>
    <p><a href="/wow/info">Information</a></p>
  </article>
  <article class="bfa-sku">
    <img src="{_IMG}/card-collection.jpg" alt="">
    <p class="bfa-sku-mark">W</p>
    <h2>World of Warcraft®: Complete Collection</h2>
    <p class="bfa-sku-lead">A new account is required.</p>
    <p class="bfa-sku-lead">Includes 30 days of game time.</p>
    <p class="bfa-sku-kind">(MMORPG) Massively multiplayer online role-playing game</p>
    <p class="bfa-price">From €49.99</p>
  </article>
</section>
{_legal()}
</div>"""
    return document(
        "Shop — World of Warcraft",
        styles("bfa"),
        "era-bfa era-bfa-shop",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def full(path: str, ctx: dict) -> str | None:
    if path == "/shop":
        return _shop_document(ctx["exp"], ctx.get("user"), bool(ctx.get("dev")))
    if path == "/forums":
        return _forums_document(ctx["exp"], ctx.get("user"), bool(ctx.get("dev")))
    return None


def take(path: str, ctx: dict):
    if path == "/account/services" and not ctx.get("user"):
        body = (
            '<section class="bfa-gate">'
            "<h2>Character Services</h2>"
            "<p>Log in to manage characters on this realm.</p>"
            '<p><a href="/account/login">Log In</a></p>'
            "</section>"
        )
        return ("Character Services", body)
    if path == "/wow/news":
        from wowweb.content.news import news_for

        body = (
            '<section class="bfa-news">'
            "<h2>News</h2>"
            f"{_news_list(news_for(ctx['exp']))}"
            "</section>"
        )
        return ("News", body)
    return None
