"""Legion community shell: 2016 masthead, 2017 profile, Battle.net shop and account."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from wowweb import accounts, armory, assets, forums, talents
from wowweb.account_ui import render_account
from wowweb.content import CLASS_INFO, class_facts
from wowweb.content.races import classes_for
from wowweb.content.news import news_for
from wowweb.content.sections import story_for

from .common import dev_note, document, esc, styles

_HERO = "/static/img/hero-legion.jpg"
_CLASS_ROW = (
    "warrior",
    "paladin",
    "hunter",
    "rogue",
    "priest",
    "deathknight",
    "shaman",
    "mage",
    "warlock",
    "monk",
    "druid",
    "demonhunter",
)
_GAME = (
    ("/wow/info/", "Game Guide"),
    ("/wow/info/classes", "Classes"),
    ("/wow/info/races", "Races"),
    ("/wow/info/professions", "Professions"),
    ("/wow/info/classes/priest/talents.html", "Talent Calculator"),
    ("/wow/realmstatus", "Realm Status"),
)
_STORY_MENU = (
    ("/story", "The Burning Legion"),
    ("/story#illidan", "Illidan Stormrage"),
)
_SEARCH = (
    (
        "Resources",
        (
            ("/wow/info/basics", "New Players: Getting Started"),
            ("/wow/info/", "Returning Players: Welcome Back"),
            ("/wow/info/patches", "Patch Notes"),
            ("/wow/info/classes/priest/talents.html", "Talent Calculator"),
            ("/wow/realmstatus", "Realm Status"),
        ),
    ),
    (
        "News",
        (
            ("/wow/news", "Most Recent"),
            ("/wow/news", "Trending"),
            ("/wow/news", "Raid"),
            ("/story", "Story"),
            ("/forums/", "Community"),
        ),
    ),
    (
        "Gameplay",
        (
            ("/wow/info/races", "Races"),
            ("/wow/info/classes", "Classes"),
            ("/wow/info/", "Dungeons, Raids, Scenarios"),
            ("/wow/info/", "Events"),
        ),
    ),
    (
        "Forums",
        (
            ("/support/", "Support"),
            ("/forums/", "Community"),
            ("/wow/news", "Developer Posts"),
            ("/forums/", "Gaming, Hardware, & Entertainment"),
            ("/forums/", "Website & Mobile Feedback"),
        ),
    ),
)
_MONTHS = (
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_TIERS = (15, 30, 45, 60, 75, 90, 100)
_TANK = {"protection", "guardian", "brewmaster", "blood", "vengeance"}
_HEAL = {"holy", "discipline", "restoration", "mistweaver", "preservation"}
_SPEC_LINE = {
    "discipline": "Shields allies and mends with the Light.",
    "holy": "Heals from a distance and keeps a group standing.",
    "shadow": "Attacks with Shadow magic over time.",
    "protection": "Holds the line and keeps enemies occupied.",
    "arms": "A weapon specialist who fights in long exchanges.",
    "fury": "Two weapons and a rush of rage.",
    "retribution": "Strikes in the name of the Light.",
    "beast mastery": "Fights beside an animal companion.",
    "marksmanship": "A careful shot from far away.",
    "survival": "Traps and a hunt up close.",
    "assassination": "Poisons and a precise finish.",
    "outlaw": "A blade, a pistol, and a quick getaway.",
    "combat": "A direct fighter who stays in the scrape.",
    "subtlety": "Strikes from stealth.",
    "elemental": "Lightning and lava at range.",
    "enhancement": "A storm on each weapon.",
    "restoration": "Mends allies and keeps them in the fight.",
    "balance": "Stars and moons at long range.",
    "feral": "Claws, stealth, and a cat's finish.",
    "guardian": "A bear who refuses to fall.",
    "arcane": "Raw mana, shaped and spent.",
    "fire": "Burns a target down.",
    "frost": "Ice, slows, and a hard freeze.",
    "affliction": "Curses that keep working.",
    "demonology": "Fights beside a summoned demon.",
    "destruction": "A heavy hit of fel fire.",
    "blood": "A death knight who stands on stolen life.",
    "unholy": "Disease and a ghoul at their side.",
    "brewmaster": "Staggers a blow and keeps moving.",
    "mistweaver": "Heals with mist and a calm breath.",
    "windwalker": "A fast string of strikes.",
    "havoc": "Fel blades and a rush forward.",
    "vengeance": "A demon hunter who holds the line.",
}
_BOARD_DESC = {
    "bugs": "Report a bug in the game.",
    "general": "Talk about World of Warcraft.",
    "guilds": "Find a guild, or post that yours is recruiting.",
    "classhalls": "Order halls, campaigns, and missions.",
    "dungeons": "Dungeons, raids, and scenarios.",
    "professions": "Gathering, crafting, and work orders.",
    "ui": "Interfaces and macros.",
    "pvp": "Arenas, battlegrounds, and world PvP.",
    "realm": "The realm forum for this server.",
}
_ORDER_HALL = "Legion Order Hall Campaigns and Missions"
_LEFT = ("Head", "Neck", "Shoulders", "Back", "Chest", "Tabard", "Wrists", "Shirt")
_RIGHT = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEPS = ("Main Hand", "Off Hand")
_ACH_CATS = (
    "Global",
    "Eastern Kingdoms",
    "Kalimdor",
    "Outland",
    "Northrend",
    "Cataclysm",
    "Pandaria",
    "Draenor",
    "Legion",
)
_TALENT_JS = """<script>
(function () {
  var root = document.querySelector("[data-lg-talents]");
  if (!root) return;
  var picks = Array.prototype.slice.call(root.querySelectorAll(".lg-pick"));
  var buildEl = document.getElementById("build");
  var ptsEl = document.getElementById("pts");
  var shareEl = document.getElementById("lg-share-url");
  function rankOf(btn) { return Number(btn.getAttribute("data-rank") || "0"); }
  function setRank(btn, rank) {
    btn.setAttribute("data-rank", rank ? "1" : "0");
    var label = btn.querySelector("[data-rank-label]");
    if (label) label.textContent = rank ? "1/1" : "0/1";
    btn.classList.toggle("is-on", !!rank);
  }
  function paint() {
    var ordered = picks.slice().sort(function (a, b) {
      return Number(a.getAttribute("data-i")) - Number(b.getAttribute("data-i"));
    });
    var digits = ordered.map(function (btn) { return rankOf(btn) ? "1" : "0"; }).join("");
    var n = 0;
    picks.forEach(function (btn) { if (rankOf(btn)) n += 1; });
    if (buildEl) buildEl.textContent = digits || "0";
    if (ptsEl) ptsEl.textContent = String(n);
    if (shareEl) {
      var specBtn = root.querySelector(".lg-spec.is-on");
      var spec = specBtn ? specBtn.getAttribute("data-tree") : "0";
      shareEl.value = location.pathname + "?build=" + digits + "&spec=" + spec;
    }
  }
  function showSpec(tree) {
    root.querySelectorAll(".lg-spec").forEach(function (btn) {
      btn.classList.toggle("is-on", btn.getAttribute("data-tree") === tree);
    });
    root.querySelectorAll(".lg-tree").forEach(function (panel) {
      panel.hidden = panel.getAttribute("data-tree") !== tree;
    });
    paint();
  }
  picks.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var tree = btn.getAttribute("data-tree");
      var row = btn.getAttribute("data-row");
      var next = rankOf(btn) ? 0 : 1;
      picks.forEach(function (other) {
        if (other.getAttribute("data-tree") !== tree || other.getAttribute("data-row") !== row) return;
        setRank(other, other === btn ? next : 0);
      });
      paint();
    });
    btn.addEventListener("contextmenu", function (ev) {
      ev.preventDefault();
      setRank(btn, 0);
      paint();
    });
  });
  root.querySelectorAll(".lg-spec").forEach(function (btn) {
    btn.addEventListener("click", function () { showSpec(btn.getAttribute("data-tree")); });
  });
  var reset = document.getElementById("lg-reset");
  if (reset) reset.addEventListener("click", function () {
    picks.forEach(function (btn) { setRank(btn, 0); });
    paint();
  });
  var share = document.getElementById("lg-share");
  if (share) share.addEventListener("click", function () {
    paint();
    if (shareEl && shareEl.select) { shareEl.focus(); shareEl.select(); }
  });
  paint();
})();
</script>"""


def _qs_one(qs, key: str) -> str:
    if not qs:
        return ""
    raw = qs.get(key)
    if isinstance(raw, list):
        return raw[0] if raw else ""
    return "" if raw is None else str(raw)


def _class_name(slug: str) -> str:
    info = CLASS_INFO.get(slug)
    if info:
        return info[0]
    return slug.replace("-", " ").title()


def _class_order(exp) -> list[str]:
    have = set(classes_for(exp))
    return [slug for slug in _CLASS_ROW if slug in have]


def _icon(src: str | None, alt: str = "") -> str:
    if not src:
        return ""
    return f'<img src="{esc(src)}" alt="{esc(alt)}">'


def _roles(specs: str) -> str:
    names = [part.strip() for part in specs.split(",") if part.strip()]
    low = [name.lower() for name in names]
    found = []
    if any(name in _TANK for name in low):
        found.append("Tank")
    if any(name in _HEAL for name in low):
        found.append("Healer")
    if any(name not in _TANK and name not in _HEAL for name in low):
        found.append("Damage")
    return ", ".join(found)


def _card_date(iso: str) -> str:
    parts = (iso or "").split("-")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return iso or ""
    year, month, day = (int(part) for part in parts)
    if not 1 <= month <= 12:
        return iso
    if 10 <= day % 100 <= 20:
        suffix = "TH"
    else:
        suffix = {1: "ST", 2: "ND", 3: "RD"}.get(day % 10, "TH")
    return f"{_MONTHS[month].upper()} {day}{suffix}, {year}"


def _shots(exp) -> list[str]:
    found = assets.screenshots(exp.id, limit=8)
    return [url for url, _caption in found] or [_HERO]


def _drop(href: str, label: str, rows) -> str:
    menu = "".join(f'<a href="{esc(link)}">{esc(text)}</a>' for link, text in rows)
    return (
        f'<div class="lg-drop"><a href="{esc(href)}">{esc(label)}</a>'
        f'<div class="lg-menu">{menu}</div></div>'
    )


def _search_panel() -> str:
    cols = []
    for heading, rows in _SEARCH:
        links = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in rows)
        cols.append(f'<div class="lg-q-col"><h2>{esc(heading)}</h2>{links}</div>')
    return f"""<div class="lg-search">
  <button class="menu-btn lg-search-btn" type="button" aria-expanded="false" aria-label="Search">
    <span class="lg-glass" aria-hidden="true"></span><span class="lg-x" aria-hidden="true">×</span>
  </button>
  <div class="lg-search-panel">
    <form class="lg-q" action="/wow/search" method="get">
      <input type="text" name="q" placeholder="Search for characters, pages, and more..." aria-label="Search for characters, pages, and more">
    </form>
    <div class="lg-q-cols">{''.join(cols)}</div>
  </div>
