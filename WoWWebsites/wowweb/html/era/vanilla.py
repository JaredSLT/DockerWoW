"""April 2006 community site and the account-creation receipt."""

from __future__ import annotations

from .common import dev_note, document, esc, styles

_IMG = "/static/img/vanilla2006"
_SHOT = "/static/img/ssotd-elwynn.jpg"
_BOX = "/new-hp/images/image-retailbox.gif"

# Open sections match the 12 April 2006 community home.
_NEWS = (
    ("/wow/", "Current News"),
    ("/wow/news", "Archived News"),
)
_ACCOUNT = (
    ("/account/login", "Log In"),
    ("/account/create", "Create Account"),
    ("/account/", "Manage Account"),
    ("/loginsupport/password.html", "Retrieve Password"),
    ("/wow/realmstatus", "Realm Status"),
)
_GUIDE = (
    ("/wow/info/", "Game Guide"),
    ("/wow/info/introduction", "Introduction"),
    ("/wow/info/basics", "Getting Started"),
    ("/wow/info/races", "Character"),
    ("/info/reputations", "Reputations"),
    ("/info/items", "Items"),
    ("/info/theworld", "The World"),
    ("/info/transportation", "Transportation"),
    ("/info/playerinteraction", "Player Interaction"),
    ("/wow/pvp/rankings", "Player vs Player"),
    ("/support/", "FAQ"),
    ("/story", "Story"),
    ("/burningcrusade", "Burning Crusade"),
)
_WORKSHOP = (
    ("/wow/info/patches", "Under Development"),
    ("/patchnotes", "Previous Patches"),
    ("/wow/pvp/rankings", "Arena"),
    ("/info/encyclopedia", "Encyclopedia"),
    ("/wow/info/classes/", "Talent Calculators"),
    ("/info/events/calendar", "Events Calendar"),
    ("/info/items/armorsets", "Armor Sets"),
    ("/wow/info/basics/map", "World Map"),
    ("/pvp/battlegrounds", "Battlegroups"),
)
_MEDIA = (
    ("/wow/media/screenshots", "Screenshots"),
    ("/wow/media/wallpapers", "Wallpapers"),
    ("/downloads/movies.html", "Movies"),
)
_FORUMS = (
    ("/forums/general", "General"),
    ("/forums/", "Class Forums"),
    ("/forums/realm", "Realm Forums"),
    ("/forums/guilds", "Guild Recruitment"),
    ("/forums/guildrelations", "Guild Relations"),
    ("/forums/support", "Support"),
)
_COMMUNITY = (
    ("/community/", "Overview"),
    ("/contests/", "Contests"),
    ("/community/comics.html", "Comics"),
)
_SUPPORT = (
    ("/support/", "Customer Support"),
)


def _sub(rows) -> str:
    return "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in rows)


def _section(key: str, label: str, rows, open_: bool) -> str:
    opened = " open" if open_ else ""
    return (
        f'<details class="v-sec v-sec-{key}"{opened}>'
        f"<summary><span>{esc(label)}</span></summary>"
        f'<div class="v-sub">{_sub(rows)}</div>'
        "</details>"
    )


def _menu() -> str:
    return f"""<nav class="v-menu">
{_section("news", "News", _NEWS, False)}
{_section("account", "Account", _ACCOUNT, False)}
{_section("guide", "Game Guide", _GUIDE, True)}
{_section("workshop", "Workshop", _WORKSHOP, True)}
{_section("media", "Media", _MEDIA, False)}
{_section("forums", "Forums", _FORUMS, True)}
{_section("community", "Community", _COMMUNITY, False)}
{_section("support", "Support", _SUPPORT, False)}
</nav>"""


def _rail(ssotd: str) -> str:
    shot = ssotd or _SHOT
    return f"""<aside class="v-rail">
  <div class="v-rail-art">
    <img src="{_IMG}/rail.jpg" alt="">
    <a class="hit hit-faq" href="/support/">FAQ Site</a>
    <a class="hit hit-realms" href="/wow/realmstatus">Realms Status</a>
    <a class="hit hit-create" href="/account/create">Account Creation</a>
    <a class="hit hit-manage" href="/account/">Account Management</a>
    <a class="hit hit-pass" href="/loginsupport/password.html">Retrieve Password</a>
    <a class="hit hit-info" href="/info/items/armorsets">High Level Armor Sets</a>
    <a class="hit hit-indev" href="/wow/info/patches">Shadow of the Necropolis</a>
    <a class="hit hit-pvp" href="/wow/pvp/rankings">PvP Rankings</a>
  </div>
  <div id="ssotd-container" class="ssotd-container">
    <a href="/wow/media/screenshots"><img src="{esc(shot)}" alt="Screenshot of the Day"></a>
  </div>
</aside>"""


