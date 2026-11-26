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

# Connected-realm grid on forums-index-2019.jpg, reading order.
_REALMS = (
    "Aerie Peak", "Aman'Thul", "Area 52", "Arthas",
    "Baelgun", "Barthilas", "Blackrock", "Bleeding Hollow",
    "Burning Legion", "Cenarius", "Dalaran", "Darkspear",
    "Earthen Ring", "Emerald Dream", "Frostmourne", "Garona",
    "Garrosh", "Hyjal", "Illidan", "Kel'Thuzad",
    "Kil'jaeden", "Korgath", "Lightbringer", "Mal'Ganis",
    "Moon Guard", "Proudmoore", "Ravenholdt", "Sargeras",
    "Saurfang", "Shattered Hand", "Stormrage", "Stormreaver",
    "Thrall", "Tichondrius", "Turalyon", "Wyrmrest Accord",
    "Zul'jin",
    "Aegwynn, Bonechewer, Daggerspine, Gurubashi, and Hakkar",
    "Agamaggan, Archimonde, Jaedenar, and The Underbog",
    "Aggramar and Fizzcrank",
    "Akama, Dragonmaw, and Mug'thol",
    "Alleria and Khadgar",
    "Alexstrasza and Terokkar",
    "Altar of Storms, Anetheron, Magtheridon, and Ysondre",
    "Alterac Mountains, Balnazzar, Gorgonnash, The Forgotten Coast, and Warsong",
    "Andorhal, Scilla, Ursin, and Zuluhed",
    "Antonidas and Uldum",
    "Anub'arak, Chromaggus, Crushridge, Garithos, Nathrezim, and Smolderthorn",
    "Anvilmar and Undermine",
    "Arathor and Drenden",
    "Argent Dawn and The Scryers",
    "Arygos and Llane",
    "Auchindoun, Cho'gall, and Laughing Skull",
    "Azgalor, Azshara, Destromath, and Thunderlord",
    "Azjol-Nerub and Khaz Modan",
    "Azuremyst and Staghelm",
    "Baelgun and Doomhammer",
    "Black Dragonflight, Gul'dan, and Skullcrusher",
    "Blackhand and Galakrond",
    "Blackwater Raiders and Shadow Council",
    "Blackwing Lair, Dethecus, Detheroc, Haomarush, Lethon, and Shadowmoon",
    "Bladefist and Kul Tiras",
    "Blade's Edge and Thunderhorn",
    "Blood Furnace, Mannoroth, and Nazjatar",
    "Bloodhoof and Duskwood",
    "Bloodscalp, Boulderfist, Dunemaul, Maiev, and Stonemaul",
    "Borean Tundra and Shadowsong",
    "Bronzebeard and Shandris",
    "Burning Blade, Lightning's Blade, and Onyxia",
    "Caelestrasz and Nagrand",
    "Cairne and Perenolde",
    "Cenarion Circle and Sisters of Elune",
    "Coilfang, Dark Iron, Dalvengyr, and Demon Soul",
    "Dawnbringer and Madoran",
    "Darrowmere and Windrunner",
    "Dath'Remar and Khaz'goroth",
    "Deathwing, Executus, Kalecgos, and Shattered Halls",
    "Dentarg and Whisperwind",
    "Detheroc and Shadowmoon",
    "Draenor and Echo Isles",
    "Dragonblight and Fenris",
    "Draka and Suramar",
    "Drak'Tharon, Firetree, Malorne, Rivendare, Spirestone, and Stormscale",
    "Drak'thul and Skywall",
    "Dreadmaul and Thaurissan",
    "Durotan and Ysera",
    "Eitrigg and Shu'halo",
    "Eldre'Thalas and Korialstrasz",
    "Elune and Gilneas",
    "Eonar and Velen",
    "Eredar, Gorefiend, Spinebreaker, and Wildhammer",
    "Exodar and Medivh",
    "Farstriders, Silver Hand, and Thorium Brotherhood",
    "Feathermoon and Scarlet Crusade",
    "Frostmane, Ner'zhul, and Tortheldrin",
    "Frostwolf and Vashj",
    "Ghostlands and Kael'thas",
    "Gnomeregan and Moonrunner",
    "Greymane and Tanaris",
    "Grizzly Hills and Lothar",
    "Gundrak and Jubei'Thos",
    "Hellscream and Zangarmarsh",
    "Hydraxis and Terenas",
    "Icecrown and Malygos",
    "Kargath and Norgannon",
    "Kilrogg and Winterhoof",
    "Kirin Tor, Sentinels, and Steamwheedle Cartel",
    "Lightninghoof, Maelstrom, and The Venture Co",
    "Malfurion and Trollbane",
    "Misha and Rexxar",
    "Mok'Nathal and Silvermoon",
    "Muradin and Nordrassil",
    "Nazgrel, Nesingwary, and Vek'nilash",
    "Quel'dorei and Sen'jin",
    "Ravencrest and Uldaman",
    "Ravenholdt and Twisting Nether",
    "Runetotem and Uther",
)


