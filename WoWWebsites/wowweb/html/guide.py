"""Game-guide and news page bodies."""

from __future__ import annotations

from typing import Iterable

from .. import assets
from ..catalog import Expansion
from ..content import CLASS_INFO, RACE_INFO, class_facts, intro_blurb, race_facts
from .layout import e


def _first_shot(exp: Expansion) -> str | None:
    shots = assets.screenshots(exp.id)
    if not shots:
        return None
    return shots[0][0]


def _mdy(iso: str) -> str:
    parts = iso.split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = parts
        return f"{month}/{day}/{year[2:]}"
    return iso


def home_page(exp: Expansion, news: list[tuple[str, str, str]], realm: dict) -> str:
    from . import era as era_pack

    mod = era_pack.module(exp.id)
    if mod is not None and hasattr(mod, "home_body"):
        return mod.home_body(exp, news, realm, None)
    chrome = exp.visual()
    up = "Up" if realm.get("up") else "Down"
    if chrome == "alpha":
        posts = []
        for i, (title, date, body) in enumerate(news):
            posts.append(
                f"""<div class="postContainer">
  <h3 class="title"><a href="/wow/news/{i}">{e(title)}</a> - <small>{_mdy(date)}</small></h3>
  <div class="postBody"><p>{e(body)}</p></div>
</div>"""
            )
        posts.append(
            """<div class="postContainer">
  <h3 class="title">Miss a News Item?</h3>
  <div class="postBody"><p>Make sure that you keep up to date on all the latest in the <a href="/wow/news">WoW News Archive</a>.</p></div>
</div>"""
        )
        return (
            '<div class="header datebanner"><span class="date">Current News</span></div>'
            + "".join(posts)
            + f'<p class="posted">Realm {e(exp.realm_name)} is {up}.</p>'
        )
    if exp.id == "tbc":
        return _home_splash()
    if chrome == "gen2":
        return _home_battle(exp, news, up)
    if chrome in ("wowcom", "gen4"):
        return _home_mast(exp, news, up)
    items = []
    for i, (title, date, body) in enumerate(news):
        hilite = " hilite" if i % 2 == 0 else ""
        parts = date.split("-")
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            year, month, day = parts
            shown = f"{month}-{day}-{year[2:]}"
        else:
            shown = date
        items.append(
            f"""<tr class="news-row{hilite}">
  <td class="date"><span class="date">{e(shown)}</span></td>
  <td>
    <div class="hdl"><h3><a href="/wow/news/{i}">{e(title)}</a></h3></div>
    <p>{e(body)}</p>
  </td>
</tr>"""
        )
    return f"""
<figure class="hero-wrap" id="imageSwitcher">
  <img class="hero" src="/static/img/{e(exp.hero)}" alt="">
  <figcaption class="hero-cap">Patch {e(exp.last_patch)}</figcaption>
</figure>
<p class="kicker">{e(intro_blurb(exp))}</p>
<table class="news" id="generalNews">
<thead><tr><th class="col1">Date</th><th class="col2">Current News</th></tr></thead>
<tbody>{''.join(items)}</tbody>
</table>
<p class="realm-chip">Realm <strong>{e(exp.realm_name)}</strong> is <strong>{up}</strong>.</p>
"""


def _home_splash() -> str:
    # Saved splash has the style block only. Button art was not kept, so the stage stays black.
    return """<style type="text/css">
.raf-page { text-align:center; background:#000; }
.raf-page .stage { width:956px; height:800px; margin:0 auto; padding:0; text-align:left; position:relative; background:#000; }
.raf-page a:active { outline:none; }
.raf-page a:focus { outline:none; }
.raf-page .button1, .raf-page .button2 { width:363px; height:35px; position:absolute; left:508px; display:block; margin:0; padding:0; color:#D0A803; font:bold 12px Arial, Helvetica, sans-serif; line-height:35px; text-align:center; text-decoration:none; }
.raf-page .button1 { top:516px; }
.raf-page .button2 { top:556px; }
.raf-page .button1:hover, .raf-page .button2:hover { color:#fff; }
</style>
<div class="raf-page">
  <div class="stage">
    <a class="button1" href="/wow/news">New Player</a>
    <a class="button2" href="/wow/news">Returning Player</a>
  </div>
</div>"""


