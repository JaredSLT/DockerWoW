"""Paths from the 10 Nov 2006 left menu that are not already a live tool.

A saved capture is preferred by the caller. These fragments are the link
lists and the few realm rules the capture does not contain.
"""

from __future__ import annotations

import re
from functools import lru_cache
from html import escape
from pathlib import Path

from ..content import CLASS_INFO, RACE_INFO

_ARCHIVE_INFO = Path(__file__).resolve().parents[2] / "static" / "archive" / "vanilla" / "info" / "index.html"

_EXACT = {
    "/realmstatus": "/wow/realmstatus",
    "/pvp": "/wow/pvp/rankings",
    "/pvp/index.html": "/wow/pvp/rankings",
    "/info/classes/talent-index": "/wow/info/classes",
    "/info/classes": "/wow/info/classes",
    "/info/races": "/wow/info/races",
    "/info/professions": "/wow/info/professions",
    "/info/flashmap": "/wow/info/basics/map",
    "/info/basics/map.html": "/wow/info/basics/map",
    "/info/underdev/implemented": "/wow/info/patches",
    "/patchnotes": "/wow/info/patches",
    "/patchnotes/": "/wow/info/patches",
    "/downloads/screenshots": "/wow/media/screenshots",
    "/downloads/wallpapers.html": "/wow/media/wallpapers",
    "/downloads/wallpapers": "/wow/media/wallpapers",
    "/downloads/wallpapers/fan-wallpapers": "/wow/media/wallpapers",
    "/news/wow-news-06-2006.html": "/wow/news",
    "/misc/awards.html": "/wow/info/awards",
    "/misc/features.html": "/wow/info/features",
    "/account/character-move.html": "/account/services",
    "/account/character-transfer-intro.html": "/account/services",
    "/shop": "/shop",
}

_EVENTS = (
    "New Years",
    "Lunar Festival",
    "Love is in the Air",
    "Noblegarden",
    "Children's Week",
    "Midsummer Fire Festival",
    "Hallow's End",
    "Winter Veil",
    "AQ War Effort",
    "Battlegrounds Holiday",
    "Darkmoon Faire",
    "Fishing Extravaganza",
    "Gurubashi Arena",
    "Elemental Invasions",
    "The Scourge Invasion",
)

_BC_LINKS = (
    ("/burningcrusade/faq.html", "System Requirements"),
    ("/burningcrusade/townhall/lookingforgroup.html", "Looking for Group"),
    ("/burningcrusade/townhall/collectors.html", "Collector's Edition"),
    ("/burningcrusade/townhall/talents-and-spells.html", "Talents and Spells"),
    ("/burningcrusade/townhall/outlandmap.html", "Map of Outland"),
    ("/burningcrusade/townhall/story.html", "The Story So Far"),
    ("/burningcrusade/townhall/cavernsoftime.html", "Caverns of Time"),
    ("/burningcrusade/townhall/classcombo.html", "Shaman and Paladins"),
    ("/downloads/movies.html", "Eastern Plaguelands PvP Trailer"),
    ("/info/classes/rogue/talents.html", "Rogue Talent Revamp"),
    ("/info/items/armorsets/", "Tier 3 Raid Armor"),
)

_COMMUNITY = (
    ("/community/comics.html", "Comics"),
    ("/community/communitylinks.html", "Community Spotlight"),
    ("/contests/", "Contests"),
    ("/community/guildrelations.html", "Guild Relations"),
    ("/community/reallifeevents.html", "Real-Life Events"),
    ("/community/fanart", "Fan Art"),
    ("/downloads/wallpapers/fan-wallpapers", "Fan Wallpapers"),
    ("/community/warcraftweekly.html", "Warcraft Weekly"),
    ("/community/insider", "World of Warcraft Insider"),
)

_MEDIA = (
    ("/downloads/screenshots", "Screenshots"),
    ("/downloads/movies.html", "Movies"),
    ("/downloads/sounds.html", "Music"),
    ("/downloads/wallpapers.html", "Wallpapers"),
    ("/downloads/other-downloads.html", "Other Downloads"),
    ("/gadgetzan/archives.html", "Gadgetzan Times"),
    ("/shop", "Blizzard Store"),
)

