"""October 2026 World of Warcraft community site."""

from __future__ import annotations

import time
from pathlib import Path

from ... import armory, assets, content, forums, lab, talents
from .common import dev_note, document, esc, styles

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

_CLASS_ORDER = (
    "warrior",
    "hunter",
    "mage",
    "rogue",
    "priest",
    "warlock",
    "paladin",
    "druid",
    "shaman",
    "monk",
    "demonhunter",
    "deathknight",
    "evoker",
)

_ROLES = {
    "warrior": "TANK, DAMAGE",
    "hunter": "DAMAGE",
    "mage": "DAMAGE",
    "rogue": "DAMAGE",
    "priest": "HEALER, DAMAGE",
    "warlock": "DAMAGE",
    "paladin": "TANK, HEALER, DAMAGE",
    "druid": "TANK, HEALER, DAMAGE",
    "shaman": "HEALER, DAMAGE",
    "monk": "TANK, HEALER, DAMAGE",
    "demonhunter": "TANK, DAMAGE",
    "deathknight": "TANK, DAMAGE",
    "evoker": "HEALER, DAMAGE",
}

_BLURBS = {
    "warrior": (
        "For as long as war has raged, heroes from every race have aimed to master the art of battle. "
        "Warriors combine strength, leadership, and a vast knowledge of arms and armor to wreak havoc in glorious combat."
    ),
    "hunter": (
        "From an early age, the call of the wild draws some adventurers from the comfort of their homes "
        "into the unforgiving primal world outside. Those who endure become hunters."
    ),
    "mage": (
        "Students gifted with a keen intellect and unwavering discipline may walk the path of the mage. "
        "The arcane magic available to magi is both great and dangerous, and thus is revealed only to the most devoted practitioners."
    ),
    "rogue": (
        "For rogues, the only code is the contract, and their honor is purchased in gold. "
        "Free from the constraints of a conscience, these mercenaries rely on brutal and efficient tactics."
    ),
    "priest": (
        "Priests are devoted to the spiritual, and express their unwavering faith by serving the people. "
        "For millennia they have left behind the confines of their temples and the comfort of their shrines "
        "so they can support their allies in war-torn lands."
    ),
    "warlock": (
        "In the face of demonic power, most heroes see death. Warlocks see only opportunity. "
        "Dominance is their aim, and they have found a path to it in the dark arts. "
        "These voracious spellcasters summon demonic minions to fight beside them."
    ),
    "paladin": (
        "This is the call of the paladin: to protect the weak, to bring justice to the unjust, "
        "and to vanquish evil from the darkest corners of the world."
    ),
    "druid": (
        "Druids harness the vast powers of nature to preserve balance and protect life. "
        "As master shapeshifters, druids can take on the forms of a variety of beasts, each focused on a specific combat role."
    ),
    "shaman": (
        "Shamans are spiritual guides and practitioners of the elements. "
        "They are masters of the elements, using spells and totems that heal or enhance their allies in battle "
        "while unleashing the fury of the elements upon their foes."
    ),
    "monk": (
        "Though born in ancient Pandaria, monks are as diverse as the energy that surrounds them. "
        "They can shoulder deadly attacks through the haze of their brews, heal broken chi flows, "
        "and beat their enemies with wind-quick fists and feet."
    ),
    "demonhunter": (
        "Demon hunters embrace the forbidden powers of the Legion. They make use of fel and chaotic magics, "
        "metamorphosis abilities, spectral sight, and hellish agility to hunt down and defeat even the most dangerous adversaries."
    ),
    "deathknight": (
        "When the Lich King's control over his death knights was broken, his former champions found their new purpose "
        "as Knights of the Ebon Blade. After Bolvar Fordragon donned the helm to keep the undead Scourge contained, "
        "he called forth a new generation of death knights to join the Ebon Blade's cause."
    ),
    "evoker": (
        "Dracthyr Evokers were created to wield the magic of all five dragonflights, "
        "and seek to forge their own path in Azeroth."
    ),
}

_ALLIANCE = (
    "human",
    "dwarf",
    "nightelf",
    "gnome",
    "draenei",
    "worgen",
    "voidelf",
    "lightforged",
    "darkiron",
    "kultiran",
    "mechagnome",
    "earthen",
    "pandaren",
    "dracthyr",
)
_HORDE = (
    "orc",
    "undead",
    "tauren",
    "troll",
    "bloodelf",
    "goblin",
    "nightborne",
    "highmountain",
    "maghar",
    "zandalari",
    "vulpera",
    "earthen",
    "pandaren",
    "dracthyr",
    "haranir",
)

