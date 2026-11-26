"""February 2015 Warlords of Draenor community site."""

from __future__ import annotations

import re

from .common import dev_note, document, esc, styles

_IMG = "/static/img/wod"

# The 3 Feb 2015 home. The 2016 news feed stays on /wow/news.
_CARDS = (
    {
        "href": "/wow/news/0",
        "image": "wod-news-foundry.jpg",
        "title": "Blackrock Foundry Raid Schedule",
        "comments": "650",
        "when": "3 hours ago",
    },
    {
        "href": "/wow/news/1",
        "image": "wod-news-forge.jpg",
        "title": "From the Forge – Making Grommash Hellscream",
        "comments": "143",
        "when": "12/17/2014",
    },
    {
        "href": "/wow/news/2",
        "image": "wod-news-unleashed.jpg",
        "title": "Warlords of Draenor™ Unleashed – Expansion Now Live!",
        "comments": "2,979",
        "when": "11/13/2014",
    },
)


def _active(crumb: str, title: str, body: str) -> str:
    if "wod-home" in body:
        return "home"
    blob = f"{crumb} {title} {body[:1500]}".lower()
    if "wod-shop" in blob or (crumb or "").lower() == "shop":
        return "shop"
    if "forum-board" in blob or "forum-index" in blob or "forum-thread" in blob:
        return "forums"
    if any(key in blob for key in ("screenshot", "wallpaper", "shot-grid")):
        return "media"
    if any(
        key in blob
        for key in (
            "game guide",
            "race-grid",
            "class-grid",
            "talent-grid",
            'class="trees"',
            "world map",
            "profession",
        )
    ):
        return "guide"
    if any(key in blob for key in ("realm status", "the armory", "class='sheet", 'class="sheet')):
        return "community"
    return ""


def _tabs(active: str) -> str:
    rows = (
        ("home", "/wow/", "Home"),
        ("guide", "/wow/info", "Game Guide"),
        ("community", "/forums/", "Community"),
        ("media", "/wow/media/screenshots", "Media"),
        ("forums", "/forums/", "Forums"),
        ("shop", "/shop", "Shop"),
    )
    bits = []
    for key, href, label in rows:
        mark = " wod-tab-on" if key == active else ""
        bits.append(
            f'<a class="wod-tab wod-tab-{key}{mark}" href="{esc(href)}">{esc(label)}</a>'
        )
    return "".join(bits)


def _service(user: str | None) -> str:
    if user:
        auth = (
            f'<a href="/account/">{esc(user)}</a>'
            '<a href="/account/logout">Log Out</a>'
        )
    else:
        auth = (
            '<span class="wod-auth"><a href="/account/login">Log in</a>'
            ' or <a href="/account/create">Create an Account</a></span>'
        )
    return f"""<div class="wod-service">
  <a class="wod-bnet" href="/wow/" title="Battle.net"><span class="wod-bnet-mark" aria-hidden="true"></span></a>
  {auth}
  <a href="/shop">Shop</a>
  <a href="/account/">Account</a>
  <details class="wod-support">
    <summary>Support</summary>
    <div><a href="/support/">Support</a></div>
  </details>
  <a class="wod-explore" href="/wow/">Explore</a>
</div>"""


def _plate(user: str | None, exp) -> str:
    if user:
        return (
            '<div class="wod-plate wod-plate-in">'
            f'<a class="wod-plate-name" href="/account/">{esc(user)}</a>'
            f'<span class="wod-plate-realm">{esc(getattr(exp, "realm_name", ""))}</span>'
            '<a class="wod-plate-out-link" href="/account/logout">Log Out</a>'
            "</div>"
        )
    return (
        '<a class="wod-plate wod-plate-out" href="/account/login">'
        "<span><strong>Log in now</strong> to enhance and personalize your experience!</span>"
        f'<img class="wod-key" src="{_IMG}/wod-key.png" alt="">'
        "</a>"
    )


