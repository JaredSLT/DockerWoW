"""October 2007 community site, the 2008 forum index, and the desktop Armory.

Last patch 2.4.3. Community pages keep the left menu and parchment.
Forums and the Armory use the frames in their own screenshots.
News, boards, talent trees, and realm status come from the live modules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

from wowweb import armory, assets, content, forums, lab, talents

from .common import dev_note, document, esc, styles

_SHOT = "/static/img/ssotd-elwynn.jpg"
_HERO = "/static/img/hero-tbc.jpg"
_IMG = "/static/img/tbc"
_PAGE = 20

# Open sections match the 26 October 2007 home. Closed sections keep
# the same menu, including the Forums list from the upgrade receipt.
_NAV = (
    ("news", "News", False, (
        ("/wow/", "Current News"),
        ("/wow/news", "Archived News"),
    )),
    ("account", "Account", False, (
        ("/account/", "Account Management"),
        ("/account/login", "Log In"),
        ("/account/create", "Account Creation"),
        ("/account/retrieve", "Retrieve Password"),
        ("/account/", "Parental Controls"),
        ("/wow/realmstatus", "Realm Status"),
        ("/wow/info/patches", "Public Test Realm"),
    )),
    ("guide", "Game Guide", True, (
        ("/wow/info", "Game Guide"),
        ("/wow/info", "Introduction"),
        ("/wow/info/basics", "Getting Started"),
        ("/wow/info/races", "Character"),
        ("/wow/info", "Reputations"),
        ("/wow/info", "Items"),
        ("/wow/info/basics/map", "The World"),
        ("/wow/info", "Transportation"),
        ("/wow/info", "Player Interaction"),
        ("/wow/pvp/rankings", "Player vs Player"),
        ("/support/", "FAQ"),
        ("/story", "Story"),
        ("/wow/info", "Burning Crusade"),
        ("/wow/info", "Wrath of the Lich King"),
        ("/wow/info/patches", "Under Development"),
        ("/wow/info/patches", "Previous Patches"),
    )),
    ("workshop", "Workshop", True, (
        ("/armory", "Armory"),
        ("/armory/arena", "Arena"),
        ("/armory", "Game Statistics"),
        ("/wow/info/classes", "Talent Calculators"),
        ("/wow/news", "Events Calendar"),
        ("/wow/info", "Armor Sets"),
        ("/wow/info/basics/map", "World Map"),
        ("/wow/pvp/rankings", "Battlegroups"),
        ("/wow/search", "Encyclopedia"),
    )),
    ("media", "Media", False, (
        ("/wow/media/screenshots", "Overview"),
        ("/wow/media/screenshots", "Screenshots"),
        ("/wow/media/screenshots", "Movies"),
        ("/wow/media/screenshots", "Music"),
        ("/wow/media/wallpapers", "Wallpapers"),
        ("/wow/media/wallpapers", "Other Downloads"),
    )),
    ("forums", "Forums", True, (
        ("/forums/general", "General"),
        ("/forums/", "Class Forums"),
        ("/forums/realm", "Realm Forums"),
        ("/forums/guilds", "Guild Recruitment"),
        ("/forums/guildrelations", "Guild Relations"),
        ("/forums/support", "Support"),
    )),
    ("community", "Community", False, (
        ("/forums/", "Overview"),
        ("/wow/news", "Contests"),
        ("/wow/news", "Comics"),
    )),
    ("support", "Support", False, (
        ("/support/", "Customer Support"),
    )),
)

_QUICK = (
    ("/account/", "Account Management"),
    ("/account/", "Parental Controls"),
    ("/support/", "Support Site"),
    ("/wow/realmstatus", "Realm Status"),
    ("/account/create", "Account Creation"),
    ("/account/retrieve", "Retrieve Password"),
    ("/account/", "Account Security"),
    ("/wow/info/patches", "Latest Patch Notes"),
    ("/account/create", "Free 10-Day WoW Trial"),
)

_LEFT_SLOTS = ("Head", "Neck", "Shoulders", "Back", "Chest", "Shirt", "Tabard", "Wrists")
_RIGHT_SLOTS = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEAPON_SLOTS = ("Main Hand", "Off Hand", "Ranged")
_TABS = (
    ("sheet", "Character Sheet"),
    ("reputation", "Reputation"),
    ("skills", "Skills"),
    ("talents", "Talents"),
    ("arena", "Arena Teams"),
    ("guild", "Guild"),
)
_ALLIANCE = {"human", "dwarf", "night elf", "gnome", "draenei"}
_HORDE = {"orc", "undead", "tauren", "troll", "blood elf"}
_CLASS_SLUGS = {
    "warrior", "paladin", "hunter", "rogue", "priest", "shaman", "mage", "warlock", "druid",
}
_GAMEPLAY = {"pvp", "quests", "professions"}
_MAIN_ORDER = (
    "support", "bugs", "general", "guildrelations", "guilds", "suggestions", "rp", "ui", "realm",
)
_LABELS = {
    "support": "Customer Service Forum",
    "bugs": "Bug Report Forum",
    "general": "General Discussion",
    "guildrelations": "Guild Relations",
    "guilds": "Guild Recruitment",
    "realm": "Realm Status",
    "rp": "Role-Playing",
    "ui": "UI & Macros Forum",
    "suggestions": "Suggestions",
    "pvp": "PvP Discussion",
    "quests": "Quest Discussion",
    "professions": "Professions",
}
_BLURBS = {
    "support": "GM moderated forum to discuss in-game issues.",
    "bugs": "Found a bug in the game? Help us squash it by reporting it here.",
    "general": "Discuss World of Warcraft.",
    "guildrelations": "A place for the open discussion of any item important to guild structure.",
    "guilds": "Searching for a guild, or want to advertise yours? Come on in.",
    "realm": "Collection of important messages regarding the status of the Realms.",
    "suggestions": "Have a suggestion for World of Warcraft? Please post it here.",
    "rp": "Pull up a chair, drink a mug of ale, meet new friends, tell stories, and role-play.",
    "ui": "Work with other players to create your own special custom interfaces and macros.",
    "pvp": "Arena, battlegrounds, and other player-versus-player discussion.",
    "quests": "Quest discussion.",
    "professions": "Professions and crafting.",
}
_UPGRADE_LINKS = (
    ("/account/", "Add Game Card"),
    ("/account/", "Payment History"),
    ("/account/retrieve", "Account Name Retrieval"),
    ("/account/retrieve", "Password Retrieval"),
    ("/account/services", "Paid Name Change"),
    ("/account/services", "Paid Char Transfer"),
    ("/account/services", "Character Move"),
    ("/account/", "PTR Character Copy"),
    ("/account/", "Parental Controls"),
    ("/account/", "Recruit-a-Friend"),
    ("/account/services", "Scroll of Resurrection"),
)


def _kind(body: str) -> str:
    head = body.lstrip()[:120]
    if "tbc-forums" in head:
        return "forums"
    if "tbc-armory" in head:
        return "armory"
    if "tbc-wide" in head:
        return "wide"
    return "community"


def _shot(exp) -> str:
    shots = assets.screenshots(getattr(exp, "id", "tbc"))
    if shots:
        return shots[0][0]
    return _SHOT


def _who(user: str | None) -> str:
    if user:
        return (
            f'Signed in as <strong>{esc(user)}</strong>'
            f' · <a href="/account/">Account</a>'
            f' · <a href="/account/logout">Log Out</a>'
        )
    return '<a href="/account/login">Log In</a> · <a href="/account/create">Create Account</a>'


def _sites() -> str:
    return (
        '<nav class="tbc-sites">'
        '<a href="/wow/">WorldofWarcraft.com</a><span>|</span>'
        '<a href="/armory">The Armory</a><span>|</span>'
        '<a href="/forums">Forums</a>'
        "</nav>"
    )


def _search_form() -> str:
    return (
        '<div class="tbc-tools">'
        '<form class="tbc-search" action="/wow/search" method="get">'
        '<input type="text" name="q" aria-label="Search">'
        '<select name="searchType" aria-label="Search in">'
        '<option value="site">Community Site</option>'
        '<option value="encyclopedia">Encyclopedia</option>'
        '<option value="ingamesupport">In-game Support</option>'
        '<option value="techsupport">Tech Support</option>'
        "</select>"
        '<button type="submit">Search</button>'
        "</form>"
        '<details class="tbc-lang"><summary>Choose a Language</summary>'
        '<a href="/wow/">English</a></details>'
        "</div>"
    )


def _section(key: str, label: str, open_: bool, rows) -> str:
    links = "".join(f'<a href="{esc(href)}">{esc(text)}</a>' for href, text in rows)
    opened = " open" if open_ else ""
    return (
        f'<details class="tbc-sec tbc-sec-{key}"{opened}>'
        f"<summary>{esc(label)}</summary>"
        f'<div class="tbc-sub">{links}</div>'
        "</details>"
    )


def _nav() -> str:
    blocks = "".join(_section(key, label, open_, rows) for key, label, open_, rows in _NAV)
    return f'<nav class="tbc-nav">{blocks}</nav>'


def _rail(exp) -> str:
    links = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in _QUICK)
    shot = esc(_shot(exp))
    return f"""<aside class="tbc-rail">
  <a class="tbc-banner-link" href="/account/create"><img src="{_IMG}/download.jpg" alt="World of Warcraft. Download Now!"></a>
  <a class="tbc-banner-link" href="/wow/info"><img src="{_IMG}/wrath.jpg" alt="World of Warcraft: Wrath of the Lich King"></a>
  <div class="tbc-quick">
    <h3>Quick Links</h3>
    {links}
  </div>
  <div id="ssotd-container">
    <h3>Screenshot of the Day</h3>
    <a href="/wow/media/screenshots"><img src="{shot}" alt="Screenshot of the Day"></a>
    <a class="tbc-ssotd-submit" href="/forums/general">Submit your Shots to the RSPA</a>
  </div>
  <a class="tbc-banner-link" href="/account/burning-crusade-upgrade.html"><img src="{_IMG}/upgrade-box.jpg" alt="The Burning Crusade Digital Upgrade $39.99"></a>
  <a class="tbc-banner-link" href="/account/"><img src="{_IMG}/raf.jpg" alt="Recruit a Friend"></a>
  <div class="tbc-newcomers">
    <h3>Newcomers Section</h3>
    <p class="tbc-discover">Discover World of Warcraft</p>
    <p>Looking to purchase World of Warcraft? Follow the links below to learn more.</p>
    <a href="/wow/media/screenshots">Cinematic Trailer</a>
    <a href="/wow/info">Features Page</a>
    <a href="/shop">Online Store</a>
    <p class="tbc-journey">Begin Your Journey</p>
    <p>Lost in Azeroth? Find your way with our Beginner's Guide!</p>
    <a class="tbc-btn" href="/wow/info/basics">Beginner's Guide</a>
    <p>Read everything you ever wanted to know about Azeroth.</p>
    <a class="tbc-btn" href="/support/">General FAQ</a>
  </div>
