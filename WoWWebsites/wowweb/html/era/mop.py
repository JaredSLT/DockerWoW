"""November 2013 community site (patch 5.4), Battle.net shop, and account gates.

The home is the anniversary page with the Shop tab, not the 2012 Services
tab and not the 2014 Warlords pre-patch homepage.
"""

from __future__ import annotations

from .common import dev_note, document, esc, styles

_IMG = "/static/img/mop"

# Visible November 2013 community posts. The catalog feed is the later
# Warlords pre-patch and is not the home page.
_STORIES = (
    {
        "title": "Happy Anniversary! World of Warcraft Celebrates 9 Years",
        "by": "Blizzard Entertainment",
        "when": "11/22/2013",
        "ago": "1 day ago",
        "comments": "603",
        "thumb": "thumb-crest.jpg",
        "lede": "It's been nine years since World of Warcraft opened its gates—nine years since fledgling heroes from all walks of life spoke to their first quest giver and began their journey through Azeroth, unaware of where those first steps would ultimately take them.",
        "more": "Patch 5.4 is the live game. Siege of Orgrimmar, flexible raids, and the Timeless Isle are the road this ninth year is still walking.",
    },
    {
        "title": "New Mount and Make-A-Wish® Charity Pet Now Available",
        "by": "Blizzard Entertainment",
        "when": "11/22/2013",
        "ago": "1 day, 4 hours ago",
        "comments": "147",
        "thumb": "promo-charity.jpg",
        "lede": "Brighten up Azeroth's skies with the new Enchanted Fey Dragon mount, and help grant wishes with the Alliance Brew Pup and the Horde Brew Pup. A portion of each purchase goes to Make-A-Wish.",
        "more": "Five dollars from each Brew Pup or Charity Bundle sold will benefit Make-A-Wish. The charity event ends 12/31/13 at 11:59 p.m. PST.",
    },
    {
        "title": "WoW Source: Warlords of Draenor",
        "by": "Blizzard Entertainment",
        "when": "11/22/2013",
        "ago": "1 day, 4 hours ago",
        "comments": "134",
        "thumb": "/static/img/hero-mop.jpg",
        "lede": "Morgan Webb sits down with Lead Encounter Designer Ion Hazzikostas, Senior Art Director Chris Robinson, and Game Director Tom Chilton to talk about what was shown at BlizzCon 2013, including a first look at the new female Forsaken model.",
        "more": "The conversation is a BlizzCon 2013 source interview. Mists of Pandaria remains the live game at patch 5.4.",
    },
    {
        "title": "5.4 Hotfixes: November 21",
        "by": "Rygarius",
        "when": "11/21/2013",
        "ago": "1 day, 6 hours ago",
        "comments": "2,456",
        "thumb": "thumb-gate.jpg",
        "lede": "Here you'll find a list of hotfixes that address various issues related to the recently released World of Warcraft Patch 5.4, Siege of Orgrimmar.",
        "more": "Hotfixes land between builds. Check back for realm restarts tied to Siege of Orgrimmar and the rest of patch 5.4.",
    },
    {
        "title": "Connected Realms Update",
        "by": "Blizzard Entertainment",
        "when": "11/20/2013",
        "ago": "2 days, 7 hours ago",
        "comments": "1,851",
        "thumb": "mop-bg.jpg",
        "lede": "As previously announced, we've been working toward connecting realms to increase the number of players on low-population realms, and since then have completed several connections.",
        "more": "Connected realms share a larger player pool while each realm keeps its own name. Further connections will be posted as they are scheduled.",
    },
    {
        "title": "Blizzard Entertainment Student Art Contest",
        "by": "Blizzard Entertainment",
        "when": "11/19/2013",
        "ago": "3 days ago",
        "comments": "35",
        "thumb": "thumb-tower.jpg",
        "lede": "Students, get ready to show off your talents: the Student Art Contest is back.",
        "more": "The contest is open to enrolled students. Winning pieces join the community gallery beside the other Warcraft art updates.",
    },
    {
        "title": "New World of Warcraft novel War Crimes Out Next Year",
        "by": "Blizzard Entertainment",
        "when": "11/18/2013",
        "ago": "4 days ago",
        "comments": "11",
        "thumb": "thumb-gate.jpg",
        "lede": "The brutal siege of Orgrimmar will be over, but Garrosh Hellscream, the most infamous orc on Azeroth, has yet to face justice. Now in chains, his tyrannical leadership of the Horde has been ended by his many enemies, and he must answer for his crimes.",
        "more": "Christie Golden's War Crimes follows that trial. The book is scheduled for the coming year.",
    },
    {
        "title": "Major Payne's Pet Menagerie: Infinite Whelpling",
        "by": "Crithto",
        "when": "11/19/2013",
        "ago": "11/19/2013",
        "comments": "73",
        "thumb": "thumb-beast.jpg",
        "lede": "Where do you suppose you could find the very essence of corrupted time and death in the form of a tiny little dragon?",
        "more": "Major Payne's Pet Menagerie looks at the Infinite Whelpling and where collectors have been finding one.",
    },
    {
        "title": "Post-BlizzCon® Online Store Sale Nov. 15 – Nov. 17",
        "by": "Blizzard Entertainment",
        "when": "11/15/2013",
        "ago": "11/15/2013",
        "comments": "66",
        "thumb": "play-free.jpg",
        "lede": "Another BlizzCon's come and gone, but there's still a chance to snag some cool commemorative Warcraft, StarCraft, and Diablo gear.",
        "more": "From November 15 through November 17, anyone could purchase select items from the BlizzCon 2013 store directly through the online store.",
    },
    {
        "title": "Blizzard Comic Contest Winner",
        "by": "Nethaera",
        "when": "11/15/2013",
        "ago": "11/15/2013",
        "comments": "14",
        "thumb": "/static/img/hero-mop.jpg",
        "lede": "And the comic contest winner for October, 2013, is… his Winner (fans).",
        "more": "The October comic contest closes with the winning strip posted for the community.",
    },
    {
        "title": "Warcraft Art Updates",
        "by": "Nethaera",
        "when": "11/15/2013",
        "ago": "11/15/2013",
        "comments": "3",
        "thumb": "side-starter.jpg",
        "lede": "We've updated our art gallery to feature ten new pieces. We've also added new fan art and Blizzard art.",
        "more": "The gallery update mixes community pieces with new Blizzard artwork from the year.",
    },
)