def _crumb(active: str, crumb: str, title: str, body: str) -> str:
    if "wod-home" in body:
        return ""
    label = esc(crumb or title)
    if active == "forums" and "forum-index" not in body:
        return (
            '<p class="wod-crumb"><a href="/wow/">World of Warcraft</a>'
            ' &gt; <a href="/forums/">Forums</a>'
            ' &gt; <a href="/forums/">Community</a>'
            f" &gt; {label}</p>"
        )
    if active == "forums":
        return '<p class="wod-crumb"><a href="/wow/">World of Warcraft</a> &gt; Forums</p>'
    return f'<p class="wod-crumb"><a href="/wow/">World of Warcraft</a> &gt; {label}</p>'


def _footer(user: str | None) -> str:
    cols = [
        (
            "World of Warcraft",
            (
                ("/wow/", "Home"),
                ("/wow/news", "News"),
                ("/wow/info", "Game Guide"),
                ("/story", "Story"),
                ("/armory/", "Armory"),
                ("/wow/realmstatus", "Realm Status"),
            ),
        ),
        (
            "Community",
            (
                ("/forums/", "Forums"),
                ("/forums/general", "General Discussion"),
                ("/forums/guilds", "Guild Recruitment"),
                ("/wow/media/screenshots", "Media"),
                ("/wow/media/wallpapers", "Wallpapers"),
            ),
        ),
        (
            "Account",
            (
                ("/account/login", "Log In"),
                ("/account/create", "Create Account"),
                ("/account/", "Account"),
                ("/account/services", "Character Services"),
                ("/shop", "Shop"),
                ("/support/", "Support"),
            )
            + ((("/account/logout", "Log Out"),) if user else ()),
        ),
    ]
    blocks = []
    for heading, links in cols:
        rows = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in links)
        blocks.append(f'<div><p class="wod-foot-label">{esc(heading)}</p>{rows}</div>')
    return (
        f'<footer class="wod-foot">{"".join(blocks)}'
        '<p class="wod-copy">©2015 Blizzard Entertainment, Inc. All rights reserved.</p>'
        "</footer>"
    )