</aside>"""


def _footer(kind: str) -> str:
    if kind == "forums":
        year = "&copy;2008"
    elif kind == "wide":
        year = "&copy;2004&ndash;2007"
    else:
        year = "&copy;2007"
    links = (
        '<a href="/support/">Online Privacy Policy</a>'
        ' | <a href="/support/">Legal Documents</a>'
        ' | <a href="/support/">Policies</a>'
    )
    if kind == "forums":
        return (
            f'<footer class="tbc-foot"><p class="tbc-copyear">{links}<br>'
            f"{year} Blizzard Entertainment. All rights reserved.</p></footer>"
        )
    return (
        f'<footer class="tbc-legal">'
        '<div class="tbc-esrb"><b>TEEN</b> Blood, Suggestive Themes, Use of Alcohol, Violence</div>'
        f'<p class="tbc-copyear">{links}<br>{year} Blizzard Entertainment. All rights reserved.</p>'
        '<div class="tbc-notice"><b>ESRB Notice:</b> Game Experience May Change During Online Play</div>'
        "</footer>"
    )


def _frame(kind: str, body: str, exp, user: str | None, login_error: str) -> str:
    err = f'<p class="tbc-login-err">{esc(login_error)}</p>' if login_error else ""
    who = f'<p class="tbc-who">{_who(user)}</p>' if user else ""
    top = f'<header class="tbc-top">{_sites()}</header>'
    if kind == "forums":
        return f"""<div class="tbc-site tbc-site-forums">
{top}
<div class="tbc-forum-head">
  <a href="/forums"><img src="{_IMG}/forum-logo.jpg" alt="World of Warcraft: The Burning Crusade"></a>
