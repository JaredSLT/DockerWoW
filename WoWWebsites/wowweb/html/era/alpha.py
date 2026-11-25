"""June 2004 beta community home, and the separate 2001 announcement site.

Layout follows accepted alpha rows in references/screenshots/LEDGER.md.
"""

from __future__ import annotations

import time
from pathlib import Path

from .common import dev_note, document, esc, styles

# June 2004 left rail. Labels match beta-home-2004-06.png, top to bottom.
_NAV = (
    (
        None,
        (
            ("/wow/", "Current News"),
            ("/wow/news", "Archived News"),
        ),
    ),
    (
        "Game Info",
        (
            ("/wow/info/races", "Races"),
            ("/wow/info/classes", "Classes"),
            ("/wow/info/basics", "Basics"),
            ("/wow/info/professions", "Trade Skills"),
            ("/wow/info/", "Items"),
        ),
    ),
    (
        "Forums",
        (
            ("/forums/general", "General"),
            ("/forums/quests", "Quest Discussion"),
            ("/forums/pvp", "PvP Discussion"),
            ("/forums/offtopic", "Off-topic"),
            ("/forums/guilds", "Guild Recruitment"),
            ("/forums/trading", "Trading Post"),
            ("/forums/rp", "Role-playing"),
            ("/forums/ui", "UI Customization"),
            ("/forums/suggestions", "Suggestions"),
            ("/forums/professions", "Trade Skills"),
            ("/forums/classes", "Classes"),
            ("/forums/realm", "Server Status"),
        ),
    ),
    (
        "Support",
        (
            ("/support/", "Technical Support"),
            ("/wow/info/patches", "Beta Readme"),
            ("/support/stuck", "Game Masters"),
            ("/support/", "Policies"),
            ("/forums/support", "Support Forum"),
        ),
    ),
    (
        "Links / Files",
        (
            ("/wow/media/wallpapers", "Desktop\nWallpaper"),
            ("/wow/media/screenshots", "Movies and Music"),
            ("/wow/info/", "Fan Site Program"),
            ("/story", "More about WoW"),
        ),
    ),
)

_YNAV = (
    ("updates", "/announce", "updates"),
    ("features", "/announce/features", "features"),
    ("screenshots", "/announce/screenshots", "screenshots"),
    ("brann", "/announce/brann", "journey of brann"),
    ("wallpapers", "/announce/wallpapers", "wallpapers"),
    ("movies", "/announce/movies", "movies"),
    ("faq", "/announce/faq", "f.a.q"),
)

# Right-hand panel on guide-2001-10.png. Same forest frame as the home.
_FEATURES = (
    "Live in a seamless, persistent world set in the Warcraft Universe.",
    "Visit familiar landmarks and explore uncharted lands.",
    "Experience a dynamic world with constantly changing events and situations.",
    "Meet, adventure and trade with thousands of other players simultaneously.",
    "Engage in fast paced combat against multiple opponents.",
    "Enjoy hundreds of hours of gameplay created by a rich and dynamic quest system.",
    "Manage characters and navigate the world using a simple and intuitive interface.",
)


def _a(href: str, text: str) -> str:
    return f'<a href="{esc(href)}">{esc(text)}</a>'


def _nav() -> str:
    blocks = ['<div class="a-mark" aria-hidden="true"></div>']
    for heading, links in _NAV:
        rows = []
        for href, label in links:
            text = "<br>".join(esc(part) for part in label.split("\n"))
            rows.append(f'<a href="{esc(href)}">{text}</a>')
        head = f'<p class="a-sec">{esc(heading)}</p>' if heading else ""
        blocks.append(f'<div class="a-group">{head}{"".join(rows)}</div>')
    return "".join(blocks)