</div>"""


def _tools(user: str | None) -> str:
    if user:
        who = f'<a class="lg-login" href="/account/">{esc(user)}</a>'
        gate = '<a class="lg-try" href="/account/logout">Log Out</a>'
    else:
        who = '<a class="lg-login" href="/account/login">Log In</a>'
        gate = '<a class="lg-try" href="/account/create">Try Free</a>'
    return f"{_search_panel()}{who}{gate}"


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = exp, crumb, online, login_error
    nav = (
        _drop("/wow/info/", "Game", _GAME)
        + _drop("/story", "Story", _STORY_MENU)
        + '<a href="/wow/news">News</a>'
        + '<a href="/forums/">Forums</a>'
        + '<a href="/shop">Shop</a>'
    )
    inner = f"""<header class="lg-head">
  <div class="lg-blizz">
    <div class="lg-wrap">
      <a class="lg-mark" href="/wow/" aria-label="Blizzard"></a>
      <nav class="lg-blizz-nav" aria-label="Blizzard">
        <a href="/wow/">Games</a>
        <a href="/shop">Shop</a>
      </nav>
      <nav class="lg-blizz-right" aria-label="Account">
        <a href="/support/">Support</a>
        <a href="/account/">Your Account</a>
      </nav>
    </div>
  </div>
  <div class="lg-sub">
    <div class="lg-wrap">
      <a class="lg-logo" href="/wow/"><span>World of</span><strong>Warcraft</strong></a>
      <nav class="lg-nav" aria-label="World of Warcraft">{nav}</nav>
      <div class="lg-tools">{_tools(user)}</div>
    </div>
  </div>