_FEATURED = (0, 1, 2, 5)


def _src(name: str) -> str:
    if name.startswith("/"):
        return name
    return f"{_IMG}/{name}"


def _css() -> list[str]:
    return styles("mop") + ["/static/css/forums.css", "/static/css/armory.css"]


def _welcome(user: str | None) -> str:
    if user:
        return (
            f'<span class="mop-welcome">Welcome, <a href="/account/">{esc(user)}</a>'
            f' · <a href="/account/logout">Log Out</a></span>'
        )
    return (
        '<span class="mop-welcome"><a href="/account/login">Log In</a>'
        ' or <a href="/account/create">Create an Account</a></span>'
    )


def _service_bar(user: str | None) -> str:
    return f"""<div class="mop-service">
  <a class="mop-atom" href="/wow/">Battle.net</a>
  {_welcome(user)}
  <a href="/shop">Shop</a>
  <a href="/account/">Account</a>
  <a href="/support/">Support</a>
  <a class="mop-explore" href="/wow/">Explore</a>
</div>"""


def _greet(user: str | None) -> str:
    if user:
        return (
            f'<a class="mop-greet" href="/account/"><span><strong>Welcome, {esc(user)}</strong>'
            "Account, characters, and character services are one click away.</span></a>"
        )
    return (
        '<a class="mop-greet" href="/account/login"><span><strong>Log in now</strong>'
        "to enhance and personalize your experience!</span></a>"
    )


def _drop(rows: tuple[tuple[str, str], ...]) -> str:
    return "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in rows)