def _home_battle(exp: Expansion, news: list[tuple[str, str, str]], up: str) -> str:
    hero = f"/static/img/{e(exp.hero)}"
    shots = assets.screenshots(exp.id)
    thumb = e(_first_shot(exp) or "/static/img/ssotd-elwynn.jpg")

    def _pic(index: int, use_hero: bool) -> str:
        if shots:
            return e(shots[index % len(shots)][0])
        return hero if use_hero else "/static/img/ssotd-elwynn.jpg"

    if news:
        title, date, body = news[0]
        slide = f"""<a class="slideshow" href="/wow/news/0">
  <img src="{hero}" alt="">
  <span class="slide-cap"><span class="kicker">Patch {e(exp.last_patch)}</span><h3>{e(title)}</h3></span>
</a>"""
    else:
        slide = f'<div class="slideshow"><img src="{hero}" alt=""></div>'
    featured = []
    for i, (title, date, _body) in enumerate(news[1:5], start=1):
        pic = _pic(i, i % 2 == 1)
        featured.append(
            f"""<a class="featured" href="/wow/news/{i}">
  <img src="{pic}" alt="">
  <span>{e(title)}</span>
</a>"""
        )
    featured_html = f'<div class="featured-news">{"".join(featured)}</div>' if featured else ""
    articles = []
    for i, (title, date, body) in enumerate(news):
        pic = _pic(i, i % 2 == 0)
        articles.append(
            f"""<article class="news-article">
  <div class="news-article-inner">
    <div class="article-left"><a href="/wow/news/{i}"><img src="{pic}" alt=""></a></div>
    <div class="article-right">
      <h3><a href="/wow/news/{i}">{e(title)}</a></h3>
      <p class="by-line">by Blizzard Entertainment <span>{e(date)}</span> · <a href="/forums/">Discuss</a></p>
      <p class="article-summary">{e(body)} <a class="more" href="/wow/news/{i}">More</a></p>
    </div>
  </div>
</article>"""
        )
    return f"""<div class="homepage">
  <div class="hp-left">
    {slide}
    {featured_html}
    {''.join(articles)}
  </div>
  <aside class="hp-side">
    <div class="side-box">
      <h3>Screenshot of the Day</h3>
      <a href="/wow/media/screenshots"><img src="{thumb}" alt="Azeroth landscape"></a>
    </div>
    <div class="side-box">
      <h3>Realm Status</h3>
      <p><a href="/wow/realmstatus/">{e(exp.realm_name)}</a> is {e(up)}.</p>
    </div>
    <div class="side-box">
      <h3>Forums</h3>
      <ul>
        <li><a href="/forums/">General Discussion</a></li>
        <li><a href="/forums/realm">Realm Forums</a></li>
        <li><a href="/forums/guilds">Guild Recruitment</a></li>
      </ul>
    </div>
    <div class="side-box">
      <h3>New Players</h3>
      <p>{e(exp.name)} · patch {e(exp.last_patch)}. <a href="/wow/info/basics/">Beginner's guide</a>.</p>
    </div>
  </aside>
</div>"""


