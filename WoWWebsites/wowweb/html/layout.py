"""Chrome shells for each visual generation."""

from __future__ import annotations

import html
from typing import Any, Iterable

from ..catalog import Expansion


def e(text: Any) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def _who(user: str | None) -> str:
    if user:
        return (
            f'<span class="who">Signed in as <strong>{e(user)}</strong> · '
            f'<a href="/account/logout">Log Out</a></span>'
        )
    return '<span class="who"><a href="/account/login">Log In</a> · <a href="/account/create">Create Account</a></span>'


def _logo(exp: Expansion) -> str:
    return f"""<a class="wow-logo" href="/wow/" title="World of Warcraft">
  <img class="badge" src="/static/img/badge.png" alt="">
  <span class="wordmark">
    <span class="world">WORLD OF</span>
    <span class="wm">WARCRAFT</span>
    <span class="era">{e(exp.name)}</span>
  </span>
</a>"""


def _search() -> str:
    # Nov 2006 topSearch: query, then a search-type select, then Search. Not a nav bar.
    return f"""<form class="search" id="topSearch" action="/wow/search" method="get">
      <div id="searchBoxContainer">
        <input class="searchBoxForm" type="text" name="q" id="searchBox">
        <select class="searchBoxForm" id="searchType" name="searchType" aria-label="Search in">
          <option value="site">Community Site</option>
          <option value="encyclopedia">Encyclopedia</option>
          <option value="ingamesupport">In-game Support</option>
          <option value="techsupport">Tech Support</option>
        </select>
        <button type="submit" id="searchBoxButton">Search</button>
      </div>
    </form>"""


def _foot(exp: Expansion, dev: bool = False) -> str:
    if not dev:
        return ""
    return (
        f"Last patch {e(exp.last_patch)} · {e(exp.last_patch_date)} · Local realm {e(exp.realm_name)}"
        f" · Visual source {e(exp.snapshot)} · Not affiliated with Blizzard Entertainment."
    )


def layout(
    exp: Expansion,
    title: str,
    body: str,
    user: str | None = None,
    crumb: str = "",
    extra_js: str = "",
    dev: bool = False,
    online: str = "",
    login_error: str = "",
) -> str:
    from . import era as era_pack

    mod = era_pack.module(exp.id)
    if mod is not None and hasattr(mod, "shell"):
        return mod.shell(
            exp, title, body, user, crumb, dev, online, login_error, extra_js
        )
    chrome = exp.visual()
    css = f"/static/css/{chrome}.css"
    if chrome == "alpha":
        inner = _shell_alpha(exp, body, user, dev, online)
    elif chrome == "gen2":
        inner = _shell_gen2(exp, title, body, user, crumb, dev)
    elif chrome == "wowcom":
        inner = _shell_wowcom(exp, title, body, user, crumb, dev)
    elif chrome == "gen4":
        inner = _shell_modern(exp, title, body, user, crumb, dev)
    else:
        inner = _shell_gen1(exp, title, body, user, crumb, dev)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{e(title)} — {e(exp.name)}</title>
<link rel="stylesheet" href="{css}">
<link rel="stylesheet" href="/static/css/icons.css">
<link rel="stylesheet" href="/static/css/armory.css">
<link rel="stylesheet" href="/static/css/forums.css">
<link rel="stylesheet" href="/static/css/shop.css">
<link rel="stylesheet" href="/static/css/account.css">
<link rel="stylesheet" href="/static/css/account-{e(exp.id)}.css">
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body class="{e(chrome)} {e(exp.id)}">
{inner}
<script src="/static/js/site.js"></script>
{extra_js}
</body>
</html>
"""


def _shell_gen1(exp: Expansion, title: str, body: str, user: str | None, crumb: str, dev: bool = False) -> str:
    # Same Nov 2006 community shell for vanilla, TBC, and Wrath (not the 2008 RAF splash).
    return f"""<div class="page-top"></div>
<div class="shell" id="hp">
  <div class="topbar top-nav-container">
    {_logo(exp)}
    <div class="top-nav">
      {_search()}
      {_who(user)}
    </div>
  </div>
  <div class="frame" id="hpWrapper">
    <div class="iron-l"></div>
    <aside class="navcol" id="nav">{_nav(exp)}</aside>
    <div class="main" id="main">
      <div class="main-top" id="main-top"><h1 class="banner redBannerLabel">{e(crumb or title)}</h1></div>
      <div class="main-body" id="main-content">
        <div class="cnt" id="cnt">{body}</div>
        <aside class="marginal" id="marginal">{_rail(exp)}</aside>
      </div>
      <div class="main-bot" id="main-bottom"></div>
    </div>
    <div class="iron-r"></div>
  </div>
  <footer>{_foot(exp, dev)}</footer>