</header>
<main class="lg-stage"><div class="lg-fit">{body}</div></main>
<footer class="lg-foot">
  <div class="lg-wrap">
    <nav aria-label="Footer">
      <a href="/esports">Esports</a>
      <a href="/support/">Support</a>
      <a href="/wow/realmstatus">Realm Status</a>
    </nav>
    <p>© 2016 Blizzard Entertainment</p>
  </div>
</footer>"""
    return document(
        f"{title} — World of Warcraft",
        styles("legion"),
        "era-legion legion",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    _ = realm, user
    pics = _shots(exp)
    cards = []
    for index, item in enumerate((news or [])[:4]):
        title, date, _blurb = item
        img = pics[index % len(pics)]
        cards.append(
            f'<a class="lg-card" href="/wow/news/{index}">'
            f'<img src="{esc(img)}" alt="">'
            f"<span><time>{esc(_card_date(date))}</time><strong>{esc(title)}</strong></span></a>"
        )
    card_html = "".join(cards) or '<p class="lg-empty">No stories posted.</p>'
    return f"""<div class="lg-home">
  <section class="lg-hero">
    <div class="lg-wrap lg-hero-copy">
      <h1>LEGION ARRIVES 08.30.16</h1>
      <p>Recover ancient artifacts of legend and take the fight to the Burning Legion. Azeroth's future depends on you.</p>
      <p class="lg-ctas">
        <a class="lg-btn" href="/story">Learn More</a>
        <a class="lg-btn lg-btn-solid" href="/shop">Pre-Purchase</a>
      </p>
    </div>
  </section>
  <section class="lg-latest">
    <div class="lg-wrap">
      <header class="lg-latest-head">
        <h2>Latest News &amp; Updates</h2>
        <a href="/wow/news">View all news</a>
      </header>
      <div class="lg-cards">{card_html}</div>
    </div>
  </section>
</div>"""


def _classes(exp) -> str:
    cards = []
    for slug in _class_order(exp):
        name, _armor, specs, blurb = class_facts(exp, slug)
        icon = _icon(assets.class_icon(exp.id, slug), name)
        cards.append(
            f'<a class="lg-class" href="/wow/info/classes/{esc(slug)}">'
            f'<span class="lg-class-art">{icon}</span>'
            f'<span class="lg-class-copy"><strong>{esc(name)}</strong>'
            f'<em>{esc(_roles(specs))}</em>'
            f'<span class="lg-specs">{esc(specs)}</span>'
            f"<span>{esc(blurb)}</span></span></a>"
        )
    return f"""<article class="lg-classes">
  <h1>Classes</h1>
  <p class="lg-lede">Knights, stalkers, and spellcasters. Each class in this era has its own weapons, role, and way through the Broken Isles.</p>
  <div class="lg-class-grid">{''.join(cards)}</div>