def _home_mast(exp: Expansion, news: list[tuple[str, str, str]], up: str) -> str:
    hero = f"/static/img/{e(exp.hero)}"
    shots = assets.screenshots(exp.id)
    if news:
        title, date, body = news[0]
        headline, lede, when = title, body, date
        story = "/wow/news/0"
    else:
        headline, lede, when = exp.name, intro_blurb(exp), exp.last_patch_date
        story = "/wow/info/"
    cards = []
    for i, (card_title, card_date, card_body) in enumerate(news):
        if shots:
            url, caption = shots[i % len(shots)]
            img, alt = e(url), e(caption)
        else:
            img, alt = hero, ""
        cards.append(
            f"""<a class="news-card" href="/wow/news/{i}">
  <img src="{img}" alt="{alt}">
  <span>
    <time>{e(card_date)}</time>
    <strong>{e(card_title)}</strong>
    <em>{e(card_body)}</em>
  </span>
</a>"""
        )
    tiles = [
        ("/wow/info/", "Game Guide", "Races, classes, and how this era plays."),
        ("/forums/", "Forums", "The community boards for this realm."),
        ("/wow/realmstatus/", "Realm Status", f"{exp.realm_name} is {up}."),
    ]
    if exp.has_armory:
        tiles.append(("/armory/", "Armory", "Characters, guilds, and items on this realm."))
    else:
        tiles.append(("/wow/pvp/rankings", "PvP Rankings", "Honor ladder for this realm."))
    tile_html = "".join(
        f'<a class="feature-tile" href="{e(href)}"><strong>{e(label)}</strong><span>{e(text)}</span></a>'
        for href, label, text in tiles
    )
    return f"""<div class="home-landing">
  <section class="mast">
    <img class="mast-img" src="{hero}" alt="">
    <div class="mast-copy">
      <p class="eyebrow">{e(exp.name)} · {e(when)}</p>
      <h1>{e(headline)}</h1>
      <p class="lede">{e(lede)}</p>
      <div class="cta-row">
        <a class="cta buy" href="/shop">Buy Now</a>
        <a class="cta learn" href="{story}">Learn More</a>
      </div>
    </div>
  </section>
  <section class="latest">
    <h2>Latest News &amp; Updates</h2>
    <div class="news-cards">{''.join(cards)}</div>
  </section>
  <section class="feature-row">{tile_html}</section>
</div>"""


def article_page(title: str, date: str, body: str) -> str:
    return f"<p class='date'>{e(date)}</p><h2>{e(title)}</h2><p>{e(body)}</p>"


def _linked_card(kind: str, href: str, name: str, icon: str | None) -> str:
    img = f'<img class="item-icon" src="{e(icon)}" alt="">' if icon else ""
    return f'<a class="{kind}-card" href="{href}">{img}{e(name)}</a>'


def guide_hub(exp: Expansion, races: list[str], classes: list[str], features: list[str]) -> str:
    race_l = "".join(
        _linked_card("race", f"/wow/info/races/{e(r)}", RACE_INFO[r][0], assets.race_icon(exp.id, r))
        for r in races
        if r in RACE_INFO
    )
    class_l = "".join(
        _linked_card("class", f"/wow/info/classes/{e(c)}", CLASS_INFO[c][0], assets.class_icon(exp.id, c))
        for c in classes
        if c in CLASS_INFO
    )
    feat = "".join(f"<li>{e(f)}</li>" for f in features)
    return f"""
<p>{e(intro_blurb(exp))}</p>
<p><em>“Because knowing is half the battle.” — Mojo Stormstout, Jr.</em></p>
<div class="twocol">
  <div>
    <h2>Races</h2><div class="race-grid">{race_l}</div>
    <h2>Classes</h2><div class="class-grid">{class_l}</div>
  </div>
  <div>
    <h2>Features</h2><ul>{feat}</ul>
    <p><a class="red" href="/wow/info/basics/">New Player Guide</a></p>
    <p><a class="red" href="/wow/info/classes/">Talent Calculators</a></p>
    <p><a class="red" href="/wow/info/basics/map">World Map</a></p>
  </div>
</div>
"""


def race_page(slug: str, exp: Expansion | None = None) -> str:
    if exp is None:
        name, faction, city, blurb = RACE_INFO[slug]
    else:
        name, faction, city, blurb = race_facts(exp, slug)
    icon = assets.race_icon(exp.id, slug) if exp is not None else None
    img = f'<img class="item-icon" src="{e(icon)}" alt="">' if icon else ""
    return f"""
{img}
<h2>{e(name)}</h2>
<p class="meta">{e(faction)} · Capital: {e(city)}</p>
<p>{e(blurb)}</p>
"""


def class_page(slug: str, exp: Expansion) -> str:
    name, armor, specs, blurb = class_facts(exp, slug)
    icon = assets.class_icon(exp.id, slug)
    img = f'<img class="item-icon" src="{e(icon)}" alt="">' if icon else ""
    return f"""
{img}
<h2>{e(name)}</h2>
<p class="meta">{e(armor)} · {e(specs)}</p>
<p>{e(blurb)}</p>
<p><a class="red" href="/wow/info/classes/{e(slug)}/talents.html">Talent Calculator</a></p>
"""