</div>"""


def _h_nav(exp: Expansion) -> str:
    if exp.visual() == "gen4":
        links = [
            ("/wow/", "Game"),
            ("/wow/news", "News"),
            ("/wow/info/", "Guide"),
            ("/armory/", "Armory"),
            ("/forums/", "Forums"),
            ("/wow/realmstatus/", "Realms"),
            ("/support/", "Support"),
            ("/account/", "Account"),
        ]
    else:
        links = [
            ("/wow/", "Game"),
            ("/wow/info/", "Guide"),
            ("/armory/", "Armory"),
            ("/forums/", "Forums"),
            ("/wow/media/screenshots", "Media"),
            ("/wow/realmstatus/", "Realms"),
            ("/support/", "Support"),
            ("/account/", "Account"),
        ]
    return "<nav class='h-nav'>" + "".join(f'<a href="{e(h)}">{e(t)}</a>' for h, t in links) + "</nav>"


def _gen2_menu(exp: Expansion, crumb: str) -> str:
    # August 2012 still said Services. By Mists the tab was Shop.
    tail = ("/account/services", "Services") if exp.id == "cata" else ("/shop", "Shop")
    links = [
        ("/wow/", "Home"),
        ("/wow/info/", "Game Guide"),
        ("/forums/", "Community"),
        ("/wow/media/screenshots", "Media"),
        ("/forums/", "Forums"),
        tail,
    ]
    low = crumb.lower()

    def active(label: str) -> bool:
        if label == "Home":
            return low == "world of warcraft"
        if label == "Game Guide":
            return any(k in low for k in ("guide", "race", "class", "profession", "feature", "talent", "player", "map", "patch", "award"))
        if label == "Forums":
            return "forum" in low
        if label == "Media":
            return any(k in low for k in ("screenshot", "wallpaper", "media"))
        if label == "Shop":
            return "shop" in low
        if label == "Services":
            return any(k in low for k in ("account", "log in", "create account"))
        return False

    items = "".join(
        f'<li><a href="{e(href)}"' + (' class="active"' if active(text) else "") + f">{e(text)}</a></li>"
        for href, text in links
    )
    return f'<ul class="bnet-menu">{items}</ul>'


def _service_bar(exp: Expansion, user: str | None) -> str:
    # 2012-08 and 2014-08: a right-side cell bar (common.css #service).
    # 2016-03 replaced it with the full-width nav-client (Games, Shop, account).
    if user:
        welcome = f'<a href="/account/">Welcome, {e(user)}</a>'
    else:
        welcome = '<a href="/account/login">Log in</a> or <a href="/account/create">Create an Account</a>'
    if exp.id == "wod":
        account = "Account" if user else "Your account"
        return f"""<div class="service-bar nav-client">
  <a class="service-home" href="/wow/" title="Battle.net Home"><span>Battle.net</span></a>
  <a class="service-games" href="/wow/">Games</a>
  <a class="service-link service-shop" href="/shop">Shop</a>
  <span class="service-spacer"></span>
  <a class="service-link service-account" href="/account/">{account}</a>
  <a class="service-link service-support" href="/support/">Support</a>
</div>"""
    shop = '<a class="service-link service-shop" href="/shop">Shop</a>' if exp.id == "mop" else ""
    return f"""<div class="service-bar">
  <a class="service-home" href="/wow/" title="Battle.net Home"><span>Battle.net</span></a>
  <span class="service-welcome">{welcome}</span>
  {shop}
  <a class="service-link service-account" href="/account/">Account</a>
  <a class="service-link service-support" href="/support/">Support</a>
  <a class="service-explore" href="/wow/">Explore</a>
