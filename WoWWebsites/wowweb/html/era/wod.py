"""February 2015 Warlords of Draenor community site."""

from __future__ import annotations

from .common import dev_note, document, esc, styles

_IMG = "/static/img/wod"


def _shown_date(iso: str) -> str:
    parts = (iso or "").split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = parts
        return f"{int(month)}/{int(day)}/{year}"
    return iso or ""


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
  <div class="wod-service-inner">
    <a class="wod-bnet" href="/wow/" title="Battle.net"><span class="wod-bnet-mark" aria-hidden="true"></span><span>Battle.net</span></a>
    {auth}
    <a href="/shop">Shop</a>
    <a href="/account/">Account</a>
    <a href="/support/">Support</a>
    <details class="wod-explore">
      <summary>Explore</summary>
      <div><a href="/wow/">World of Warcraft</a></div>
    </details>
  </div>
</div>"""


def _plate(user: str | None, exp) -> str:
    if user:
        return (
            f'<a class="wod-plate wod-plate-in" href="/account/">'
            f'<span class="wod-plate-name">{esc(user)}</span>'
            f'<span class="wod-plate-realm">{esc(getattr(exp, "realm_name", ""))}</span>'
            "</a>"
        )
    return (
        '<a class="wod-plate wod-plate-out" href="/account/login">'
        "<span><strong>Log in now</strong> to enhance and personalize your experience!</span>"
        '<span class="wod-key" aria-hidden="true"></span>'
        "</a>"
    )


def _crumb(active: str, crumb: str, title: str, body: str) -> str:
    if "wod-home" in body:
        return ""
    label = esc(crumb or title)
    if active == "forums" and "forum-index" not in body:
        return (
            '<p class="wod-crumb"><a href="/wow/">World of Warcraft</a>'
            ' › <a href="/forums/">Forums</a>'
            ' › <a href="/forums/">Community</a>'
            f" › {label}</p>"
        )
    if active == "forums":
        return '<p class="wod-crumb"><a href="/wow/">World of Warcraft</a> › Forums</p>'
    return f'<p class="wod-crumb"><a href="/wow/">World of Warcraft</a> › {label}</p>'


def _footer() -> str:
    cols = (
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
            ),
        ),
    )
    blocks = []
    for heading, links in cols:
        rows = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in links)
        blocks.append(f'<div><p class="wod-foot-label">{esc(heading)}</p>{rows}</div>')
    return (
        f'<footer class="wod-foot">{"".join(blocks)}'
        '<p class="wod-copy">©2015 Blizzard Entertainment, Inc. All rights reserved.</p>'
        "</footer>"
    )


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online, login_error
    active = _active(crumb, title, body)
    doc_title = "World of Warcraft" if title == "World of Warcraft" else f"{title} — World of Warcraft"
    inner = f"""{_service(user)}
<div class="wod-wrap">
  <header class="wod-head">
    <a class="wod-logo" href="/wow/">
      <img src="{_IMG}/wod-logo.jpg" alt="World of Warcraft Warlords of Draenor">
    </a>
    <form class="wod-search" action="/wow/search" method="get">
      <input type="text" name="q" placeholder="Search characters, items, forums and more..." aria-label="Search characters, items, forums and more">
      <button type="submit" aria-label="Search"></button>
    </form>
  </header>
  <div class="wod-navrow">
    <nav class="wod-tabs" aria-label="World of Warcraft">{_tabs(active)}</nav>
    {_plate(user, exp)}
  </div>
  <div class="wod-panel">
    {_crumb(active, crumb, title, body)}
    {body}
  </div>
  {_footer()}
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


def _news_card(index: int, title: str, date: str) -> str:
    return (
        f'<a class="wod-card" href="/wow/news/{index}">'
        f'<img src="{_IMG}/wod-hero.jpg" alt="">'
        f'<span class="wod-card-title">{esc(title)}</span>'
        f'<span class="wod-meta">{esc(_shown_date(date))}</span>'
        "</a>"
    )


def home_body(exp, news, realm, user) -> str:
    _ = user
    realm = realm or {}
    flag = "Up" if realm.get("up") else "Down"
    name = realm.get("name") or getattr(exp, "realm_name", "")
    rows = list(news or [])
    cards = "".join(
        _news_card(i, item[0], item[1]) for i, item in enumerate(rows[:3])
    )
    if rows:
        title, date, blurb = rows[0][0], rows[0][1], rows[0][2] if len(rows[0]) > 2 else ""
        feature = (
            '<article class="wod-feature">'
            f'<a href="/wow/news/0"><img src="{_IMG}/wod-hero.jpg" alt=""></a>'
            "<div>"
            f'<h3><a href="/wow/news/0">{esc(title)}</a></h3>'
            f"<p>{esc(blurb)}</p>"
            f'<span class="wod-meta">{esc(_shown_date(date))}</span>'
            "</div></article>"
        )
    else:
        feature = ""
    return f"""<div class="wod-home">
  <p class="wod-inlabel">World of Warcraft</p>
  <section class="wod-hero">
    <img src="{_IMG}/wod-hero.jpg" alt="">
    <div class="wod-hero-copy">
      <p class="wod-kicker">Expansion Set</p>
      <p class="wod-hero-title">World of Warcraft</p>
      <p class="wod-hero-era">Warlords of Draenor</p>
      <p class="wod-avail">Available Now</p>
      <a class="wod-upgrade" href="/shop">Upgrade</a>
    </div>
  </section>
  <aside class="wod-side">
    <div class="wod-starter">
      <img src="{_IMG}/wod-starter.jpg" alt="">
      <span class="wod-starter-label">Starter Edition</span>
      <a class="wod-play" href="/account/create">Play Free Now</a>
    </div>
    <div class="wod-connect">
      <h2>Stay Connected</h2>
      <div class="wod-social" aria-hidden="true">
        <span class="soc soc-rss"></span>
        <span class="soc soc-fb"></span>
        <span class="soc soc-tw"></span>
        <span class="soc soc-yt"></span>
        <span class="soc soc-rd"></span>
      </div>
    </div>
    <a class="wod-expinfo" href="/wow/info">
      <span>New Expansion Info</span>
      <img src="{_IMG}/wod-box-wod.jpg" alt="">
    </a>
    <p class="wod-realm">Realm <strong>{esc(name)}</strong> is <strong class="wod-{flag.lower()}">{flag}</strong>.</p>
  </aside>
  <div class="wod-cards">{cards}</div>
  {feature}
</div>"""


def _shop_body() -> str:
    return f"""<div class="wod-shop">
  <div class="wod-shop-head">
    <h2>Games and Subscriptions</h2>
    <a href="/shop">View options</a>
  </div>
  <div class="wod-products">
    <article class="wod-product">
      <img src="{_IMG}/wod-box-base.jpg" alt="">
      <h3>World of Warcraft</h3>
      <a class="wod-buy" href="/account/create">Buy</a>
      <a class="wod-try" href="/account/create">Try Free</a>
    </article>
    <article class="wod-product">
      <img src="{_IMG}/wod-box-wod.jpg" alt="">
      <h3>World of Warcraft</h3>
      <p class="wod-product-sub">Warlords of Draenor (Expansion)</p>
      <a class="wod-buy" href="/account/create">Buy</a>
    </article>
  </div>
  <p class="wod-subscribe"><a href="/account/">Subscribe now</a></p>
  <p class="wod-shop-blurb">World of Warcraft is an online subscription fantasy adventure game, made up of a core game and its content expansions. Open Shop and choose the option you want.</p>
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
    <img class="wod-shop-cast" src="{_IMG}/wod-box-wod.jpg" alt="">
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