</div>
<div class="tbc-forum-frame">{body}</div>
{_footer(kind)}
</div>"""
    if kind == "armory":
        return f"""<div class="tbc-site tbc-site-armory">
{top}
<div class="tbc-armory-head">
  <a class="tbc-armory-logo" href="/armory"><img src="{_IMG}/armory-logo.jpg" alt="The Armory"></a>
  <div class="tbc-armory-center">
    <a href="/wow/"><img class="tbc-wowmark" src="{_IMG}/wow-logo.jpg" alt="World of Warcraft"></a>
    <form class="tbc-armory-find" action="/armory" method="get">
      <span>Quick Search</span>
      <select name="kind" aria-label="Quick Search"><option value="characters">Characters</option><option value="arena">Arena Teams</option></select>
      <input type="text" name="q" aria-label="Search the Armory">
      <button type="submit">Search</button>
    </form>
    <p class="tbc-armory-adv"><a href="/armory">Advanced Search</a> <a href="/armory/arena">Items</a></p>
  </div>
  <img class="tbc-elf" src="{_IMG}/elf.png" alt="">
</div>
<div class="tbc-armory-frame">{body}</div>
{_footer(kind)}
</div>"""
    rail = "" if kind == "wide" else _rail(exp)
    return f"""<div class="tbc-site">
{top}{err}
<div class="tbc-mast">
  <a class="tbc-logo" href="/wow/"><img src="{_IMG}/logo.jpg" alt="World of Warcraft: The Burning Crusade"></a>
  {_search_form()}
  {who}
</div>
<img class="tbc-side-left" src="{_IMG}/side-left.jpg" alt="">
<img class="tbc-side-right" src="{_IMG}/side-right.jpg" alt="">
<div class="tbc-frame">
  {_nav()}
  <div class="tbc-main">
    <div class="tbc-parch">{body}</div>
    {rail}
  </div>
</div>
{_footer(kind)}
</div>"""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = crumb, online
    kind = _kind(body)
    return document(
        f"{title} — World of Warcraft",
        styles("tbc"),
        "era-tbc",
        _frame(kind, body, exp, user, login_error),
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _stamp(iso: str) -> str:
    parts = (iso or "").split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = parts
        return f"{int(month):02d}-{int(day):02d}-{year[2:]}"
    return iso


def _byline(body: str) -> str:
    text = (body or "").strip().rstrip(".")
    if text.lower().startswith("posted by"):
        name = text.split(":", 1)[-1] if ":" in text else text[9:]
        return name.strip() or "Blizzard"
    return "Blizzard"


def _home_tail() -> str:
    return """<div class="tbc-lower">
<section class="tbc-spot">
  <h3>Community</h3>
  <p><strong>Community Spotlight.</strong> Machinima, fan art, and comics from players. Read the latest on the <a href="/wow/news">news page</a> or talk it over on the <a href="/forums/general">forums</a>.</p>
  <p><a href="/forums/general">Warcraft Weekly</a> · <a href="/wow/news">Spotlight Archive</a></p>
</section>
<div class="tbc-split">
  <div class="tbc-help"><h3>Need Help</h3><p>For support related issues, <a href="/support/">click here</a>.</p></div>
  <div class="tbc-jobs"><h3>Jobs</h3><p><a href="/wow/news">Blizzard is hiring.</a></p></div>
</div>
<div class="tbc-links">
  <div>
    <h3>WoW: Wrath of the Lich King</h3>
    <ul>
      <li><a href="/wow/info">Wrath of the Lich King</a></li>
      <li><a href="/wow/media/screenshots">Screenshots</a></li>
      <li><a href="/wow/info">Features</a></li>
      <li><a href="/wow/media/screenshots">Movies</a></li>
    </ul>
  </div>
  <div>
    <h3>Movies and Trailers</h3>
    <ul>
      <li><a href="/wow/media/screenshots">Lament of the Highborne</a></li>
      <li><a href="/wow/news">BlizzCon</a></li>
      <li><a href="/wow/media/wallpapers">Wallpapers</a></li>
      <li><a href="/wow/info/patches">Latest Patch Notes</a></li>
    </ul>
  </div>
</div>
<div class="tbc-split">
  <div class="tbc-insider">
    <h3>World of Warcraft Insider</h3>
    <p>Your source of up-to-date, behind the scenes information about World of Warcraft.</p>
    <p><a href="/wow/news">Latest issue</a></p>
  </div>
  <div class="tbc-store">
    <h3>Online Store</h3>
    <ul>
      <li><a href="/account/burning-crusade-upgrade.html">Burning Crusade Digital Upgrade</a></li>
      <li><a href="/shop">Online Store</a></li>
    </ul>
  </div>