def _login(user: str | None, login_error: str) -> str:
    if user:
        return (
            '<div class="a-login">'
            f"<p>Signed in as <strong>{esc(user)}</strong></p>"
            '<p><a href="/account/">Manage Account</a></p>'
            '<p><a href="/account/logout">Log Out</a></p>'
            "</div>"
        )
    err = f'<p class="a-err">{esc(login_error)}</p>' if login_error else ""
    return (
        '<form class="a-login" method="post" action="/account/login">'
        '<input type="hidden" name="stay" value="sidebar">'
        f"{err}"
        '<label><span>Login:</span> <input name="identity" maxlength="16" autocomplete="username"></label>'
        '<label><span>Pass:</span> <input name="password" type="password" autocomplete="current-password"></label>'
        '<p class="a-actions"><button type="submit">Submit</button> '
        '<a class="a-help" href="/support/">Help</a></p>'
        "</form>"
    )


def _sidebar(user: str | None, login_error: str, online: str) -> str:
    checked = " checked" if online == "up" else ""
    return f"""<aside class="a-side">
  {_login(user, login_error)}
  <ul class="a-side-links">
    <li><a href="/wow/info/">What is World of Warcraft?</a></li>
    <li><a href="/account/retrieve">Retrieve Password</a></li>
    <li><a href="/wow/info/patches">Latest Patch Notes</a></li>
  </ul>
  <div class="a-stat">
    <p class="a-status-label">Beta Signup Status:</p>
    <p class="a-status-link"><a href="/wow/news">Signups Concluded</a></p>
  </div>
  <div class="a-stat">
    <p class="a-status-label"><a href="/wow/realmstatus">Server Status:</a></p>
    <p class="a-checks">
      <label><input type="checkbox" disabled{checked}> <a href="/wow/realmstatus">Beta Server</a></label>
      <label><input type="checkbox" disabled{checked}> <a href="/wow/realmstatus">PvP Server</a></label>
    </p>
  </div>
</aside>"""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = crumb
    inner = f"""<div class="a-site">
<header class="a-mast">
  <a class="a-logo" href="/wow/">
    <img src="/static/img/alpha/logo.png" alt="World of Warcraft">
    <em class="a-beta">Beta Web Site</em>
  </a>
  <p class="a-country"><a href="/wow/">Choose a country:</a><br><a href="/wow/">USA</a> <span>Korea</span></p>
</header>
<div class="a-frame">
  <nav class="a-nav" aria-label="Beta Web Site">{_nav()}</nav>
  <div class="a-sheet">
    <img class="a-corner" src="/static/img/alpha/corner.png" alt="">
    <div class="a-upper">{_sidebar(user, login_error, online)}</div>
    <div class="a-content">{body}</div>
  </div>
</div>
<p class="a-legal">©2004 Blizzard Entertainment. All rights reserved.</p>
</div>"""
    return document(
        f"{title} — World of Warcraft",
        styles("alpha"),
        "era-alpha",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _mdy(iso: str) -> str:
    parts = (iso or "").split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = parts
        return f"{int(month):02d}/{int(day):02d}/{year[2:]}"
    return iso


def _post(title: str, byline: str, body: str) -> str:
    return (
        '<article class="a-post">'
        f'<h2><span class="a-title">{title}</span> <span class="a-by">- {byline}</span></h2>'
        f"{body}</article>"
    )


def home_body(exp, news, realm, user) -> str:
    # The two 29 June 2004 posts are the accepted home. The archive under them
    # is the live news feed, so the page is not a dead copy of the capture.
    _ = exp, user, realm
    peek = _post(
        "A Peek at the Next Patch",
        "Katricia on 06/28/04",
        """<p>The next patch is just around the corner (it really is) and I wanted to give you all a quick glance at what's coming up:</p>
<ul>
  <li>The level cap will be increased to 50.</li>
  <li>The Sunken Temple, a dungeon in Swamp of Sorrows, will be opened.</li>
  <li>Many of the quests in The Barrens will be reworked or polished.</li>
  <li>New death graphics will be implemented.</li>
</ul>
<p>More sneak peeks to come. Enjoy these tidbits!</p>""",
    )
    europe = _post(
        "European Beta Sign-up Date Announced!",
        "Indoflaven on 06/28/04",
        "<p>Blizzard Entertainment today announced July 5th as the date players in Europe can start "
        "signing up for the European Closed Beta Test of its eagerly awaited MMORPG, World of Warcraft. "
        "The sign-ups will take place on "
        f'{_a("https://www.blizzard.de", "www.blizzard.de")}, '
        f'{_a("https://www.blizzard.fr", "www.blizzard.fr")}, and '
        f'{_a("https://www.blizzard.co.uk", "www.blizzard.co.uk")}. '
        f'Learn more in {_a("/wow/news", "this press release")}.</p>',
    )
    earlier = ""
    if news:
        items = "".join(
            f'<li>{_a(f"/wow/news/{i}", title)} <span>{esc(_mdy(date))}</span></li>'
            for i, (title, date, _body) in enumerate(news)
        )
        earlier = _post("Earlier News", "", f"<ul class=\"a-earlier\">{items}</ul>")
    return peek + europe + earlier


def _ynav(active: str) -> str:
    parts = []
    for key, href, label in _YNAV:
        mark = ' class="on"' if key == active else ""
        parts.append(f'<a href="{esc(href)}"{mark}>{esc(label)}</a>')
        if key != "faq":
            parts.append("<span>|</span>")
    order = "|".join(label for _key, _href, label in _YNAV)
    return f'<nav class="y-nav" data-nav="{esc(order)}" aria-label="Announcement">{"".join(parts)}</nav>'


def _yintro() -> str:
    return """<section class="y-intro">
  <p><span class="drop">F</span>our years have passed since the aftermath of Warcraft III: Reign of Chaos, and a great tension smolders throughout the ravaged world of Azeroth. As the battle-worn races begin to rebuild their shattered kingdoms, new threats, both ancient and ominous, arise to plague the world once again.</p>
  <p><span class="drop">R</span>ich in legend and filled with adventure, the World of Warcraft awaits! For the first time, players experience the lands of Azeroth from a new, in-depth perspective. As heroes, they explore familiar battlefields, discover new lands and take on epic quests and challenges in Blizzard's massively multiplayer, on-line, role-playing game.</p>
  <p class="y-welcome"><a href="/wow/">Welcome to the World of Warcraft.</a></p>
  <p class="y-badge"><a href="/announce/privacy"><strong>ESRB</strong> Privacy Certified<small>click to privacy statement</small></a></p>
</section>"""


def _ybook() -> str:
    return """<section class="y-book" id="brann">
  <img src="/static/img/alpha/book.png" alt="">
  <a href="/wow/"><img class="y-blizz" src="/static/img/alpha/blizz.png" alt="Blizzard Entertainment"></a>
</section>"""


def _updates() -> str:
    rows = [
        ("10/05/01", "World of Warcraft Screenshot Gallery Updated",
         f"The {_a('/announce/screenshots', 'Screenshot Section')} now features additional screenshots."),
        ("10/02/01", "World of Warcraft covered in Computer Gaming World",
         "The November issue of Computer Gaming World features a 10 page special on World of Warcraft "
         f"with exclusive screenshots, information and more. CGW is on newsstands now. Visit the Computer Gaming World website {_a('/announce/features', 'here')}. "
         f"See the cover image {_a('/announce/screenshots', 'here')}."),
        ("09/27/01", "Screenshot Gallery Updated",
         f"The {_a('/announce/screenshots', 'Screenshot Section')} now features additional screenshots and concept art."),
        ("09/26/01", "Dress up your Desktop, World of Warcraft style!",
         'The fourth and final wallpaper in the announcement series, entitled "World of Warcraft", '
         f"is available in the {_a('/announce/wallpapers', 'wallpapers section')}."),
        ("09/24/01", "The Journal of Brann is Unlocked!",
         "Embark on a Journey through the World of Warcraft through the eyes of Brann, the Dwarven explorer. "
         "Follow Brann through the forest of Elwynn in this, the first installment of his journal. "
         f"{_a('/announce/brann', 'Enter his World of Warcraft page')} and click Brann's Journal to begin the Journey."),
        ("09/12/01", "New World of Warcraft Forum",
         f"Dying to talk about World of Warcraft with other fans? Try our new World of Warcraft {_a('/announce/forums', 'General Discussion')} forum."),
        ("09/12/01", "Dress up your Desktop, World of Warcraft style!",
         'Download "Discovery," the third in a series of panoramic desktop backgrounds for your PC available in the '
         f"{_a('/announce/wallpapers', 'wallpapers section')}. One more to go!"),
        ("09/04/01", "Dress up your Desktop, World of Warcraft style!",
         'Download "Dawn," the second in a series of panoramic desktop backgrounds for your PC available in the '
         f"{_a('/announce/wallpapers', 'wallpapers section')}. More to come."),
        ("09/02/01", "Blizzard Unveils the Unannounced Project",
         "Blizzard announces World of Warcraft, a Massively Multi-Player, On-line role playing game set in the Warcraft universe. "
         f"Read the press release {_a('/announce/features', 'here')}."),
        ("", "Download the Cinematics Trailer for World of Warcraft",
         f"Get the latest from the Blizzard cinematics team available in the {_a('/announce/movies', 'movies section')}."),
        ("", "World of Warcraft Gameplay Movie!",
         f"See actual gameplay footage in the World of Warcraft gameplay preview available from the {_a('/announce/movies', 'movies section')}."),
        ("", "First Screenshots Posted!",
         f"Ten, brand-new shots from the game are available in the {_a('/announce/screenshots', 'screenshots section')}."),
        ("", "Dress up your Desktop, World of Warcraft style!",
         'Download "Imagination," the first in a series of panoramic desktop backgrounds for your PC available in the '
         f"{_a('/announce/wallpapers', 'wallpapers section')}. Expect more soon!"),
        ("", "Gamespot Features World of Warcraft",
         f"Visit {_a('/announce/features', 'Gamespot')} for an exclusive web preview of the game."),
        ("", "Still have questions?",
         f"Visit our new World of Warcraft {_a('/announce/faq', 'F.A.Q.')}."),
        ("", "Coming Soon: Journey of Brann", "Who is Brann? Where is he going?"),
    ]
    items = []
    for date, title, body in rows:
        when = f'<span class="y-date">-- {esc(date)} --</span>' if date else ""
        items.append(f"<li>{when}<strong>{esc(title)}</strong><p>{body}</p></li>")
    return f'<h2>Updates</h2><ul class="y-updates">{"".join(items)}</ul>'


def _features_panel() -> str:
    items = "".join(f"<li>{esc(line)}</li>" for line in _FEATURES)
    return f'<h2>Game Features</h2><ul class="y-feats">{items}</ul>'


def _screens_panel() -> str:
    from wowweb import assets

    shots = assets.screenshots("alpha", limit=10)
    if not shots:
        grid = "<p>The first screenshots are on their way into this gallery.</p>"
    else:
        cards = "".join(
            f'<a class="y-shot" href="{esc(url)}"><img src="{esc(url)}" alt="{esc(caption)}"><span>{esc(caption)}</span></a>'
            for url, caption in shots
        )
        grid = f'<div class="y-shots">{cards}</div>'
    return (
        "<h2>Screenshots</h2>"
        "<p>The Screenshot Section features shots and concept art from the world.</p>"
        f"{grid}<p>{_a('/wow/media/screenshots', 'Community screenshot archive')}</p>"
    )


def _wall_panel() -> str:
    papers = (
        ("/static/img/hero-alpha.jpg", "Imagination"),
        ("/static/img/alpha/forest.jpg", "Dawn"),
        ("/static/img/alpha/book.png", "Discovery"),
        ("/static/img/hero-alpha.jpg", "World of Warcraft"),
    )
    items = "".join(f"<li>{_a(href, name)}</li>" for href, name in papers)
    return (
        "<h2>Wallpapers</h2>"
        "<p>Panoramic desktop backgrounds from the announcement series.</p>"
        f"<ul class=\"y-links\">{items}</ul>"
        f"<p>{_a('/wow/media/wallpapers', 'More wallpapers')}</p>"
    )


def _movie_panel() -> str:
    return (
        "<h2>Movies</h2>"
        "<p>The cinematics trailer and the gameplay movie are listed with the announcement updates.</p>"
        f"<p>{_a('/announce/screenshots', 'Screenshots')}</p>"
        f"<p>{_a('/wow/media/screenshots', 'Community screenshot archive')}</p>"
    )


def _faq_panel() -> str:
    return (
        "<h2>F.A.Q.</h2>"
        "<dl class=\"y-faq\">"
        "<dt>What is World of Warcraft?</dt>"
        "<dd>A massively multiplayer online role-playing game set in Azeroth, four years after Warcraft III.</dd>"
        "<dt>What can I do there?</dt>"
        f"<dd>Read the {_a('/announce/features', 'game features')}, then the {_a('/wow/info/', 'beta game guide')}.</dd>"
        "<dt>Where do I talk to other players?</dt>"
        f"<dd>The {_a('/announce/forums', 'General Discussion')} forum is open.</dd>"
        "<dt>I forgot my password.</dt>"
        "<dd>There is no emailed reset. Sign in and change the password on the "
        f"{_a('/account/login', 'account page')}. {_a('/support/', 'Support')} has the same answer.</dd>"
        "</dl>"
    )


def _brann_panel() -> str:
    return (
        "<h2>Brann's Journal</h2>"
        "<p>Elwynn Forest. First installment.</p>"
        "<p>The road out of Stormwind is quieter than the tavern stories. Goldshire's lamps are lit by the time "
        "the bridge is behind me, and the vineyards to the west have been picked over. I am writing this down "
        "so the Explorers' League has a page instead of a rumor.</p>"
        "<p>Who is Brann? A dwarf with a pack, a pen, and a map that still has empty corners. Where is he going? "
        "Further into Elwynn, then wherever the road argues with him.</p>"
        f"<p>{_a('/announce', 'Back to updates')}</p>"
    )


def _privacy_panel() -> str:
    return (
        "<h2>Privacy</h2>"
        "<p>Signing in uses an account name and a password. This site does not mail a password reset.</p>"
        f"<p>{_a('/account/login', 'Account login')} · {_a('/announce', 'Back to updates')}</p>"
    )


_PANELS = {
    "updates": ("World of Warcraft", _updates),
    "features": ("Game Features", _features_panel),
    "screenshots": ("Screenshots", _screens_panel),
    "brann": ("Brann's Journal", _brann_panel),
    "wallpapers": ("Wallpapers", _wall_panel),
    "movies": ("Movies", _movie_panel),
    "faq": ("F.A.Q.", _faq_panel),
    "privacy": ("Privacy", _privacy_panel),
}


def announce_document(exp, dev: bool, panel: str = "updates") -> str:
    title, builder = _PANELS[panel]
    inner = f"""<div class="y-site">
<header class="y-head">
  <a class="y-logo" href="/announce"><img src="/static/img/alpha/logo.png" alt="World of Warcraft"></a>
  {_ynav(panel)}
</header>
<div class="y-cols">
  {_yintro()}
  {_ybook()}
  <section class="y-panel" id="{esc(panel)}">{builder()}</section>
</div>
</div>"""
    return document(
        title,
        styles("alpha"),
        "era-alpha era-alpha-2001",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def _stamp(ts) -> str:
    try:
        return time.strftime("%a %b %d %H:%M:%S", time.localtime(int(ts)))
    except (TypeError, ValueError, OSError):
        return ""


def _bnet_forum(ctx: dict) -> str:
    """18 Sep 2001 Battle.net board chrome. Rows come from the forums backend."""
    from wowweb import forums

    exp = ctx["exp"]
    threads: list[dict] = []
    try:
        page_no = int((ctx.get("qs") or {}).get("page", ["1"])[0])
    except (TypeError, ValueError):
        page_no = 1
    page_no = max(1, page_no)
    try:
        conn = forums.connect(Path(ctx["data_dir"]))
        forums.seed_if_empty(conn, exp)
        threads = forums.list_threads(conn, exp, "general")
        conn.close()
    except OSError:
        threads = []
    page_size = 25
    pages = max(1, (len(threads) + page_size - 1) // page_size)
    page_no = min(page_no, pages)
    start = (page_no - 1) * page_size
    rows = []
    for thread in threads[start : start + page_size]:
        when = _stamp(thread.get("created"))
        title = thread.get("title") or "Thread"
        rows.append(
            "<li>"
            + _a(f"/forums/general/{thread.get('id')}", title)
            + f" - {esc(thread.get('author') or '')}"
            + f' <span class="b-when">{esc(when)}</span>'
            + "</li>"
        )
    if not rows:
        rows.append("<li>No threads on this board yet.</li>")
    pager = ""
    if pages > 1:
        links = []
        for number in range(1, pages + 1):
            mark = ' class="on"' if number == page_no else ""
            links.append(f'<a href="/announce/forums?page={number}"{mark}>{number}</a>')
        pager = f'<p class="b-pages">{"".join(links)}</p>'
    top = (
        ("/wow/realmstatus", "Battle.net Status"),
        ("/support/", "Open Technical Support"),
        ("/support/", "Blizzard Technical Support"),
        ("/forums/pvp", "The War Room"),
        ("/wow/pvp/rankings", "Ladder Discussion"),
        ("/forums/guilds", "Clan Hall"),
        ("/wow/info/basics/map", "Map Development"),
        ("/announce", "Warcraft II"),
        ("/wow/", "World of Warcraft"),
    )
    # Two wrapped lines, the way the September 2001 board stacked its green links.
    link_html = " ".join(f"[{_a(href, label)}]" for href, label in top)
    side = (
        ("/announce", "News"),
        ("/announce/forums", "Forums"),
        ("/wow/pvp/rankings", "Ladder"),
        ("/wow/info/", "Strategy"),
        ("/wow/media/screenshots", "Files"),
        ("/support/", "Support"),
    )
    buttons = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in side)
    inner = f"""<div class="b-frame">
  <nav class="b-side" aria-label="Battle.net">{buttons}</nav>
  <div class="b-main">
    <p class="b-toplinks">{link_html}</p>
    <p class="b-actions"><a class="b-btn" href="/wow/search">Search Forum</a> <a class="b-btn" href="/forums/general">Post Message</a></p>
    <p class="b-mod">This forum is Moderated by Blizzard | {_a("/support/", "Read The Forum Rules")}</p>
    <p class="b-rules">Posts must be related to General Discussion about World of Warcraft. While the development team (Team 2) may not have time to respond to posts, they will be reading them. Before posting read the {_a("/support/", "Forum Rules")}.</p>
    <p class="b-topic">Topic: {_a("/forums/general", "General Discussion")}</p>
    {pager}
    <ul class="b-topics">{"".join(rows)}</ul>
    {pager}
  </div>
</div>"""
    return document(
        "General Discussion",
        styles("alpha"),
        "era-bnet",
        inner,
        dev_note_text=dev_note(exp, bool(ctx.get("dev"))),
    )


def take(path: str, ctx: dict):
    # Logged-out services would redirect. Keep the beta shell on a real page.
    if path != "/account/services" or ctx.get("user"):
        return None
    return (
        "Character Services",
        "<h2>Character Services</h2>"
        "<p>Sign in to review character services on this realm.</p>"
        '<p><a href="/account/login">Log In</a> · <a href="/account/create">Create Account</a></p>',
    )


def full(path: str, ctx: dict) -> str | None:
    if path == "/announce/forums":
        return _bnet_forum(ctx)
    panel = {
        "/announce": "updates",
        "/announce/features": "features",
        "/announce/screenshots": "screenshots",
        "/announce/brann": "brann",
        "/announce/wallpapers": "wallpapers",
        "/announce/movies": "movies",
        "/announce/faq": "faq",
        "/announce/privacy": "privacy",
    }.get(path)
    if panel is None:
        return None
    return announce_document(ctx["exp"], bool(ctx.get("dev")), panel)