_LEFT = ("Head", "Neck", "Shoulders", "Back", "Chest", "Shirt", "Tabard", "Wrists")
_RIGHT = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEAPONS = ("Main Hand", "Off Hand", "Ranged")
_TABS = (
    ("character", "Character"),
    ("achievements", "Achievements"),
    ("collections", "Collections"),
    ("dungeons", "Dungeons & Raids"),
    ("pvp", "Player vs Player"),
    ("reputation", "Reputation"),
)

_SHOP = (
    ("World of Warcraft: Forever", "Available November 4. Upgrade to get in-game benefits and reserve a name.", "From $29.99", "PRE-PURCHASE"),
    ("World of Warcraft: Midnight", "Jump straight into the fight against the Void. An enhanced Level 80 boost is included.", "From $24.99", "Was $49.99"),
    ("World of Warcraft Subscription", "A single subscription for World of Warcraft and WoW Classic.", "From $12.99/month", ""),
    ("Enhanced Level 80 Character Boost", "Game service for one character.", "From $40.20", "Was $60.00"),
    ("Level 85 Character Boost (Progression)", "Progression game service.", "$60.00", ""),
)


def _long_date(iso: str) -> str:
    parts = (iso or "").split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = parts
        month_i = int(month)
        if 1 <= month_i <= 12:
            return f"{_MONTHS[month_i]} {int(day)}, {year}"
    return iso


def _q(ctx: dict, key: str, default: str = "") -> str:
    raw = (ctx.get("qs") or {}).get(key) or []
    if not raw:
        return default
    return str(raw[0])


def _ago(stamp) -> str:
    try:
        delta = int(time.time()) - int(stamp)
    except (TypeError, ValueError):
        return ""
    if delta < 60:
        return "1m"
    if delta < 3600:
        return f"{delta // 60}m"
    if delta < 86400:
        return f"{delta // 3600}h"
    return f"{delta // 86400}d"


def _mast(user: str | None) -> str:
    if user:
        account_bits = (
            f'<a href="/account/">{esc(user)}</a>'
            '<a href="/account/logout">Log Out</a>'
        )
    else:
        account_bits = (
            '<a href="/account/login">Log In</a>'
            '<a href="/account/create">Create Account</a>'
            '<a href="/account/">Account</a>'
        )
    return f"""<header class="mn-mast">
  <details class="mn-drop">
    <summary class="mn-blizz">Blizzard</summary>
    <div class="mn-panel">
      <a href="/wow/">World of Warcraft</a>
      <a href="/support/">Support</a>
    </div>
  </details>
  <a class="mn-logo" href="/wow/"><span>World of</span> Warcraft</a>
  <nav class="mn-links" aria-label="Primary">
    <details class="mn-drop">
      <summary>Game Versions <em class="mn-new">NEW</em></summary>
      <div class="mn-panel">
        <a href="/wow/">World of Warcraft: Forever</a>
        <a href="/wow/">Midnight</a>
        <a href="/classic">WoW Classic</a>
        <a href="/wow/realmstatus">Server Status</a>
      </div>
    </details>
    <a href="/armory/">Armory</a>
    <span class="mn-forum-only">
      <a href="/wow/news">News</a>
      <a href="/shop">Subscription</a>
    </span>
    <details class="mn-drop mn-more">
      <summary aria-label="More">…</summary>
      <div class="mn-panel">
        <a href="/wow/news">News</a>
        <a href="/forums/">Forums</a>
        <a href="/wow/info/">Game Guide</a>
        <a href="/wow/info/classes">Classes</a>
        <a href="/wow/info/races">Races</a>
        <a href="/housing">Housing</a>
        <a href="/shop">Subscription</a>
        <a href="/support/">Support</a>
      </div>
    </details>
  </nav>
  <details class="mn-drop mn-search">
    <summary aria-label="Search">Search</summary>
    <form class="mn-panel" action="/wow/search" method="get">
      <input type="search" name="q" placeholder="Search">
      <button type="submit">Search</button>
    </form>
  </details>
  <details class="mn-drop mn-account">
    <summary>Account</summary>
    <div class="mn-panel">{account_bits}<a href="/account/services">Character and Guild Services</a></div>
  </details>
  <a class="mn-try" href="/account/create">Try Free</a>
  <a class="mn-sub" href="/shop">Subscribe Now</a>
</header>"""