</div>
<p class="tbc-blizz">BLIZZARD<span>ENTERTAINMENT</span></p>
</div>"""


def home_body(exp, news, realm, user) -> str:
    _ = user, realm
    stories = list(news) if news else content.news_for(exp)
    posts = []
    for i, (title, date, body) in enumerate(stories):
        copy = ""
        text = (body or "").strip()
        if text and not text.lower().startswith("posted by"):
            copy = f'<p class="tbc-copy">{esc(text)}</p>'
        posts.append(
            f'<article class="tbc-post">'
            f'<h2><a href="/wow/news/{i}">{esc(title)}</a></h2>'
            f'<p class="tbc-by"><a href="/wow/news/{i}">Posted by: {esc(_byline(text))}</a> | {esc(_stamp(date))}</p>'
            f"{copy}</article>"
        )
    return f"""<div class="tbc-home">
<div class="tbc-feature">
  <a href="/wow/media/screenshots"><img src="{_IMG}/feature.jpg" alt="Lament of the Highborne music video"></a>
  <p class="tbc-feature-nav"><a href="/wow/media/screenshots">Back</a><a href="/wow/news">Next</a></p>
</div>
<p class="tbc-credit">Fan art by Jiao Qiao</p>
<section class="tbc-news">{''.join(posts)}</section>
{_home_tail()}
</div>"""


def _news_archive(exp) -> str:
    posts = []
    for i, (title, date, body) in enumerate(content.news_for(exp)):
        posts.append(
            f'<article class="tbc-post">'
            f'<h2><a href="/wow/news/{i}">{esc(title)}</a></h2>'
            f'<p class="tbc-by">Posted by: {esc(_byline(body))} | {esc(_stamp(date))}</p>'
            f"</article>"
        )
    return f'<h2>Archived News</h2><section class="tbc-news">{"".join(posts)}</section>'


def _public_error(text: str) -> str:
    low = (text or "").lower()
    if not text:
        return ""
    if "mariadb" in low or "private server" in low or "recreation" in low:
        return "The realm database is not reachable."
    return text


def _qs(ctx: dict, key: str, default: str = "") -> str:
    raw = (ctx.get("qs") or {}).get(key)
    if isinstance(raw, list):
        return raw[0] if raw else default
    if raw is None:
        return default
    return str(raw)


def _realm_markup(exp, realm: dict) -> str:
    flag = "Up" if realm.get("up") else "Down"
    kind = realm.get("type") or "—"
    pop = realm.get("population")
    if pop in (None, ""):
        pop = "—"
    state = "up" if realm.get("up") else "down"
    return f"""<h2>Realm Status</h2>
<p>Realm status for {esc(getattr(exp, "name", ""))}.</p>
<table class="grid">
<tr><th>Status</th><th>Realm Name</th><th>Type</th><th>Population</th></tr>
<tr>
  <td class="{state}">{flag}</td>
  <td>{esc(realm.get("name") or getattr(exp, "realm_name", ""))}</td>
  <td>{esc(kind)}</td>
  <td>{esc(pop)}</td>
</tr>
</table>
<p>Messages about a realm belong on the <a href="/forums/realm">Realm Forums</a>.</p>"""


def _upgrade() -> str:
    def _line(rows) -> str:
        return " | ".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in rows)
    links = f"{_line(_UPGRADE_LINKS[:5])}<br>{_line(_UPGRADE_LINKS[5:])}"
    return f"""<div class="tbc-wide tbc-upgrade">
