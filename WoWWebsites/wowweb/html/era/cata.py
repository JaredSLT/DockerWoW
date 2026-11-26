"""Cataclysm community site, late 2011 Battle.net chrome (patch 4.3).

The last tab is Services. News, forums, characters, and items come from
the live modules. Screenshot thread titles are not rebuilt here.
"""

from __future__ import annotations

from pathlib import Path

from .common import dev_note, document, esc, styles

_TABS = (
    ("home", "/wow/", "Home"),
    ("game", "/wow/info", "Game"),
    ("community", "/community", "Community"),
    ("media", "/wow/media/screenshots", "Media"),
    ("forums", "/forums/", "Forums"),
    ("services", "/account/services", "Services"),
)
_ICONS = ("⌂", "⚔", "⚑", "▣", "✉", "✦")
_PAGE = 8
_BOARD_PAGE = 20
_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_SECONDARY = {"Archaeology", "Cooking", "First Aid", "Fishing"}
_FORSAKEN = {"undead": "Forsaken"}
_ALLIANCE = {"human", "dwarf", "nightelf", "gnome", "draenei", "worgen"}
_FORUM_GROUPS = (
    ("Support", ("bugs",)),
    ("Community", ("general", "guilds")),
    ("Gameplay & Guides", ("dungeons", "professions", "ui")),
    ("PvP", ("pvp",)),
    ("Realms", ("realm",)),
)
_CLASS_SLUGS = {
    "deathknight", "druid", "hunter", "mage", "paladin", "priest",
    "rogue", "shaman", "warlock", "warrior",
}
_BOARD_BLURB = {
    "general": "Discuss the world of Warcraft.",
    "pvp": "Arenas, battlegrounds, and world PvP.",
    "dungeons": "Dungeons and raids across Azeroth.",
    "professions": "Crafting, gathering, and Archaeology.",
    "ui": "Addons and macros.",
    "guilds": "Recruit a guild, or find one.",
    "realm": "Talk about this realm.",
    "bugs": "Report a bug in the game.",
    "deathknight": "Death Knight discussion.",
    "druid": "Druid discussion.",
    "hunter": "Hunter discussion.",
    "mage": "Mage discussion.",
    "paladin": "Paladin discussion.",
    "priest": "Priest discussion.",
    "rogue": "Rogue discussion.",
    "shaman": "Shaman discussion.",
    "warlock": "Warlock discussion.",
    "warrior": "Warrior discussion.",
}
_PROFILE_NAV = (
    ("summary", "Summary", False),
    ("talents", "Talents & Glyphs", False),
    ("auctions", "Auctions", True),
    ("events", "Events", True),
    ("achievements", "Achievements", False),
    ("statistics", "Statistics", False),
    ("reputation", "Reputation", False),
    ("pvp", "PvP", False),
    ("activity", "Activity Feed", False),
    ("guild", "Guild", False),
)
_LEFT = ("Head", "Neck", "Shoulders", "Back", "Chest", "Shirt", "Tabard", "Wrists")
_RIGHT = ("Hands", "Waist", "Legs", "Feet", "Finger 1", "Finger 2", "Trinket 1", "Trinket 2")
_WEAPONS = ("Main Hand", "Off Hand", "Ranged")
_WEAPON = {
    "0": ("One-Hand", "Axe"),
    "1": ("Two-Hand", "Axe"),
    "2": ("", "Bow"),
    "3": ("", "Gun"),
    "4": ("One-Hand", "Mace"),
    "5": ("Two-Hand", "Mace"),
    "6": ("", "Polearm"),
    "7": ("One-Hand", "Sword"),
    "8": ("Two-Hand", "Sword"),
    "10": ("", "Staff"),
    "13": ("", "Fist Weapon"),
    "15": ("", "Dagger"),
    "16": ("", "Thrown"),
    "18": ("", "Crossbow"),
    "19": ("", "Wand"),
    "20": ("", "Fishing Pole"),
}
_ARMOR = {
    "1": "Cloth", "2": "Leather", "3": "Mail", "4": "Plate", "6": "Shield",
}
_DUNGEONS = (
    ("Cataclysm", "Dragon Soul, the Hour of Twilight, and the heroics of the reshaped world."),
    ("Wrath of the Lich King", "Northrend's dungeons and raids."),
    ("The Burning Crusade", "Outland, from Hellfire to the Sunwell."),
    ("Classic", "Dungeons of the original Eastern Kingdoms and Kalimdor."),
)
_FACTIONS = (
    ("Cataclysm", "Reputations opened by the Cataclysm, kept on the character in game."),
    ("Wrath of the Lich King", "Northrend reputations."),
    ("The Burning Crusade", "Outland reputations."),
)


def _when(iso: str) -> str:
    parts = (iso or "").split("-")
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = parts
        index = int(month) - 1
        if 0 <= index < 12:
            return f"{_MONTHS[index]} {int(day)}, {year}"
    return iso or ""