</div>"""


def _sitemap(exp: Expansion, dev: bool = False) -> str:
    cols = [
        (
            "Battle.net Home",
            [
                ("/wow/", "What is Battle.net"),
                ("/shop", "Buy Games"),
                ("/account/", "Account"),
                ("/support/", "Support"),
                ("/account/", "Real ID"),
                ("/account/", "BattleTag"),
            ],
        ),
        (
            "Games",
            [
                ("/wow/", "World of Warcraft"),
                ("/wow/", exp.name),
                ("/wow/media/screenshots", "Downloads"),
            ],
        ),
        (
            "Account",
            [
                ("/account/login", "Log In"),
                ("/account/create", "Create Account"),
                ("/account/", "Account Settings"),
            ],
        ),
        (
            "Support",
            [
                ("/support/", "Customer Support"),
                ("/wow/realmstatus/", "Realm Status"),
                ("/forums/bugs", "Bug Report"),
            ],
        ),
    ]
    blocks = []
    for heading, links in cols:
        lis = "".join(f'<li><a href="{e(href)}">{e(text)}</a></li>' for href, text in links)
        blocks.append(f"<div><h4>{e(heading)}</h4><ul>{lis}</ul></div>")
    return (
        f'<footer class="sitemap">{"".join(blocks)}'
        f'<p class="copy">©{e(exp.year)} Blizzard Entertainment, Inc. All rights reserved.</p>'
        f'<p class="local-note">{_foot(exp, dev)}</p></footer>'
    )


def _shell_gen2(exp: Expansion, title: str, body: str, user: str | None, crumb: str, dev: bool = False) -> str:
    home = crumb == "World of Warcraft"
    if user:
        plate = (
            f'<div class="card-login card-user"><strong>{e(user)}</strong>'
            f' Signed in on {e(exp.realm_name)}. <a href="/account/">Account</a></div>'
        )
    else:
        plate = (
            '<a class="card-login" href="/account/login">'
            "<strong>Log in now</strong> to enhance and personalize your experience!</a>"
        )
    if home:
        inner = body
    else:
        inner = (
            f'<div class="content-header"><h1>{e(crumb or title)}</h1></div>'
            f'<div class="bnet-inner">{body}</div>'
        )
    bar = _service_bar(exp, user)
    # WoD's nav-client sits outside the 1006px wrapper. Earlier eras pin #service
    # to the top-right of that wrapper.
    if exp.id == "wod":
        lead, inside = bar, ""
    else:
        lead, inside = "", bar
    return f"""{lead}
<div class="bnet">
  {inside}
  <header class="bnet-header">
    <a class="bnet-logo" href="/wow/">
      <span class="world">World of</span>
      <span class="wm">Warcraft</span>
      <span class="era">{e(exp.name)}</span>
    </a>
    <form class="bnet-search" action="/wow/search" method="get">
      <input type="text" name="q" aria-label="Search characters, items, forums and more">
      <button type="submit">Go</button>
    </form>
    <div class="header-plate">
      {_gen2_menu(exp, crumb)}
      <div class="user-plate">{plate}</div>
    </div>
  </header>
  <div class="bnet-content">{inner}</div>
  {_sitemap(exp, dev)}
</div>"""


def _shell_wowcom(exp: Expansion, title: str, body: str, user: str | None, crumb: str, dev: bool = False) -> str:
    # Desktop labels from the SiteNav captures, not the later notes.
    # Legion 20180101030831 has no "Home" item (the logo is home) and keeps Story.
    # BfA 20200701020001 and Shadowlands 20220801005211 drop Story and add
    # WoW Classic plus Subscribe. Every account/shop href stays on this host.
    if exp.id == "legion":
        sub = [
            ("/wow/info/", "Game"),
            ("/story", "Story"),
            ("/wow/news", "News"),
            ("/forums/", "Forums"),
            ("/shop", "Shop"),
            ("/esports", "Esports"),
        ]
        subscribe = ""
    else:
        sub = [
            ("/wow/info/", "Game"),
            ("/wow/news", "News"),
            ("/forums/", "Forums"),
            ("/shop", "Shop"),
            ("/esports", "Esports"),
            ("/classic", "WoW Classic"),
        ]
        subscribe = '<a class="sub-subscribe" href="/shop">Subscribe</a>'
    sub_html = "".join(f'<a href="{e(href)}">{e(text)}</a>' for href, text in sub)
    if user:
        account = (
            f'<span class="who">Signed in as <strong>{e(user)}</strong> · '
            f'<a href="/account/logout">Log Out</a></span>'
        )
        login = ""
    else:
        account = '<a class="blizz-account" href="/account/login">My Account</a>'
        login = '<a class="sub-login" href="/account/login">Log in</a>'
    return f"""<header class="wowcom-head">
  <div class="blizz-bar">
    <a class="blizz-mark" href="/wow/">Blizzard</a>
    <nav class="blizz-links" aria-label="Blizzard">
      <a href="/wow/">Games</a>
      <a href="/shop">Shop</a>
      <a href="/wow/news">News</a>
      <a href="/esports">Esports</a>
      <a href="/support/">Support</a>
    </nav>
    {account}
  </div>
  <div class="wow-sub">
    <div class="wow-sub-bar">
      <a class="sub-logo" href="/wow/">World of Warcraft</a>
      <nav class="subnav" aria-label="World of Warcraft">{sub_html}</nav>
      <div class="sub-right">
        {login}
        {subscribe}
        <a class="try" href="/account/create">Try Free</a>
      </div>
    </div>
  </div>