<nav class="tbc-acctbar">{links}</nav>
<h2>Upgrade Your Account</h2>
<p><span class="tbc-drop">C</span>ongratulations! You have successfully upgraded your World of Warcraft account.</p>
<p>You can launch your World of Warcraft: The Burning Crusade game client now and log in with your account. Enter the game and explore Outland, the new world waiting for you beyond the Dark Portal, and discover the countless secrets and rewards of this shattered realm.</p>
<p>If you would like to learn more about all the new features included in World of Warcraft: The Burning Crusade, you can check out the expansion <a href="/wow/info">features page</a> to learn more. And if you would like to modify your billing or account information, simply return to <a href="/account/">Account Management</a> now.</p>
<p>Thank you for purchasing World of Warcraft: The Burning Crusade. Best of luck in all your journeys, both in Azeroth... and beyond.</p>
<p>Blizzard Entertainment</p>
<div class="tbc-upgraded"><img src="{_IMG}/upgraded.jpg" width="468" height="280" alt="Account Upgraded"></div>
<p class="tbc-blizz">BLIZZARD<span>ENTERTAINMENT</span></p>
</div>"""


def full(path: str, ctx: dict) -> str | None:
    if path != "/account/burning-crusade-upgrade.html":
        return None
    exp = ctx["exp"]
    return shell(
        exp,
        "Upgrade Your Account",
        _upgrade(),
        ctx.get("user"),
        "Upgrade Your Account",
        bool(ctx.get("dev")),
    )


def _services_gate() -> str:
    return (
        "<h2>Character Services</h2>"
        "<p>Paid name changes and character transfers are available after you log in.</p>"
        '<p><a href="/account/login">Log In</a> · <a href="/account/create">Create Account</a></p>'
    )


def _boards(exp) -> list[tuple[str, str]]:
    rows = list(forums.boards_for(exp))
    slugs = {slug for slug, _title in rows}
    if "guildrelations" not in slugs:
        rows.append(("guildrelations", "Guild Relations"))
    return rows


def _label(slug: str, title: str) -> str:
    return _LABELS.get(slug, title)


def _board_card(slug: str, title: str) -> str:
    label = _label(slug, title)
    blurb = _BLURBS.get(slug, f"Discuss {label}.")
    return (
        f'<article class="tbc-board">'
        f'<a href="/forums/{esc(slug)}">{esc(label)}</a>'
        f"<p>{esc(blurb)}</p></article>"
    )


_INDEX_PAIRS = (
    (
        ("support", "Customer Service Forum", "GM moderated forum to discuss in-game issues."),
        ("bugs", "Bug Report Forum", "Found a bug in the game? Help us squash it by reporting it here!"),
    ),
    (
        ("tech", "Technical Support", "If you are experiencing problems installing or patching World of Warcraft, connecting to the realms or are crashing during game play, post here for assistance."),
        ("mac", "Mac Technical Support", "If you are experiencing problems installing or patching World of Warcraft, connecting to the realms or are crashing during game play, and you are using a Macintosh computer, post here for assistance."),
    ),
    (
        ("arena-tournament", "Arena Tournament", "A forum for players participating in the 2008 World of Warcraft Arena Tournament to discuss all aspects of the competition."),
        ("archive", "Blizzard Archive", "An archive of official Blizzard responses to various topics related to World of Warcraft."),
    ),
    (
        ("general", "General Discussion", "Discuss World of Warcraft."),
        ("guide", "Guide Forum", "Share your guides for classes, professions, leveling and more."),
    ),
    (
        ("guildrelations", "Guild Relations", "This forum is designed to be a place for the open discussion of any item important to guild structure."),
        ("guilds", "Guild Recruitment - Alliance", "Searching for an Alliance guild, or do you want to advertise your Alliance guild? Come on in!"),
    ),
    (
        ("guilds-horde", "Guild Recruitment - Horde", "Searching for a Horde guild, or do you want to advertise your horde guild? Come on in!"),
        ("offtopic", "Off-topic Discussion", "Off-topic posts of interest to the World of Warcraft community."),
    ),
    (
        ("realm", "Realm Status", "Collection of important messages regarding the status of the Realms."),
        ("rp", "Role-Playing", "Pull up a chair, drink a mug of ale, meet new friends, tell stories, and role-play in this forum."),
    ),
    (
        ("suggestions", "Suggestions", "Have a suggestion for World of Warcraft? Please post it here."),
        ("ui", "UI & Macros Forum", "Work with other players to create your own special custom interfaces and macros."),
    ),
    (
        ("welcome", "Welcome to WoW - A Beginner's Forum", "New to the World of Warcraft? Ask questions from experienced players and learn more about the adventures that await you!"),
        ("ptr", "Test Realm Forum", "Submit bugs and discuss changes from the latest World of Warcraft Public Test Realms."),
    ),
    (
        ("wrath", "Wrath of the Lich King", "Discuss the upcoming Wrath of the Lich King expansion."),
        ("starcraft", "StarCraft II", "Discuss Blizzard's upcoming RTS (Real Time Strategy) title, StarCraft II."),
    ),
    (
        ("invitational", "Worldwide Invitational Forum", "Discuss the Blizzard Worldwide Invitational happening this June in Paris!"),
        None,
    ),
)


def _index_card(row) -> str:
    if not row:
        return "<article class=\"tbc-board\"></article>"
    slug, label, blurb = row
    return (
        f'<article class="tbc-board">'
        f'<a href="/forums/{esc(slug)}">{esc(label)}</a>'
        f"<p>{esc(blurb)}</p></article>"
    )


def _forum_index(exp) -> str:
    rows = _boards(exp)
    by_slug = {slug: title for slug, title in rows}
    cells = []
    for left, right in _INDEX_PAIRS:
        cells.append(_index_card(left))
        cells.append(_index_card(right))
    play = "".join(
        _board_card(slug, by_slug[slug]) for slug in ("pvp", "quests", "professions") if slug in by_slug
    )
    classes = "".join(
        _board_card(slug, title) for slug, title in rows if slug in _CLASS_SLUGS
    )
    realm = _board_card("realm", by_slug["realm"]) if "realm" in by_slug else ""
    return f"""<div class="tbc-forums">
<h1>Forum Community</h1>
<div class="tbc-welcome">
  <div>
    <p><strong>Welcome to the World of Warcraft community forums!</strong></p>
    <p><span class="tbc-dropb">B</span>lizzard provides the World of Warcraft community forums for its players to chat, exchange ideas, and submit feedback. Posting on the World of Warcraft community forums requires a World of Warcraft account. Only customers are allowed to post on these forums, but anyone can read them. Please note that you must adhere to the <a href="/support/">Forum Guidelines</a> if you wish to post on the forums.</p>
  </div>
  <aside class="tbc-aside">
    <p><strong>New to the forums?</strong></p>
    <p>Read our <a href="/wow/info/basics">Introduction to the Forums</a>. This includes information about getting started, forum features, forum icons, and more.</p>
    <p><strong>Found a bad post or account name?</strong></p>
    <p>If you find a bad forum post or account name that violates the forum guidelines, you can report it <a href="/support/">here</a>.</p>
  </aside>
</div>
<div class="tbc-boardgrid">{''.join(cells)}</div>
<details class="tbc-fold">
  <summary>Gameplay Discussion Forums<p>Various forums related to the discussion of in-game topics.</p></summary>
  <div class="tbc-boardgrid">{play}</div>
</details>
<details class="tbc-fold">
  <summary>Classes<p>Discuss your favorite class.</p></summary>
  <div class="tbc-boardgrid">{classes}</div>
</details>
<details class="tbc-fold">
  <summary>WoW Realm Forums<p>Discuss topics related to World of Warcraft with players on your specific realm.</p></summary>
  <div class="tbc-boardgrid">{realm}</div>
</details>
<details class="tbc-fold" open>
  <summary>Battlegroup Forums<p>Discuss your latest wins and losses with your Battlegroup and show off your realm pride!</p></summary>
  <p class="tbc-bg">Don't know which Battlegroup your realm is in? Click <a href="/wow/pvp/rankings">here</a> to find out!</p>