def _tabs(active: str) -> str:
    def link(key: str, href: str, label: str) -> str:
        here = " mop-here" if active == key else ""
        current = ' aria-current="page"' if active == key else ""
        return f'<a class="mop-tab{here}"{current} href="{href}">{label}</a>'

    def slot(key: str, href: str, label: str, rows: tuple[tuple[str, str], ...]) -> str:
        return f'<div class="mop-slot">{link(key, href, label)}<div class="mop-drop">{_drop(rows)}</div></div>'

    guide = slot(
        "guide",
        "/wow/info/",
        "Game Guide",
        (
            ("/wow/info/", "Game Guide"),
            ("/wow/info/races", "Races"),
            ("/wow/info/classes", "Classes"),
            ("/wow/info/professions", "Professions"),
            ("/wow/info/basics/", "New Players"),
            ("/wow/realmstatus", "Realm Status"),
        ),
    )
    community = slot(
        "community",
        "/forums/",
        "Community",
        (
            ("/forums/", "Forums"),
            ("/forums/general", "General Discussion"),
            ("/story", "Story"),
            ("/armory/", "Armory"),
            ("/wow/media/screenshots", "Screenshots"),
        ),
    )
    media = slot(
        "media",
        "/wow/media/screenshots",
        "Media",
        (
            ("/wow/media/screenshots", "Screenshots"),
            ("/wow/media/wallpapers", "Wallpapers"),
        ),
    )
    forums = slot(
        "forums",
        "/forums/",
        "Forums",
        (
            ("/forums/", "Forum Index"),
            ("/forums/general", "General Discussion"),
            ("/forums/realm", "Realm Forum"),
            ("/forums/guilds", "Guild Recruitment"),
        ),
    )
    return f"""<nav class="mop-tabs" aria-label="World of Warcraft">
  {link("home", "/wow/", "Home")}
  {guide}
  {community}
  {media}
  {forums}
  {link("shop", "/shop", "Shop")}
</nav>"""


def _footer() -> str:
    cols = (
        (
            "Battle.net Home",
            (
                ("/wow/", "What is Battle.net?"),
                ("/shop", "Shop"),
                ("/account/", "Account"),
                ("/support/", "Support"),
                ("/account/", "Real ID"),
                ("/account/", "BattleTag"),
            ),
        ),
        (
            "Games",
            (
                ("/wow/", "World of Warcraft®"),
                ("/shop", "Diablo® III"),
                ("/shop", "StarCraft® II"),
                ("/shop", "Hearthstone™"),
                ("/wow/", "Classic Games"),
                ("/wow/media/wallpapers", "Game Client Downloads"),
            ),
        ),
        (
            "Account",
            (
                ("/account/login", "Can't log in?"),
                ("/account/create", "Create Account"),
                ("/account/", "Account Summary"),
                ("/support/password", "Account Security"),
                ("/shop", "Add a Game"),
                ("/account/", "Redeem Codes"),
            ),
        ),
        (
            "Support",
            (
                ("/support/", "Support Articles"),
                ("/support/", "Parental Controls"),
                ("/support/password", "Protect Your Account"),
                ("/support/password", "Help! I got hacked!"),
            ),
        ),
    )
    blocks = []
    for heading, links in cols:
        items = "".join(f'<li><a href="{esc(href)}">{esc(label)}</a></li>' for href, label in links)
        blocks.append(f"<div><h4>{esc(heading)}</h4><ul>{items}</ul></div>")
    return f"""<div class="mop-footwrap"><footer class="mop-foot">
  <div class="mop-foot-cols">
    {''.join(blocks)}
    <a class="mop-playfree" href="/account/create"><img src="{_IMG}/play-free.jpg" alt=""><span>Play it Free</span></a>
  </div>
  <p class="mop-legal"><a href="/support/">Terms of Use</a> · <a href="/support/">Legal</a> · <a href="/support/">Privacy Policy</a> · <a href="/support/">Copyright Infringement</a></p>
  <p class="mop-copy">© 2013 Blizzard Entertainment, Inc. All rights reserved.</p>
  <p class="mop-badges"><span class="mop-blizzard">Blizzard Entertainment</span><span class="mop-teen"><b>T</b><small>Teen</small></span></p>
</footer></div>"""


def _tab_key(body: str, crumb: str, title: str) -> str:
    if 'class="mop-home"' in body or 'class="mop-news"' in body:
        return "home"
    if 'class="mop-realms"' in body:
        return "guide"
    if "class='forums" in body or 'class="forums' in body:
        return "forums"
    low = f"{crumb} {title}".lower()
    if "screenshot" in low or "wallpaper" in low or low.strip() == "media":
        return "media"
    if low.strip() == "story":
        return "community"
    if 'class="sheet' in body or "armory" in low:
        return "community"
    if any(word in low for word in ("guide", "race", "class", "profession", "talent", "patch", "feature", "map", "player", "award", "zone")):
        return "guide"
    return ""