</article>"""


def _spec_index(trees, raw: str) -> int:
    text = (raw or "").strip().lower()
    if text.isdigit():
        number = int(text)
        if 0 <= number < len(trees):
            return number
    for index, tree in enumerate(trees):
        if tree.name.lower() == text:
            return index
    return 0


def _talents(exp, slug: str, trees, build: str, spec_raw: str) -> str:
    ranks = talents.parse_build(trees, build)
    chosen = _spec_index(trees, spec_raw)
    flat = [1 if (ranks[i] if i < len(ranks) else 0) else 0 for i in range(sum(len(tree.talents) for tree in trees))]
    specs = []
    panels = []
    cursor = 0
    for tree_i, tree in enumerate(trees):
        on = " is-on" if tree_i == chosen else ""
        line = _SPEC_LINE.get(tree.name.lower(), f"The {tree.name} specialization.")
        specs.append(
            f'<button type="button" class="lg-spec{on}" data-tree="{tree_i}">'
            f"<strong>{esc(tree.name)}</strong><span>{esc(line)}</span></button>"
        )
        by_row: dict[int, list[str]] = {}
        for tal in tree.talents:
            rank = flat[cursor] if cursor < len(flat) else 0
            icon = _icon(assets.talent_icon(exp, tal.name), tal.name)
            mark = " is-on" if rank else ""
            button = (
                f'<button type="button" class="lg-pick{mark}" data-i="{cursor}" data-tree="{tree_i}" '
                f'data-row="{tal.row}" data-rank="{rank}" data-requires="">'
                f"{icon}<span class=\"lg-pick-name\">{esc(tal.name)}</span>"
                f'<span data-rank-label>{rank}/1</span></button>'
            )
            by_row.setdefault(tal.row, []).append(button)
            cursor += 1
        rows = []
        for row in sorted(by_row):
            level = _TIERS[row] if row < len(_TIERS) else _TIERS[-1]
            rows.append(
                f'<div class="lg-tier"><span class="lg-level">{level}</span>'
                f'<div class="lg-choices">{"".join(by_row[row])}</div></div>'
            )
        hidden = "" if tree_i == chosen else " hidden"
        panels.append(
            f'<div class="lg-tree" data-tree="{tree_i}"{hidden}>{"".join(rows)}</div>'
        )
    row = []
    for class_slug in _class_order(exp):
        current = " is-current" if class_slug == slug else ""
        icon = _icon(assets.class_icon(exp.id, class_slug), _class_name(class_slug))
        row.append(
            f'<a class="lg-classlink{current}" href="/wow/info/classes/{esc(class_slug)}/talents.html">'
            f"{icon}<span>{esc(_class_name(class_slug))}</span></a>"
        )
    return f"""<article class="lg-talents" data-lg-talents>
  <header class="lg-tal-head">
    <h1>Talent Calculator</h1>
    <p>{esc(_class_name(slug))}</p>
  </header>
  <nav class="lg-classrow" aria-label="Classes">{''.join(row)}</nav>
  <h2>Choose a Specialization</h2>
  <p class="lg-note">Available at level 10</p>
  <p class="lg-tal-actions">
    <button type="button" id="lg-share">Share</button>
    <button type="button" id="lg-reset">Reset</button>
  </p>
  <input id="lg-share-url" readonly value="" aria-label="Share link">
  <div class="lg-specs-row">{''.join(specs)}</div>
  <h2>Choose Talents</h2>
  <p class="lg-note">Select one talent per tier. Some choices depend on the specialization. Selected <strong id="pts">0</strong> · <code id="build">{esc(talents.encode_build(flat))}</code></p>
  {''.join(panels)}
</article>
{_TALENT_JS}"""


def _story(exp) -> str:
    blocks = []
    for block in story_for(exp):
        paras = "".join(f"<p>{esc(line)}</p>" for line in block.paragraphs)
        blocks.append(f"<section><h2>{esc(block.heading)}</h2>{paras}</section>")
    return f"""<article class="lg-story" id="illidan">
  <header class="lg-story-hero">
    <h1>Illidan Stormrage</h1>
    <p>The Betrayer</p>
  </header>
  <div class="lg-story-grid">
    <div class="lg-story-copy">
      <p class="lg-lede">Illidan Stormrage was called the Betrayer. He took fel power, broke with his own people, and spent that power on one war: the Burning Legion.</p>
      <p>The night elves locked him away. He later raised the Illidari, demon hunters who fight the Legion with its own weapons. His body was taken to the Vault of the Wardens. The hunt he started did not end there.</p>
    </div>
    <aside class="lg-illidari">
      <p class="lg-card-name">Illidari</p>
      <p>There is no price he would not pay to see the Legion ended.</p>
      <h2>Character Information</h2>
      <ul>
        <li><strong>Male</strong><span>Gender</span></li>
        <li><strong>Night Elf</strong><span>Race</span></li>
        <li><strong>Unknown</strong><span>Location</span></li>
      </ul>
    </aside>
  </div>
  <div class="lg-story-more">{''.join(blocks)}</div>