def _board_tools(body: str, user: str | None) -> str:
    if "forum-board" not in body:
        return body
    found = re.search(r'action="(/forums/[^"]+)"', body)
    href = found.group(1) if found and user else "/account/login"
    return (
        '<div class="wod-forum">'
        '<form class="wod-fsearch" action="/wow/search" method="get">'
        '<input type="search" name="q" placeholder="Search this forum..." aria-label="Search this forum">'
        "</form>"
        f'<a class="wod-create" href="{esc(href)}">Create Topic</a>'
        f"{body}</div>"
    )


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online, login_error
    active = _active(crumb, title, body)
    home = "wod-home" in body
    doc_title = "World of Warcraft" if title == "World of Warcraft" else f"{title} — World of Warcraft"
    if home:
        mast = f"""{_service(user)}
  <header class="wod-head">
    <a class="wod-logo" href="/wow/">
      <img src="{_IMG}/wod-logo.png" alt="World of Warcraft Warlords of Draenor">
    </a>
    <form class="wod-search" action="/wow/search" method="get">
      <input type="text" name="q" placeholder="Search characters, items, forums and more..." aria-label="Search characters, items, forums and more">
      <button type="submit" aria-label="Search"></button>
    </form>
  </header>"""
    else:
        mark = ""
        if "wod-shop" not in body:
            mark = '<a class="wod-wordmark" href="/wow/">Warlords of Draenor</a>'
        mast = mark
    inner = f"""<div class="wod-wrap">
  {mast}
  <div class="wod-frame">
    <div class="wod-navrow">
      <nav class="wod-tabs" aria-label="World of Warcraft">{_tabs(active)}</nav>
      {_plate(user, exp)}
    </div>
    <div class="wod-panel">
      {_crumb(active, crumb, title, body)}
      {_board_tools(body, user)}
    </div>
  </div>
  {_footer(user)}
</div>"""
    css = styles("wod") + [
        "/static/css/forums.css",
        "/static/css/armory.css",
        "/static/css/shop.css",
    ]
    return document(
        doc_title,
        css,
        "era-wod",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _card(card: dict) -> str:
    return (
        f'<a class="wod-card" href="{esc(card["href"])}">'
        f'<img src="{_IMG}/{esc(card["image"])}" alt="">'
        f'<span class="wod-card-title">{esc(card["title"])}</span>'
        '<span class="wod-card-meta">'
        f'<span class="wod-comments">{esc(card["comments"])}</span>'
        f'<span class="wod-when">{esc(card["when"])}</span>'
        "</span></a>"
    )


def home_body(exp, news, realm, user) -> str:
    _ = news, user
    realm = realm or {}
    flag = "Up" if realm.get("up") else "Down"
    name = realm.get("name") or getattr(exp, "realm_name", "")
    cards = "".join(_card(card) for card in _CARDS)
    lead = _CARDS[0]
    return f"""<div class="wod-home">
  <p class="wod-inlabel">World of Warcraft</p>
  <section class="wod-hero">
    <img src="{_IMG}/wod-hero.jpg" alt="">
    <p class="wod-sr">Expansion Set</p>
    <p class="wod-sr">Available Now</p>
    <a class="wod-upgrade" href="/shop">Upgrade</a>
  </section>
  <aside class="wod-side">
    <div class="wod-starter">
      <img src="{_IMG}/wod-starter.jpg" alt="">
      <span class="wod-sr">Starter Edition</span>
      <a class="wod-play" href="/account/create">Play Free Now</a>
    </div>
    <div class="wod-connect">
      <h2>Stay Connected</h2>
      <img class="wod-social" src="{_IMG}/wod-social.jpg" alt="">
    </div>
    <div class="wod-expblock">
      <a class="wod-expinfo" href="/wow/info">
        <span>New Expansion Info</span>
        <img src="{_IMG}/wod-exp.jpg" alt="">
      </a>
      <p class="wod-realm">Realm <strong>{esc(name)}</strong> is <strong class="wod-{flag.lower()}">{flag}</strong>.</p>
    </div>
  </aside>
  <div class="wod-cards">{cards}</div>
  <article class="wod-feature">
    <a href="{esc(lead["href"])}"><img src="{_IMG}/{esc(lead["image"])}" alt=""></a>
    <div>
      <h3><a href="{esc(lead["href"])}">{esc(lead["title"])}</a></h3>
      <p>Blackrock Foundry opens today. Are you ready?</p>
      <span class="wod-card-meta">
        <span class="wod-comments">{esc(lead["comments"])}</span>
        <span class="wod-when">{esc(lead["when"])}</span>
      </span>
    </div>
  </article>
</div>"""


def _shop_body() -> str:
    return f"""<div class="wod-shop">
  <div class="wod-shop-head">
    <h2>Games and Subscriptions</h2>
    <a href="/shop">View options</a>
  </div>
  <div class="wod-products">
    <article class="wod-product">
      <img src="{_IMG}/wod-shop-base.jpg" alt="World of Warcraft">
      <a class="wod-buy" href="/account/create">Buy</a>
      <a class="wod-try" href="/account/create">Try Free</a>
    </article>
    <article class="wod-product">
      <img src="{_IMG}/wod-shop-wod.jpg" alt="World of Warcraft: Warlords of Draenor">
      <p class="wod-product-sub">Warlords of Draenor (Expansion)</p>
      <a class="wod-buy" href="/account/create">Buy</a>
    </article>
  </div>
  <p class="wod-subscribe"><a href="/account/">Subscribe now</a></p>
  <p class="wod-shop-blurb">World of Warcraft is an online subscription fantasy adventure game, made up of a core game and its content expansions. Open Shop and choose the option that interests you most.</p>
  <div class="wod-shop-services">
    <section>
      <h3>Free Services</h3>
      <ul>
        <li><a href="/support/">Recruit a Friend</a></li>
        <li><a href="/support/">Item Restoration</a></li>
      </ul>
    </section>
    <section>
      <h3>Character Services</h3>
      <ul>
        <li><a href="/account/services">Character Transfer</a></li>
        <li><a href="/account/services">Faction Change</a></li>
        <li><a href="/account/services">Race Change</a></li>
      </ul>
    </section>
    <img class="wod-shop-cast" src="{_IMG}/wod-shop-cast.jpg" alt="">
  </div>
</div>"""


def full(path: str, ctx: dict) -> str | None:
    _ = path, ctx
    return None


def take(path: str, ctx: dict):
    _ = ctx
    if path != "/shop":
        return None
    return "Shop", _shop_body()