def _crumb(body: str, crumb: str, title: str) -> str:
    if 'class="mop-home"' in body:
        return ""
    if 'class="mop-realms"' in body:
        return (
            '<p class="mop-crumb"><a href="/wow/">World of Warcraft</a> <span>›</span> '
            '<a href="/wow/info/">Game Guide</a> <span>›</span> <span>Realm Status</span></p>'
        )
    label = esc(crumb or title)
    return (
        '<p class="mop-crumb"><a href="/wow/">World of Warcraft</a> '
        f"<span>›</span> <span>{label}</span></p>"
    )


def _logo() -> str:
    return """<a class="mop-logo" href="/wow/">
  <span class="mop-world">World of</span>
  <span class="mop-wm">Warcraft</span>
  <span class="mop-era">Mists of Pandaria</span>
</a>"""


def _community(exp, title: str, body: str, user, crumb: str) -> str:
    _ = exp
    panel = "mop-panel mop-profile" if 'class="sheet' in body else "mop-panel"
    return f"""<div class="mop-site">
  <header class="mop-top">
    {_logo()}
    <div class="mop-tools">
      {_service_bar(user)}
      <form class="mop-search" action="/wow/search" method="get">
        <input type="text" name="q" aria-label="Search characters, items, forums and more" placeholder="Search characters, items, forums and more...">
        <button type="submit" aria-label="Search"></button>
      </form>
    </div>
  </header>
  <div class="mop-navline">
    {_tabs(_tab_key(body, crumb, title))}
    {_greet(user)}
  </div>
  <div class="{panel}">
    {_crumb(body, crumb, title)}
    {body}
  </div>
  {_footer()}
</div>"""


def _portal_bar(user: str | None) -> str:
    return f"""<div class="mop-portal-top">
  <a class="mop-portal-logo" href="/wow/"><span class="mop-atom-mark" aria-hidden="true"></span>Battle.net</a>
  <form class="mop-portal-search" action="/wow/search" method="get">
    <input type="text" name="q" aria-label="Search Battle.net" placeholder="Search Battle.net">
    <button type="submit" aria-label="Search"></button>
  </form>
  {_service_bar(user)}
</div>"""


def _account_bar(active: str) -> str:
    def item(key: str, href: str, label: str) -> str:
        here = " mop-acct-here" if active == key else ""
        return f'<a class="mop-acct-link{here}" href="{href}">{label}</a>'

    return f"""<header class="mop-acctbar">
  <a class="mop-acct-title" href="/account/">Account</a>
  <nav class="mop-acct-nav" aria-label="Account">
    {item("summary", "/account/", "Summary")}
    {item("settings", "/account/password", "Settings")}
    {item("games", "/shop", "Games &amp; Codes")}
    {item("history", "/account/", "Transaction History")}
    {item("security", "/account/password", "Security Options")}
  </nav>
  <p class="mop-balance">Balance: <strong>$0.00 USD</strong></p>
</header>"""


def _services_frame(exp, body: str) -> str:
    realm = esc(getattr(exp, "realm_name", "") or "Realm")
    return f"""<div class="mop-acct-site">
  {_account_bar("games")}
  <div class="mop-svc">
    <div class="mop-svc-head">
      <span class="mop-svc-seal" aria-hidden="true">W</span>
      <div>
        <p class="mop-kicker">Character Services</p>
        <h1>Character Transfer</h1>
      </div>
    </div>
    <p class="mop-svc-tools">
      <span class="mop-pill mop-pill-on">Service</span>
      <a href="/account/">History/Status</a>
      <a href="/account/">Return to dashboard</a>
    </p>
    <div class="mop-svc-grid">
      <aside class="mop-svc-side">
        <div class="mop-svc-pick">
          <span class="mop-svc-silhouette" aria-hidden="true"></span>
          <p>Select a character to continue</p>
        </div>
        <p class="mop-svc-cost">COST: $25.00 USD</p>
        <p>Please make sure the character you wish to perform a character service for is not logged in to World of Warcraft, as this may make the character ineligible.</p>
        <p class="mop-svc-wait">Average wait time: 1 hour</p>
      </aside>
      <div class="mop-svc-board">
        <ul class="mop-realms">
          <li class="mop-realm-open"><span aria-hidden="true">−</span> {realm} (PvE)</li>
        </ul>
        <div class="mop-svc-chars">{body}</div>
      </div>
    </div>
  </div>
</div>"""