</article>"""


def _news_index(exp) -> str:
    items = news_for(exp)
    pics = _shots(exp)
    if not items:
        return '<article class="lg-news"><h1>News</h1><p>No stories posted.</p></article>'
    title, date, body = items[0]
    feature = (
        f'<a class="lg-feature" href="/wow/news/0">'
        f'<img src="{esc(pics[0])}" alt="">'
        f"<span><time>{esc(_card_date(date))}</time><strong>{esc(title)}</strong>"
        f"{('<em>' + esc(body) + '</em>') if body else ''}</span></a>"
    )
    rail = []
    for index, (card_title, card_date, _card_body) in enumerate(items[1:3], start=1):
        rail.append(
            f'<a class="lg-rail" href="/wow/news/{index}">'
            f'<img src="{esc(pics[index % len(pics)])}" alt="">'
            f"<span><time>{esc(_card_date(card_date))}</time><strong>{esc(card_title)}</strong></span></a>"
        )
    rest = []
    for index, (card_title, card_date, _card_body) in enumerate(items[3:], start=3):
        rest.append(
            f'<li><time>{esc(_card_date(card_date))}</time> '
            f'<a href="/wow/news/{index}">{esc(card_title)}</a></li>'
        )
    more = f'<ul class="lg-more">{"".join(rest)}</ul>' if rest else ""
    return f"""<article class="lg-news">
  <div class="lg-news-top">{feature}<div class="lg-rail-col">{''.join(rail)}</div></div>
  {more}
</article>"""


def _article(exp, index: int) -> tuple[str, str] | None:
    items = news_for(exp)
    if index < 0 or index >= len(items):
        return None
    title, date, body = items[index]
    copy = f"<p>{esc(body)}</p>" if body else ""
    html = (
        '<article class="lg-article">'
        f"<p><a href=\"/wow/news\">News</a></p>"
        f"<time>{esc(_card_date(date))}</time>"
        f"<h1>{esc(title)}</h1>"
        f"{copy}"
        "</article>"
    )
    return title, html


def _visible_board(exp, slug: str, fallback: str) -> str:
    if slug == "classhalls":
        return _ORDER_HALL
    return forums.board_title(exp, slug) or fallback


def _board_card(exp, slug: str, title: str) -> str:
    icon = ""
    if slug in _CLASS_ROW:
        icon = _icon(assets.class_icon(exp.id, slug), title)
    if not icon:
        icon = '<span class="lg-ficon" aria-hidden="true"></span>'
    desc = _BOARD_DESC.get(slug, "Class discussion." if slug in _CLASS_ROW else f"Discuss {title}.")
    return (
        f'<a class="lg-fcard" href="/forums/{esc(slug)}">{icon}'
        f"<span><strong>{esc(_visible_board(exp, slug, title))}</strong><em>{esc(desc)}</em></span></a>"
    )


def _forums(exp) -> str:
    boards = forums.boards_for(exp)
    by_slug = {slug: title for slug, title in boards}
    groups = (
        ("Support", ("bugs",), (("/support/", "Customer Support", "Help with the game and this account."),)),
        ("Community", ("general", "guilds"), ()),
        ("Legion", ("classhalls",), ()),
        ("Gameplay and Guides", ("dungeons", "professions", "ui"), ()),
        ("PvP", ("pvp",), ()),
        ("Classes", tuple(slug for slug in _CLASS_ROW if slug in by_slug), ()),
        ("Realms", ("realm",), ()),
    )
    used = set()
    sections = []
    for heading, slugs, extras in groups:
        cards = []
        for href, label, desc in extras:
            cards.append(
                '<a class="lg-fcard" href="' + esc(href) + '">'
                '<span class="lg-ficon" aria-hidden="true"></span>'
                f"<span><strong>{esc(label)}</strong><em>{esc(desc)}</em></span></a>"
            )
        for slug in slugs:
            if slug not in by_slug:
                continue
            used.add(slug)
            cards.append(_board_card(exp, slug, by_slug[slug]))
        if cards:
            sections.append(f'<section class="lg-fsec"><h2>{esc(heading)}</h2><div class="lg-fcards">{"".join(cards)}</div></section>')
    other = [_board_card(exp, slug, title) for slug, title in boards if slug not in used]
    if other:
        sections.append(f'<section class="lg-fsec"><h2>Other</h2><div class="lg-fcards">{"".join(other)}</div></section>')
    return f"""<article class="lg-forums">
  <header class="lg-fbanner">
    <h1>Welcome to the official World of Warcraft forums</h1>
  </header>
  <form class="lg-forum-search" action="/wow/search" method="get">
    <input type="text" name="q" placeholder="Search all forums" aria-label="Search all forums">
  </form>
  {''.join(sections)}