def _foot() -> str:
    return """<footer class="mn-foot">
  <a href="/support/">Support</a>
  <a href="/wow/news">News</a>
  <a href="/forums/">Forums</a>
  <a href="/wow/realmstatus">Server Status</a>
  <p>© 2026 Blizzard Entertainment. All rights reserved.</p>
</footer>"""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = title, crumb, online, login_error
    inner = f"""<div class="mn-shell">
{_mast(user)}
<main class="mn-main">{body}</main>
{_foot()}
</div>"""
    return document(
        "World of Warcraft",
        styles("midnight"),
        "era-midnight midnight",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    _ = exp, realm, user
    cards = (
        ("Claim Your World of Warcraft: Forever Character Names", "/wow/news"),
        ("Unlock a Year of World of Warcraft and Get Bonus Treasures", "/shop"),
        ("Pre-Purchase World of Warcraft: Forever Upgrades and Begin Your Next Journey in Azeroth", "/shop"),
        ("Your Next Adventure in WoW: Forever Starts in the WoW Portal Room", "/wow/news"),
    )
    card_html = "".join(
        f'<a class="mn-mini" href="{esc(href)}"><span>{esc(title)}</span></a>'
        for title, href in cards
    )
    live = []
    for i, item in enumerate(news or []):
        title, date, _body = item
        live.append(
            f'<li><a href="/wow/news/{i}">{esc(title)}</a> <time>{esc(_long_date(date))}</time></li>'
        )
    live_html = f'<ul class="mn-live">{"".join(live)}</ul>' if live else ""
    return f"""<section class="mn-hero">
  <div class="mn-hero-logos" aria-hidden="true">
    <span>World of Warcraft Forever</span>
    <span>World of Warcraft Midnight</span>
    <span>World of Warcraft Classic</span>
  </div>
  <p class="mn-kicker">World of Warcraft: Forever</p>
  <h1>Explore an Azeroth Reborn</h1>
  <p class="mn-dek">Return to wonder in an ever-expanding adventure where the journey is the destination.</p>
  <p class="mn-cta">
    <a class="mn-yellow" href="/shop">Pre-Purchase Now</a>
    <a class="mn-ghost" href="/wow/info/">Go to Game Page</a>
  </p>
  <p class="mn-plat">Available on Windows/Mac · Battle.net</p>
</section>
<section class="mn-updates">
  <header class="mn-updates-head">
    <h2>Latest Updates</h2>
    <p><a href="/wow/news">Hotfixes</a> <a href="/wow/news">Content Updates</a></p>
  </header>
  <article class="mn-feature">
    <div>
      <h3>Midnight's 12.1.5 Content Update is Now Live</h3>
      <p>Midnight's 12.1.5 content update brings the Labyrinth of Kindo'jan, a massive nine-chamber Delve-like challenge, a new single-boss raid, Season 2's mid-season refresh, the dramatic conclusion to the saga of Quel'Thalas and Zul'Aman, Aqir Invasions, and more.</p>
      <p><a href="/wow/news">Learn More</a></p>
    </div>
  </article>
  <div class="mn-minis">{card_html}</div>
  <p class="mn-view"><a class="mn-yellow" href="/wow/news">View All</a></p>
  {live_html}
</section>
<section class="mn-subscr">
  <h2>What's Included in My WoW Subscription?</h2>
  <div class="mn-sub-grid">
    <div>
      <p class="mn-kicker">Subscriptions &amp; Expansions</p>
      <h3>What's Included in My WoW Subscription?</h3>
      <p>Join millions of players and enter a world of myth, magic, and endless adventure. With a single subscription you can access World of Warcraft and WoW Classic. When you purchase a 6-month or 12-month subscription offer, you'll receive the offer bonuses listed in the shop.</p>
      <p><a class="mn-yellow" href="/shop">Subscribe Now</a></p>
    </div>
    <article>
      <h3>World of Warcraft</h3>
      <p>Play World of Warcraft with access to every past expansion. Create your hero, embark on daring adventures, and rise to new heights of power as you level up your character. When you're ready for even more adventure, buy the latest expansion: Midnight.</p>
    </article>
    <article>
      <h3>World of Warcraft: Forever</h3>
      <p>Available November 4. Upgrade to get in-game benefits and early name reservation. Quest through an untamed Azeroth, with expanded, reimagined, and new zones to explore.</p>
    </article>
    <article>
      <h3>Burning Crusade Classic Anniversary</h3>
      <p>Join fellow heroes and rally to face the might of the Burning Legion. Burning Crusade Classic Anniversary brings the playable races of blood elves and draenei, along with flying mounts.</p>
    </article>
    <article>
      <h3>Classic Era</h3>
      <p>Embark on a fresh journey on realms of PvE, PvP, and Hardcore. Experience the game that sparked it all with a reset of the content timeline.</p>
    </article>
  </div>
</section>"""


def _news_index(exp) -> str:
    rows = content.news_for(exp)
    cards = []
    for i, (title, date, body) in enumerate(rows):
        text = body or content.PATCH_NOTES.get(exp.id, "")
        cards.append(
            f'<a class="mn-news-card" href="/wow/news/{i}">'
            f"<h2>{esc(title)}</h2>"
            f"<time>{esc(_long_date(date))}</time>"
            f"<p>{esc(text)}</p></a>"
        )
    when = _long_date(rows[0][1]) if rows else ""
    note = content.PATCH_NOTES.get(exp.id, "")
    return f"""<section class="mn-news">
  <h1>News</h1>
  <div class="mn-news-grid">{''.join(cards)}</div>
  <article class="mn-hotfixes">
    <h2>Hotfixes{(': ' + esc(when)) if when else ''}</h2>
    <p>{esc(note)}</p>
  </article>
</section>"""


def _article(index: int, title: str, date: str, body: str, count: int) -> str:
    text = body or "This note has no longer body in the news list."
    prev_link = f'<a href="/wow/news/{index - 1}">Previous</a>' if index else ""
    next_link = f'<a href="/wow/news/{index + 1}">Next</a>' if index + 1 < count else ""
    return f"""<article class="mn-article">
  <p class="mn-ribbon">News</p>
  <h1>{esc(title)}</h1>
  <p class="mn-by">{esc(_long_date(date))} by Blizzard Entertainment</p>
  <div class="mn-copy"><p>{esc(text)}</p></div>
  <p class="mn-pager">{prev_link} <a href="/wow/news">All News</a> {next_link}</p>
</article>"""


def _classes(exp) -> str:
    have = set(content.classes_for(exp))
    cards = []
    for slug in _CLASS_ORDER:
        if slug not in have:
            continue
        name, _armor, _specs, fallback = content.class_facts(exp, slug)
        blurb = _BLURBS.get(slug, fallback)
        role = _ROLES.get(slug, "")
        icon = assets.class_icon(exp.id, slug)
        img = f'<img src="{esc(icon)}" alt="">' if icon else '<span class="mn-ph"></span>'
        trees = talents.trees_for(exp, slug)
        talent = ""
        if trees:
            talent = f'<a class="mn-talent" href="/wow/info/classes/{esc(slug)}/talents.html">Talents</a>'
        cards.append(
            f'<a class="mn-class" href="/wow/info/classes/{esc(slug)}">{img}'
            f"<span><strong>{esc(name)}</strong><em>{esc(role)}</em>"
            f"<p>{esc(blurb)}</p>{talent}</span></a>"
        )
    return f"""<section class="mn-classes">
  <header class="mn-page-hero">
    <h1>Classes</h1>
    <p>From knights in shiny armor to skulking stalkers and cunning spellcasters, each class in World of Warcraft presents unique challenges and gameplay for you to master. What is your calling?</p>
  </header>
  <div class="mn-class-grid">{''.join(cards)}</div>
</section>"""


def _race_card(exp, slug: str) -> str:
    name, faction, _capital, _blurb = content.race_facts(exp, slug)
    icon = assets.race_icon(exp.id, slug)
    img = f'<img src="{esc(icon)}" alt="">' if icon else '<span class="mn-ph"></span>'
    return (
        f'<a class="mn-race" href="/wow/info/races/{esc(slug)}">{img}'
        f"<strong>{esc(name)}</strong><em>{esc(faction)}</em></a>"
    )


def _races(exp) -> str:
    have = set(content.races_for(exp))
    alliance = "".join(_race_card(exp, slug) for slug in _ALLIANCE if slug in have)
    horde = "".join(_race_card(exp, slug) for slug in _HORDE if slug in have)
    return f"""<section class="mn-races">
  <header class="mn-page-hero mn-page-races">
    <h1>Denizens of Azeroth</h1>
    <p>Azeroth is home to a large variety of races, some native to its lands and some hailing from other realms. Whether as a stalwart defender of the Alliance or a fierce guardian of the Horde, deciding which race to play will define who you'll fight for in this neverending war. Where do your loyalties lie?</p>
  </header>
  <section class="mn-faction mn-alliance">
    <h2>For the Alliance</h2>
    <p>The steadfast Alliance is driven by tradition. They are staunch defenders of justice and duty who protect the realm of Azeroth against any aggressors, including the savage Horde.</p>
    <div class="mn-race-grid">{alliance}</div>
  </section>
  <section class="mn-faction mn-horde">
    <h2>For the Horde</h2>
    <p>The indomitable Horde is driven by unity. They are fervent keepers of freedom and hope, relentlessly opposed to any who threaten these ideals, including the stringent Alliance.</p>
    <div class="mn-race-grid">{horde}</div>
  </section>
</section>"""


def _guide(exp) -> str:
    links = (
        ("/wow/info/classes", "Classes"),
        ("/wow/info/races", "Races"),
        ("/housing", "Player Housing"),
        ("/wow/info/professions", "Professions"),
        ("/wow/info/basics/map", "World Map"),
        ("/wow/realmstatus", "Server Status"),
    )
    items = "".join(f'<li><a href="{esc(href)}">{esc(label)}</a></li>' for href, label in links)
    feats = "".join(f"<li>{esc(name)}</li>" for name in content.features_for(exp))
    return f"""<section class="mn-guide">
  <h1>Game Guide</h1>
  <ul class="mn-guide-links">{items}</ul>
  <h2>This expansion</h2>
  <ul>{feats}</ul>
</section>"""


def _housing() -> str:
    return """<section class="mn-housing">
  <h1 class="mn-sr">Player Housing</h1>
  <div class="mn-house-frame">
    <input type="radio" name="mn-house" id="mn-house-plan" checked>
    <input type="radio" name="mn-house" id="mn-house-yard">
    <div class="mn-house-view mn-house-plan" aria-label="Floor plan">
      <div class="mn-plan">
        <span class="room"></span><span class="room"></span><span class="room"></span>
      </div>
    </div>
    <div class="mn-house-view mn-house-yard" aria-label="Neighborhood">
      <div class="mn-yard"><span class="tree"></span><span class="cottage"></span><span class="path"></span></div>
    </div>
    <div class="mn-house-controls">
      <label for="mn-house-yard">Next</label>
      <label for="mn-house-plan">Previous</label>
    </div>
  </div>
</section>"""


def _status(exp, realm: dict, dev: bool, name_filter: str = "") -> str:
    name = realm.get("name") or exp.realm_name
    flag = "Up" if realm.get("up") else "Down"
    kind = realm.get("type") or "—"
    pop = realm.get("population")
    pop_text = "—" if pop in (None, "") else str(pop)
    zone = realm.get("timezone") or "PST"
    note = ""
    if dev and realm.get("error"):
        note = f'<p class="mn-warn">{esc(realm.get("error"))}</p>'
    show = not name_filter or name_filter in str(name).lower()
    row = ""
    if show:
        row = f"""<tr>
        <td class="{'mn-up' if realm.get('up') else 'mn-down'}">{esc(flag)}</td>
        <td>{esc(name)}</td>
        <td>{esc(kind)}</td>
        <td>{esc(pop_text)}</td>
        <td>{esc(zone)}</td>
        <td>Midnight</td>
      </tr>"""
    return f"""<section class="mn-status">
  <header class="mn-status-hero">
    <h1>Server Status</h1>
    <p>This page lists all available World of Warcraft servers and has information on whether or not a server is up or down. If your server is listed as down, rest assured that we're aware of it and working diligently to bring it back online as quickly as possible.</p>
    <p><a href="/account/services">Character Transfer</a></p>
  </header>
  <form class="mn-filters" action="/wow/realmstatus" method="get">
    <label>Game Version <input name="version" value="World of Warcraft"></label>
    <label>Region <input name="region" value="{esc(name)}"></label>
    <label>Category <input name="category" value="All"></label>
    <label>Search <input name="name" placeholder="Realm Name"></label>
    <button type="submit">Filter</button>
  </form>
  <p class="mn-token">WoW Token price changes on the auction house and is not listed as a fixed gold amount.</p>
  {note}
  <table class="mn-realms">
    <thead><tr><th>Status</th><th>Realm Name</th><th>Type</th><th>Population</th><th>Timezone</th><th>Category</th></tr></thead>
    <tbody>
      {row}
    </tbody>
  </table>
</section>"""


def _forum_index(exp) -> str:
    boards = dict(forums.boards_for(exp))

    def link(slug: str, label: str) -> str:
        href = f"/forums/{slug}" if slug in boards else "/forums/general"
        if slug == "support":
            href = "/support/"
        return f'<a href="{esc(href)}">{esc(label)}</a>'

    classes = "".join(
        link(slug, title) for slug, title in forums.boards_for(exp) if slug in _CLASS_ORDER
    )
    return f"""<section class="mn-forums">
  <div class="mn-forum-banner"><p>World of Warcraft</p></div>
  <h1>Categories</h1>
  <p class="mn-forum-tabs"><span>Categories</span> <span>Top</span> <span>Latest</span> <span>Blizz Tracker</span></p>
  <div class="mn-cats">
    <article>
      <h2>Community</h2>
      <p>Discuss World of Warcraft.</p>
      <p>{link("general", "General Discussion")} {link("ui", "UI & Macros")}</p>
    </article>
    <article>
      <h2>WoW: Forever</h2>
      <p>{link("general", "World of Warcraft: Forever General Discussion")}</p>
    </article>
    <article>
      <h2>WoW Classic</h2>
      <p>{link("general", "WoW Classic General Discussion")} {link("general", "The Burning Crusade Classic")}</p>
    </article>
    <article>
      <h2>In Development</h2>
      <p>Discuss in-development content. Midnight PTR notes live with bug reports.</p>
      <p>{link("bugs", "Midnight: 12.1.5 Public Test Realm")}</p>
    </article>
    <article>
      <h2>Gameplay</h2>
      <p>Gameplay discussion for World of Warcraft.</p>
      <p>{link("housing", "Housing")} {link("quests", "Quests")} {link("professions", "Professions")} {link("dungeons", "Dungeons, Raids and Scenarios")}</p>
    </article>
    <article>
      <h2>PVP</h2>
      <p>Discuss Arenas and Battleground here with your fellow players.</p>
      <p>{link("pvp", "Arenas")} {link("pvp", "Battlegrounds")}</p>
    </article>
    <article>
      <h2>Lore</h2>
      <p>Discuss World of Warcraft lore, fan fiction, or role-play.</p>
      <p>{link("general", "Story Forum")}</p>
    </article>
    <article>
      <h2>Classes</h2>
      <p>For all your class discussion needs.</p>
      <p>{classes}</p>
    </article>
    <article>
      <h2>Support</h2>
      <p>{link("bugs", "Bug Report")} {link("support", "Customer Support")}</p>
    </article>
    <article>
      <h2>Recruitment</h2>
      <p>{link("guilds", "Guild Recruitment")} {link("realm", exp.realm_name + " Realm")}</p>
    </article>
  </div>
</section>"""


def _forum_board(exp, slug: str, title: str, threads: list, user: str | None) -> str:
    chips = "".join(
        f'<a href="/forums/{esc(board)}">{esc(label)}</a>'
        for board, label in forums.boards_for(exp)
        if board != slug
    )
    rows = []
    for thread in threads:
        last = thread.get("last") or thread.get("created")
        rows.append(
            "<tr>"
            f'<td><a href="/forums/{esc(slug)}/{int(thread["id"])}">{esc(thread["title"])}</a>'
            f'<span>{esc(title)}</span></td>'
            f"<td>{esc(thread.get('author'))}</td>"
            f"<td>{esc(thread.get('replies'))}</td>"
            "<td>—</td>"
            f"<td>{esc(_ago(last))}</td>"
            "</tr>"
        )
    body = "".join(rows) or '<tr><td colspan="5">No topics yet.</td></tr>'
    if user:
        form = f"""<form class="mn-post" method="post" action="/forums/{esc(slug)}/new">
  <label>Title <input name="title" required maxlength="120"></label>
  <label>Body <textarea name="body" required rows="6"></textarea></label>
  <button type="submit">Post</button>
</form>"""
    else:
        form = '<p><a href="/account/login">Log in</a> to start a topic.</p>'
    return f"""<section class="mn-forums mn-board">
  <p class="mn-crumb"><a href="/forums/">Forums</a> / {esc(title)}</p>
  <h1>{esc(title)}</h1>
  <div class="mn-chips">{chips}</div>
  <table class="mn-topics">
    <thead><tr><th>Topic</th><th>Author</th><th>Replies</th><th>Views</th><th>Activity</th></tr></thead>
    <tbody>{body}</tbody>
  </table>
  {form}
</section>"""


def _shop(query: str) -> str:
    needle = query.strip().lower()
    cards = []
    for title, body, price, flag in _SHOP:
        if needle and needle not in title.lower() and needle not in body.lower():
            continue
        mark = f"<em>{esc(flag)}</em>" if flag else ""
        cards.append(
            f'<article class="mn-product"><h3>{esc(title)}</h3><p>{esc(body)}</p>'
            f'<p class="mn-price">{esc(price)} {mark}</p></article>'
        )
    grid = "".join(cards) or "<p>No products match that search.</p>"
    return f"""<section class="mn-shop" data-era-bare="1">
  <header class="mn-shop-top">
    <a class="bnet-logo" href="/shop">Battle.net</a>
    <nav>
      <span>Download Battle.net</span>
      <a href="/support/">Support</a>
      <a href="/account/">Account</a>
    </nav>
  </header>
  <nav class="mn-shop-games" aria-label="Games">
    <span>Warcraft</span><span>Diablo</span><span>Overwatch</span>
    <span>Hearthstone</span><span>StarCraft</span><span>Heroes</span>
    <form action="/shop" method="get"><input type="search" name="q" value="{esc(query)}" placeholder="Search Shop"></form>
  </nav>
  <div class="mn-shop-hero">
    <p class="mn-kicker">World of Warcraft: Forever</p>
    <h1>Reserve your name and customize your character ahead of November 4 launch</h1>
    <a class="mn-blue" href="/account/create">Pre-purchase Now</a>
  </div>
  <h2>Recommended</h2>
  <div class="mn-products">{grid}</div>
  <p class="mn-fine">This shelf is a display. Nothing here is charged.</p>
</section>"""


def _armory(exp, query: str, results: list, error: str) -> str:
    rows = []
    for row in results:
        rows.append(
            "<tr>"
            f'<td><a href="/armory/character/{esc(row.get("name"))}">{esc(row.get("name"))}</a></td>'
            f'<td>{esc(row.get("level"))}</td>'
            f'<td>{esc(row.get("race"))}</td>'
            f'<td>{esc(row.get("class"))}</td>'
            f'<td>{esc(row.get("realm") or exp.realm_name)}</td>'
            "</tr>"
        )
    table = ""
    if error:
        table = f'<p class="mn-warn">{esc(error)}</p>'
    elif query:
        body = "".join(rows) or '<tr><td colspan="5">No characters found.</td></tr>'
        table = (
            "<table class=\"mn-realms\"><thead><tr><th>Name</th><th>Level</th><th>Race</th>"
            f"<th>Class</th><th>Realm</th></tr></thead><tbody>{body}</tbody></table>"
        )
    return f"""<section class="mn-armory">
  <h1>Armory</h1>
  <p>Search characters on {esc(exp.realm_name)}.</p>
  <form action="/armory/" method="get">
    <label>Character name <input name="q" value="{esc(query)}"></label>
    <button type="submit">Search</button>
  </form>
  {table}
</section>"""


def _gear(exp, equipped: dict, names: tuple[str, ...]) -> str:
    bits = []
    for name in names:
        item = equipped.get(name)
        if not item:
            continue
        icon = assets.display_icon(exp, item.get("display_id"))
        img = f'<img src="{esc(icon)}" alt="">' if icon else ""
        bits.append(
            f'<a href="/armory/item/{esc(item.get("item_id"))}">{img}'
            f'<span>{esc(item.get("name") or name)}</span></a>'
        )
    return "".join(bits)


def character_profile(exp, char: dict, tab: str) -> str:
    chosen = tab if any(key == tab for key, _label in _TABS) else "character"
    tabs = []
    for key, label in _TABS:
        cls = " mn-on" if key == chosen else ""
        tabs.append(f'<a class="mn-tab{cls}" href="?tab={esc(key)}">{esc(label)}</a>')
    equipped = {}
    for item in char.get("equipment") or []:
        slot = str(item.get("slot") or "")
        if slot:
            equipped[slot] = item
    faction = ""
    race = str(char.get("race") or "")
    for _slug, (name, side, *_rest) in content.RACE_INFO.items():
        if name.lower() == race.lower():
            faction = side
            break
    guild = ""
    if char.get("guild"):
        gname = char["guild"].get("name") if isinstance(char["guild"], dict) else char["guild"]
        guild = f' &lt;{esc(gname)}&gt;'
    if chosen == "character":
        panel = (
            f'<div class="mn-doll"><div class="mn-gear">{_gear(exp, equipped, _LEFT)}</div>'
            f'<div class="mn-model">{esc(char.get("class") or "")}</div>'
            f'<div class="mn-gear mn-gear-right">{_gear(exp, equipped, _RIGHT + _WEAPONS)}</div></div>'
        )
    elif chosen == "achievements":
        panel = f'<p class="mn-panel-note">{esc(char.get("achievements") or 0)} achievements recorded.</p>'
    else:
        panel = '<p class="mn-panel-note">Nothing else is recorded for this character on this tab.</p>'
    return f"""<section class="mn-profile">
  <header class="mn-profile-head mn-{esc(faction.lower() or 'neutral')}">
    <h1>{esc(char.get("name"))}</h1>
    <p><span>{esc(char.get("achievements") or 0)}</span>
      <span>level {esc(char.get("level"))} {esc(race)} {esc(char.get("class"))}</span>
      {guild} — {esc(char.get("realm") or exp.realm_name)}</p>
  </header>
  <nav class="mn-tabs">{''.join(tabs)}</nav>
  {panel}
</section>"""


def _services(ctx: dict) -> tuple[str, str] | None:
    user = ctx.get("user")
    if not user:
        body = """<section class="mn-services">
  <h1>Character and Guild Services</h1>
  <p><a href="/account/login">Log in</a> to use character and guild services.</p>
</section>"""
        return ("Character and Guild Services", body)
    from ...services.page import services_page

    body = services_page(ctx["labcfg"], ctx["exp"], user, ctx["data_dir"])
    body = body.replace("<h2>Character Services</h2>", "<h2>Character and Guild Services</h2>", 1)
    return ("Character and Guild Services", f'<section class="mn-services">{body}</section>')


def _forums_take(path: str, ctx: dict):
    exp = ctx["exp"]
    if path == "/forums":
        return ("Forums", _forum_index(exp))
    parts = [part for part in path.split("/") if part]
    if len(parts) != 2:
        return None
    slug = parts[1]
    title = forums.board_title(exp, slug)
    if not title:
        return None
    data = Path(ctx["data_dir"])
    conn = forums.connect(data)
    try:
        forums.seed_if_empty(conn, exp)
        threads = forums.list_threads(conn, exp, slug)
    finally:
        conn.close()
    return (title, _forum_board(exp, slug, title, threads, ctx.get("user")))


def full(path: str, ctx: dict) -> str | None:
    _ = path, ctx
    return None


def take(path: str, ctx: dict):
    path = (path or "/").rstrip("/") or "/"
    exp = ctx["exp"]
    if path == "/wow/news":
        return ("News", _news_index(exp))
    if path.startswith("/wow/news/"):
        try:
            index = int(path.rsplit("/", 1)[-1])
            rows = content.news_for(exp)
            title, date, body = rows[index]
        except (ValueError, IndexError):
            return None
        return (title, _article(index, title, date, body, len(rows)))
    if path == "/wow/info":
        return ("Game Guide", _guide(exp))
    if path == "/wow/info/classes":
        return ("Classes", _classes(exp))
    if path == "/wow/info/races":
        return ("Races", _races(exp))
    if path == "/housing":
        return ("Housing", _housing())
    if path == "/wow/realmstatus":
        realm = lab.realm_status(ctx["labcfg"], exp)
        return ("Server Status", _status(exp, realm, bool(ctx.get("dev")), _q(ctx, "name").strip().lower()))
    if path == "/forums" or path.startswith("/forums/"):
        return _forums_take(path, ctx)
    if path == "/shop":
        return ("Shop", _shop(_q(ctx, "q")))
    if path == "/armory":
        query = _q(ctx, "q")
        results, error = armory.search_with_status(ctx["labcfg"], exp, query)
        if error and "MariaDB" in error and not ctx.get("dev"):
            error = "The realm database is not reachable."
        return ("The Armory", _armory(exp, query, results, error))
    if path.startswith("/armory/character/"):
        name = path.rsplit("/", 1)[-1]
        char = armory.get_character(ctx["labcfg"], exp, name)
        if not char:
            return None
        return (char["name"], character_profile(exp, char, _q(ctx, "tab", "character")))
    if path == "/account/services":
        return _services(ctx)
    return None