def _excerpt(text: str, limit: int = 220) -> str:
    flat = " ".join((text or "").split())
    if len(flat) <= limit:
        return flat
    cut = flat[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def _active(crumb: str) -> str:
    low = (crumb or "").lower()
    if "forum" in low:
        return "forums"
    if any(key in low for key in ("screenshot", "wallpaper", "media")):
        return "media"
    if low == "community" or low.startswith("community"):
        return "community"
    if any(key in low for key in ("account", "log in", "create account", "password", "services")):
        return "services"
    if low in ("world of warcraft", "home"):
        return "home"
    if any(key in low for key in (
        "game guide", "races", "classes", "profession", "talent", "world map",
        "patch", "feature", "new player", "armory", "items", "guild", "beginner", " — game",
    )):
        return "game"
    return ""


def _coins(value) -> str:
    try:
        copper = int(value)
    except (TypeError, ValueError):
        return "—"
    gold, rest = divmod(copper, 10000)
    silver, copper = divmod(rest, 100)
    parts = []
    if gold:
        parts.append(f'<span class="coin g">{gold}</span>')
    if silver or gold:
        parts.append(f'<span class="coin s">{silver}</span>')
    parts.append(f'<span class="coin c">{copper}</span>')
    return " ".join(parts)


def _gear_kind(item: dict) -> tuple[str, str]:
    kind = str(item.get("class") if item.get("class") is not None else "")
    sub = str(item.get("subclass") if item.get("subclass") is not None else "")
    if kind == "2" and sub in _WEAPON:
        hand, name = _WEAPON[sub]
        return hand, name
    if kind == "4" and sub in _ARMOR:
        return "", _ARMOR[sub]
    return "", ""


def _tabs(active: str) -> str:
    links = []
    for key, href, label in _TABS:
        mark = " on" if key == active else ""
        links.append(f'<a class="cata-tab {key}{mark}" href="{esc(href)}">{esc(label)}</a>')
    return f'<nav class="cata-tabs" aria-label="World of Warcraft">{"".join(links)}</nav>'


def _service(user: str | None) -> str:
    if user:
        who = (
            f'<span class="cata-hello">Welcome, {esc(user)} | '
            f'<a href="/account/logout">Log Out</a></span>'
        )
    else:
        who = (
            '<span class="cata-hello"><a href="/account/login">Log in</a>'
            ' or <a href="/account/create">Create an Account</a></span>'
        )
    return f"""<div class="cata-service">
  {who}
  <a href="/account/">Account</a>
  <a href="/support/">Support</a>
  <details class="cata-explore">
    <summary>Explore</summary>
    <div>
      <a href="/armory/">The Armory</a>
      <a href="/wow/realmstatus">Realm Status</a>
      <a href="/wow/news">News</a>
      <a href="/story">Story</a>
      <a href="/shop">Shop</a>
      <a href="/wow/pvp/rankings">PvP Rankings</a>
    </div>
  </details>
</div>"""


def _plate(exp, user: str | None, crumb: str) -> str:
    if user:
        return (
            '<div class="cata-plate cata-plate-user">'
            f'<a href="/account/"><strong>{esc(user)}</strong></a>'
            f"<span>{esc(exp.realm_name)}</span></div>"
        )
    if "forum" in (crumb or "").lower():
        line = "Log in with your Battle.net account to post comments and personalize your site content."
    else:
        line = '<span class="cata-hot">Log in now</span> to enhance and<br>personalize your experience!'
    return (
        f'<a class="cata-plate" href="/account/login">{line}'
        f'<img class="cata-goblin" src="{_IMG}/goblin.png" alt=""></a>'
    )


def _footer(show_play: bool) -> str:
    columns = (
        (
            "Battle.net Home",
            (
                ("/wow/", "What is Battle.net?"),
                ("/shop", "Buy Games"),
                ("/account/", "Account"),
                ("/support/", "Support"),
                ("/account/", "Real ID"),
            ),
        ),
        (
            "Games",
            (
                ("/shop", "StarCraft II"),
                ("/wow/", "World of Warcraft"),
                ("/shop", "Diablo III"),
                ("/shop", "Classic Games"),
                ("/wow/media/wallpapers", "Game Client Downloads"),
            ),
        ),
        (
            "Account",
            (
                ("/account/login", "Can't log in?"),
                ("/account/create", "Create Account"),
                ("/account/", "Account Summary"),
                ("/account/password", "Account Security"),
                ("/shop", "Add a Game"),
                ("/shop", "Redeem Promo Codes"),
            ),
        ),
        (
            "Support",
            (
                ("/support/", "Support Articles"),
                ("/support/", "Parental Controls"),
                ("/support/", "Protect Your Account"),
                ("/support/", "Help! I got hacked!"),
            ),
        ),
    )
    blocks = []
    for heading, links in columns:
        items = "".join(f'<li><a href="{esc(href)}">{esc(label)}</a></li>' for href, label in links)
        blocks.append(f"<div><h4>{esc(heading)}</h4><ul>{items}</ul></div>")
    play = ""
    if show_play:
        play = (
            f'<a class="cata-foot-play" href="/account/create">'
            f'<img src="{_IMG}/footer-play.jpg" alt="Play it Free"></a>'
        )
    return (
        f'<footer class="cata-foot">{"".join(blocks)}{play}'
        '<p class="cata-copy">©2011 Blizzard Entertainment, Inc. All rights reserved. '
        '<a href="/support/">Terms of Use</a> '
        '<a href="/support/">Legal</a> '
        '<a href="/support/">Privacy Policy</a> '
        '<a href="/support/">Copyright Infringement</a>'
        '<span class="cata-lang">Americas — English (US)</span></p>'
        f'<p class="cata-blizz"><img src="{_IMG}/blizzard-logo.jpg" alt="Blizzard Entertainment"></p></footer>'
    )


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = online
    active = _active(crumb or title)
    err = f'<p class="cata-login-err">{esc(login_error)}</p>' if login_error else ""
    if active == "forums":
        placeholder = "Search the Armory, forums and more..."
    else:
        placeholder = "Search characters, items, forums and more..."
    inner = f"""<div class="cata-wrap">
  {_service(user)}
  <div class="cata-topline">
    <a class="cata-logo" href="/wow/"><img src="{_IMG}/logo.jpg" alt="World of Warcraft Cataclysm"></a>
    <form class="cata-find" action="/wow/search" method="get">
      <input type="text" name="q" aria-label="Search characters, items, forums and more" placeholder="{esc(placeholder)}">
      <button type="submit" aria-label="Search">Search</button>
    </form>
  </div>
  <div class="cata-panel">
    <header class="cata-navline">
      {_tabs(active)}
      {_plate(exp, user, crumb or title)}
    </header>
    {err}
    <main class="cata-stage">{body}</main>
  </div>
  {_footer(active == "home")}
</div>"""
    css = styles("cata") + [
        "/static/css/forums.css",
        "/static/css/armory.css",
        "/static/css/shop.css",
    ]
    return document(
        f"{title} — World of Warcraft",
        css,
        "era-cata cata",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def _shot(exp, index: int) -> str:
    from ... import assets

    shots = assets.screenshots(exp.id, limit=6)
    if shots:
        return shots[index % len(shots)][0]
    return "/static/img/hero-cata.jpg"


def _article(exp, index: int, title: str, date: str, body: str) -> str:
    return f"""<article class="cata-story">
  <h3><a href="/wow/news/{index}">{esc(title)}</a></h3>
  <p class="cata-by">by Blizzard Entertainment <span>{esc(_when(date))}</span></p>
  <a class="cata-thumb" href="/wow/news/{index}"><img src="{esc(_shot(exp, index))}" alt=""></a>
  <p>{esc(_excerpt(body))}</p>
  <p class="cata-more"><a href="/wow/news/{index}">More ›</a></p>
</article>"""


_IMG = "/static/img/cata"

# Late 2011 community home. These are the photographed stories, not the 2012 news feed.
_HOME_THUMBS = (
    ("thumb-dungeons.jpg", "/wow/info", "WoW Dungeons and Raids Panel"),
    ("thumb-talents.jpg", "/wow/info/classes", "World of Warcraft Class Talent System"),
    ("thumb-pandaria.jpg", "/story", "World of Warcraft Preview Panel: Mists of Pandaria"),
    ("thumb-annual.jpg", "/shop", "Sign Up for the World of Warcraft Annual Pass and Get Diablo III Free"),
)
_HOME_STORIES = (
    (
        "New Warcraft Fan Art",
        "Zarhym &amp; Nebu",
        "1 day, 10 hours ago",
        "15",
        "story-fanart.jpg",
        'The <a href="/wow/media/screenshots">World of Warcraft Fan Art Section</a> has been updated with five new pieces of fan artwork. Would you like to share your artistic talents with the community? Submit your fan art today!',
        "/wow/news/0",
        "More",
    ),
    (
        "World of Warcraft Annual Pass Update",
        "Blizzard Entertainment",
        "1 day, 14 hours ago",
        "235",
        "story-annual.jpg",
        "The World of Warcraft Annual Pass has been expanded to include more countries and is now available in Russia, Switzerland, Brazil, Mexico, Argentina, Chile and more.*",
        "/shop",
        "More",
    ),
    (
        "BlizzCon 2011 Store Post-Show Sale Begins November 11",
        "Blizzard Entertainment",
        "1 day, 19 hours ago",
        "43",
        "story-blizzcon.jpg",
        "Miss out on picking up that special piece of commemorative BlizzCon loot? Beginning Friday, November 11 (rescheduled from the originally announced date of November 4), we're making select items from the BlizzCon 2011 store available once more to those who joined us for the show in person or via the BlizzCon Virtual Ticket.",
        "/wow/news",
        "Read on Blizzcon.com",
    ),
    (
        "Art Gallery Update",
        "Zarhym &amp; Nebu",
        "2 days, 10 hours ago",
        "5",
        "story-gallery.jpg",
        'We\'ve updated our <a href="/wow/media/screenshots">Trading Card Game art gallery</a> to feature ten new pieces. Each image is taken directly from the official <a href="/wow/">World of Warcraft Trading Card Game</a>. Be sure to give a shout-out to your favorite pieces in the comments.',
        "/wow/media/screenshots",
        "More",
    ),
    (
        "New Wallpaper Available",
        "Zarhym &amp; Nebu",
        "2 days, 12 hours ago",
        "60",
        "story-wallpaper.jpg",
        'We\'ve updated our <a href="/wow/media/wallpapers">BlizzCon Media section</a> with the <a href="/wow/media/wallpapers">BlizzCon 2011 Wallpaper</a>! This key art, created by Glenn Rane for BlizzCon 2011, features a trio of Blizzard notables: Thrall, Diablo, and Sarah Kerrigan, in addition to the peering eyes of the pandaren.',
        "/wow/media/wallpapers",
        "Read on Blizzcon.com",
    ),
    (
        "Guardian Cub Tradable Pet Now Available",
        "Blizzard Entertainment",
        "2 days, 16 hours ago",
        "431",
        "story-cub.jpg",
        'Now available in the <a href="/shop">Pet Store</a>: the new and titanically cute <a href="/shop">Guardian Cub</a> companion. Orphaned by its titan creators, the fledgling Guardian Cub has taken wing to look for a happy home. Adopt one today and it will stay by your side through thick and thin, following your character just about anywhere your adventures take you—even into the skies of Azeroth.',
        "/shop",
        "More",
    ),
    (
        "The Blizzard Charity Auction benefitting St. Jude Children's Research Hospital® Continues",
        "Blizzard Entertainment",
        "3 days, 11 hours ago",
        "68",
        "story-charity.jpg",
        "The Blizzard Charity Auction benefitting St. Jude Children's Research Hospital continues as this week we introduce a new batch of retired server blades. Take a look at the list of recently opened auctions below and bid generously — net proceeds will be donated to help children battling cancer and other deadly diseases.",
        "/wow/news",
        "More",
    ),
    (
        "2011 Pumpkin Contest Winners",
        "Blizzard Entertainment",
        "3 days, 16 hours ago",
        "135",
        "story-pumpkin.jpg",
        'The winners of this year\'s pumpkin-carving contest have been chosen — and they\'re monstrously spectacular. We\'d like to thank everyone who participated this year, and we can\'t wait to see your mad scientist skills in action again next time around. Check out all of the creepy, incredible, and creative winning pumpkins <a href="/wow/media/screenshots">here</a>.',
        "/wow/media/screenshots",
        "More",
    ),
    (
        "Vote For Your Favorite Costume!",
        "Blizzard Entertainment",
        "6 days, 9 hours ago",
        "742",
        "story-costume.jpg",
        'We\'re giving 20 contestants we weren\'t able to recognize at BlizzCon a second chance at sartorial glory, by offering you a chance to vote on your favorites. We\'ve added images of each contestant to a brand-new <a href="/wow/news">Costume Contest Voting Gallery</a>. Each contestant\'s picture is marked with a number. That\'s where you come in; just make note of the number belonging to your favorite costume, then cast your vote in the poll below.',
        "/wow/news",
        "Read on Blizzcon.com",
    ),
    (
        "Public Test Realm Patch 4.3 Notes",
        "Kaivax",
        "6 days, 18 hours ago",
        "13567",
        "story-ptr.jpg",
        'The time for testing out many of the upcoming patch 4.3 features is soon upon us. In this article you\'ll find frequent updates to the official patch 4.3 notes as development continues. You can find a list of the major features we\'ve discussed thus far on our <a href="/forums/">official forums</a>.',
        "/wow/info/patches",
        "More",
    ),
    (
        "Blizzard Art Gallery Update",
        "Zarhym &amp; Nebu",
        "6 days, 18 hours ago",
        "23",
        "story-wotlk.jpg",
        'We\'ve added more pieces to our <a href="/wow/media/screenshots">World of Warcraft: Wrath of the Lich King Art gallery</a>. Have a look at assorted pieces of stunning artwork that reveal an all-new look at the wonders of the Warcraft universe.',
        "/wow/media/screenshots",
        "More",
    ),
)


def home_body(exp, news, realm, user) -> str:
    _ = exp, news, realm, user
    thumbs = []
    for image, href, label in _HOME_THUMBS:
        thumbs.append(
            f'<a class="cata-mini" href="{esc(href)}">'
            f'<img src="{_IMG}/{image}" alt="">'
            f"<span>{label}</span></a>"
        )
    stories = []
    for title, author, when, comments, image, body, href, more in _HOME_STORIES:
        stories.append(
            f'<article class="cata-story">'
            f'<h3><a href="{esc(href)}">{title}</a></h3>'
            f'<p class="cata-by">by <span class="cata-author">{author}</span> '
            f'<span class="cata-when">{when}</span> '
            f'<span class="cata-comments">{comments}</span></p>'
            f'<a class="cata-thumb" href="{esc(href)}"><img src="{_IMG}/{image}" alt=""></a>'
            f"<p>{body}</p>"
            f'<p class="cata-more"><a href="{esc(href)}">{more} ›</a></p>'
            f"</article>"
        )
    return f"""<div class="cata-home">
  <div class="cata-home-main">
    <a class="cata-hero" href="/shop">
      <img src="{_IMG}/hero-annual.jpg" alt="Sign up for the World of Warcraft Annual Pass and get Diablo III free">
      <span class="cata-dots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
    </a>
    <div class="cata-minis">{"".join(thumbs)}</div>
    <div class="cata-news">{"".join(stories)}</div>
    <p class="cata-next"><a href="/wow/news">Next</a></p>
  </div>
  <aside class="cata-rail">
    <a class="cata-play" href="/account/create"><img src="{_IMG}/play-free.jpg" alt="Play it Free"></a>
    <div class="cata-mop-block">
      <a class="cata-mop" href="/story">Mists of Pandaria</a>
      <a class="cata-mop-art" href="/story"><img src="{_IMG}/mop.jpg" alt="Mists of Pandaria"></a>
    </div>
  </aside>
</div>"""


def _guide_races(exp) -> str:
    from ...content import race_facts, races_for
    from ... import assets

    alliance = []
    horde = []
    for slug in races_for(exp):
        name, faction, _city, _blurb = race_facts(exp, slug)
        label = _FORSAKEN.get(slug, name)
        icon = assets.race_icon(exp.id, slug)
        img = f'<img src="{esc(icon)}" alt="">' if icon else ""
        link = f'<a href="/wow/info/races/{esc(slug)}">{img}{esc(label)}</a>'
        if slug in _ALLIANCE or faction == "Alliance":
            alliance.append(link)
        else:
            horde.append(link)
    return (
        "<h3>Races</h3>"
        f'<p class="cata-sidehead">Alliance</p><div class="cata-race-col">{"".join(alliance)}</div>'
        f'<p class="cata-sidehead">Horde</p><div class="cata-race-col">{"".join(horde)}</div>'
    )


def _guide_professions(exp) -> str:
    from ...content import professions_for

    primary = []
    secondary = []
    for name, _desc in professions_for(exp):
        slug = name.lower().replace(" ", "")
        link = f'<a href="/wow/info/professions/{esc(slug)}">{esc(name)}</a>'
        if name in _SECONDARY:
            secondary.append(link)
        else:
            primary.append(link)
    return (
        "<h3>Professions</h3>"
        f'<p class="cata-sidehead">Primary</p><div class="cata-links">{"".join(primary)}</div>'
        f'<p class="cata-sidehead">Secondary</p><div class="cata-links">{"".join(secondary)}</div>'
    )


def guide_body(exp) -> str:
    from ...content import class_facts, classes_for, features_for, intro_blurb
    from ... import assets

    classes = []
    for slug in classes_for(exp):
        name, _armor, _specs, _blurb = class_facts(exp, slug)
        icon = assets.class_icon(exp.id, slug)
        img = f'<img src="{esc(icon)}" alt="">' if icon else ""
        classes.append(
            f'<a href="/wow/info/classes/{esc(slug)}">{img}{esc(name)}</a>'
            f'<a class="cata-tal" href="/wow/info/classes/{esc(slug)}/talents.html">Talents</a>'
        )
    dungeons = "".join(f"<li><strong>{esc(name)}</strong> {esc(text)}</li>" for name, text in _DUNGEONS)
    factions = "".join(f"<li><strong>{esc(name)}</strong> {esc(text)}</li>" for name, text in _FACTIONS)
    features = "".join(f"<li>{esc(line)}</li>" for line in features_for(exp))
    return f"""<div class="cata-guide">
  <p class="cata-crumbs"><a href="/wow/">World of Warcraft</a> › <strong>Game Guide</strong></p>
  <p class="cata-lead">{esc(intro_blurb(exp))}</p>
  <div class="cata-guide-top">
    <a class="cata-begin" href="/wow/info/basics">
      <strong>Beginner's Guide</strong>
      <span>Our complete beginner's guide will teach you everything you need to know to get started.</span>
    </a>
    <p class="cata-guide-note">Races, classes, dungeons, and professions for {esc(exp.name)}. Patch {esc(exp.last_patch)}.</p>
  </div>
  <div class="cata-guide-cols">
    <section>{_guide_races(exp)}</section>
    <section>
      <h3>Dungeons &amp; Raids</h3>
      <ul class="cata-plain">{dungeons}</ul>
      <h3>Factions</h3>
      <ul class="cata-plain">{factions}</ul>
    </section>
    <section>{_guide_professions(exp)}</section>
  </div>
  <section class="cata-guide-more">
    <h3>Classes</h3>
    <div class="cata-class-row">{"".join(classes)}</div>
    <h3>Features</h3>
    <ul class="cata-plain">{features}</ul>
    <p class="cata-guide-jump">
      <a href="/wow/info/basics">New Players</a>
      <a href="/wow/info/classes">Talent Calculators</a>
      <a href="/wow/info/basics/map">World Map</a>
      <a href="/wow/info/patches">Previous Patches</a>
      <a href="/wow/info/races">Races</a>
      <a href="/story">Story</a>
    </p>
  </section>
</div>"""


def news_index(exp) -> str:
    from ...content import news_for

    rows = news_for(exp)
    stories = "".join(_article(exp, i, t, d, b) for i, (t, d, b) in enumerate(rows))
    return f"""<div class="cata-news-index">
  <p class="cata-crumbs"><a href="/wow/">World of Warcraft</a> › <strong>News</strong></p>
  <div class="cata-news">{stories}</div>
</div>"""


def community_body(exp) -> str:
    return f"""<div class="cata-community">
  <p class="cata-crumbs"><a href="/wow/">World of Warcraft</a> › <strong>Community</strong></p>
  <h1>Community</h1>
  <p>Forums, guilds, and pictures from {esc(exp.realm_name)}.</p>
  <ul class="cata-plain">
    <li><a href="/forums/">Forums</a></li>
    <li><a href="/forums/general">General Discussion</a></li>
    <li><a href="/forums/guilds">Guild Recruitment</a></li>
    <li><a href="/forums/realm">{esc(exp.realm_name)} Realm Forum</a></li>
    <li><a href="/wow/media/screenshots">Screenshots</a></li>
    <li><a href="/wow/media/wallpapers">Wallpapers</a></li>
    <li><a href="/story">Story</a></li>
  </ul>
</div>"""


def _forum_conn(ctx: dict):
    from ... import forums

    conn = forums.connect(Path(ctx["data_dir"]))
    forums.seed_if_empty(conn, ctx["exp"])
    return conn, forums


def _recent(conn, exp, limit: int = 8) -> list[tuple]:
    return conn.execute(
        """
        SELECT t.id, t.board, t.title, t.author, t.created
        FROM threads t
        WHERE t.expansion = ?
        ORDER BY t.created DESC, t.id DESC
        LIMIT ?
        """,
        (exp.id, int(limit)),
    ).fetchall()


_FORUM_SECTIONS = (
    (
        "Support",
        (
            ("/support/", "Customer Support", "Blizzard Support Agent moderated forum to discuss and inquire about in-game and account related issues."),
            ("/wow/realmstatus", "Service Status [Read Only]", "Collection of important messages regarding the status of services, such as issues relating to realms."),
            ("/support/", "Technical Support", "For problems installing or patching World of Warcraft, connecting to the realms or crashing during game play."),
            ("/support/", "Mac Technical Support", "For problems installing or patching World of Warcraft, connecting to the realms or crashing while using a Macintosh computer."),
            ("/forums/bugs", "Bug Report", "Found a bug in the game? Help us squash it by reporting it here!"),
            ("/forums/general", "PTR Discussion", "Discuss changes from the latest World of Warcraft Public Test Realms."),
            ("/forums/bugs", "PTR Bug Report", "Submit bugs from the latest World of Warcraft Public Test Realms."),
        ),
    ),
    (
        "Community",
        (
            ("/forums/general", "General Discussion", "Discuss World of Warcraft."),
            ("/forums/general", "Oceanic General Discussion", "To provide a friendly and focused environment for Oceanic players to discuss all aspects of World of Warcraft with one another."),
            ("/forums/guilds", "Guild Recruitment", "Searching for a guild, or do you want to advertise your guild? Come on in!"),
            ("/forums/guilds", "Oceanic Guild Recruitment", "Searching for an Oceanic guild, or do you want to advertise your Oceanic guild? Come on in!"),
            ("/story", "Story Forum", "We invite you to discuss the Warcraft Universe and storylines of Azeroth here."),
            ("/forums/guilds", "Raid and Guild Leadership", "Discuss raid and guild management, guild recruiting practices, and more."),
            ("/forums/general", "World's End Tavern", "Pull up a chair, drink a mug of ale, meet new friends, tell stories, and role-play in this forum."),
        ),
    ),
    (
        "Gameplay and Guides",
        (
            ("/wow/info/basics", "New Player Help and Guides", "New to the World of Warcraft? Ask questions from experienced players and learn more about the adventures that await you!"),
            ("/wow/info", "Quests", "Discussion forum for the many World of Warcraft Quests."),
            ("/forums/professions", "Professions", "Discussion forum for the many World of Warcraft Professions."),
            ("/forums/dungeons", "Dungeons and Raids", "Discuss the instance dungeons in World of Warcraft."),
            ("/forums/guilds", "Achievements and Guild Advancement", "Discussion forum for World of Warcraft Achievements and Guild."),
            ("/forums/ui", "UI and Macro", "Work with other players to create your own special custom interfaces and macros."),
        ),
    ),
    (
        "PvP",
        (
            ("/forums/pvp", "Arenas", "Discuss all aspects of World of Warcraft Arenas with your fellow players."),
            ("/forums/pvp", "Battlegrounds", "Discuss all aspects of Battlegrounds with your fellow players."),
        ),
    ),
    (
        "Class Roles",
        (
            ("/wow/info/classes", "Damage Dealing", "The slash of the sword, a flick of the wand. Show your weapons and discuss the strategy of dealing damage."),
            ("/wow/info/classes", "Healing", "To aid your companions is to see success. Kneel and meditate on the art of healing."),
            ("/wow/info/classes", "Tanking", "A wall unwavering, a leader unshaken. Gather and confer on the craft of tanking."),
        ),
    ),
    (
        "Website Feedback",
        (
            ("/forums/general", "Website Features", "Discuss the new community site features and potential improvements."),
            ("/forums/bugs", "Website Bug Reports", "Report any World of Warcraft Community website bugs here."),
        ),
    ),
)
_CLASS_ORDER = (
    "deathknight", "druid", "hunter", "mage", "paladin",
    "priest", "rogue", "shaman", "warlock", "warrior",
)
_REALM_NAMES = (
    "Aegwynn", "Aerie Peak", "Agamaggan", "Aggramar",
    "Akama", "Alexstrasza", "Alleria", "Altar of Storms",
)


def forum_index_body(ctx: dict) -> str:
    from ... import forums

    exp = ctx["exp"]
    conn, _forums = _forum_conn(ctx)
    try:
        recent = _recent(conn, exp, 12)
    finally:
        conn.close()
    boards = dict(forums.boards_for(exp))
    sections = []
    for heading, cards in _FORUM_SECTIONS:
        bits = []
        for href, label, blurb in cards:
            bits.append(
                f'<a class="cata-board" href="{esc(href)}"><strong>{esc(label)}</strong>'
                f"<span>{esc(blurb)}</span></a>"
            )
        sections.append(
            f'<section><h2 class="cata-cat">{esc(heading)}</h2>'
            f'<div class="cata-boards">{"".join(bits)}</div></section>'
        )
    classes = []
    for slug in _CLASS_ORDER:
        title = boards.get(slug)
        if not title:
            continue
        classes.append(f'<a href="/forums/{esc(slug)}">{esc(title)}</a>')
    if classes:
        sections.append(
            '<section><h2 class="cata-cat">Classes</h2>'
            f'<div class="cata-class-pills">{"".join(classes)}</div></section>'
        )
    realms = []
    for name in _REALM_NAMES:
        realms.append(f'<a href="/forums/realm">{esc(name)}</a>')
    realm_block = (
        '<section class="cata-realms"><h2 class="cata-cat">Realms</h2>'
        '<form class="cata-realm-find" action="/wow/search" method="get">'
        '<input type="text" name="q" aria-label="Search realms" placeholder="">'
        "</form>"
        f'<div class="cata-realm-grid">{"".join(realms)}</div>'
        '<p class="cata-realm-foot"><span>(230 hidden forums)</span> '
        '<a href="/forums/realm">All Realms ›</a></p></section>'
    )
    blizz = []
    for row in recent:
        if "blizzard" not in str(row[3]).lower():
            continue
        blizz.append(
            f'<a href="/forums/{esc(row[1])}/{int(row[0])}"><strong>{esc(row[2])}</strong>'
            f'<span>{esc(row[3])} · {esc(boards.get(row[1], row[1]))}</span></a>'
        )
    latest = ""
    if blizz:
        latest = (
            '<section class="cata-latest"><h2>Latest Blizzard Posts <a href="/forums/general">View all</a></h2>'
            f'<div class="cata-blizz">{"".join(blizz[:3])}</div></section>'
        )
    topics = "".join(
        f'<li><a href="/forums/{esc(row[1])}/{int(row[0])}">{esc(row[2])}</a>'
        f'<span>{esc(boards.get(row[1], row[1]))}</span></li>'
        for row in recent[:8]
    )
    return f"""<div class="cata-forum">
  <p class="cata-crumbs"><a href="/wow/">World of Warcraft</a> › <strong>Forums</strong></p>
  {latest}
  <div class="cata-forum-grid">
    <div>{"".join(sections)}{realm_block}</div>
    <aside><h2 class="cata-cat">Popular Topics</h2><ul class="cata-topics">{topics}</ul>
      <p><a href="/forums/general">Forums Code of Conduct</a></p></aside>
  </div>
</div>"""


def _last_posters(conn, ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    slot = ",".join(str(int(i)) for i in ids)
    rows = conn.execute(
        f"""SELECT p.thread_id, p.author FROM posts p
            JOIN (SELECT thread_id, MAX(id) AS id FROM posts
                  WHERE thread_id IN ({slot}) GROUP BY thread_id) last
              ON last.id = p.id"""
    ).fetchall()
    return {int(row[0]): row[1] for row in rows}


def forum_board_body(ctx: dict, slug: str) -> tuple[str, str] | None:
    from ... import forums

    exp = ctx["exp"]
    title = forums.board_title(exp, slug)
    if not title:
        return None
    qs = ctx.get("qs") or {}
    try:
        page = max(1, int((qs.get("page") or ["1"])[0]))
    except (TypeError, ValueError):
        page = 1
    conn, _forums = _forum_conn(ctx)
    try:
        threads = forums.list_threads(conn, exp, slug)
        posters = _last_posters(conn, [int(row["id"]) for row in threads])
    finally:
        conn.close()
    pages = max(1, (len(threads) + _BOARD_PAGE - 1) // _BOARD_PAGE)
    if page > pages:
        page = pages
    start = (page - 1) * _BOARD_PAGE
    rows = []
    for thread in threads[start : start + _BOARD_PAGE]:
        poster = posters.get(int(thread["id"])) or thread["author"]
        mark = " cata-blz" if "blizzard" in str(thread["author"]).lower() else ""
        rows.append(
            "<tr>"
            f'<td class="cata-subj"><a class="topic{mark}" href="/forums/{esc(slug)}/{int(thread["id"])}">{esc(thread["title"])}</a></td>'
            f"<td>{esc(thread['author'])}</td>"
            f'<td class="num">{esc(thread["replies"])}</td>'
            '<td class="num">—</td>'
            f"<td>{esc(poster)}</td>"
            "</tr>"
        )
    body_rows = "".join(rows) or '<tr><td colspan="5">No threads yet.</td></tr>'
    pager = ""
    if pages > 1:
        links = []
        for number in range(1, pages + 1):
            mark = " on" if number == page else ""
            links.append(f'<a class="{mark.strip()}" href="?page={number}">{number}</a>')
        pager = f'<nav class="cata-pager">{"".join(links)}</nav>'
    user = ctx.get("user")
    if user:
        form = f"""<form id="new-thread" class="cata-post" method="post" action="/forums/{esc(slug)}/new">
  <label>Title <input name="title" required maxlength="120"></label>
  <label>Body <textarea name="body" required rows="6"></textarea></label>
  <button type="submit">Create Thread</button>
</form>"""
        button = '<a class="cata-create" href="#new-thread">Create Thread</a>'
    else:
        form = '<p id="new-thread"><a href="/account/login">Log in</a> to create a thread.</p>'
        button = '<a class="cata-create" href="/account/login">Create Thread</a>'
    html = f"""<div class="cata-boardpage">
  <p class="cata-crumbs"><a href="/wow/">World of Warcraft</a> › <a href="/forums/">Forums</a> › <strong>{esc(title)}</strong></p>
  <p class="cata-board-tools">{button}<span class="cata-views"><span class="on">Simple</span> <span>Advanced</span></span></p>
  <table class="cata-threads">
    <thead><tr><th>Subject</th><th>Author</th><th>Replies</th><th>Views</th><th>Last Poster</th></tr></thead>
    <tbody>{body_rows}</tbody>
  </table>
  <p class="cata-board-tools">{button}</p>
  {pager}
  {form}
</div>"""
    return f"{title} — Forums", html


def _slot(exp, item: dict | None) -> str:
    from ... import assets

    if not item or not item.get("item_id"):
        return '<span class="cata-slot empty"></span>'
    icon = assets.display_icon(exp, item.get("display_id"))
    img = f'<img src="{esc(icon)}" alt="">' if icon else ""
    name = item.get("name") or ""
    return (
        f'<a class="cata-slot" href="/armory/item/{esc(item["item_id"])}" title="{esc(name)}">{img}</a>'
    )


def character_body(exp, char: dict) -> str:
    from ... import talents

    equipped = {}
    for item in char.get("equipment") or []:
        slot = str(item.get("slot") or "")
        if slot:
            equipped[slot] = item
    left = "".join(_slot(exp, equipped.get(name)) for name in _LEFT)
    right = "".join(_slot(exp, equipped.get(name)) for name in _RIGHT)
    weapons = "".join(_slot(exp, equipped.get(name)) for name in _WEAPONS)
    nav = []
    for anchor, label, locked in _PROFILE_NAV:
        lock = '<span class="cata-lock"></span>' if locked else ""
        nav.append(f'<a href="#{esc(anchor)}">{esc(label)}{lock}</a>')
    guild = char.get("guild") or {}
    guild_name = guild.get("name") if isinstance(guild, dict) else ""
    if guild_name:
        guild_line = f'<p class="cata-guild"><a href="/armory/guild/{esc(guild_name)}">{esc(guild_name)}</a></p>'
        guild_block = (
            f'<p><a href="/armory/guild/{esc(guild_name)}">{esc(guild_name)}</a></p>'
        )
    else:
        guild_line = '<p class="cata-guild">No guild</p>'
        guild_block = "<p>No guild.</p>"
    slug = str(char.get("class") or "").lower().replace(" ", "").replace("-", "")
    trees = talents.trees_for(exp, slug) or ()
    tree_line = ", ".join(esc(tree.name) for tree in trees) or "Talent trees open from the class page."
    calc = f'/wow/info/classes/{esc(slug)}/talents.html' if slug else "/wow/info/classes"
    kills = char.get("honorable_kills")
    kill_line = f"<p>Honorable kills: {esc(kills)}</p>" if kills not in (None, "") else ""
    money = char.get("money_text") or ""
    online = "Online" if char.get("online") else "Offline"
    name = char.get("name") or ""
    return f"""<div class="cata-profile">
  <p class="cata-crumbs"><a href="/wow/">World of Warcraft</a> › <a href="/wow/info">Game</a> › <strong>{esc(name)} @ {esc(char.get("realm") or exp.realm_name)}</strong></p>
  <header class="cata-profile-top">
    <div>
      <h1>{esc(name)}</h1>
      {guild_line}
      <p class="cata-ident">{esc(char.get("level"))} {esc(char.get("race"))} {esc(char.get("class"))}, {esc(char.get("realm") or exp.realm_name)}</p>
      <p class="cata-score">{esc(char.get("achievements") or 0)}</p>
    </div>
    <p class="cata-views"><span class="on">Simple</span> <span>Advanced</span> <span>3D</span></p>
  </header>
  <div class="cata-profile-grid">
    <nav class="cata-profile-nav">{"".join(nav)}</nav>
    <div>
      <section id="summary" class="cata-doll">
        <div class="cata-doll-col">{left}</div>
        <div class="cata-figure"><span>{esc(char.get("class") or "")}</span></div>
        <div class="cata-doll-col">{right}</div>
        <div class="cata-weapons">{weapons}</div>
      </section>
      <section id="talents"><h2>Talents &amp; Glyphs</h2><p>{tree_line}</p><p><a href="{calc}">Talent calculator</a></p><p>Glyphs are chosen in the game.</p></section>
      <section id="auctions"><h2>Auctions <span class="cata-lock"></span></h2><p>This character's auctions are private.</p><p><a href="/armory/auctions">Auction House</a></p></section>
      <section id="events"><h2>Events <span class="cata-lock"></span></h2><p>No public events on this profile.</p></section>
      <section id="achievements"><h2>Achievements</h2><p>{esc(char.get("achievements") or 0)} completed.</p></section>
      <section id="statistics"><h2>Statistics</h2>
        <p>Level {esc(char.get("level"))} {esc(char.get("race"))} {esc(char.get("class"))}</p>
        <p>{esc(online)}</p>
        <p>{esc(money)}</p>
      </section>
      <section id="reputation"><h2>Reputation</h2><p>Reputation is kept on the character in the game.</p></section>
      <section id="pvp"><h2>PvP</h2>{kill_line}<p><a href="/wow/pvp/rankings">PvP Rankings</a></p></section>
      <section id="activity"><h2>Activity Feed</h2><p>No recent activity on this profile.</p></section>
      <section id="guild"><h2>Guild</h2>{guild_block}</section>
      <p class="cata-findchar">Find {esc(name)}: <a href="/wow/search?q={esc(name)}">Search</a></p>
    </div>
  </div>
</div>"""


def item_body(exp, item: dict) -> str:
    from ... import assets

    name = item.get("name") or "Item"
    hand, kind = _gear_kind(item)
    quality = str(item.get("quality") or item.get("Quality") or "1")
    icon = assets.display_icon(exp, item.get("display_id")) if exp is not None else ""
    img = f'<img src="{esc(icon)}" alt="">' if icon else ""
    bits = []
    if hand:
        bits.append(f'<p class="cata-hand">{esc(hand)}</p>')
    if kind:
        bits.append(f'<p class="cata-kind">{esc(kind)}</p>')
    bits.append("<p>Damage <span>—</span></p>")
    bits.append("<p>Speed <span>—</span></p>")
    bits.append("<p>Durability <span>—</span></p>")
    level = item.get("ItemLevel")
    req = item.get("RequiredLevel")
    if req not in (None, ""):
        bits.append(f"<p>Requires Level {esc(req)}</p>")
    if level not in (None, ""):
        bits.append(f"<p>Item Level {esc(level)}</p>")
    sell = item.get("SellPrice")
    buy = item.get("BuyPrice")
    if sell not in (None, ""):
        bits.append(f"<p>Sell Price {_coins(sell)}</p>")
    crumb_mid = ""
    if kind:
        crumb_mid = f" › {esc(kind)}"
        if hand:
            crumb_mid = f" › Weapon › {esc(kind)}"
    entry = item.get("entry") or ""
    return f"""<div class="cata-item">
  <p class="cata-crumbs"><a href="/wow/">World of Warcraft</a> › <a href="/armory/">Items</a>{crumb_mid} › <strong>{esc(name)}</strong></p>
  <div class="cata-tip">
    <div class="cata-tip-icon">{img}</div>
    <div>
      <h1 class="q{esc(quality)}">{esc(name)}</h1>
      {"".join(bits)}
    </div>
    <p class="cata-tip-side"><a href="/armory/auctions">Search for this item in the Auction House</a></p>
    <p class="cata-tip-side"><a href="/wow/info/professions/enchanting">Disenchanting requires Enchanting</a></p>
  </div>
  <p class="cata-item-tabs"><span class="on">Cost and Facts</span> <a href="/wow/info/professions/enchanting">Disenchants Into</a></p>
  <table class="cata-facts">
    <thead><tr><th>Sell Price</th><th>Buy Back Price</th><th>Faction</th><th>Attributes</th></tr></thead>
    <tbody><tr>
      <td>{_coins(sell) if sell not in (None, "") else "—"}</td>
      <td>{_coins(buy) if buy not in (None, "") else "—"}</td>
      <td>—</td>
      <td>—</td>
    </tr></tbody>
  </table>
  <h2>Comments</h2>
  <p>Talk about this item on the <a href="/forums/general">forums</a>.</p>
  <p class="cata-item-id">Item #{esc(entry)}</p>
</div>"""


def search_body(ctx: dict) -> str:
    from ... import armory, search as site_search

    exp = ctx["exp"]
    qs = ctx.get("qs") or {}
    q = (qs.get("q") or [""])[0]
    kind = (qs.get("kind") or ["all"])[0]
    if not q.strip():
        return """<div class="cata-search">
  <h1>Search</h1>
  <p>Search characters, items, forums and more.</p>
</div>"""
    hits = site_search.search(ctx.get("labcfg"), exp, Path(ctx["data_dir"]), q, "site")
    characters = []
    arena = []
    store_error = armory.character_store(ctx.get("labcfg"), exp)
    extra = []
    if not store_error:
        characters, store_error = armory.search_with_status(ctx.get("labcfg"), exp, q)
        needle = q.casefold()
        arena = [row for row in armory.arena_ladder(ctx.get("labcfg"), exp) if needle in str(row.get("name") or "").casefold()]
        extra = site_search.search(ctx.get("labcfg"), exp, Path(ctx["data_dir"]), q, "encyclopedia")
    seen = set()
    merged = []
    for hit in list(hits) + list(extra):
        href = hit.get("href") or ""
        if href in seen:
            continue
        seen.add(href)
        merged.append(hit)
    forums = [hit for hit in merged if hit.get("kind") in ("thread", "forum")]
    pages = [hit for hit in merged if hit.get("kind") not in ("thread", "forum")]
    guilds: list[dict] = []
    counts = {
        "all": len(merged) + len(characters) + len(arena) + len(guilds),
        "arena": len(arena),
        "characters": len(characters),
        "forums": len(forums),
        "guilds": len(guilds),
    }

    def tab(key: str, label: str) -> str:
        mark = " on" if kind == key else ""
        href = f"/wow/search?q={esc(q)}&kind={esc(key)}"
        return f'<a class="{mark.strip()}" href="{href}">{esc(label)} ({counts[key]})</a>'

    def cards(rows: list[dict]) -> str:
        if not rows:
            return "<p>No results.</p>"
        bits = []
        for hit in rows:
            bits.append(
                '<article class="cata-hit">'
                f'<a href="{esc(hit.get("href"))}">{esc(hit.get("title"))}</a>'
                f'<p>{esc(hit.get("summary"))}</p></article>'
            )
        return "".join(bits)

    char_bits = []
    for row in characters:
        char_bits.append(
            f'<li><a href="/armory/character/{esc(row.get("name"))}">{esc(row.get("name"))}</a>'
            f' <span>Level {esc(row.get("level"))} {esc(row.get("race"))} {esc(row.get("class"))}'
            f' {esc(row.get("realm") or "")}</span></li>'
        )
    if store_error and not characters:
        char_html = f"<p>{esc(store_error)}</p>"
    elif char_bits:
        char_html = f'<ul class="cata-hits">{"".join(char_bits)}</ul>'
    else:
        char_html = "<p>No characters found.</p>"
    if arena:
        arena_html = '<ul class="cata-hits">' + "".join(
            f'<li><span>{esc(row.get("name"))}</span> <span>{esc(row.get("type"))} · Rating {esc(row.get("rating"))}</span></li>'
            for row in arena
        ) + "</ul>"
    else:
        arena_html = "<p>No arena teams found.</p>"
    guild_html = "<p>No guilds found.</p>"
    show_main = kind in ("all", "forums")
    show_side = kind in ("all", "arena", "characters", "guilds")
    main = ""
    if show_main:
        main = f'<div class="cata-search-main"><h2>Forums</h2>{cards(forums)}<h2>Pages</h2>{cards(pages)}</div>'
    side = ""
    if show_side and kind in ("all", "arena"):
        side += f'<section><h2>Arena team results for {esc(q)}</h2>{arena_html}</section>'
    if show_side and kind in ("all", "characters"):
        side += f"<section><h2>Character results for {esc(q)}</h2>{char_html}</section>"
    if show_side and kind in ("all", "guilds"):
        side += f"<section><h2>Guild results for {esc(q)}</h2>{guild_html}</section>"
    return f"""<div class="cata-search">
  <h1>Search results for <strong>{esc(q)}</strong></h1>
  <p class="cata-sort">Sort by: <strong>Relevance</strong> <span>Date</span> <span>Popularity</span></p>
  <nav class="cata-search-tabs">{tab("all", "All")}{tab("arena", "Arena Teams")}{tab("characters", "Characters")}{tab("forums", "Forums")}{tab("guilds", "Guilds")}</nav>
  <div class="cata-search-grid">{main}<aside>{side}</aside></div>
</div>"""


def _account_full(path: str, ctx: dict) -> str | None:
    from ... import accounts
    from ...account_ui.cata import render as account_render

    user = ctx.get("user") or ""
    if path == "/account/password" and not user:
        return None
    if path == "/account/create":
        mode = "create"
    elif path == "/account/password":
        mode = "password"
    elif path == "/account/login":
        mode = "login"
    else:
        mode = "summary" if user else "login"
    characters: list = []
    cfg = ctx.get("labcfg")
    if user and cfg is not None:
        try:
            characters = accounts.account_summary(cfg, ctx["exp"], user).get("characters") or []
        except Exception:
            characters = []
    inner = account_render(
        ctx["exp"],
        user=user,
        error="",
        notice="",
        mode=mode,
        email="",
        characters=characters,
        login_kind="account",
        separate_game_name=False,
    )
    bar = ""
    if mode != "login":
        who = (
            f'<a href="/account/logout">Log Out</a>'
            if user
            else '<a href="/account/login">Log in</a> or <a href="/account/create">Create an Account</a>'
        )
        bar = f"""<header class="bnet-bar">
  <a class="bnet-brand" href="/account/">Battle.net</a>
  <form class="bnet-find" action="/wow/search" method="get">
    <input type="text" name="q" aria-label="Search Battle.net" placeholder="Search Battle.net">
    <button type="submit">Search</button>
  </form>
  <nav class="bnet-links">{who}
    <a href="/account/">Account</a>
    <a href="/support/">Support</a>
    <a class="bnet-explore" href="/wow/">Explore</a>
  </nav>
</header>"""
    titles = {
        "login": "Log In",
        "create": "Account Creation",
        "summary": "Account Home",
        "password": "Change Password",
    }
    return document(
        f"{titles.get(mode, 'Account')} — Battle.net",
        styles("cata"),
        f"cata acct-bnet mode-{mode}",
        bar + inner,
    )


def full(path: str, ctx: dict) -> str | None:
    if path in ("/account", "/account/login", "/account/create", "/account/password"):
        return _account_full(path, ctx)
    return None


def take(path: str, ctx: dict) -> tuple[str, str] | None:
    exp = ctx["exp"]
    if path in ("/wow/info", "/wow/info/introduction"):
        return "Game Guide", guide_body(exp)
    if path == "/wow/news":
        return "News", news_index(exp)
    if path == "/community":
        return "Community", community_body(exp)
    if path == "/account/services" and not ctx.get("user"):
        return "Character Services", (
            "<h2>Character Services</h2>"
            "<p>Log in to change a name, a faction, or a guild.</p>"
            '<p><a href="/account/login">Log In</a></p>'
        )
    if path == "/wow/search":
        return "Search", search_body(ctx)
    if path == "/forums":
        return "Forums", forum_index_body(ctx)
    if path.startswith("/forums/") and path.count("/") == 2:
        slug = path.rsplit("/", 1)[-1]
        if slug and not slug.isdigit():
            return forum_board_body(ctx, slug)
    if path.startswith("/armory/character/"):
        from ... import armory

        name = path.rsplit("/", 1)[-1]
        if not name:
            return None
        char = armory.get_character(ctx.get("labcfg"), exp, name)
        if not char:
            return None
        return f"{char['name']} — Game", character_body(exp, char)
    if path.startswith("/armory/item/"):
        from ... import armory

        raw = path.rsplit("/", 1)[-1]
        try:
            item_id = int(raw)
        except ValueError:
            return None
        item = armory.get_item(ctx.get("labcfg"), exp, item_id)
        if not item:
            return None
        return f"{item.get('name') or 'Item'} — Items", item_body(exp, item)
    return None