</article>"""


def _threads(ctx, slug: str) -> list:
    data_dir = ctx.get("data_dir")
    if not data_dir:
        return []
    conn = forums.connect(Path(data_dir))
    try:
        forums.seed_if_empty(conn, ctx["exp"])
        return forums.list_threads(conn, ctx["exp"], slug)
    finally:
        conn.close()


def _stamp(value) -> str:
    try:
        return datetime.fromtimestamp(int(value), timezone.utc).strftime("%b %d")
    except (TypeError, ValueError, OSError):
        return ""


def _board(exp, slug: str, title: str, threads: list, user, qs) -> str:
    _ = exp
    page_size = 20
    pages = max(1, (len(threads) + page_size - 1) // page_size)
    try:
        page = int(_qs_one(qs, "page") or "1")
    except ValueError:
        page = 1
    page = min(max(page, 1), pages)
    start = (page - 1) * page_size
    rows = []
    for thread in threads[start : start + page_size]:
        when = _stamp(thread.get("last") or thread.get("created"))
        rows.append(
            "<li>"
            f'<a href="/forums/{esc(slug)}/{esc(thread["id"])}">{esc(thread["title"])}</a>'
            f'<span class="lg-replies">{esc(thread.get("replies") or 0)}</span>'
            f'<span class="lg-author">{esc(thread.get("author") or "")}</span>'
            f"<time>{esc(when)}</time></li>"
        )
    listing = "".join(rows) or '<li class="lg-empty">No threads yet.</li>'
    if pages > 1:
        links = []
        for number in range(1, pages + 1):
            mark = " is-on" if number == page else ""
            links.append(f'<a class="{mark}" href="?page={number}">{number}</a>')
        pager = f'<nav class="lg-pager">{"".join(links)}</nav>'
    else:
        pager = ""
    if user:
        post = f"""<form id="new-topic" class="acct" method="post" action="/forums/{esc(slug)}/new">
  <h2>New Topic</h2>
  <label>Title <input name="title" required maxlength="120"></label>
  <label>Body <textarea name="body" required rows="6"></textarea></label>
  <button type="submit">Post</button>
</form>"""
        action = '<a class="lg-new" href="#new-topic">New Topic</a>'
    else:
        post = ""
        action = '<a class="lg-new" href="/account/login">New Topic</a>'
    return f"""<article class="lg-board">
  <p class="lg-crumb"><a href="/wow/">World of Warcraft</a> <span>›</span> <a href="/forums/">Forums</a> <span>›</span> {esc(title)}</p>
  <header class="lg-board-head">
    <h1>{esc(title)}</h1>
    <form action="/wow/search" method="get"><input type="text" name="q" placeholder="Search" aria-label="Search"></form>
    {action}
  </header>
  <ul class="lg-topics">{listing}</ul>
  {pager}
  {post}
</article>"""


def _equipped(char) -> dict:
    found = {}
    for item in char.get("equipment") or []:
        slot = str(item.get("slot") or "")
        if slot:
            found[slot] = item
    return found


def _slot_html(exp, slot: str, item) -> str:
    if not item or not item.get("item_id"):
        return f'<li class="lg-slot lg-slot-empty"><span class="lg-socket"></span><span>{esc(slot)}</span></li>'
    icon = _icon(assets.display_icon(exp, item.get("display_id")), item.get("name") or slot)
    name = item.get("name") or f"Item {item.get('item_id')}"
    href = f"/armory/item/{int(item['item_id'])}"
    return (
        f'<li class="lg-slot">{icon}<a href="{esc(href)}">{esc(name)}</a>'
        f'<span class="lg-slot-name">{esc(slot)}</span></li>'
    )


def _profile(exp, char, tab: str, view: str) -> str:
    tabs = (
        ("character", "Character"),
        ("achievements", "Achievements"),
        ("collections", "Collections"),
        ("raids", "Raid Progression"),
        ("pvp", "Player vs Player"),
        ("reputation", "Reputation"),
    )
    nav = "".join(
        f'<a class="{"is-on" if tab == key else ""}" href="?tab={key}">{label}</a>'
        for key, label in tabs
    )
    race = str(char.get("race") or "")
    class_name = str(char.get("class") or "")
    race_icon = _icon(assets.race_icon(exp.id, race.lower().replace(" ", "").replace("'", "")), race)
    class_icon = _icon(assets.class_icon(exp.id, class_name.lower().replace(" ", "")), class_name)
    guild = char.get("guild") or {}
    gname = guild.get("name") if isinstance(guild, dict) else ""
    if gname:
        guild_html = f'<a href="/armory/guild/{quote(str(gname), safe="")}">{esc(gname)}</a>'
    else:
        guild_html = ""
    points = char.get("achievements") or 0
    header = f"""<header class="lg-ident">
  <span class="lg-crest">{class_icon or race_icon}</span>
  <div>
    <h1>{esc(char.get("name"))}</h1>
    <p class="lg-points"><span>{esc(points)}</span> achievement points</p>
    <p>{esc(char.get("level"))} {esc(race)} {esc(class_name)} {guild_html} {esc(char.get("realm") or "")}</p>
  </div>