</header>
<div class="shell">
  <div class="main">
    <div class="main-top"><h1 class="banner">{e(crumb or title)}</h1></div>
    <div class="main-body">
      <div class="cnt">{body}</div>
      <aside class="marginal">{_rail(exp, ssotd=False)}</aside>
    </div>
  </div>
  <footer>{_foot(exp, dev)}</footer>
</div>"""


def _shell_alpha(exp: Expansion, body: str, user: str | None, dev: bool = False, online: str = "") -> str:
    if user:
        account = (
            f'<div class="bevel"><div class="a-fields">'
            f'<p class="a-signed">Signed in as <strong>{e(user)}</strong></p>'
            f'<p><a href="/account/logout">Log Out</a></p>'
            f'<p><a href="/account/">Manage Account</a></p>'
            f"</div></div>"
        )
    else:
        account = """
<form class="a-login" method="post" action="/account/login">
  <div class="bevel"><div class="a-fields">
    <label><span>Login:</span> <input name="username" value="" size="17" maxlength="16" autocomplete="username"></label>
    <label><span>Pass:</span> <input name="password" type="password" size="17" autocomplete="current-password"></label>
    <hr class="a-hr">
    <button type="submit">Login</button>
  </div></div>
</form>"""
    return f"""<header class="a-head">
  <div class="a-stats">
    <a href="/wow/realmstatus/">
      <span class="a-stat-left"></span>
      <span class="a-stat-world">World Server Status</span>
      <span class="a-stat-count">{e(online or "0")}</span>
    </a>
  </div>
  <div class="a-country">
    <a class="yellow" href="/wow/">Choose a country:</a>
    <div class="a-countries">
      <a href="/wow/">USA</a>
      <span>Korea</span>
    </div>
  </div>
  <a class="a-logo" href="/wow/" title="WoW Beta Site">
    <span>World of</span>
    <strong>Warcraft</strong>
  </a>
</header>
<div class="a-frame">
  <nav class="a-nav">
    <a href="/wow/">News</a>
    <a href="/wow/info/">Game Info</a>
    <a href="/forums/">Forums</a>
    <a href="/wow/info/classes/">Database</a>
    <a href="/wow/media/screenshots">Links and Files</a>
    <a href="/support/">Support</a>
    <div class="a-flames"></div>
  </nav>
  <div class="a-sheet">
    <div class="a-sheet-top">
      <aside class="a-side sidebar">
        {account}
        <ul class="a-links">
          <li><a href="/account/create">Create Account</a></li>
          <li><a href="/wow/info/">World of Warcraft Guide</a></li>
          <li><a href="/forums/">World of Warcraft Forums</a></li>
        </ul>
      </aside>
    </div>
    <div class="a-main">{body}</div>
    <p class="a-legal"><span class="small">Online Privacy Policy</span> | <span class="small">Legal Documents</span><br>©2004 Blizzard Entertainment. All rights reserved.</p>
  </div>
  <div class="a-edge"></div>
</div>
<footer class="a-foot">{_foot(exp, dev)}</footer>"""


def _shell_modern(exp: Expansion, title: str, body: str, user: str | None, crumb: str, dev: bool = False) -> str:
    return f"""<header class="mod-head">
  {_logo(exp)}
  {_h_nav(exp)}
  {_who(user)}
</header>
<div class="shell">
  <div class="main">
    <div class="main-top"><h1 class="banner">{e(crumb or title)}</h1></div>
    <div class="main-body">
      <div class="cnt">{body}</div>
      <aside class="marginal">{_rail(exp, ssotd=False)}</aside>
    </div>
  </div>
  <footer>{_foot(exp, dev)}</footer>