def _account_frame(mode: str, user, body: str) -> str:
    if mode == "login":
        return f"""<div class="mop-portal">
  {_portal_bar(user)}
  <div class="mop-portal-stage">
    <img class="mop-portal-left" src="{_IMG}/tile-liberty.jpg" alt="">
    <img class="mop-portal-right" src="{_IMG}/shop-hero.jpg" alt="">
    <p class="mop-portal-tag">Join millions of players<br>Epic gaming experiences</p>
    <a class="mop-portal-join" href="/account/create">Sign Up Now!</a>
    <div class="mop-modal">{body}</div>
  </div>
</div>"""
    if mode == "create":
        return f"""<div class="mop-portal mop-portal-form">
  {_portal_bar(user)}
  <div class="mop-sheet">{body}</div>
</div>"""
    active = "settings" if mode == "password" else "summary"
    return f"""<div class="mop-acct-site">
  {_account_bar(active)}
  <div class="mop-sheet">{body}</div>
</div>"""


def _gate(body: str) -> str:
    if "acct-mop" in body:
        if "acct-login" in body:
            return "login"
        if "acct-create" in body:
            return "create"
        if "acct-password" in body:
            return "password"
        return "summary"
    if "<h2>Character Services</h2>" in body:
        return "services"
    return ""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online, login_error
    gate = _gate(body or "")
    if gate == "services":
        inner = _services_frame(exp, body)
        klass = "era-mop gen2 mop acct-gate gate-services"
    elif gate:
        inner = _account_frame(gate, user, body)
        klass = f"era-mop gen2 mop acct-gate gate-{gate}"
    else:
        inner = _community(exp, title, body, user, crumb or "")
        klass = "era-mop gen2 mop"
    return document(
        f"{title} — World of Warcraft",
        _css(),
        klass,
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _article_block(index: int, story: dict, *, featured: bool = False) -> str:
    href = f"/wow/news/{index}"
    src = esc(_src(story["thumb"]))
    title = esc(story["title"])
    if featured:
        return (
            f'<a class="mop-feature" href="{href}"><img src="{src}" alt="">'
            f"<span>{title}</span></a>"
        )
    comments = ""
    if story.get("comments"):
        comments = f'<span class="mop-comments">{esc(story["comments"])}</span>'
    return f"""<article class="mop-post">
  <a href="{href}"><img src="{src}" alt=""></a>
  <div>
    <h2><a href="{href}">{title}</a></h2>
    <p class="mop-by">by {esc(story["by"])} <time datetime="{esc(story["when"])}">{esc(story["ago"])}</time> {comments}</p>
    <p>{esc(story["lede"])} <a class="mop-more" href="{href}">More ›</a></p>
  </div>
</article>"""


def home_body(exp, news, realm, user) -> str:
    _ = exp, news, realm, user
    featured = "".join(_article_block(i, _STORIES[i], featured=True) for i in _FEATURED)
    posts = "".join(_article_block(i, story) for i, story in enumerate(_STORIES))
    return f"""<div class="mop-home">
  <div class="mop-primary">
    <a class="mop-promo" href="/wow/news/1">
      <img src="{_IMG}/promo-charity.jpg" alt="">
      <span class="mop-promo-copy">
        <span class="mop-promo-kicker">Support Make-A-Wish</span>
        <strong>Exclusive Charity Bundle</strong>
        <span>$5 from each Brew Pup or Charity Bundle sold will benefit Make-A-Wish.</span>
        <span class="mop-promo-more">Learn More</span>
      </span>
    </a>
    <div class="mop-features">{featured}</div>
    {posts}
    <p class="mop-pager"><a class="mop-next" href="/wow/news">Next</a></p>
  </div>
  <aside class="mop-side">
    <div class="mop-side-box">
      <img src="{_IMG}/side-starter.jpg" alt="">
      <strong>World of Warcraft</strong>
      <span>Starter Edition</span>
      <a class="mop-play" href="/account/create">Play Free Now</a>
    </div>
  </aside>
</div>"""


def _pop_label(value) -> tuple[str, str]:
    text = "" if value is None else str(value).strip()
    lowered = text.lower()
    if lowered in {"high", "medium", "low"}:
        return text.title(), lowered
    if text in {"", "—", "-"}:
        return "Low", "low"
    try:
        number = float(text)
    except ValueError:
        return text, "low"
    if number >= 200:
        return "High", "high"
    if number >= 50:
        return "Medium", "medium"
    return "Low", "low"


def _type_label(realm: dict, unread: bool) -> str:
    if unread:
        return "—"
    raw = str(realm.get("type") or "").strip()
    mapped = {
        "": "PvE",
        "Normal": "PvE",
        "PvE": "PvE",
        "PvP": "PvP",
        "RP": "RP",
        "RP PvP": "RP PvP",
        "FFA PvP": "PvP",
    }.get(raw, raw or "PvE")
    if mapped == "—":
        return mapped
    return f"({mapped})"


def realm_body(exp, realm: dict, dev: bool) -> str:
    unread = bool(realm.get("error")) and not realm.get("type") and not realm.get("population")
    up = bool(realm.get("up"))
    state = "Up" if up else "Down"
    state_class = "mop-up" if up else "mop-down"
    if unread:
        pop, pop_class = "—", "none"
        queue = "—"
    else:
        pop, pop_class = _pop_label(realm.get("population"))
        queue = "0"
    name = esc(realm.get("name") or getattr(exp, "realm_name", ""))
    note = ""
    if dev and realm.get("error"):
        note = f'<p class="mop-warn">{esc(realm.get("error"))}</p>'
    return f"""<div class="mop-realms-page">
  <div class="mop-realms-head">
    <h1>Realm Status</h1>
    <p>This page lists World of Warcraft realms and the status of each. A realm is either Up or Down. Messages about realm status and scheduled maintenance are posted in the <a href="/forums/realm">Service Status forum</a>. If a realm is down, it is brought back online as quickly as possible.</p>
  </div>
  {note}
  <div class="mop-realm-tools">
    <a class="mop-all" href="/wow/realmstatus">All Realms</a>
    <span class="mop-show-filters">Show Filters</span>
  </div>
  <table class="mop-realm-table">
    <thead>
      <tr><th>Status</th><th>Realm Name</th><th>Type</th><th>Population</th><th>Locale</th><th>Queue</th></tr>
    </thead>
    <tbody>
      <tr>
        <td class="mop-status {state_class}">{esc(state)}</td>
        <td>{name}</td>
        <td>{esc(_type_label(realm, unread))}</td>
        <td class="mop-pop mop-pop-{esc(pop_class)}">{esc(pop)}</td>
        <td>English</td>
        <td>{esc(queue)}</td>
      </tr>
    </tbody>
  </table>
</div>"""


def _news_index() -> str:
    rows = []
    for i, story in enumerate(_STORIES):
        rows.append(
            "<li>"
            f'<a href="/wow/news/{i}">{esc(story["title"])}</a>'
            f'<span>{esc(story["when"])} · {esc(story["by"])}</span>'
            "</li>"
        )
    return (
        '<div class="mop-news mop-news-index"><h1>News</h1>'
        "<p>November 2013. Patch 5.4, Siege of Orgrimmar.</p>"
        f"<ul>{''.join(rows)}</ul></div>"
    )


def _news_article(index: int) -> str:
    story = _STORIES[index]
    nxt = ""
    if index + 1 < len(_STORIES):
        nxt = f'<a class="mop-next" href="/wow/news/{index + 1}">Next</a>'
    return (
        '<article class="mop-news mop-story">'
        f"<h1>{esc(story['title'])}</h1>"
        f'<p class="mop-by">by {esc(story["by"])} <time>{esc(story["when"])}</time></p>'
        f'<img src="{esc(_src(story["thumb"]))}" alt="">'
        f"<p>{esc(story['lede'])}</p>"
        f"<p>{esc(story['more'])}</p>"
        f'<p class="mop-pager"><a href="/wow/news">All news</a> {nxt}</p>'
        "</article>"
    )


def _shop_document(exp, dev: bool) -> str:
    tiles = (
        ("tile-wow.jpg", "World of Warcraft®", "/wow/"),
        ("", "Subscription", "/account/create"),
        ("tile-liberty.jpg", "StarCraft® II: Wings of Liberty®", "/shop"),
        ("tile-swarm.jpg", "StarCraft® II: Heart of the Swarm®", "/shop"),
    )
    cards = []
    for image, label, href in tiles:
        if image:
            art = f'<img src="{_IMG}/{image}" alt="">'
        else:
            art = '<span class="shop-medal" aria-hidden="true">W</span>'
        cards.append(
            f'<a class="shop-tile" href="{esc(href)}">{art}<span>{esc(label)}</span></a>'
        )
    games = (
        ("World of Warcraft", "29"),
        ("Diablo III", "1"),
        ("StarCraft II", "5"),
        ("Hearthstone", "1"),
        ("Battle.net", "1"),
    )
    kinds = (
        ("Games", "6"),
        ("Subscriptions", "1"),
        ("Pets", "10"),
        ("Mounts", "5"),
        ("Helms", "3"),
        ("Game Services", "10"),
        ("Battle.net Balance", ""),
    )
    game_links = "".join(
        f'<li><a href="/shop">{esc(name)} <span>({esc(count)})</span></a></li>' for name, count in games
    )
    kind_links = "".join(
        f'<li><a href="/shop">{esc(name)}{(" <span>(" + esc(count) + ")</span>") if count else ""}</a></li>'
        for name, count in kinds
    )
    inner = f"""<div class="shop-site">
  <header class="shop-top">
    <a class="shop-logo" href="/shop"><span class="mop-atom-mark" aria-hidden="true"></span>Battle.net Shop <small>Beta</small></a>
    {_service_bar(None)}
  </header>
  <div class="shop-wrap">
    <p class="shop-crumb"><a href="/shop">Shop</a> <span class="shop-region">Americas &amp; Southeast Asia</span></p>
    <div class="shop-layout">
      <aside class="shop-browse">
        <ul class="shop-games">{game_links}</ul>
        <h2>Browse by Type</h2>
        <ul>{kind_links}</ul>
        <p><a href="/account/">Redeem a Code</a></p>
      </aside>
      <div class="shop-main">
        <div class="shop-hero">
          <img src="{_IMG}/shop-hero.jpg" alt="">
          <p><span>Diablo</span> Evil is in its Prime</p>
        </div>
        <div class="shop-tiles">{''.join(cards)}</div>
      </div>
    </div>
  </div>
</div>"""
    _ = exp
    return document(
        "Battle.net Shop",
        _css(),
        "era-mop gen2 mop shop-gate",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def full(path: str, ctx: dict) -> str | None:
    if path.rstrip("/") != "/shop":
        return None
    return _shop_document(ctx["exp"], bool(ctx.get("dev")))


def take(path: str, ctx: dict):
    norm = path.rstrip("/") or "/"
    if norm == "/account/services":
        user = ctx.get("user")
        if not user:
            from wowweb.services.page import render_page

            body = render_page(ctx["exp"], user="", characters=[], guilds=[])
            body += '<p><a href="/account/login">Log In</a> to use these services on your characters.</p>'
            return "Character Services", body
        from wowweb.services.page import services_page

        body = services_page(ctx["labcfg"], ctx["exp"], user, ctx["data_dir"])
        return "Character Services", body
    if norm == "/wow/realmstatus":
        from wowweb import lab

        realm = lab.realm_status(ctx["labcfg"], ctx["exp"])
        return "Realm Status", realm_body(ctx["exp"], realm, bool(ctx.get("dev")))
    if norm == "/wow/news":
        return "News", _news_index()
    if norm.startswith("/wow/news/"):
        tail = norm.rsplit("/", 1)[-1]
        if not tail.isdigit():
            return None
        index = int(tail)
        if index < 0 or index >= len(_STORIES):
            return "News", (
                '<div class="mop-news"><h1>News</h1>'
                "<p>That story is not on this site.</p>"
                '<p><a href="/wow/news">All news</a></p></div>'
            )
        return _STORIES[index]["title"], _news_article(index)
    return None