</header>
<nav class="lg-tabs" aria-label="Profile">{nav}</nav>"""
    gear = _equipped(char)
    if tab == "achievements":
        cats = "".join(f"<li>{esc(name)}</li>" for name in _ACH_CATS)
        body = (
            '<div class="lg-ach">'
            "<h2>Achievements</h2>"
            f"<ul class=\"lg-cats\">{cats}</ul>"
            f"<p>{esc(points)} achievement points are stored for this character.</p>"
            '<p class="lg-empty">Individual achievement rows are not in this character export.</p>'
            "</div>"
        )
    elif tab == "collections":
        pets = "is-on" if view != "mounts" else ""
        mounts = "is-on" if view == "mounts" else ""
        which = "mounts" if view == "mounts" else "battle pets"
        body = (
            '<div class="lg-collect">'
            f'<p class="lg-subtabs"><a class="{pets}" href="?tab=collections&amp;view=pets">Pet Journal</a>'
            f'<a class="{mounts}" href="?tab=collections&amp;view=mounts">Mounts</a></p>'
            f'<h2>{"Mounts" if view == "mounts" else "Battle Pet Slots"}</h2>'
            f'<p class="lg-empty">No {which} are stored for this character.</p>'
            "</div>"
        )
    elif tab == "pvp":
        kills = char.get("honorable_kills")
        extra = f"<p>Honorable kills: {esc(kills)}</p>" if kills not in (None, "") else ""
        body = f'<div class="lg-plain"><h2>Player vs Player</h2>{extra}<p class="lg-empty">No arena teams are stored for this character.</p></div>'
    elif tab == "raids":
        body = '<div class="lg-plain"><h2>Raid Progression</h2><p class="lg-empty">Raid progression is not in this character export.</p></div>'
    elif tab == "reputation":
        body = '<div class="lg-plain"><h2>Reputation</h2><p class="lg-empty">Reputation is not in this character export.</p></div>'
    else:
        known = set(_LEFT + _RIGHT + _WEPS)
        other = [item for slot, item in gear.items() if slot not in known and item.get("item_id")]
        extra = "".join(
            _slot_html(exp, str(item.get("slot") or "Slot"), item) for item in other
        )
        body = (
            '<div class="lg-doll">'
            f'<ul>{"".join(_slot_html(exp, slot, gear.get(slot)) for slot in _LEFT)}</ul>'
            f'<ul>{"".join(_slot_html(exp, slot, gear.get(slot)) for slot in _RIGHT)}</ul>'
            "</div>"
            f'<ul class="lg-weapons">{"".join(_slot_html(exp, slot, gear.get(slot)) for slot in _WEPS)}{extra}</ul>'
        )
    return f'<article class="lg-profile">{header}{body}</article>'


def _shop_document(exp, dev: bool) -> str:
    _ = exp
    inner = """<header class="bn-bar">
  <div class="bn-wrap">
    <a class="bn-logo" href="/wow/">Blizzard</a>
    <nav aria-label="Battle.net">
      <a href="/wow/">Games</a>
      <a class="is-on" href="/shop">Shop</a>
      <a href="/wow/news">News</a>
      <a href="/esports">Esports</a>
    </nav>
    <nav class="bn-right" aria-label="Account">
      <a href="/support/">Support</a>
      <a href="/account/">Your Account</a>
    </nav>
  </div>
</header>
<main class="bn-shop">
  <p class="bn-banner">Buy World of Warcraft: Complete Collection and <strong>Save 25%</strong>.</p>
  <div class="bn-grid">
    <article class="bn-card">
      <h1>World of Warcraft</h1>
      <p class="bn-price">GBP 9.99</p>
      <button type="button">Buy Now</button>
      <p>Purchase World of Warcraft and play up to level 100.</p>
    </article>
    <article class="bn-card">
      <h1>World of Warcraft: Complete Collection</h1>
      <p class="bn-price"><span>GBP 29.99</span> <s>GBP 39.99</s></p>
      <button type="button">Buy Now</button>
      <p>The Complete Collection includes World of Warcraft, Legion, and a level 100 character boost. Play up to level 110.</p>
    </article>
  </div>
  <p class="bn-note">This shelf is a display. Nothing here is charged.</p>
  <p class="bn-more"><a href="/shop/battletag">BattleTag Change</a></p>
</main>"""
    return document(
        "Shop — Battle.net",
        styles("legion"),
        "shop-bnet",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def _battletag_document(exp, dev: bool) -> str:
    inner = """<header class="bn-bar">
  <div class="bn-wrap">
    <a class="bn-logo" href="/wow/">Blizzard</a>
    <nav aria-label="Battle.net">
      <a href="/wow/">Games</a>
      <a class="is-on" href="/shop">Shop</a>
      <a href="/esports">Esports</a>
    </nav>
    <nav class="bn-right" aria-label="Account">
      <a href="/support/">Support</a>
      <a href="/account/">Your Account</a>
    </nav>
  </div>