_PVP_LINKS = (
    ("/pvp/", "PvP Rankings"),
    ("/pvp/ranks.html", "Ranks"),
    ("/pvp/honorguide.html", "Honor System"),
    ("/pvp/honor-system-faq.html", "Honor FAQ"),
    ("/pvp/rewards-weapons.html", "Weapons"),
    ("/pvp/rewards-mounts.html", "Mounts"),
    ("/info/items/armorsets/", "Armor Sets"),
    ("/pvp/battlegrounds/", "Battlegrounds"),
    ("/pvp/battlegrounds/info-alteracvalley.html", "Alterac Valley"),
    ("/pvp/battlegrounds/info-arathi.html", "Arathi Basin"),
    ("/pvp/battlegrounds/info-warsong.html", "Warsong Gulch"),
)


def _links(pairs: tuple[tuple[str, str], ...]) -> str:
    items = "".join(f'<li><a href="{escape(href, quote=True)}">{escape(text)}</a></li>' for href, text in pairs)
    return f"<ul>{items}</ul>"


def _page(title: str, inner: str) -> tuple[str, str]:
    return title, inner


def rewrite(path: str) -> str:
    """Map a 2006 path onto a handler that already exists."""
    if path in _EXACT:
        return _EXACT[path]
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "info" and parts[1] == "races":
        slug = parts[2].removesuffix(".html")
        if slug in RACE_INFO:
            return f"/wow/info/races/{slug}"
    if len(parts) >= 3 and parts[0] == "info" and parts[1] == "classes":
        slug = parts[2].removesuffix(".html")
        if slug in CLASS_INFO:
            rest = "/".join(parts[3:])
            tail = f"/{rest}" if rest else ""
            return f"/wow/info/classes/{slug}{tail}"
    if len(parts) >= 3 and parts[0] == "info" and parts[1] == "professions":
        slug = parts[2].removesuffix(".html")
        if slug not in {"basics", "intro", "professionlinks"}:
            return f"/wow/info/professions/{slug}"
    return path


@lru_cache(maxsize=1)
def _guide_links() -> tuple[tuple[str, str], ...]:
    if not _ARCHIVE_INFO.is_file():
        return ()
    text = _ARCHIVE_INFO.read_text(encoding="utf-8", errors="replace")
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for href, label in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.I | re.S):
        href = href.split("#", 1)[0].split("?", 1)[0]
        if not href.startswith("/"):
            continue
        label = re.sub(r"<[^>]+>", "", label)
        label = re.sub(r"\s+", " ", label).strip()
        if not label or href in seen:
            continue
        seen.add(href)
        found.append((href.rstrip("/") or "/", label))
    return tuple(found)


def _title_for(path: str) -> str:
    key = path.rstrip("/") or "/"
    for href, label in _guide_links():
        if href == key or href == path:
            return label
    leaf = key.rsplit("/", 1)[-1].removesuffix(".html")
    leaf = leaf.replace("-", " ").replace("_", " ")
    return leaf.title() if leaf else "World of Warcraft"


def _siblings(path: str) -> tuple[tuple[str, str], ...]:
    key = path.rstrip("/")
    parent = key.rsplit("/", 1)[0] or "/"
    rows = []
    for href, label in _guide_links():
        if href == key:
            continue
        if href.startswith(parent + "/") or href == parent:
            rows.append((href if href.startswith("/") else "/" + href, label))
    return tuple(rows[:40])