def _svg(paths: str) -> str:
    return (
        '<svg class="bfa-ico" viewBox="0 0 24 24" aria-hidden="true" '
        'fill="none" stroke="currentColor" stroke-width="1.6" '
        'stroke-linejoin="round" stroke-linecap="round">'
        f"{paths}</svg>"
    )


_ICO = {
    "helm": _svg('<path d="M4 14a8 8 0 0 1 16 0v3H4z"/><path d="M8 17v2h8v-2M12 6v2"/>'),
    "axes": _svg('<path d="M4 20L14 8M8 4h6l2 4-6 2zM14 20L6 10M18 6l2 3-4 2"/>'),
    "shield": _svg('<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/>'),
    "help": _svg('<circle cx="12" cy="12" r="8"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7V14"/><path d="M12 17h.01"/>'),
    "head": _svg('<path d="M5 13a5 5 0 0 1 5-5h1a4 4 0 0 1 4 4v1h2a2 2 0 0 1 2 2v1H8"/><path d="M8 16v3M4 13h2"/>'),
    "bang": _svg('<path d="M12 4v10"/><path d="M12 18h.01"/>'),
    "swords": _svg('<path d="M5 4l8 8M4 8l4-4 2 2M14 14l5 5M19 4l-8 8M20 8l-4-4-2 2M10 14l-5 5"/>'),
    "knot": _svg('<path d="M8 8a3 3 0 1 1 4 4l-1 1a3 3 0 1 0 4 0M16 16a3 3 0 1 1-4-4l1-1a3 3 0 1 0-4 0"/>'),
    "globe": _svg('<circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c2.5 2.6 2.5 13.4 0 16M12 4c-2.5 2.6-2.5 13.4 0 16"/>'),
    "gem": _svg('<path d="M12 3l7 6-7 12L5 9z"/>'),
    "mug": _svg('<path d="M7 6h8v8a4 4 0 0 1-8 0z"/><path d="M15 8h2.5a2 2 0 0 1 0 4H15M8 4v2M11 4v2"/>'),
    "home": _svg('<path d="M4 11l8-7 8 7"/><path d="M7 10v9h10v-9"/>'),
    "w": _svg('<circle cx="12" cy="12" r="8" fill="currentColor" stroke="none"/>'),
}


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
    _ = user
    games = (
        ("/wow/", "World of Warcraft"),
        ("/classic", "WoW Classic"),
    )
    esports = (
        ("/esports", "Esports"),
        ("/wow/pvp/rankings", "PvP Rankings"),
    )
    mark = f'<img src="{_IMG}/blizzard.png" alt="Blizzard">'
    return (
        '<div class="bfa-blizz">'
        f'<a class="bfa-bmark" href="/wow/">{mark}</a>'
        '<nav class="bfa-blizz-nav" aria-label="Blizzard">'
        f"{_drop('Games', games, 'bfa-drop bfa-drop-lite')}"
        '<a href="/shop">Shop</a>'
        '<a href="/wow/news">News</a>'
        f"{_drop('Esports', esports, 'bfa-drop bfa-drop-lite')}"
        "</nav>"
        '<nav class="bfa-blizz-right" aria-label="Support">'
        '<a href="/support/">Support</a>'
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


def _fcard(icon: str, title: str, blurb: str, links: str) -> str:
    text = f"<p>{esc(blurb)}</p>" if blurb else ""
    return (
        '<section class="bfa-fcard">'
        '<header class="bfa-fhead">'
        f"{icon}<div><h2>{esc(title)}</h2>{text}</div></header>"
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
    left = [
        _fcard(
            _ICO["helm"],
            "Community",
            "Discuss World of Warcraft",
            b("general", "General Discussion") + "<span>Oceanic General Discussion</span>",
        ),
        _fcard(
            _ICO["shield"],
            "WoW Classic",
            "",
            "<span>WoW Classic General Discussion</span>"
            "<span>WoW Classic Support and Bug Report</span>"
            + b("guilds", "WoW Classic New Guild Listings")
            + "<span>Classic Connections 2004-2006 - Find People Here</span>",
        ),
        _fcard(
            _ICO["head"],
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
            _ICO["swords"],
            "PvP",
            "Discuss Arenas and Battleground here with your fellow players.",
            b("pvp", "Arenas") + b("pvp", "Battlegrounds") + b("pvp", "War Mode and World PvP"),
        ),
        _fcard(
            _ICO["globe"],
            "In Development",
            "Discuss our in-development content.",
            "<span>8.2.5 PTR General Discussion</span>"
            + "<span>8.2.5 Bug Report</span>"
            + _goto("/wow/info/classes", "BFA Items and Classes")
            + b("islands", "BFA Dungeons, Island Expeditions, and Raids")
            + _goto("/classic", "WoW Classic Beta Test"),
        ),
    ]
    right = [
        _fcard(_ICO["axes"], "Classes", "For all your class discussion needs.", classes),
        _fcard(
            _ICO["help"],
            "Guides",
            "New to World of Warcraft or returning after some time away? Come and join us.",
            _goto("/wow/info/basics", "New Player Help and Guides")
            + _goto("/wow/info", "Returning Player Help & Discussions")
            + b("ui", "UI and Macro"),
        ),
        _fcard(
            _ICO["bang"],
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
            _ICO["knot"],
            "Recruitment",
            "Searching for a guild or community? Or do you want to advertise yours? Come on in!",
            b("guilds", "Guild Recruitment")
            + "<span>Oceanic Guild Recruitment</span>"
            + "<span>Communities Recruitment</span>",
        ),
        _fcard(
            _ICO["gem"],
            "Lore",
            "Discuss World of Warcraft Lore or share your original fan fiction, or role-play.",
            b("general", "World's End Tavern: Role-play and Fan Fiction")
            + b("general", "Story Forum"),
        ),
        _fcard(
            _ICO["mug"],
            "Off-Topic",
            "For all your non-Blizzard game discussions.",
            "<span>Games, Gaming and Hardware</span>"
            + "<span>Movies, TV and Entertainment</span>"
            + "<span>Books and Comics</span>",
        ),
    ]
    # Boards the category grid did not name still have to open.
    used.add("realm")
    leftover = "".join(
        _goto(f"/forums/{slug}", title) for slug, title in boards.items() if slug not in used
    )
    if leftover:
        right.append(_fcard(_ICO["helm"], "This Realm", "Boards open on this realm.", leftover))
    realms = "".join(f'<li><a href="/forums/realm">{esc(name)}</a></li>' for name in _REALMS)
    who = "My Account"
    who_href = "/account/" if user else "/account/login"
    games = (("/wow/", "World of Warcraft"), ("/classic", "WoW Classic"))
    inner = f"""<div class="bfa-forums">
<header class="bfa-fbar">
  <a class="bfa-bmark" href="/wow/"><img src="{_IMG}/blizzard.png" alt="Blizzard"></a>
  <nav aria-label="Blizzard">
    {_drop("Games", games, "bfa-drop bfa-drop-lite")}
    <a href="/shop">Shop</a>
    <a href="/wow/news">News</a>
    {_drop("Esports", _ESPORTS, "bfa-drop bfa-drop-lite")}
  </nav>
  <nav class="bfa-fbar-right" aria-label="Account">
    <a href="/support/">Support</a>
    <a href="{esc(who_href)}">{esc(who)}</a>
  </nav>
</header>
<div class="bfa-fhero">
  <p class="bfa-fcrumb"><a href="/wow/" aria-label="Home">{_ICO["home"]}</a> <span>Forums</span></p>
  <a class="bfa-fhero-hit" href="/wow/">World of Warcraft</a>
</div>
<main class="bfa-fmain">
  <h1><span class="bfa-wcoin">W</span> All Categories</h1>
  <nav class="bfa-ftabs" aria-label="Forum views">
    <a class="on" href="/forums">Categories</a>
    <a href="/forums/general">Top</a>
    <a href="/forums/general">Latest</a>
    <a href="/wow/news">Blizz Tracker</a>
  </nav>
  <div class="bfa-fcols">
    <div class="bfa-fcol">{''.join(left)}</div>
    <div class="bfa-fcol">{''.join(right)}</div>
  </div>
  <section class="bfa-realms">
    <h2>{_ICO["globe"]} All Realms</h2>
    <ul>{realms}</ul>
  </section>
</main>
<footer class="bfa-ffoot">
  <p class="bfa-flang">{_ICO["globe"]} English (US)</p>
  <p class="bfa-fblizz"><img src="{_IMG}/blizzard.png" alt=""><span>Entertainment</span></p>
  <p class="bfa-fmeta">
    <span>Careers</span> | <span>About</span> | <a href="/support/">Support</a> |
    <span>Contact Us</span> | <span>Press</span> | <span>API</span>
  </p>
  <p>©2019 Blizzard Entertainment, Inc. All rights reserved.</p>
  <p>All trademarks referenced herein are the properties of their respective owners.</p>
  <p class="bfa-fmeta"><span>Privacy</span> | <span>Terms</span> | <span>Cookies</span></p>
  <div class="bfa-frating">
    <img src="{_IMG}/esrb.jpg" alt="ESRB Teen. Privacy Certified.">
    <ul>
      <li>Blood and Gore</li><li>Crude Humor</li><li>Suggestive Themes</li>
      <li>Use of Alcohol</li><li>Violence</li><li>Mild Language</li>
      <li>Users Interact</li><li>In-Game Purchases</li>
    </ul>
  </div>
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
    _ = exp, user
    inner = f"""<div class="bfa-shop">
<header class="bfa-shop-bar">
  <a class="bfa-shop-home" href="/wow/" aria-label="Home"></a>
  <nav aria-label="Shop">
    <a href="/wow/">Home</a>
    {_drop("Games", (("/wow/", "World of Warcraft"), ("/classic", "WoW Classic")), "bfa-drop bfa-drop-lite")}
    <a href="/account/services">Services</a>
    <a href="/shop">Blizzard Gear</a>
  </nav>
  <form action="/wow/search" method="get">
    <input type="search" name="q" aria-label="Search the shop" placeholder="Search the shop">
  </form>
  <nav class="bfa-shop-right" aria-label="Account">
    <a href="/account/">Wishlist</a>
    <a href="/account/">Blizzard Balance</a>
  </nav>
</header>
<div class="bfa-shop-banner">
  <img src="{_IMG}/shop-banner.jpg" alt="World of Warcraft Battle for Azeroth">
</div>
<nav class="bfa-shop-filters" aria-label="Browse">
  <a class="on" href="/shop">Great for new players</a>
  <a href="/shop">Games</a>
  <a href="/shop">Mounts</a>
  <a href="/shop">Pets</a>
  <a href="/shop">Toys</a>
  <a href="/shop">Packs</a>
  <a href="/account/services">Game Services</a>
  <a href="/shop">Gear</a>
  <span class="bfa-shop-tools">
    <span>Group by <b>Categories</b></span>
    <span>Sort by <b>Featured products</b></span>
  </span>
</nav>
<section class="bfa-shop-grid">
  <header>
    <h1>Great for new players</h1>
    <p>Just arrived in World of Warcraft? Start here.</p>
  </header>
  <article class="bfa-sku">
    <img src="{_IMG}/card-wow.jpg" alt="">
    <div class="bfa-sku-body">
      <p class="bfa-sku-mark">W</p>
      <h2>World of Warcraft®</h2>
      <p class="bfa-sku-lead">Begin your adventure in Azeroth today.</p>
      <p class="bfa-sku-kind">(MMORPG) Massively multiplayer online role-playing game</p>
      <p><a href="/wow/info">Information</a></p>
    </div>
  </article>
  <article class="bfa-sku">
    <img src="{_IMG}/card-collection.jpg" alt="">
    <div class="bfa-sku-body">
      <p class="bfa-sku-mark">W</p>
      <h2>World of Warcraft®: Complete Collection</h2>
      <p class="bfa-sku-lead">A new account is required.</p>
      <p class="bfa-sku-lead">Includes 30 days of game time.</p>
      <p class="bfa-sku-kind">(MMORPG) Massively multiplayer online role-playing game</p>
      <p class="bfa-price">From €49.99</p>
    </div>
  </article>
</section>
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
