"""May 2024 eu.shop.battle.net Classic family shop, used as the Cataclysm Classic shell.

The accepted shot is the shop only. Home is that family page. A fourth NEW
mount is cut off at the bottom of the frame, so it is not named here.
"""

from __future__ import annotations

from .common import dev_note, document, esc, styles

_IMG = "/static/img/cata-classic"

_BLURB = (
    "Includes access to World of Warcraft, upcoming Cataclysm Classic, "
    "Classic Season of Discovery and Hardcore Realms!"
)

_GAMES = ("Call of Duty", "Diablo", "Overwatch", "StarCraft", "More")

_MENU = (
    ("/wow/", "World of Warcraft Classic"),
    ("/shop", "Shop"),
    ("/wow/news", "News"),
    ("/wow/info", "Guide"),
    ("/wow/realmstatus", "Realm Status"),
    ("/forums", "Forums"),
    ("/forums/general", "General"),
    ("/support/", "Support"),
    ("/account/", "Account"),
    ("/account/login", "Log In"),
    ("/account/create", "Create Account"),
    ("/account/services", "Services"),
)

_SUBS = (
    (
        "sub-cataclysm.jpg",
        "Cataclysm Classic key art",
        "WORLD OF WARCRAFT CLASSIC CATACLYSM",
        "World of Warcraft®: Subscription",
    ),
    (
        "sub-offer.jpg",
        "Classic special subscription art",
        "WORLD OF WARCRAFT CLASSIC",
        "World of Warcraft®: Special Subscription Offer",
    ),
)

_MOUNTS = (
    ("mount-arborwyrm.jpg", "Auspicious Arborwyrm", "€25.00"),
    ("mount-whalebone.jpg", "Kalu'ak Whalebone Glider", "€25.00"),
    ("mount-phasehunter.jpg", "Re-Awakened Phase-Hunter Mount", "€15.00"),
)

_HOUSE = (
    '<svg class="cc-house" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">'
    '<path fill="currentColor" d="M8 1.8 1.2 7.2h1.6V14h3.7V9.2h3V14h3.7V7.2h1.6L8 1.8z"/>'
    "</svg>"
)


def _family() -> str:
    subs = []
    for filename, alt, kicker, title in _SUBS:
        subs.append(
            '<article class="cc-card cc-sub">'
            f'<img src="{_IMG}/{filename}" alt="{esc(alt)}">'
            '<div class="cc-card-body">'
            f'<p class="cc-kicker"><span class="cc-w" aria-hidden="true">W</span> {esc(kicker)}</p>'
            f"<h3>{esc(title)}</h3>"
            f'<p class="cc-gold">{esc(_BLURB)}</p>'
            '<p class="cc-cat"><a href="/shop">Subscriptions</a></p>'
            '<p class="cc-more"><a href="/account/">Learn More</a></p>'
            "</div></article>"
        )
    mounts = []
    for filename, name, price in _MOUNTS:
        mounts.append(
            '<article class="cc-card cc-mount">'
            '<div class="cc-shot">'
            '<span class="cc-new">NEW</span>'
            f'<img src="{_IMG}/{filename}" alt="{esc(name)}">'
            "</div>"
            '<div class="cc-card-body">'
            '<p class="cc-kicker"><span class="cc-w" aria-hidden="true">W</span> WORLD OF WARCRAFT CLASSIC</p>'
            f"<h3>{esc(name)}</h3>"
            '<p class="cc-cat">Mounts</p>'
            f'<p class="cc-price">{esc(price)}</p>'
            "</div></article>"
        )
    return (
        '<div class="cc-family">'
        '<section class="cc-section">'
        '<div class="cc-copy"><h2>Subscriptions</h2>'
        "<p>Begin your journey or renew your subscription.</p></div>"
        f'<div class="cc-grid cc-grid-2">{"".join(subs)}</div>'
        "</section>"
        '<hr class="cc-rule">'
        '<section class="cc-section">'
        '<div class="cc-copy"><h2>Mounts</h2>'
        "<p>Saddle up, because your mount will travel as fast as your riding skill will take you.</p></div>"
        f'<div class="cc-grid cc-grid-3">{"".join(mounts)}</div>'
        "</section>"
        "</div>"
    )


def _games() -> str:
    menu = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in _MENU)
    franchises = "".join(f'<span class="cc-franchise cc-caret">{esc(name)}</span>' for name in _GAMES)
    return (
        '<details class="cc-drop">'
        '<summary class="cc-caret">Warcraft</summary>'
        f'<div class="cc-menu">{menu}</div>'
        "</details>"
        f"{franchises}"
    )


def _crumb(body: str, crumb: str) -> str:
    home = f'<a class="cc-home" href="/wow/" aria-label="Home">{_HOUSE}</a>'
    sep = '<span class="cc-sep" aria-hidden="true">&gt;</span>'
    if "cc-family" in body:
        here = "<span>World of Warcraft Classic</span>"
        tail = ""
    else:
        here = '<a href="/shop">World of Warcraft Classic</a>'
        tail = f"{sep}<span>{esc(crumb)}</span>" if crumb else ""
    return f'<nav class="cc-crumb" aria-label="Breadcrumb">{home}{sep}{here}{tail}</nav>'


def _who(user: str | None) -> str:
    if not user:
        return ""
    return (
        f'<a class="cc-who" href="/account/">Signed in as {esc(user)}</a>'
        '<a class="cc-who" href="/account/logout">Log Out</a>'
    )


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online
    err = f'<p class="acct-error">{esc(login_error)}</p>' if login_error else ""
    inner = f"""<div class="cc-site" id="top">
  <div class="cc-wrap">
    <header class="cc-bar">
      <nav class="cc-games" aria-label="Games">{_games()}</nav>
      <form class="cc-search" action="/wow/search" method="get">
        <span class="cc-mag" aria-hidden="true"></span>
        <input type="search" name="q" placeholder="Search Shop" aria-label="Search Shop">
      </form>
      <a class="cc-balance cc-caret" href="/account/">Battle.net Balance</a>
      {_who(user)}
    </header>
    {_crumb(body, crumb)}
    <main class="cc-main">{err}{body}</main>
  </div>
  <a class="cc-top" href="#top" aria-label="Back to top">⌃</a>
</div>"""
    return document(
        f"{title} — World of Warcraft Classic",
        styles(exp.id),
        "era-cata-classic",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    _ = exp, news, realm, user
    return _family()


def full(path: str, ctx: dict) -> str | None:
    _ = path, ctx
    return None


def take(path: str, ctx: dict):
    if path == "/shop":
        return "Shop", _family()
    if path == "/account/services" and not ctx.get("user"):
        body = (
            '<section class="cc-gate">'
            "<h2>Character Services</h2>"
            "<p>Sign in to use character services.</p>"
            '<p><a href="/account/login">Log In</a></p>'
            "</section>"
        )
        return "Character Services", body
    return None