def talent_page(exp: Expansion, class_id: str, trees: Iterable, ranks: list[int], points: int, build: str) -> str:
    idx = 0
    cols = []
    for tree_i, tree in enumerate(trees):
        base = idx
        by_name = {}
        for offset, tal in enumerate(tree.talents):
            by_name.setdefault(tal.name, base + offset)
        cells = []
        for tal in tree.talents:
            r = ranks[idx] if idx < len(ranks) else 0
            r = min(r, tal.max_rank)
            req = by_name[tal.requires] if tal.requires and tal.requires in by_name else ""
            icon = assets.talent_icon(exp, tal.name)
            img = f'<img class="ticon" src="{e(icon)}" alt="">' if icon else ""
            cells.append(
                f'<button type="button" class="talent" data-i="{idx}" data-max="{tal.max_rank}" '
                f'data-tree="{tree_i}" data-row="{tal.row}" data-requires="{req}" '
                f'title="{e(tal.name)} ({r}/{tal.max_rank}) {e(tal.desc)}" '
                f'style="grid-column:{tal.col+1};grid-row:{tal.row+1}">'
                f'{img}<span class="tname">{e(tal.name)}</span>'
                f'<span class="trank" data-rank>{r}/{tal.max_rank}</span></button>'
            )
            idx += 1
        cols.append(
            f'<div class="tree"><h3>{e(tree.name)}</h3>'
            f'<div class="talent-grid">{"".join(cells)}</div></div>'
        )
    js = f"""<script>
document.addEventListener('DOMContentLoaded', function() {{
  if (window.initTalents) initTalents({points});
}});
</script>"""
    return (
        f'<p>Available points: <strong id="pts">{points}</strong> · Build '
        f'<code id="build">{e(build)}</code> · click to spend, right-click to remove.</p>'
        f'<div class="trees">{"".join(cols)}</div>'
        + js
    )


def map_page() -> str:
    zones = [
        (12, 18, "Dun Morogh"),
        (38, 22, "Elwynn Forest"),
        (55, 30, "Westfall"),
        (70, 18, "Loch Modan"),
        (22, 48, "Durotar"),
        (40, 52, "The Barrens"),
        (18, 62, "Mulgore"),
        (58, 58, "Stranglethorn Vale"),
        (72, 42, "Eastern Plaguelands"),
        (8, 28, "Teldrassil"),
    ]
    marks = "".join(
        f'<a class="zone" style="left:{x}%;top:{y}%" href="#" title="{e(n)}">{e(n)}</a>'
        for x, y, n in zones
    )
    return f"""
<p>Flash world map stand-in. Hover a name; the old plugin is not required.</p>
<div class="worldmap">{marks}</div>
"""


def realm_page(exp: Expansion, realm: dict, dev: bool = False) -> str:
    flag = "Up" if realm.get("up") else "Down"
    note = ""
    if dev and realm.get("error"):
        note = f"<p class='warn'>{e(realm.get('error'))}</p>"
    unread = bool(realm.get("error")) and not realm.get("type") and not realm.get("population")
    if unread:
        note += "<p>The realm database is not reachable. Status is the world port only.</p>"
    type_cell = realm.get("type") or ("—" if unread else "PvE")
    pop_cell = realm.get("population") if realm.get("population") not in (None, "") else ("—" if unread else "0")
    return f"""
<p>Realm status for {e(exp.name)}.</p>
{note}
<table class="grid">
<tr><th>Realm</th><th>Type</th><th>Population</th><th>Status</th></tr>
<tr>
  <td>{e(realm.get('name'))}</td>
  <td>{e(type_cell)}</td>
  <td>{e(pop_cell)}</td>
  <td class="{('up' if realm.get('up') else 'down')}">{flag}</td>
</tr>
</table>
<p class="fine">Messages related to realm status belong on the
<a href="/forums/realm">Realm Forum</a>.</p>
"""


def account_form(action: str, button: str, extra: str = "", identity: str = "account") -> str:
    if identity == "email":
        who = '<label>Email <input name="email" type="email" required></label>'
    else:
        who = '<label>Account Name <input name="username" required maxlength="16" autocomplete="username"></label>'
    return f"""
<form class="acct" method="post" action="{e(action)}">
  {who}
  <label>Password <input type="password" name="password" required></label>
  {extra}
  <button type="submit">{e(button)}</button>
</form>
"""