</details>
</div>"""


def _extra_titles() -> dict[str, str]:
    found = {"guildrelations": "Guild Relations"}
    for left, right in _INDEX_PAIRS:
        for row in (left, right):
            if row:
                found[row[0]] = row[1]
    return found


def _resolve_board(exp, slug: str) -> str | None:
    title = forums.board_title(exp, slug)
    if title:
        return title
    return _extra_titles().get(slug)


def _when(value) -> str:
    try:
        stamp = int(value or 0)
    except (TypeError, ValueError):
        return ""
    if stamp <= 0:
        return ""
    return datetime.fromtimestamp(stamp, timezone.utc).strftime("%m/%d/%y")


def _login_box(user: str | None) -> str:
    if user:
        return f'<p class="tbc-flogin">Signed in as <strong>{esc(user)}</strong></p>'
    return (
        '<form class="tbc-flogin" method="post" action="/account/login">'
        '<label>Account <input name="identity" autocomplete="username"></label>'
        '<label>Password <input type="password" name="password" autocomplete="current-password"></label>'
        '<button type="submit">Login</button>'
        '<a href="/support/">Help</a>'
        "</form>"
    )


def _thread_rows(slug: str, threads: list[dict], page: int) -> tuple[str, str]:
    pages = max(1, (len(threads) + _PAGE - 1) // _PAGE)
    page_n = min(max(page, 1), pages)
    start = (page_n - 1) * _PAGE
    rows = []
    for thread in threads[start : start + _PAGE]:
        last = _when(thread.get("last") or thread.get("created"))
        rows.append(
            "<tr>"
            f'<td class="tbc-subject"><a href="/forums/{esc(slug)}/{esc(thread["id"])}">{esc(thread["title"])}</a></td>'
            f'<td>{esc(thread.get("author"))}</td>'
            f'<td>{esc(thread.get("replies") or 0)}</td>'
            f'<td>{esc(thread.get("views") or 0)}</td>'
            f'<td class="tbc-last">{esc(last)}<br>{esc(thread.get("author"))}</td>'
            "</tr>"
        )
    body = "".join(rows) or '<tr class="tbc-empty"><td colspan="5">No threads yet.</td></tr>'
    links = []
    if pages > 1:
        for number in range(1, pages + 1):
            mark = ' class="is-on"' if number == page_n else ""
            links.append(f'<a{mark} href="?page={number}">{number}</a>')
    pager = f'<p class="tbc-pager">{"".join(links)}</p>' if links else ""
    return body, pager


def _post_form(slug: str, user: str | None) -> str:
    if not user:
        return '<p><a href="/account/login">Log in</a> with a realm account to post.</p>'
    return (
        f'<form class="tbc-postform" method="post" action="/forums/{esc(slug)}/new">'
        '<label>Title <input name="title" required maxlength="120"></label>'
        '<label>Body <textarea name="body" required rows="5"></textarea></label>'
        '<button type="submit">Post</button></form>'
    )


def _forum_board(exp, slug: str, title: str, threads: list[dict], user, page: int) -> str:
    rows, pager = _thread_rows(slug, threads, page)
    heading = _label(slug, title)
    if not heading.lower().endswith("forum"):
        heading = f"{heading} Forum"
    return f"""<div class="tbc-forums tbc-one-board">
<div class="tbc-boardtop">
  <div>
    <p class="tbc-crumb"><a href="/forums">Forum Community</a> · {esc(heading)}</p>
    <h1>{esc(heading)}</h1>
  </div>
  {_login_box(user)}
</div>
<p class="tbc-boardtools"><a href="#post">New Topic</a> <a href="/wow/search">Quick Search</a> <a href="/wow/search">Advanced Search</a></p>
<table class="tbc-threads">
<thead><tr><th>Subject</th><th>Author</th><th>Replies</th><th>Views</th><th>Last Post</th></tr></thead>
<tbody>{rows}</tbody>
</table>
{pager}
<div id="post">{_post_form(slug, user)}</div>
</div>"""


def _forum_thread(exp, slug: str, thread: dict, user) -> str:
    _ = exp
    posts = []
    for post in thread.get("posts") or []:
        posts.append(
            f'<article class="tbc-fpost"><header>{esc(post.get("author"))}'
            f' · {esc(_when(post.get("created")))}</header>'
            f"<pre>{esc(post.get('body'))}</pre></article>"
        )
    form = ""
    if user:
        form = (
            f'<form class="tbc-postform" method="post" action="/forums/{esc(slug)}/{esc(thread["id"])}/reply">'
            '<label>Reply <textarea name="body" required rows="5"></textarea></label>'
            '<button type="submit">Reply</button></form>'
        )
    else:
        form = '<p><a href="/account/login">Log in</a> to reply.</p>'
    return (
        f'<div class="tbc-forums tbc-one-board">'
        f'<p class="tbc-crumb"><a href="/forums">Forum Community</a> · '
        f'<a href="/forums/{esc(slug)}">{esc(slug)}</a></p>'
        f'<h1>{esc(thread.get("title"))}</h1>{"".join(posts)}{form}</div>'
    )


def _forum_take(path: str, ctx: dict):
    exp = ctx["exp"]
    parts = [part for part in path.split("/") if part]
    if len(parts) == 1:
        return "Forum Community", _forum_index(exp)
    if len(parts) < 2:
        return None
    slug = parts[1]
    title = _resolve_board(exp, slug)
    if title is None:
        return None
    data_dir = ctx.get("data_dir")
    if data_dir is None:
        threads: list[dict] = []
        thread = None
    else:
        conn = forums.connect(data_dir)
        try:
            forums.seed_if_empty(conn, exp)
            if len(parts) == 3 and parts[2].isdigit():
                thread = forums.get_thread(conn, exp, int(parts[2]))
                threads = []
            else:
                thread = None
                threads = forums.list_threads(conn, exp, slug)
        finally:
            conn.close()
    if len(parts) == 3 and parts[2].isdigit():
        if not thread:
            return None
        return thread["title"], _forum_thread(exp, slug, thread, ctx.get("user"))
    if len(parts) != 2:
        return None
    try:
        page = int(_qs(ctx, "page", "1") or "1")
    except ValueError:
        page = 1
    return title, _forum_board(exp, slug, title, threads, ctx.get("user"), page)


def _faction(race: str) -> str:
    key = (race or "").strip().lower()
    if key in _ALLIANCE:
        return "Alliance"
    if key in _HORDE:
        return "Horde"
    return ""


def _mini(exp, kind: str, name: str) -> str:
    if kind == "race":
        src = assets.race_icon(exp.id, (name or "").lower().replace(" ", ""))
    else:
        src = assets.class_icon(exp.id, (name or "").lower().replace(" ", ""))
    if not src:
        return ""
    return f'<img class="tbc-mini" src="{esc(src)}" alt="">'


def search_markup(exp, rows: list[dict], q: str, error: str = "") -> str:
    body = []
    for row in rows:
        name = row.get("name") or ""
        href = "/armory/character/" + quote(str(name), safe="")
        guild = row.get("guild") or "—"
        faction = row.get("faction") or _faction(str(row.get("race") or ""))
        fac_cls = "tbc-fac-alliance" if faction == "Alliance" else "tbc-fac-horde" if faction == "Horde" else "tbc-fac"
        body.append(
            "<tr>"
            f'<td><a href="{esc(href)}">{esc(name)}</a></td>'
            f'<td>{esc(row.get("level"))}</td>'
            f'<td>{_mini(exp, "race", row.get("race"))}{esc(row.get("race"))}</td>'
            f'<td>{_mini(exp, "class", row.get("class"))}{esc(row.get("class"))}</td>'
            f'<td><span class="{fac_cls}" title="{esc(faction)}"></span>{esc(faction)}</td>'
            f"<td>{esc(guild)}</td>"
            f'<td>{esc(row.get("realm") or getattr(exp, "realm_name", ""))}</td>'
            "</tr>"
        )
    note = _public_error(error)
    if not body:
        message = note or ("Enter a name to search." if not q else "No characters found.")
        body.append(f'<tr><td colspan="7">{esc(message)}</td></tr>')
    err = f'<p class="tbc-armory-err">{esc(note)}</p>' if note else ""
    return f"""<div class="tbc-armory">