</div>"""


def _class_forum_links(exp: Expansion) -> list[tuple[str, str]]:
    links = [
        ("/forums/warrior", "Warrior"),
        ("/forums/paladin", "Paladin"),
        ("/forums/hunter", "Hunter"),
        ("/forums/rogue", "Rogue"),
        ("/forums/priest", "Priest"),
        ("/forums/shaman", "Shaman"),
        ("/forums/mage", "Mage"),
        ("/forums/warlock", "Warlock"),
        ("/forums/druid", "Druid"),
    ]
    if exp.expansion_level >= 2:
        links.insert(5, ("/forums/deathknight", "Death Knight"))
    return links


def _nav(exp: Expansion) -> str:
    menus = [
        (
            "News",
            [
                ("/wow/", "Current News"),
                ("/wow/news", "Archived News"),
                ("/wow/info/awards", "Awards and Honors"),
            ],
        ),
        (
            "Account",
            [
                ("/account/create", "Create Account"),
                ("/account/", "Manage Account"),
                ("/wow/realmstatus/", "Realm Status"),
            ],
        ),
        (
            "Game Guide",
            [
                ("/wow/info/", "Introduction"),
                ("/wow/info/features", "Features"),
                ("/wow/info/races", "Races"),
                ("/wow/info/classes", "Classes"),
                ("/wow/info/professions", "Professions"),
                ("/wow/info/basics/", "New Players"),
                ("/wow/info/patches", "Previous Patches"),
            ],
        ),
        (
            "Interactive",
            [
                ("/wow/pvp/rankings", "PvP Rankings"),
                ("/wow/info/classes/", "Talent Calculators"),
                ("/wow/info/basics/map", "World Map"),
            ]
            + ([("/armory/", "The Armory")] if exp.has_armory else [("/armory/", "The Armory (coming in TBC)")]),
        ),
        (
            "Media",
            [
                ("/wow/media/screenshots", "Screenshots"),
                ("/wow/media/wallpapers", "Wallpapers"),
            ],
        ),
        (
            "Forums",
            [
                ("/forums/", "General"),
                *_class_forum_links(exp),
                ("/forums/realm", "Realm Forums"),
                ("/forums/guilds", "Guild Recruitment"),
            ],
        ),
        (
            "Community",
            [
                ("/wow/media/screenshots", "Screenshots"),
                ("/wow/media/wallpapers", "Wallpapers"),
                ("/forums/", "Forums"),
            ],
        ),
        (
            "Support",
            [
                ("/support/", "Customer Support"),
                ("/forums/bugs", "Bug Report"),
                ("/wow/realmstatus/", "Realm Status"),
            ],
        ),
    ]
    open_labels = {"News", "Game Guide"}
    chunks = []
    for i, (label, links) in enumerate(menus):
        items = "".join(
            f'<li><a class="menuFiller" href="{e(href)}">{e(text)}</a></li>' for href, text in links
        )
        opened = label in open_labels
        state = "open" if opened else "closed"
        chunks.append(
            f"""<div class="menu {state}" data-menu="{i}">
  <button type="button" class="menu-btn" aria-expanded="{str(opened).lower()}">
    <em>{e(label)}</em><span class="pm"></span>
  </button>
  <div class="menu-inner"><ul>{items}</ul></div>
</div>"""
        )
    return f'<div class="left-menu">{"".join(chunks)}</div>'


def _rail(exp: Expansion, ssotd: bool = True) -> str:
    shot = ""
    if ssotd:
        from .. import assets

        shots = assets.screenshots(exp.id)
        src = shots[0][0] if shots else "/static/img/ssotd-elwynn.jpg"
        shot = f"""
<div class="ibox" id="ssotd-container">
  <h3>Screenshot of the Day</h3>
  <a href="/wow/media/screenshots"><img class="ssotd ssotd-screen" src="{e(src)}" alt="Azeroth landscape"></a>
  <p class="ssotd-link"><a href="/wow/media/screenshots">Screenshot Archive</a></p>
</div>
"""
    return f"""{shot}
<div class="ibox">
  <h3>Realm Status</h3>
  <p><a href="/wow/realmstatus/">{e(exp.realm_name)}</a></p>
</div>
<div class="ibox" id="gameinfo-newcomers-container">
  <h3>New Players</h3>
  <p>{e(exp.name)} · patch {e(exp.last_patch)}. Start with the
  <a href="/wow/info/basics/">beginner's guide</a>.</p>
</div>
"""


def simple_list(heading: str, items: Iterable[str]) -> str:
    lis = "".join(f"<li>{e(i)}</li>" for i in items)
    return f"<h2>{e(heading)}</h2><ul>{lis}</ul>"


def error_page(message: str) -> str:
    return f"<h2>Not Found</h2><p>{e(message)}</p><p><a href='/wow/'>Return to the community site</a></p>"