</header>
<main class="bn-product">
  <p class="lg-crumb"><a href="/shop">Shop</a> <span>›</span> Battle.net Products <span>›</span> BattleTag Change</p>
  <h1>BattleTag Change</h1>
  <p class="bn-kicker">Battle.net game service</p>
  <p class="bn-price">GBP 8.00</p>
  <button type="button">Buy Now</button>
  <ul>
    <li>Good for a one-time BattleTag change.</li>
    <li>Non-transferable.</li>
    <li>Requires a Battle.net account.</li>
  </ul>
  <p class="bn-note">This shelf is a display. Nothing here is charged.</p>
</main>"""
    return document(
        "BattleTag Change — Battle.net",
        styles("legion"),
        "shop-bnet",
        inner,
        dev_note_text=dev_note(exp, dev),
    )


def _account_fragment(ctx, mode: str) -> str:
    exp = ctx["exp"]
    user = ctx.get("user") or ""
    summary = {"email": "", "characters": []}
    if user and ctx.get("labcfg") is not None:
        try:
            summary = accounts.account_summary(ctx["labcfg"], exp, user) or summary
        except Exception:
            summary = {"email": "", "characters": []}
    return render_account(
        exp,
        user=user,
        error="",
        notice="",
        mode=mode,
        email=summary.get("email") or "",
        characters=summary.get("characters") or [],
        login_kind="email" if accounts.email_login(exp) else "account",
        separate_game_name=exp.proto == "bnet",
    )


def _account_document(ctx, mode: str) -> str:
    titles = {
        "login": "Log In",
        "create": "Create Account",
        "summary": "Account Management",
        "password": "Password & Security",
    }
    fragment = _account_fragment(ctx, mode)
    inner = f'<div class="bnet-gate">{fragment}<p class="bnet-mini"><a href="/wow/">World of Warcraft</a> · <a href="/support/">Support</a></p></div>'
    return document(
        f"{titles.get(mode, 'Account')} — Battle.net",
        styles("legion"),
        f"era-legion legion acct-screen acct-screen-{mode}",
        inner,
        dev_note_text=dev_note(ctx["exp"], bool(ctx.get("dev"))),
    )


def full(path: str, ctx: dict) -> str | None:
    exp = ctx["exp"]
    dev = bool(ctx.get("dev"))
    user = ctx.get("user") or ""
    if path == "/shop":
        return _shop_document(exp, dev)
    if path == "/shop/battletag":
        return _battletag_document(exp, dev)
    if path == "/account/services" and not user:
        body = (
            '<section class="lg-page"><h1>Character Services</h1>'
            "<p>Sign in to manage characters on this account.</p>"
            '<p><a href="/account/login">Log In</a></p></section>'
        )
        return shell(exp, "Character Services", body, None, "Character Services", dev)
    if path == "/account/create":
        if not accounts.registration_open():
            return None
        return _account_document(ctx, "create")
    if path == "/account/login":
        return _account_document(ctx, "login")
    if path == "/account":
        return _account_document(ctx, "summary" if user else "login")
    if path == "/account/password":
        if not user:
            return None
        return _account_document(ctx, "password")
    return None


def take(path: str, ctx: dict) -> tuple[str, str] | None:
    exp = ctx["exp"]
    if path in ("/wow/info/classes", "/wow/info/classes/"):
        return "Classes", _classes(exp)
    if "/wow/info/classes/" in path and path.endswith("/talents.html"):
        slug = path.split("/wow/info/classes/", 1)[1].split("/", 1)[0]
        trees = talents.trees_for(exp, slug)
        if not trees:
            return None
        qs = ctx.get("qs") or {}
        return (
            f"{_class_name(slug)} Talents",
            _talents(exp, slug.lower(), trees, _qs_one(qs, "build"), _qs_one(qs, "spec")),
        )
    if path == "/story":
        return "Story", _story(exp)
    if path == "/wow/news":
        return "News", _news_index(exp)
    if path.startswith("/wow/news/"):
        tail = path.rsplit("/", 1)[-1]
        if not tail.isdigit():
            return None
        article = _article(exp, int(tail))
        return article
    if path == "/forums":
        return "Forums", _forums(exp)
    parts = [part for part in path.split("/") if part]
    if len(parts) == 2 and parts[0] == "forums":
        slug = parts[1]
        title = forums.board_title(exp, slug)
        if not title:
            return None
        visible = _visible_board(exp, slug, title)
        return visible, _board(exp, slug, visible, _threads(ctx, slug), ctx.get("user"), ctx.get("qs"))
    if path.startswith("/armory/character/"):
        name = path.rsplit("/", 1)[-1]
        cfg = ctx.get("labcfg")
        if not name or cfg is None:
            return None
        char = armory.get_character(cfg, exp, name)
        if not char:
            return None
        tab = (_qs_one(ctx.get("qs"), "tab") or "character").lower()
        if tab not in {"character", "achievements", "collections", "raids", "pvp", "reputation"}:
            tab = "character"
        return str(char.get("name") or name), _profile(exp, char, tab, _qs_one(ctx.get("qs"), "view"))
    return None