def _top(user: str | None) -> str:
    who = ""
    if user:
        who = (
            f'<p class="v-who">Signed in as {esc(user)}'
            f' · <a href="/account/logout">Log Out</a></p>'
        )
    return f"""<header class="v-top">
  <img class="v-header" src="{_IMG}/header.jpg" alt="">
  <img class="v-logo" src="{_IMG}/logo.jpg" alt="">
  <a class="hit-logo" href="/wow/">World of Warcraft Community Site</a>
  <a class="hit-acct" href="/account/">Account Management</a>
  <a class="hit-realm" href="/wow/realmstatus">Realm Status</a>
  {who}
</header>"""


def _frame(body: str, ssotd: str) -> str:
    # Account management fills the parchment. The home keeps the right rail.
    rail = "" if 'class="acct-vanilla"' in body else _rail(ssotd)
    wide = " v-wide" if not rail else ""
    return f"""<div class="v-iron">
  <div class="v-iron-t"><div><div></div></div></div>
  <div class="v-iron-m"><div class="v-iron-r">
    <div class="v-parch">
      <div class="v-center{wide}">{body}</div>
      {rail}
    </div>
  </div></div>
  <div class="v-iron-b"><div><div></div></div></div>
</div>"""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = crumb, online, login_error
    inner = f"""<div class="v-bleed v-bleed-l"></div>
<div class="v-bleed v-bleed-r"></div>
<div class="v-site">
<div class="v-trees v-trees-l"></div>
<div class="v-trees v-trees-r"></div>
{_top(user)}
<img class="v-elf" src="{_IMG}/elf.png" alt="">
<div class="v-body">
{_menu()}
{_frame(body, _SHOT)}
</div>
</div>"""
    css = styles("vanilla") + ["/static/css/forums.css"]
    return document(
        f"{title} — World of Warcraft",
        css,
        "era-vanilla",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    # The 12 April 2006 home is this snapshot, not the later news list.
    _ = exp, news, realm, user
    return """<div class="v-home">
<div class="v-arena">
  <img src="/static/img/vanilla2006/arena.jpg" alt="Welcome to the Arena">
</div>
<section class="v-news">
  <h3>General News</h3>
  <div class="v-cols"><span>News Title</span><span>Date</span></div>
  <details class="v-story" open>
    <summary>
      <span class="v-title">New WoW.com Sneak Peek!</span>
      <span class="v-by">Blaze</span>
      <span class="v-date">4-12-06</span>
    </summary>
    <div class="v-copy">
      <p>There is nothing wrong with your web browser. Do not attempt to adjust the monitor. We control the horizontal. We control the vertical. You are about to experience the awe and mystery which reaches from the inner mind to... the new World of Warcraft website! That's right, our crack team of web technology goblins and gnomish design specialists has been toiling in the dark recesses of the web team's dungeon for quite some time, redesigning the official community site. And now, you can get a first look at the new and improved functionality and the redesign of the site's main page. Here are some of the cool new features you may want to try out:</p>
      <ul>
        <li>Improved left side menu</li>
        <li>Enhanced main page layout</li>
        <li>Cycling flash banner</li>
        <li>Streamlined news section</li>
        <li>PvP Top Ten</li>
      </ul>
      <p>We are excited to present you with the new look of World of Warcraft on the Web, and we hope you like the new design! Please let us know if you experience any problems when viewing the new main page. Send your error reports including information about your operating system, browser, your browser's version, and a screenshot (if possible) to <a href="mailto:wowguide@blizzard.com">wowguide@blizzard.com</a>.</p>
    </div>
  </details>
  <details class="v-story">
    <summary>
      <span class="v-title">Select Realm Transfers</span>
      <span class="v-by">Eyonix</span>
      <span class="v-date">4-12-06</span>
    </summary>
  </details>
</section>
</div>"""


_ACCT_NEWS = (
    ("/wow/", "Current News"),
    ("/wow/news", "Archived News"),
)
_ACCT_ACCOUNT = (
    ("/account/", "Manage Account"),
    ("/account/password", "Change Password"),
    ("/account/create", "Create Account"),
    ("/account/login", "Log In"),
)
_ACCT_GUIDE = (
    ("/wow/info/", "Game Guide"),
    ("/wow/info/introduction", "Introduction"),
    ("/wow/info/basics", "Getting Started"),
    ("/wow/info/races", "Character"),
    ("/info/reputations", "Reputations"),
    ("/info/items", "Items"),
    ("/info/theworld", "The World"),
    ("/info/transportation", "Transportation"),
    ("/info/playerinteraction", "Player Interaction"),
    ("/support/", "FAQ"),
    ("/story", "Story"),
    ("/wow/info/patches", "Under Development"),
    ("/patchnotes", "Previous Patches"),
)
_ACCT_WORKSHOP = (
    ("/info/encyclopedia", "Encyclopedia"),
    ("/wow/pvp/rankings", "Game Statistics"),
    ("/wow/info/classes/", "Talent Calculators"),
    ("/info/events/calendar", "Events Calendar"),
    ("/calendar", "Raid Calendar"),
    ("/info/items/armorsets", "Armor Sets"),
    ("/wow/info/basics/map", "World Map"),
    ("/wareffort", "War Effort Rankings"),
)
_ACCT_MEDIA = (
    ("/wow/media/screenshots", "Screenshots"),
    ("/wow/media/wallpapers", "Wallpapers"),
    ("/downloads/movies.html", "Movies"),
)
_ACCT_COMMUNITY = (
    ("/community/", "Overview"),
    ("/community/comics.html", "Comics"),
    ("/community/communitylinks.html", "Community"),
    ("/contests/", "Contests"),
    ("/community/guildrelations.html", "Guild Relations"),
    ("/community/reallifeevents.html", "Real-Life Events"),
    ("/community/fanart", "Fan Art"),
    ("/downloads/wallpapers/fan-wallpapers", "Fan Wallpapers"),
)
_ACCT_SUPPORT = (
    ("/support/", "Support News"),
    ("/support/account", "Account Admin"),
    ("/support/billing", "Billing and Account"),
    ("/support/tech", "Technical Support"),
    ("/support/ingame", "In-Game Support"),
    ("/support/policies", "Policies"),
    ("/support/tools", "Support Tools"),
)


def _acct_menu() -> str:
    # Open sections are the ones expanded on the December 2006 summary.
    return f"""<nav class="v-menu a6-menu">
{_section("news", "News", _ACCT_NEWS, False)}
{_section("account", "Account", _ACCT_ACCOUNT, False)}
{_section("guide", "Game Guide", _ACCT_GUIDE, True)}
{_section("workshop", "Workshop", _ACCT_WORKSHOP, True)}
{_section("media", "Media", _ACCT_MEDIA, False)}
{_section("forums", "Forums", _FORUMS, True)}
{_section("community", "Community", _ACCT_COMMUNITY, True)}
{_section("support", "Support", _ACCT_SUPPORT, True)}
</nav>"""


def _account_document(ctx: dict) -> str:
    from wowweb import accounts
    from wowweb.account_ui.vanilla import render

    exp = ctx["exp"]
    user = ctx.get("user") or ""
    try:
        summary = accounts.account_summary(ctx["labcfg"], exp, user)
    except Exception:
        summary = {"email": "", "characters": []}
    panel = render(
        exp,
        user=user,
        error=str(ctx.get("error") or ""),
        notice=str(ctx.get("notice") or ""),
        mode="summary",
        email=summary.get("email") or "",
        characters=summary.get("characters") or [],
        login_kind="account",
        separate_game_name=False,
    )
    legal = (
        '<p class="a6-legal"><a href="/legal/">Online Privacy Policy</a> | '
        '<a href="/legal/">Legal Documents</a> | <a href="/policy/">Policies</a><br>'
        "&copy;2004-2006 Blizzard Entertainment, Inc. All rights reserved.</p>"
    )
    inner = f"""<div class="a6">
<img class="a6-dwarf" src="/static/img/vanilla/acct-dwarf.png" alt="">
<img class="a6-ice" src="/static/img/vanilla/acct-ice.jpg" alt="">
<header class="a6-top">
  <img src="/static/img/vanilla/acct-header.jpg" alt="">
  <a class="a6-logo" href="/wow/">World of Warcraft Community Site</a>
  <form class="a6-search" action="/wow/search" method="get">
    <input type="text" name="q" aria-label="Search">
    <select name="searchType" aria-label="Search in">
      <option value="site">Community Site</option>
      <option value="encyclopedia">Encyclopedia</option>
      <option value="ingamesupport">In-game Support</option>
      <option value="techsupport">Tech Support</option>
    </select>
    <button type="submit">Search</button>
  </form>
</header>
<div class="a6-body">
{_acct_menu()}
{_frame(panel + legal, "")}
</div>
</div>"""
    return document(
        "Account Management — World of Warcraft",
        styles("vanilla"),
        "era-vanilla era-vanilla-acct",
        inner,
        dev_note_text=dev_note(exp, bool(ctx.get("dev"))),
    )


def _board_page(ctx: dict, slug: str) -> str | None:
    from wowweb import forums

    exp = ctx["exp"]
    title = forums.board_title(exp, slug)
    if not title:
        return None
    qs = ctx.get("qs") or {}
    try:
        page = max(1, int((qs.get("page") or ["1"])[0]))
    except (TypeError, ValueError, IndexError):
        page = 1
    threads = []
    last_authors = {}
    try:
        conn = forums.connect(ctx["data_dir"])
        try:
            forums.seed_if_empty(conn, exp)
            threads = forums.list_threads(conn, exp, slug)
            ids = [int(row["id"]) for row in threads]
            if ids:
                slot = ",".join(str(i) for i in ids)
                rows = conn.execute(
                    f"""SELECT p.thread_id, p.author FROM posts p
                        JOIN (SELECT thread_id, MAX(id) AS id FROM posts
                              WHERE thread_id IN ({slot}) GROUP BY thread_id) last
                          ON last.id = p.id"""
                ).fetchall()
                last_authors = {int(row[0]): row[1] for row in rows}
        finally:
            conn.close()
    except Exception:
        threads = []
    page_size = 20
    pages = max(1, (len(threads) + page_size - 1) // page_size)
    if page > pages:
        page = pages
    start = (page - 1) * page_size
    body_rows = []
    for thread in threads[start : start + page_size]:
        tid = int(thread["id"])
        replies = max(0, int(thread.get("replies") or 0) - 1)
        poster = last_authors.get(tid) or thread.get("author") or ""
        blizz = " fb-blizz" if "blizzard" in str(thread.get("author") or "").lower() else ""
        body_rows.append(
            "<tr>"
            '<td class="fb-flag"><span class="fb-note"></span></td>'
            f'<td class="fb-subject"><a href="/forums/{esc(slug)}/{tid}">{esc(thread.get("title"))}</a></td>'
            f'<td class="fb-author{blizz}">{esc(thread.get("author"))}</td>'
            f'<td class="fb-num">{replies}</td>'
            '<td class="fb-num">0</td>'
            f'<td class="fb-thread">by {esc(poster)}</td>'
            "</tr>"
        )
    if not body_rows:
        body_rows.append('<tr><td class="fb-empty" colspan="6">No threads yet.</td></tr>')
    numbers = []
    for number in range(1, pages + 1):
        if number == page:
            numbers.append(f'<span class="fb-on">{number}</span>')
        else:
            numbers.append(f'<a href="?page={number}">{number}</a>')
    options = []
    for board_slug, board_title in forums.boards_for(exp):
        label = "WoW General" if board_slug == "general" else (forums.board_title(exp, board_slug) or board_title)
        selected = " selected" if board_slug == slug else ""
        options.append(f'<option value="/forums/{esc(board_slug)}"{selected}>{esc(label)}</option>')
    user = ctx.get("user")
    if user:
        new_href = "#new-topic"
        form = f"""<form id="new-topic" class="fb-post" method="post" action="/forums/{esc(slug)}/new">
  <label>Title <input name="title" required maxlength="120"></label>
  <label>Body <textarea name="body" required rows="6"></textarea></label>
  <button type="submit">Post</button>
</form>"""
        who = f'<a class="fb-login" href="/account/logout">Log Out</a>'
    else:
        new_href = "/account/login"
        form = '<p id="new-topic" class="fb-login-note"><a href="/account/login">Log in</a> with a realm account to post.</p>'
        who = '<a class="fb-login" href="/account/login">Login</a>'
    inner = f"""<div class="fb">
<header class="fb-banner">
  <a class="fb-home" href="/wow/">World of Warcraft</a>
  <form class="fb-nav" action="/forums/{esc(slug)}" method="get">
    <label>Forum Nav
      <select name="board" aria-label="Forum Nav" onchange="if(this.value)location.href=this.value">
        {''.join(options)}
      </select>
    </label>
  </form>
  {who}
</header>
<div class="fb-tools">
  <a class="fb-new" href="{new_href}">New Topic</a>
  <form class="fb-find" action="/wow/search" method="get">
    <input type="hidden" name="searchType" value="site">
    <input type="text" name="q" aria-label="Search">
    <button type="submit">Search</button>
  </form>
</div>
<p class="fb-pages">Page: {' '.join(numbers)}</p>
<table class="fb-table">
  <thead><tr><th></th><th>Subject</th><th>Author</th><th>Replies</th><th>Views</th><th>Thread</th></tr></thead>
  <tbody>{''.join(body_rows)}</tbody>
</table>
{form}
</div>"""
    return document(
        f"{title} — Forums",
        styles("vanilla"),
        "era-vanilla era-vanilla-board",
        inner,
        dev_note_text=dev_note(exp, bool(ctx.get("dev"))),
    )


def full(path: str, ctx: dict) -> str | None:
    if path == "/account/completed":
        exp = ctx["exp"]
        return receipt_document(exp, ctx.get("user"), bool(ctx.get("dev")))
    if path == "/account" and ctx.get("user"):
        return _account_document(ctx)
    parts = [part for part in path.split("/") if part]
    if len(parts) == 2 and parts[0] == "forums":
        return _board_page(ctx, parts[1])
    return None


def take(path: str, ctx: dict):
    # Logged-out services would redirect. The community page itself answers.
    if path != "/account/services" or ctx.get("user"):
        return None
    return (
        "Character Services",
        "<h2>Character Services</h2>"
        "<p>Sign in to change a character name or transfer a character. "
        "These services are free.</p>"
        '<p><a href="/account/login">Log In</a> · <a href="/account/create">Create Account</a></p>',
    )


def receipt_document(exp, user, dev: bool) -> str:
    # Values that were covered in the photographs stay blank. The subscription
    # line is the unredacted plan on the December 2004 receipt.
    shown = esc(user) if user else ""
    name_cell = f'<span class="r-value">{shown}</span>' if shown else '<span class="r-blank"></span>'
    inner = f"""<header class="r-head">
  <img src="{_IMG}/logo.jpg" alt="World of Warcraft">
  <p class="r-sub">Account Creation</p>
</header>
<main class="r-sheet">
  <h1>Account Creation Complete!</h1>
  <p class="r-print"><span class="r-printer" aria-hidden="true"></span> Please print this page and save it for your records.</p>
  <img class="r-box" src="{_BOX}" alt="Welcome to World of Warcraft">
  <p>Congratulations! You have successfully completed the World of Warcraft account creation process! You can now use the account you've just created to login and play. If you have questions or concerns about the account creation procedure or your billing information, please contact our billing and account services by email (<a href="mailto:billing@blizzard.com">billing@blizzard.com</a>) or via phone (1-800-59-BLIZZARD). Users in Singapore should please use 1-800-225-5969 (1-800-CALL-WOW).</p>
  <p>If you are new to the game, we recommend you take advantage of the in-game help system, which will help you learn how to complete various actions such as starting quests, initiating combat, searching bodies, and training your character. For further beginner information, check our <a href="/wow/info/basics">Getting Started page</a>.</p>
  <div class="r-panels">
    <section class="r-block">
      <h2>Account Details</h2>
      <table class="r-table">
        <tr><th>Account Name</th><td>{name_cell}</td></tr>
        <tr><th>Password</th><td><span class="r-blank"></span></td></tr>
        <tr><th>Password Question</th><td><span class="r-blank"></span></td></tr>
        <tr><th>Password Answer</th><td><span class="r-blank"></span></td></tr>
      </table>
    </section>
    <section class="r-block">
      <h2>Contact Info</h2>
      <div class="r-blank r-blank-block"></div>
    </section>
  </div>
  <section class="r-block r-pay">
    <h2>Payment Method</h2>
    <table class="r-table">
      <tr><th>Full Name</th><td><span class="r-blank"></span></td></tr>
      <tr><th>ZIP/Postal Code</th><td><span class="r-blank"></span></td></tr>
      <tr><th>Card Number</th><td><span class="r-blank"></span></td></tr>
      <tr><th>Card Exp Date</th><td><span class="r-blank"></span></td></tr>
      <tr><th>Subscription</th><td>1 Month Recurring - $14.99</td></tr>
    </table>
  </section>
  <p class="r-foot">signup.worldofwarcraft.com/completed.html</p>
</main>"""
    return document(
        "Account Creation Complete — World of Warcraft",
        styles("vanilla"),
        "era-vanilla era-vanilla-receipt",
        inner,
        dev_note_text=dev_note(exp, dev),
    )