<h1>Search</h1>
<p>Search characters on {esc(getattr(exp, "realm_name", ""))}.</p>
<nav class="tbc-result-tabs"><a class="is-on" href="/armory">Characters</a><a href="/armory/arena">Arena Teams</a></nav>
{err}
<p class="tbc-pageline">1 of 1</p>
<table class="tbc-results">
<thead><tr><th>Name</th><th>Level</th><th>Race</th><th>Class</th><th>Faction</th><th>Guild</th><th>Realm</th></tr></thead>
<tbody>{''.join(body)}</tbody>
</table>
<p class="tbc-pageline">1 of 1</p>
</div>"""


def _armory_search(ctx: dict):
    exp = ctx["exp"]
    q = _qs(ctx, "q", "").strip()
    rows: list[dict] = []
    error = ""
    cfg = ctx.get("labcfg")
    if q and cfg is not None:
        rows, error = armory.search_with_status(cfg, exp, q)
    return "The Armory", search_markup(exp, rows, q, error)


def _equipped(char: dict) -> dict[str, dict]:
    found = {}
    for item in char.get("equipment") or []:
        slot = str(item.get("slot") or "")
        if slot:
            found[slot] = item
    return found


def _slot(exp, name: str, item: dict | None) -> str:
    if not item or not item.get("item_id"):
        return f'<span class="tbc-slot" title="{esc(name)}"></span>'
    icon = assets.display_icon(exp, item.get("display_id"))
    img = f'<img src="{esc(icon)}" alt="">' if icon else ""
    label = item.get("name") or name
    return (
        f'<a class="tbc-slot" href="/armory/item/{esc(item["item_id"])}" title="{esc(label)}">{img}</a>'
    )


def _slots(exp, names, equipped) -> str:
    return "".join(_slot(exp, name, equipped.get(name)) for name in names)


def _stat_line(label: str) -> str:
    return f"<li><span>{esc(label)}</span><b>—</b></li>"


def _profile(exp, char: dict) -> str:
    equipped = _equipped(char)
    resists = ("Arcane", "Fire", "Nature", "Frost", "Shadow")
    stats = ("Strength", "Agility", "Stamina", "Intellect", "Spirit", "Armor")
    spell = ("Bonus Damage", "Bonus Healing", "Hit Rating", "Crit Chance", "Penetration", "Mana Regen")
    guild = (char.get("guild") or {}).get("name") or ""
    guild_html = f"&lt;{esc(guild)}&gt;" if guild else "No guild"
    return f"""<div class="tbc-profile">
<p class="tbc-ribbon">Profile</p>
<div class="tbc-doll">
  <div class="tbc-slots">{_slots(exp, _LEFT_SLOTS, equipped)}</div>
  <div class="tbc-mid">
    <h3>Talent Specialization</h3>
    <p class="tbc-spec"><a href="?tab=talents">Talents</a></p>
    <h3>Primary Professions</h3>
    <p>Not recorded on this logout.</p>
    <h3>Resistances</h3>
    <ul class="tbc-res">{''.join(_stat_line(name) for name in resists)}</ul>
    <p class="tbc-bars"><span class="tbc-hp">Health <b>—</b></span><span class="tbc-mp">Mana <b>—</b></span></p>
    <div class="tbc-statcols">
      <div><h3>Base Stats</h3><ul>{''.join(_stat_line(name) for name in stats)}</ul></div>
      <div><h3>Spell</h3><ul>{''.join(_stat_line(name) for name in spell)}</ul></div>
    </div>
  </div>
  <div class="tbc-slots">{_slots(exp, _RIGHT_SLOTS, equipped)}</div>
  <div class="tbc-weapons">{_slots(exp, _WEAPON_SLOTS, equipped)}</div>
