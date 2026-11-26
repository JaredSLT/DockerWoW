"""October 2026 World of Warcraft community site."""

from __future__ import annotations

import time
from pathlib import Path

from ... import armory, assets, content, forums, lab, talents
from .common import dev_note, document, esc, styles

_IMG = "/static/img/midnight"

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
        "Shaman are the spiritual leaders of their tribes and clans. They are masters of the elements, "
        "using spells and totems that heal or enhance their allies in battle while unleashing the fury of the elements upon their foes."
    ),
    "monk": (
        "Bare-knuckle brawlers whose no-weapon styles were born in ancient Pandaria, monks are as diverse as the energy that surrounds them. "
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

_ALLY_ROW = ("human", "dwarf", "nightelf", "gnome", "draenei", "worgen")
_ALLY_MID = ("pandaren", "dracthyr")
_ALLY_REST = ("voidelf", "lightforged", "darkiron", "kultiran", "mechagnome", "earthen")
_HORDE_ROW = ("orc", "undead", "tauren", "troll", "bloodelf", "goblin")
_HORDE_REST = (
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
_RACE_ART = {
    "human",
    "dwarf",
    "nightelf",
    "gnome",
    "draenei",
    "worgen",
    "pandaren",
    "dracthyr",
    "orc",
    "undead",
    "tauren",
    "troll",
    "bloodelf",
    "goblin",
}

_LEFT = ("Head", "Neck", "Shoulders", "Back", "Chest", "Shirt", "Tabard", "Wrists")
_RIGHT = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEAPONS = ("Main Hand", "Off Hand")
_TABS = (
    ("character", "Character"),
    ("achievements", "Achievements"),
    ("collections", "Collections"),
    ("dungeons", "Dungeons & Raids"),
    ("pvp", "Player vs Player"),
    ("reputation", "Reputation"),
)

_SHOP = (
    ("World of Warcraft: Forever", "Available November 4. Upgrade to get in-game benefits. Massively Multiplayer RPG.", "From $29.99", "PRE-PURCHASE"),
    ("Warcraft III: Reforged", "Warcraft III: Reforged and the Forsaken Kingdoms story.", "From $29.99", ""),
    ("World of Warcraft: Midnight", "Midnight is here. Jump straight into the fight against the Void with an enhanced Level 80 boost, included with Midnight.", "From $24.99", "Was $49.99"),
    ("World of Warcraft: Subscription", "A single subscription for World of Warcraft and WoW Classic.", "From $12.99/month", ""),
    ("Enhanced Level 80 Character Boost", "Game service for one character.", "From $40.20", "Was $60.00"),
    ("Level 85 Character Boost (Progression)", "Progression game service.", "$60.00", ""),
)

_PORTAL_TITLE = "Your Next Adventure in WoW: Forever Starts in the WoW Portal Room"

_SEARCH_ICON = (
    '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">'
    '<circle cx="10" cy="10" r="6.2" fill="none" stroke="currentColor" stroke-width="2"/>'
    '<path d="M15 15.5L20.5 21" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
    "</svg>"
)
_USER_ICON = (
    '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">'
    '<circle cx="12" cy="8" r="3.2" fill="none" stroke="currentColor" stroke-width="2"/>'
    '<path d="M5 19.2c1.4-3 3.8-4.4 7-4.4s5.6 1.4 7 4.4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
    "</svg>"
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
  <details class="mn-drop mn-blizz-drop">
    <summary class="mn-blizz"><img src="{_IMG}/blizz.png" alt="Blizzard"></summary>
    <div class="mn-panel">
      <a href="/wow/">World of Warcraft</a>
      <a href="/support/">Support</a>
    </div>
  </details>
  <a class="mn-logo" href="/wow/"><img src="{_IMG}/wow.png" alt="World of Warcraft"></a>
  <nav class="mn-links" aria-label="Primary">
    <details class="mn-drop">
      <summary>Game Versions</summary>
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
      <summary aria-label="More"><span aria-hidden="true">···</span></summary>
      <div class="mn-panel">
        <a href="/wow/news">News</a>
        <a href="/forums/">Forums</a>
        <a href="/wow/info">Game Guide</a>
        <a href="/wow/info/classes">Classes</a>
        <a href="/wow/info/races">Races</a>
        <a href="/housing">Housing</a>
        <a href="/shop">Subscription</a>
        <a href="/support/">Support</a>
      </div>
    </details>
  </nav>
  <details class="mn-drop mn-search">
    <summary aria-label="Search">{_SEARCH_ICON}</summary>
    <form class="mn-panel" action="/wow/search" method="get">
      <input type="search" name="q" placeholder="Search">
      <button type="submit">Search</button>
    </form>
  </details>
  <details class="mn-drop mn-account">
    <summary>{_USER_ICON} Account</summary>
    <div class="mn-panel">{account_bits}<a href="/account/services">Character and Guild Services</a></div>
  </details>
  <a class="mn-try" href="/account/create">Try Free</a>
  <a class="mn-sub" href="/shop">Subscribe Now</a>
</header>"""


def _foot() -> str:
    return """<footer class="mn-foot">
  <p class="mn-follow">Follow Warcraft</p>
  <p class="mn-social">
    <a href="/forums/" aria-label="Facebook"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M14 9h3V6h-3c-2.2 0-4 1.8-4 4v2H8v3h2v7h3v-7h2.6l.4-3H13v-2c0-.6.4-1 1-1z"/></svg></a>
    <a href="/wow/news" aria-label="X"><svg viewBox="0 0 24 24" width="15" height="15"><path fill="currentColor" d="M4 4l6.6 8.4L4.4 20H6l5.2-6.1L15.8 20H20l-6.9-8.8L19.4 4H17.8l-4.8 5.6L8.2 4H4z"/></svg></a>
    <a href="/wow/" aria-label="YouTube"><svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M22 12.2s0-3.2-.4-4.6c-.2-.9-.9-1.6-1.8-1.8C18.2 5.4 12 5.4 12 5.4s-6.2 0-7.8.4c-.9.2-1.6.9-1.8 1.8C2 9 2 12.2 2 12.2s0 3.2.4 4.6c.2.9.9 1.6 1.8 1.8 1.6.4 7.8.4 7.8.4s6.2 0 7.8-.4c.9-.2 1.6-.9 1.8-1.8.4-1.4.4-4.6.4-4.6zM10 15.5v-6.6l5.2 3.3-5.2 3.3z"/></svg></a>
    <a href="/forums/" aria-label="Reddit"><svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="13" r="6" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="9.5" cy="12.5" r="1" fill="currentColor"/><circle cx="14.5" cy="12.5" r="1" fill="currentColor"/><path d="M9 15.2c.8.7 1.8 1 3 1s2.2-.3 3-1" fill="none" stroke="currentColor" stroke-width="1.4"/></svg></a>
    <a href="/wow/" aria-label="Instagram"><svg viewBox="0 0 24 24" width="16" height="16"><rect x="5" y="5" width="14" height="14" rx="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="16.4" cy="7.6" r="0.9" fill="currentColor"/></svg></a>
  </p>
  <nav class="mn-legal" aria-label="Footer">
    <a href="/support/">Careers</a>
    <a href="/wow/">About</a>
    <a href="/support/">Support</a>
    <a href="/support/">Contact Us</a>
    <a href="/wow/news">Press</a>
    <a href="/support/">API</a>
  </nav>
  <p class="mn-copy">© 2026 Blizzard Entertainment, Inc. All rights reserved.</p>
  <p class="mn-legal-links">
    <a href="/support/">Privacy</a>
    <a href="/support/">Legal</a>
    <a href="/support/">Terms</a>
  </p>
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
        ("Claim Your World of Warcraft: Forever Character Names", "/wow/news", "mini-names.jpg"),
        ("Unlock a Year of World of Warcraft and Get Bonus Treasures", "/shop", "mini-year.jpg"),
        ("Pre-Purchase World of Warcraft: Forever Upgrades and Begin Your Next Journey in Azeroth", "/shop", "mini-prep.jpg"),
        (_PORTAL_TITLE, "/wow/news/portal-room", "mini-portal.jpg"),
    )
    card_html = "".join(
        f'<a class="mn-mini" href="{esc(href)}"><img src="{_IMG}/{esc(art)}" alt="">'
        f"<span>{esc(title)}</span></a>"
        for title, href, art in cards
    )
    live = "".join(f"<li>{esc(title)}</li>" for title, _date, _body in (news or []))
    return f"""<section class="mn-hero">
  <img class="mn-hero-art" src="{_IMG}/hero.jpg" alt="">
  <img class="mn-lock mn-lock-forever" src="{_IMG}/logo-forever.png" alt="World of Warcraft Forever">
  <img class="mn-lock mn-lock-midnight" src="{_IMG}/logo-midnight.png" alt="World of Warcraft Midnight">
  <img class="mn-lock mn-lock-classic" src="{_IMG}/logo-classic.png" alt="World of Warcraft Classic">
  <div class="mn-sr">
    <p>World of Warcraft: Forever</p>
    <h1>Explore an Azeroth Reborn</h1>
    <p>Return to wonder in an ever-expanding adventure where the journey is the destination.</p>
    <p>Available on Windows/Mac · Battle.net</p>
    <ul>{live}</ul>
  </div>
  <a class="mn-hit mn-hit-buy" href="/shop">Pre-Purchase Now</a>
  <a class="mn-hit mn-hit-game" href="/wow/info">Go to Game Page</a>
</section>
<section class="mn-updates">
  <header class="mn-updates-head">
    <h2><span class="mn-w" aria-hidden="true">W</span> Latest Updates</h2>
    <p><a href="/wow/news">Hotfixes →</a> <a href="/wow/news">Content Updates →</a></p>
  </header>
  <article class="mn-feature">
    <div>
      <h3>Midnight's 12.1.5 Content Update is Now Live</h3>
      <p>Midnight's 12.1.5 content update brings the Labyrinth of Kindo'jan, a massive nine-chamber Delve-like challenge, a new single-boss raid, Season 2's mid-season refresh, the dramatic conclusion to the saga of Quel'Thalas and Zul'Aman, Aqir Invasions, and more.</p>
      <p><a class="mn-more" href="/wow/news">Learn More →</a></p>
    </div>
    <img src="{_IMG}/update-1215.jpg" alt="">
  </article>
  <div class="mn-minis">{card_html}</div>
  <p class="mn-view"><a class="mn-yellow" href="/wow/news">View All</a></p>
</section>
<section class="mn-subscr" id="mn-sub">
  <div class="mn-subtabs">
    <h2>What's Included in My WoW Subscription?</h2>
    <p><a href="#mn-sub">What's Included in My WoW Subscription?</a> <a href="/support/">System Requirements</a></p>
  </div>
  <div class="mn-sub-grid">
    <div>
      <p class="mn-kicker">Subscriptions &amp; Expansions</p>
      <h3>What's Included in My WoW Subscription?</h3>
      <p>Join millions of players and enter a world of myth, magic, and endless adventure. With a single subscription you can access World of Warcraft and WoW Classic. When you purchase a 6-month or 12-month subscription offer, you'll receive the offer bonuses listed in the shop.</p>
      <p><a class="mn-yellow" href="/shop">Subscribe Now</a></p>
    </div>
    <article>
      <h3><span class="mn-w" aria-hidden="true">W</span> World of Warcraft</h3>
      <p>Play World of Warcraft with access to every past expansion. Create your hero, embark on daring adventures, and rise to new heights of power as you level up your character. When you're ready for even more adventure, buy the latest expansion: Midnight.</p>
      <h3><span class="mn-w" aria-hidden="true">W</span> Burning Crusade Classic Anniversary</h3>
      <p>Join fellow heroes and rally to face the might of the Burning Legion. Burning Crusade Classic Anniversary brings the playable races of blood elves and draenei, along with flying mounts.</p>
    </article>
    <article>
      <h3><span class="mn-w" aria-hidden="true">W</span> World of Warcraft: Forever</h3>
      <p>Available November 4. Upgrade to get in-game benefits and Early Name Reservation. Quest your way through an untamed and breathtaking Azeroth, rich with expanded, reimagined, and new zones to explore.</p>
      <h3><span class="mn-w" aria-hidden="true">W</span> Classic Era</h3>
      <p>Embark on a fresh journey together with realms of PvE, PvP, and Hardcore. Experience the game that sparked it all with a complete reset of the content timeline and clean slate economy.</p>
    </article>
  </div>
</section>"""


def _news_index(exp) -> str:
    rows = content.news_for(exp)
    hidden = "".join(f"<li>{esc(title)}</li>" for title, _date, _body in rows)
    note = content.PATCH_NOTES.get(exp.id, "")
    stories = (
        (
            "news-hot1.jpg",
            "/wow/news",
            "Hotfixes: October 30, 2026",
            "Here you will find a list of hotfixes that address various issues related to World of Warcraft: Midnight, Mists of Pandaria Classic, Season of Discovery, The Burning Crusade Classic, WoW Classic Era, and Hardcore. " + note,
            "14 hours ago",
        ),
        (
            "mini-year.jpg",
            "/wow/news",
            "Prepare for Forever, Try Midnight's Talebound, and Discover Sweet Treats in WoW Weekly",
            "From the global launch of World of Warcraft: Forever on November 4 to the eerie adventures of Midnight's Talebound demo, this week's news is packed with helpful guides, fresh stories, new rewards, and haunting additions to your collection.",
            "a day ago",
        ),
        (
            "update-1215.jpg",
            "/wow/news",
            "WoW: Midnight's Talebound Demo is Now Live",
            "Take the Talebound demo for a spooky spin on the Player Test Realm and experience the Red Hollow introduction. No subscription is required to take part.",
            "a day ago",
        ),
        (
            "mini-prep.jpg",
            "/wow/",
            "World of Warcraft: Forever Goes Live Globally November 4!",
            "Begin your first adventure or return to a new and reimagined Azeroth in World of Warcraft: Forever, launching worldwide November 4.",
            "2 days ago",
        ),
        (
            "mini-names.jpg",
            "/wow/",
            "Return to Azeroth in World of Warcraft: Forever",
            "Welcome back to Azeroth. Whether it has been a few years, or many — familiar roads, old friends, and new adventures are waiting for you in World of Warcraft: Forever.",
            "2 days ago",
        ),
        (
            "news-podcast.jpg",
            "/wow/news/portal-room",
            "Watch the WoW: Forever Podcast: All About Tech",
            "Join WoW: Forever Podcast host Countdown To Classic as they talk tech with the people building the worlds of Warcraft.",
            "2 days ago",
        ),
    )
    hot_html = []
    for art, href, title, body, when in stories:
        hot_html.append(
            f'<article class="mn-hotfix"><a href="{esc(href)}"><img src="{_IMG}/{esc(art)}" alt=""></a>'
            f"<div><h2><a href=\"{esc(href)}\">{esc(title)}</a></h2>"
            f"<p>{esc(body)}</p><time>{esc(when)}</time></div></article>"
        )
    return f"""<section class="mn-news">
  <h1 class="mn-sr">News</h1>
  <ul class="mn-sr">{hidden}</ul>
  <div class="mn-news-mosaic">
    <a class="mn-news-feature" href="/wow/news"><img src="{_IMG}/news-podcast.jpg" alt="Watch the WoW: Forever Podcast: All About Tech"></a>
    <a href="/shop"><img src="{_IMG}/news-names.jpg" alt="Claim Your World of Warcraft: Forever Character Names"></a>
    <a href="/wow/"><img src="{_IMG}/news-forever.jpg" alt="World of Warcraft: Forever Goes Live Globally November 4"></a>
  </div>
  <div class="mn-news-row">
    <a href="/wow/news"><img src="{_IMG}/news-zul.jpg" alt="BCCA: The Gods of Zul'Aman Now Live"></a>
    <a href="/shop"><img src="{_IMG}/news-upgrades.jpg" alt="Pre-Purchase World of Warcraft: Forever Upgrades"></a>
    <a href="/shop"><img src="{_IMG}/news-year.jpg" alt="Unlock a Year of World of Warcraft"></a>
  </div>
  <div class="mn-hotfix-list">{''.join(hot_html)}</div>
</section>"""


def _article(index: int, title: str, date: str, body: str, count: int) -> str:
    text = body or "This note has no longer body in the news list."
    prev_link = f'<a href="/wow/news/{index - 1}">Previous</a>' if index else ""
    next_link = f'<a href="/wow/news/{index + 1}">Next</a>' if index + 1 < count else ""
    return f"""<article class="mn-article">
  <img class="mn-article-hero" src="{_IMG}/article-hero.jpg" alt="">
  <h1>{esc(title)}</h1>
  <p class="mn-by">{esc(_long_date(date))} by Blizzard Entertainment</p>
  <div class="mn-copy"><p>{esc(text)}</p></div>
  <p class="mn-pager">{prev_link} <a href="/wow/news">All News</a> {next_link}</p>
</article>"""


def _portal() -> str:
    return f"""<article class="mn-article">
  <img class="mn-article-hero" src="{_IMG}/article-hero.jpg" alt="">
  <h1>{esc(_PORTAL_TITLE)}</h1>
  <p class="mn-by">October 27, 2026 by <a href="/wow/news">Blizzard Entertainment</a></p>
  <p class="mn-share"><a class="mn-share-btn" href="/forums/">Share</a> <a class="mn-share-btn" href="/wow/news">Tweet</a> <a class="mn-share-count" href="#comments">4 Comments</a></p>
  <div class="mn-copy">
    <p>Azeroth has always been more than a place to play — it is a world shaped by the people we meet along the way. The WoW Portal Room offers a starting point for making those connections, whether you're searching for familiar camaraderie or an entirely new circle of adventurers.</p>
    <p>The WoW Portal Room is ready to welcome World of Warcraft: Forever players and help them build on the friendships, stories, and shared adventures that make Azeroth feel like home. Alongside players at every stage of their journey, you can turn that enduring connection into new conversations, groups, and communities.</p>
    <h2>A Gathering Place for Every Kind of WoW Player</h2>
    <p>The WoW Portal Room is the official World of Warcraft Discord server, bringing players and community Ambassadors together in an inclusive hub. Whether you're learning the ropes, returning to the game, sharing years of knowledge, or looking for a new group for your next chapter, the Portal Room can point you in the right direction. Like any portal, it is a gateway — not the final destination.</p>
    <h2>Meet the WoW Ambassadors</h2>
    <p>WoW Ambassadors are experienced players who represent their Discord communities in the WoW Portal Room. They help players of all backgrounds and experience levels find welcoming spaces that match how they enjoy Warcraft — whether that means tackling content together, swapping stories, learning from others, or simply staying connected to the world and its community.</p>
    <p>Ready to find your people? <a href="/forums/">Join the WoW Portal Room</a>.</p>
  </div>
  <p class="mn-comments" id="comments"><a href="/forums/">4 Comments</a></p>
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
        trees = talents.trees_for(exp, slug)
        talent = ""
        if trees:
            talent = f'<a class="mn-talent" href="/wow/info/classes/{esc(slug)}/talents.html">Talents</a>'
        cards.append(
            f'<article class="mn-class">'
            f'<a href="/wow/info/classes/{esc(slug)}"><img src="{_IMG}/class-{esc(slug)}.jpg" alt="">'
            f"<span><strong>{esc(name)}</strong><em>{esc(role)}</em>"
            f"<p>{esc(blurb)}</p></span></a>{talent}</article>"
        )
    return f"""<section class="mn-classes">
  <header class="mn-page-hero mn-page-classes">
    <h1>Classes</h1>
    <p>From knights in shiny armor to skulking stalkers and cunning spellcasters, each class in World of Warcraft presents unique challenges and gameplay for you to master. What is your calling?</p>
  </header>
  <div class="mn-class-grid">{''.join(cards)}</div>
</section>"""


def _race_card(exp, slug: str) -> str:
    name, faction, _capital, _blurb = content.race_facts(exp, slug)
    if slug in _RACE_ART:
        img = f'<img src="{_IMG}/race-{esc(slug)}.jpg" alt="">'
    else:
        img = '<span class="mn-ph"></span>'
    return (
        f'<a class="mn-race" href="/wow/info/races/{esc(slug)}">{img}'
        f"<strong>{esc(name)}</strong><em class=\"mn-sr\">{esc(faction)}</em></a>"
    )


def _race_row(exp, slugs, have: set[str]) -> str:
    return "".join(_race_card(exp, slug) for slug in slugs if slug in have)


def _races(exp) -> str:
    have = set(content.races_for(exp))
    return f"""<section class="mn-races">
  <header class="mn-page-hero mn-page-races">
    <h1>Denizens of Azeroth</h1>
    <p>Azeroth is home to a large variety of races, some native to its lands and some hailing from other realms. Whether as a stalwart defender of the Alliance or a fierce guardian of the Horde, deciding which race to play will define who you'll fight for in this neverending war. Where do your loyalties lie?</p>
  </header>
  <section class="mn-faction mn-alliance">
    <img class="mn-crest" src="{_IMG}/crest-alliance.png" alt="">
    <h2>For the Alliance</h2>
    <p>The steadfast Alliance is driven by tradition. They are staunch defenders of justice and duty who protect the realm of Azeroth against any aggressors, including the savage Horde.</p>
    <div class="mn-race-grid">{_race_row(exp, _ALLY_ROW, have)}</div>
    <div class="mn-race-grid mn-race-mid">{_race_row(exp, _ALLY_MID, have)}</div>
  </section>
  <section class="mn-faction mn-horde">
    <img class="mn-crest" src="{_IMG}/crest-horde.png" alt="">
    <h2>For the Horde</h2>
    <p>The indomitable Horde is driven by unity. They are fervent keepers of freedom and hope, relentlessly opposed to any who threaten these ideals, including the stringent Alliance.</p>
    <div class="mn-race-grid">{_race_row(exp, _HORDE_ROW, have)}</div>
    <p class="mn-sr">Haranir</p>
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
    return f"""<section class="mn-housing">
  <h1 class="mn-sr">Player Housing</h1>
  <div class="mn-house-frame">
    <img src="{_IMG}/housing.jpg" alt="Player housing neighborhood and floor plan">
    <a class="mn-buyhouse" href="/shop">Buy Now</a>
  </div>
  <p class="mn-house-note">Housing feature available only through purchase of, or entitlement to, World of Warcraft: Midnight. In-game housing experience and items may differ from this preview.</p>
</section>"""


def _status(exp, realm: dict, dev: bool, name_filter: str = "") -> str:
    name = realm.get("name") or exp.realm_name
    up = bool(realm.get("up"))
    flag = "Up" if up else "Down"
    kind = realm.get("type") or "Normal"
    pop = realm.get("population")
    pop_text = "—" if pop in (None, "") else str(pop)
    zone = realm.get("timezone") or "PST"
    note = ""
    if dev and realm.get("error"):
        note = f'<p class="mn-warn">{esc(realm.get("error"))}</p>'
    show = not name_filter or name_filter in str(name).lower()
    row = ""
    if show:
        mark = "mn-check" if up else "mn-cross"
        row = f"""<tr>
        <td class="{mark}"><span class="mn-sr">{esc(flag)}</span></td>
        <td>{esc(name)}</td>
        <td>{esc(kind)}</td>
        <td>{esc(pop_text)}</td>
        <td>{esc(zone)}</td>
        <td>United States</td>
      </tr>"""
    return f"""<section class="mn-status">
  <header class="mn-status-hero">
    <h1>Server Status</h1>
    <p>This page lists all available World of Warcraft servers and has information on whether or not a server is up or down. If your server is listed as down, rest assured that we're aware of it and working diligently to bring it back online as quickly as possible.</p>
    <p><a href="/account/services">Character Transfer</a></p>
  </header>
  <form class="mn-filters" action="/wow/realmstatus" method="get">
    <label>Game Version
      <select name="version"><option>World of Warcraft</option></select>
    </label>
    <p class="mn-token">1 Token = 289985 Gold</p>
    <label>Region
      <select name="region"><option>Americas &amp; Oceania</option></select>
    </label>
    <label>Category
      <select name="category"><option>All</option></select>
    </label>
    <label>Search
      <input name="name" placeholder="Realm Name">
    </label>
    <button type="submit" aria-label="Filter">Search</button>
  </form>
  {note}
  <table class="mn-realms">
    <thead><tr><th>Status</th><th>Realm Name</th><th>Type</th><th>Population</th><th>Timezone</th><th>Category</th></tr></thead>
    <tbody>{row}</tbody>
  </table>
</section>"""


def _board_href(boards: dict, slug: str) -> str:
    if slug == "support":
        return "/support/"
    if slug in boards:
        return f"/forums/{slug}"
    return "/forums/general"


def _forum_index(exp) -> str:
    boards = dict(forums.boards_for(exp))

    def link(slug: str, label: str) -> str:
        return f'<a href="{esc(_board_href(boards, slug))}">{esc(label)}</a>'

    classes = (
        ("deathknight", "Death Knight"),
        ("demonhunter", "Demon Hunter"),
        ("druid", "Druid"),
        ("hunter", "Hunter"),
        ("mage", "Mage"),
        ("monk", "Monk"),
        ("paladin", "Paladin"),
        ("priest", "Priest"),
        ("rogue", "Rogue"),
        ("shaman", "Shaman"),
        ("warlock", "Warlock"),
        ("warrior", "Warrior"),
        ("evoker", "Evoker"),
    )
    class_links = " ".join(link(slug, label) for slug, label in classes if slug in boards)
    return f"""<section class="mn-forums">
  <div class="mn-forum-banner"><img src="{_IMG}/forums-banner.jpg" alt="World of Warcraft"></div>
  <p class="mn-crumb"><a href="/forums/">Forums</a></p>
  <h1>Categories <span>tags</span></h1>
  <p class="mn-forum-tabs"><span class="mn-on">Categories</span> <span>Top</span> <span>Latest</span> <span>Blizz Tracker</span></p>
  <div class="mn-cats">
    <div class="mn-cat-col">
    <article>
      <h2>Community</h2>
      <p>Discuss World of Warcraft.</p>
      <p>{link("general", "General Discussion")} {link("general", "Oceanic General Discussion")} {link("general", "WoW Community Council")}</p>
    </article>
    <article>
      <h2>WoW: Forever</h2>
      <p>{link("general", "World of Warcraft: Forever General Discussion")} {link("general", "WoW: Forever Community Connections")}</p>
    </article>
    <article>
      <h2>WoW Classic</h2>
      <p>{link("general", "WoW Classic General Discussion")} {link("general", "The Burning Crusade Classic")} {link("general", "Mists of Pandaria Classic Discussion")} {link("bugs", "WoW Classic Bug Report")} {link("guilds", "WoW Classic New Guild Listings")} {link("general", "Classic Connections")} {link("general", "Season of Discovery")} {link("general", "WoW Classic Hardcore")}</p>
    </article>
    <article>
      <h2>In Development</h2>
      <p>Discuss in-development content.</p>
      <p>{link("bugs", "WoW: Forever Beta Discussion")} {link("bugs", "Midnight: Echoes of the Worldcore PTR")} {link("bugs", "Midnight: 12.1.5 Public Test Realm")} {link("bugs", "Burning Crusade Classic Zul'Aman PTR")}</p>
    </article>
    <article>
      <h2>Support</h2>
      <p>{link("support", "Customer Support")} {link("support", "Technical Support")} {link("bugs", "Bug Report")} {link("bugs", "Website Bug Report")} {link("bugs", "Mobile Bug Report")}</p>
    </article>
    <article>
      <h2>Guides</h2>
      <p>New to World of Warcraft or returning after some time away? Come and join us.</p>
      <p><a href="/wow/info">New Player Help and Guides</a></p>
    </article>
    </div>
    <div class="mn-cat-col">
    <article>
      <h2>Gameplay</h2>
      <p>Gameplay discussion for World of Warcraft.</p>
      <p>{link("housing", "Housing")} {link("housing", "Housing Blueprints")} {link("general", "Quests")} {link("professions", "Professions")} {link("general", "Pet Battles")} {link("dungeons", "Dungeons, Raids and Scenarios")} {link("general", "Transmogrification")} {link("general", "Achievements")}</p>
    </article>
    <article>
      <h2>PVP</h2>
      <p>Discuss Arenas and Battlegrounds here with your fellow players.</p>
      <p>{link("pvp", "War Mode and World PvP")} {link("pvp", "Arenas")} {link("pvp", "Battlegrounds")}</p>
    </article>
    <article>
      <h2>Lore</h2>
      <p>Discuss World of Warcraft lore, fan fiction, or role-play.</p>
      <p>{link("general", "World's End Tavern")} {link("general", "Story Forum")}</p>
    </article>
    <article>
      <h2>Off-Topic</h2>
      <p>For all your non-Blizzard game discussions.</p>
      <p>{link("general", "Games, Gaming and Hardware")} {link("general", "Movies, TV and Entertainment")} {link("general", "Books and Comics")}</p>
    </article>
    <article>
      <h2>Classes</h2>
      <p>For all your class discussion needs.</p>
      <p>{class_links}</p>
    </article>
    <article>
      <h2>Recruitment</h2>
      <p>Looking for a guild, community, or group?</p>
      <p>{link("guilds", "Guild Recruitment")} {link("guilds", "Oceanic Guild Recruitment")} {link("guilds", "Communities Recruitment")} {link("realm", exp.realm_name + " Realm")}</p>
    </article>
    </div>
  </div>
</section>"""


def _forum_board(exp, slug: str, title: str, threads: list, user: str | None) -> str:
    chips = (
        ("/forums/housing", "Housing"),
        ("/forums/housing", "Housing Blueprints"),
        ("/forums/general", "Quests"),
        ("/forums/professions", "Professions"),
        ("/forums/general", "Pet Battles"),
        ("/forums/dungeons", "Dungeons, Raids and Scenarios"),
        ("/forums/general", "Transmogrification"),
        ("/forums/general", "Achievements"),
    )
    chip_html = "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in chips)
    rows = []
    for thread in threads:
        last = thread.get("last") or thread.get("created")
        rows.append(
            "<tr>"
            f'<td><a href="/forums/{esc(slug)}/{int(thread["id"])}">{esc(thread["title"])}</a>'
            f"<span>{esc(title)}</span></td>"
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
        form = '<p class="mn-post"><a href="/account/login">Log in</a> to start a topic.</p>'
    return f"""<section class="mn-forums mn-board">
  <p class="mn-crumb"><a href="/forums/">Forums</a> <span>/</span> {esc(title)}</p>
  <h1>{esc(title)} <span>Subcategories</span> <span>tags</span></h1>
  <p class="mn-forum-tabs"><span>Top</span> <span class="mn-on">Latest</span> <span>Blizz Tracker</span></p>
  <div class="mn-chips">{chip_html}</div>
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
            f'<p class="mn-price">{esc(price)} {mark}</p>'
            f'<a href="/account/create">Buy</a></article>'
        )
    grid = "".join(cards) or "<p>No products match that search.</p>"
    names = "".join(f"<li>{esc(title)} {esc(price)}</li>" for title, _body, price, _flag in _SHOP)
    games = ("Warcraft", "Diablo", "Overwatch", "Hearthstone", "StarCraft", "Heroes")
    nav = "".join(f'<a href="/shop">{esc(name)}</a>' for name in games)
    shelf = ""
    if not needle:
        shelf = (
            f'<img class="mn-shop-shelf" src="{_IMG}/shop-shelf.jpg" alt="">'
            f'<img class="mn-shop-feature" src="{_IMG}/shop-feature.jpg" alt="">'
        )
        grid = ""
    return f"""<section class="mn-shop" data-era-bare="1">
  <header class="mn-shop-top">
    <a class="bnet-logo" href="/shop"><svg viewBox="0 0 40 40" width="28" height="28" aria-hidden="true"><path fill="#148eff" d="M20 3c6.6 0 12 3.6 14.2 8.2-3.6.6-6.6.2-9.2-1.6.8 5.2.4 9.4-2.4 13.2-3.6-1.6-6-5.4-6.2-9.6.2-2.2 2.6-4.6 5.6-5.6-4.6 1-8.4 4.6-8.4 10.2C13.6 26.2 19 32 26 32c2.8 0 5.4-.8 7.4-2.4-1.8 4.6-6.4 7.8-11.8 7.8C13.2 37.4 6 30.2 6 21.4 6 11.6 12.4 3 20 3z"/></svg> Battle.net</a>
    <nav>
      <a href="/support/">Download Battle.net</a>
      <a href="/support/">Support</a>
      <a href="/account/">Account</a>
    </nav>
  </header>
  <nav class="mn-shop-games" aria-label="Games">
    {nav}
    <a href="/shop">More</a>
    <form action="/shop" method="get"><input type="search" name="q" value="{esc(query)}" placeholder="Search Shop"></form>
    <a href="/account/">Battle.net Balance</a>
  </nav>
  <div class="mn-shop-hero">
    <img src="{_IMG}/shop-hero.jpg" alt="">
    <div class="mn-sr">
      <p>World of Warcraft: Forever</p>
      <h1>Reserve your name and customize your character ahead of November 4 launch</h1>
    </div>
    <a class="mn-hit mn-hit-shop" href="/account/create">Pre-purchase Now</a>
  </div>
  <ul class="mn-sr">{names}</ul>
  {shelf}
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


def _gear(exp, equipped: dict, names: tuple[str, ...], side: str) -> str:
    bits = []
    for name in names:
        item = equipped.get(name)
        if not item:
            bits.append(f'<div class="mn-slot mn-slot-empty {side}"><span>{esc(name)}</span></div>')
            continue
        icon = assets.display_icon(exp, item.get("display_id"))
        img = f'<img src="{esc(icon)}" alt="">' if icon else '<i class="mn-slot-gem"></i>'
        bits.append(
            f'<a class="mn-slot {side}" href="/armory/item/{esc(item.get("item_id"))}">{img}'
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
        guild = f" &lt;{esc(gname)}&gt;"
    if chosen == "character":
        panel = (
            f'<div class="mn-doll"><div class="mn-gear">{_gear(exp, equipped, _LEFT, "left")}</div>'
            f'<div class="mn-model"><p>{esc(char.get("class") or "")}</p></div>'
            f'<div class="mn-gear mn-gear-right">{_gear(exp, equipped, _RIGHT + _WEAPONS, "right")}</div></div>'
            '<ul class="mn-stats">'
            "<li><b>—</b><span>Health</span></li><li><b>—</b><span>Rage</span></li>"
            "<li><b>—</b><span>Strength</span></li><li><b>—</b><span>Stamina</span></li>"
            "<li><b>—</b><span>Critical Strike</span></li><li><b>—</b><span>Haste</span></li>"
            "<li><b>—</b><span>Mastery</span></li><li><b>—</b><span>Versatility</span></li>"
            "</ul>"
            '<section class="mn-spec"><h2>Specialization</h2>'
            f'<article><p>Recorded class</p><strong>{esc(char.get("class") or "")}</strong></article>'
            "</section>"
        )
    elif chosen == "achievements":
        panel = f'<p class="mn-panel-note">{esc(char.get("achievements") or 0)} achievements recorded.</p>'
    else:
        panel = '<p class="mn-panel-note">Nothing else is recorded for this character on this tab.</p>'
    return f"""<section class="mn-profile">
  <header class="mn-profile-head mn-{esc((faction or 'neutral').lower())}">
    <h1>{esc(char.get("name"))}</h1>
    <p><span class="mn-sr">{esc(char.get("achievements") or 0)} achievements</span>
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
    if path == "/wow/news/portal-room":
        return (_PORTAL_TITLE, _portal())
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