def special(path: str) -> tuple[str, str] | None:
    """Hand-written destinations. None lets a capture or the guide list answer."""
    key = path.rstrip("/") or "/"
    if key in {"/loginsupport/password.html", "/loginsupport/password", "/loginsupport"}:
        return _page(
            "Retrieve Password",
            "<p>There is no emailed password reset. Sign in and change the password here.</p>"
            '<p><a href="/account/login">Log In</a> · <a href="/account/password">Change Password</a></p>',
        )
    if key in {"/account/parental-control-schedule.html", "/account/parental-control-schedule"}:
        return _page(
            "Parental Controls",
            "<p>This realm does not enforce a parental-control schedule.</p>"
            '<p><a href="/account/">Manage Account</a></p>',
        )
    if key in {"/ptr", "/ptr/index.html"}:
        return _page(
            "Public Test Realm",
            '<p>There is no public test realm on this server.</p>'
            '<p><a href="/realmstatus/">Realm Status</a></p>',
        )
    if key in {"/account/recruit-a-friend.html", "/account/recruit-a-friend"}:
        return _page(
            "Recruit a Friend",
            "<p>This realm does not sell game time, so the Recruit a Friend grant is not applied.</p>"
            '<p><a href="/account/create">Create Account</a></p>',
        )
    if key == "/support/jobs":
        return _page("Jobs", "<p>There is no application form on this page.</p>")
    if key in {
        "/support/account",
        "/support/billing",
        "/support/tech",
        "/support/ingame",
        "/support/policies",
        "/support/tools",
    }:
        titles = {
            "/support/account": "Account Administration",
            "/support/billing": "Billing and Account",
            "/support/tech": "Technical Support",
            "/support/ingame": "In-Game Support",
            "/support/policies": "Policies",
            "/support/tools": "Support Tools",
        }
        return _page(titles[key], '<p><a href="/support/">Customer Support</a></p>')
    if key in {"/wareffort/servers.html", "/wareffort/servers", "/wareffort"}:
        return _page(
            "War Effort Rankings",
            "<p>This realm has no war-effort table.</p>"
            '<p><a href="/info/underdev/">Under Development</a></p>',
        )
    if key in {"/press", "/press/061109.shtml"}:
        return _page(
            "Press Releases",
            "<p>Blizzard is proud to announce that World of Warcraft: The Burning Crusade will be in stores "
            "nationwide starting on January 16, 2007. Closed beta testing of the expansion continues until launch.</p>"
            '<p><a href="/misc/awards.html">Awards and Honors</a></p>',
        )
    if key in {"/legal", "/policy"}:
        title = "Legal Documents" if key == "/legal" else "Policies"
        return _page(title, '<p><a href="/support/policies">Policies</a></p>')
    if key in {"/burningcrusade", "/burningcrusade/townhall"}:
        return _page("The Burning Crusade", _links(_BC_LINKS))
    if key == "/community":
        return _page("Community", _links(_COMMUNITY))
    if key == "/trailer":
        return _page("Cinematic Trailer", '<p><a href="/downloads/movies.html">Movies</a></p>')
    if key == "/downloads":
        return _page("Downloads", _links(_MEDIA))
    if key in {"/contests", "/community/comics.html"}:
        return _page("Contests" if key == "/contests" else "Comics", _links(_COMMUNITY))
    if key in {"/calendar", "/info/events/calendar"}:
        items = "".join(f"<li>{escape(name)}</li>" for name in _EVENTS)
        return _page("Events Calendar", f"<ul>{items}</ul>")
    if key in {"/pvp/flash-rewards", "/pvp/battlegrounds"}:
        return _page("PvP", _links(_PVP_LINKS))
    if key in {"/info/encyclopedia", "/info/encyclopedia/index.xml"}:
        return _page(
            "Encyclopedia",
            '<form action="/wow/search" method="get">'
            '<input type="hidden" name="searchType" value="encyclopedia">'
            '<label>Search items, races, and classes <input type="text" name="q"></label> '
            '<button type="submit">Search</button></form>',
        )
    if key == "/info/items/armorsets":
        return _page("Armor Sets", '<p><a href="/info/items/armorsets/index.html">Tier 3 Raid Armor</a></p>' + _links(_PVP_LINKS))
    if key in {"/downloads/movies.html", "/downloads/sounds.html", "/downloads/other-downloads.html", "/gadgetzan/archives.html"}:
        return _page(_title_for(key), _links(_MEDIA))
    if key in {
        "/community/communitylinks.html",
        "/community/guildrelations.html",
        "/community/reallifeevents.html",
        "/community/fanart",
        "/community/warcraftweekly.html",
        "/community/insider",
    }:
        return _page(_title_for(key) if key != "/community/insider" else "World of Warcraft Insider", _links(_COMMUNITY))
    if key.startswith("/burningcrusade/"):
        return _page(_title_for(key), _links(_BC_LINKS))
    if key.startswith("/pvp/"):
        return _page(_title_for(key), _links(_PVP_LINKS))
    if key.startswith("/info/") or key.startswith("/misc/") or key.startswith("/downloads/"):
        sibs = _siblings(path)
        title = _title_for(path)
        if sibs:
            return _page(title, _links(sibs))
        return _page(title, "")
    return None