</div>
<p class="tbc-updated">Last Updated: —</p>
<p class="tbc-guildline">{guild_html}</p>
<section class="tbc-arena-block"><h3>Arena</h3><p>2v2 · 3v3 · 5v5</p><p><a href="/armory/arena">More Arena Teams</a></p></section>
</div>"""


def _trees(exp, class_name: str) -> str:
    slug = (class_name or "").lower().replace(" ", "").replace("-", "")
    trees = talents.trees_for(exp, slug)
    if not trees:
        return "<p>No talent trees for this class.</p>"
    columns = []
    for index, tree in enumerate(trees):
        cells = []
        for tal in tree.talents:
            icon = assets.talent_icon(exp, tal.name)
            img = f'<img src="{esc(icon)}" alt="">' if icon else ""
            cells.append(
                f'<div class="tbc-tal" style="grid-column:{tal.col + 1};grid-row:{tal.row + 1}" '
                f'title="{esc(tal.name)}">{img}<b>0/{esc(tal.max_rank)}</b></div>'
            )
        columns.append(
            f'<section class="tbc-tree tbc-tree-{index}">'
            f"<h3>{esc(tree.name)}</h3>"
            f'<div class="tbc-talgrid">{"".join(cells)}</div>'
            f'<p class="tbc-points">{esc(tree.name)}: 0</p></section>'
        )
    points = talents.points_available(exp)
    return (
        f'<p class="tbc-ribbon">Talents</p>'
        f'<p class="tbc-pointcap">{esc(points)}-point cap</p>'
        f'<div class="tbc-trees">{"".join(columns)}</div>'
    )


def _roster(exp, char: dict, guild: dict | None) -> str:
    info = guild or {}
    name = info.get("name") or (char.get("guild") or {}).get("name") or ""
    if not name:
        return '<aside class="tbc-roster"><h3>Guild</h3><p>No guild.</p></aside>'
    me = (char.get("name") or "").lower()
    items = []
    for member in info.get("members") or []:
        mark = " is-self" if str(member.get("name") or "").lower() == me else ""
        href = "/armory/character/" + quote(str(member.get("name") or ""), safe="")
        items.append(
            f'<li class="{mark.strip()}">'
            f'<a href="{esc(href)}">{esc(member.get("name"))}</a>'
            f'{_mini(exp, "class", member.get("class"))}'
            f'<span>level {esc(member.get("level"))}</span></li>'
        )
    if not items:
        items.append("<li>Roster is not on this logout.</li>")
    return (
        f'<aside class="tbc-roster"><h3>Guild Roster for &quot;{esc(name)}&quot;</h3>'
        f'<ul>{"".join(items)}</ul></aside>'
    )


def character_markup(exp, char: dict, tab: str, guild: dict | None = None) -> str:
    chosen = tab if tab in {key for key, _label in _TABS} else "sheet"
    name = char.get("name") or ""
    base = "/armory/character/" + quote(str(name), safe="")
    tabs = []
    for key, label in _TABS:
        href = base if key == "sheet" else f"{base}?tab={key}"
        mark = " is-on" if key == chosen else ""
        tabs.append(f'<a class="{mark.strip()}" href="{esc(href)}">{esc(label)}</a>')
    if chosen == "talents":
        center = _trees(exp, str(char.get("class") or ""))
    elif chosen == "reputation":
        center = "<h2>Reputation</h2><p>No reputation data on this logout.</p>"
    elif chosen == "skills":
        center = "<h2>Skills</h2><p>No skill data on this logout.</p>"
    elif chosen == "arena":
        center = (
            "<h2>Arena Teams</h2><p>No arena team is stored for this character.</p>"
            '<p><a href="/armory/arena">Arena</a></p>'
        )
    else:
        center = _profile(exp, char)
    icon = assets.class_icon(exp.id, (char.get("class") or "").lower().replace(" ", ""))
    portrait = f'<img class="tbc-portrait" src="{esc(icon)}" alt="">' if icon else '<span class="tbc-portrait"></span>'
    guild_name = (char.get("guild") or {}).get("name") or ""
    guild_html = f"&lt;{esc(guild_name)}&gt;" if guild_name else ""
    level = esc(char.get("level"))
    race = esc(char.get("race"))
    klass = esc(char.get("class"))
    return f"""<div class="tbc-armory">
<nav class="tbc-tabs">{''.join(tabs)}</nav>
<div class="tbc-sheet">
  <div class="tbc-sheet-main">
    <header class="tbc-ident">
      <div class="tbc-portrait-wrap">{portrait}<span class="tbc-level">{level}</span></div>
      <div>
        <h1>{esc(name)}</h1>
        <p class="tbc-gname">{guild_html}</p>
        <p>Level {level} {race} {klass}</p>
        <p>{esc(char.get("realm") or getattr(exp, "realm_name", ""))}</p>
      </div>
    </header>
    {center}
  </div>
  {_roster(exp, char, guild)}
</div>
</div>"""


def _character_take(path: str, ctx: dict):
    name = path.rsplit("/", 1)[-1]
    if not name:
        return _armory_search(ctx)
    cfg = ctx.get("labcfg")
    if cfg is None:
        return None
    char = armory.get_character(cfg, ctx["exp"], name)
    if not char:
        return None
    guild = None
    gname = (char.get("guild") or {}).get("name")
    if gname:
        guild = armory.get_guild(cfg, ctx["exp"], gname)
    tab = _qs(ctx, "tab", "sheet")
    return char["name"], character_markup(ctx["exp"], char, tab, guild)


def take(path: str, ctx: dict):
    exp = ctx.get("exp")
    if path == "/account/services" and not ctx.get("user"):
        return "Character Services", _services_gate()
    if path == "/wow/news":
        return "Archived News", _news_archive(exp)
    if path == "/wow/realmstatus":
        cfg = ctx.get("labcfg")
        if cfg is None:
            realm = {"name": getattr(exp, "realm_name", ""), "up": False, "type": "", "population": ""}
        else:
            realm = lab.realm_status(cfg, exp)
            realm = {
                "name": realm.get("name"),
                "up": realm.get("up"),
                "type": realm.get("type"),
                "population": realm.get("population"),
            }
        return "Realm Status", _realm_markup(exp, realm)
    if path == "/forums" or path.startswith("/forums/"):
        return _forum_take(path, ctx)
    if path in ("/armory", "/armory/character"):
        return _armory_search(ctx)
    if path.startswith("/armory/character/"):
        return _character_take(path, ctx)
    return None
