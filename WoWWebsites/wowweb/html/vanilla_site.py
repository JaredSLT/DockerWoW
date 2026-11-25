"""November 2006 worldofwarcraft.com documents.

The homepage is the captured new-hp page. Other vanilla pages reuse that
page's left menu and iron frame. Burning Crusade and Wrath do not use this.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from html import escape
from pathlib import Path

from .. import assets
from ..catalog import Expansion

ROOT = Path(__file__).resolve().parents[2]
HOME_FILE = ROOT / "references" / "vanilla" / "home.html"
ARCHIVE = ROOT / "static" / "archive" / "vanilla"

_CLASS_STYLE = (
    "font-weight:bold; text-decoration: none; font-family:arial,comic sans ms,technical; "
    "font-size: 11px; position: relative; left: -3px; "
    "background-image:url('/new-hp/images/menu/mainmenu/bullet-trans-indent-bg.gif'); "
    "width:139px; height:15px; padding:0; margin:0; border:0; padding-left:10px;"
)
_CLASS_LINKS = (
    ("/forums/warrior", "Warrior"),
    ("/forums/paladin", "Paladin"),
    ("/forums/hunter", "Hunter"),
    ("/forums/rogue", "Rogue"),
    ("/forums/priest", "Priest"),
    ("/forums/shaman", "Shaman"),
    ("/forums/mage", "Mage"),
    ("/forums/warlock", "Warlock"),
    ("/forums/druid", "Druid"),
)

# Longer prefixes first. Off-site hosts in the capture become local paths.
_REWRITES = (
    ("http://forums.worldofwarcraft.com/board.html?forumId=10001", "/forums/general"),
    ("http://forums.worldofwarcraft.com/#classes", "/forums/#classes"),
    ("http://forums.worldofwarcraft.com/realmforums.shtml", "/forums/realm"),
    ("http://forums.worldofwarcraft.com/board.html?forumId=11123", "/forums/guilds"),
    ("http://forums.worldofwarcraft.com/board.html?forumId=11124", "/forums/guildrelations"),
    ("http://forums.worldofwarcraft.com/board.html?forumId=11110&sid=1", "/forums/support"),
    ("http://forums.worldofwarcraft.com/", "/forums/"),
    ("http://signup.worldofwarcraft.com/", "/account/create"),
    ("https://signup.worldofwarcraft.com/", "/account/create"),
    ("http://shop.blizzard.com/", "/shop"),
    ("http://www.blizzard.com/press/", "/press/"),
    ("http://www.blizzard.com/market.shtml", "/shop"),
    ("http://www.blizzard.com/support/wowindex/", "/support/"),
    ("http://www.blizzard.com/support/wowaa/", "/support/account"),
    ("http://www.blizzard.com/support/wowbilling/?id=abl01897p", "/support/billing"),
    ("http://www.blizzard.com/support/wowbilling/?id=abl01917p", "/account/parental-control-schedule.html"),
    ("http://www.blizzard.com/support/wowbilling/", "/support/billing"),
    ("http://www.blizzard.com/support/wowgm/?id=agm01712p", "/support/policies"),
    ("http://www.blizzard.com/support/wowgm/", "/support/ingame"),
    ("http://www.blizzard.com/support/wow/?id=aww01669p", "/support/tools"),
    ("http://www.blizzard.com/support/wow/", "/support/tech"),
    ("http://www.blizzard.com/inblizz/fanart/page1.shtml", "/community/fanart"),
    ("http://www.blizzard.com/inblizz/fanart/", "/community/fanart"),
    ("http://www.blizzard.com/jobopp/", "/support/jobs"),
    ("http://www.blizzard.com/privacy.shtml", "/legal/"),
    ("http://www.blizzard.com/wow/ssotd/screenshot.aspx", "/downloads/screenshots"),
    ("http://newsletter.vugames.com/bz0806nl01/", "/community/insider"),
    ("http://subscribe.blizzard.com/", "/community/insider"),
    ("https://login.blizzard.fileplanet.com/login.aspx?o=login&d=fileplanet&r=http://www.fileplanet.com/blizzard_promotion/wow_raf.htm", "/account/create"),
    ("http://www.worldofwarcraft.com", ""),
    ("https://www.worldofwarcraft.com", ""),
    ("http://www.blizzard.com", "/wow/"),
    (
        "http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash",
        "/downloads/",
    ),
)

_INFO_CAPTURES = {
    "/info": "info/index.html",
    "/wow/info": "info/index.html",
    "/wow/info/introduction": "info/index.html",
}

# These pages must state a realm limit, or they are a live tool. A saved
# capture must not replace them.
_SKIP_CAPTURE = {
    "/account",
    "/ptr",
    "/loginsupport",
    "/loginsupport/password",
    "/loginsupport/password.html",
    "/account/parental-control-schedule",
    "/account/parental-control-schedule.html",
    "/account/recruit-a-friend",
    "/account/recruit-a-friend.html",
    "/wareffort",
    "/wareffort/servers",
    "/wareffort/servers.html",
    "/support/jobs",
}


@lru_cache(maxsize=1)
def _home_raw() -> str:
    return HOME_FILE.read_text(encoding="utf-8", errors="replace")


def _split_home(raw: str) -> tuple[str, str]:
    """Cut the homepage around the center column.

    The closer starts just after that column's table, so the statue and the
    iron frame stay attached to the same row as the left menu.
    """
    start = raw.index('<div id="mainWrapper">')
    statue = raw.index('alt="statue"')
    end_table = raw.rindex("</table>", 0, statue)
    return raw[:start], raw[end_table + len("</table>") :]


def screenshot_of_the_day(exp: Expansion) -> str:
    shots = assets.screenshots(exp.id)
    if shots:
        return shots[0][0]
    return "/static/img/ssotd-elwynn.jpg"


def _class_menu() -> str:
    rows = []
    for href, label in _CLASS_LINKS:
        rows.append(
            f'<div style="{_CLASS_STYLE}">&nbsp;&nbsp;'
            f'<a class="menuFiller" href="{href}">{label}</a></div>'
        )
    return "".join(rows)


def _ladder_json(rows: list[dict]) -> str:
    payload = []
    for row in rows[:10]:
        payload.append({"name": str(row.get("name") or ""), "kills": str(row.get("kills") or "0")})
    return json.dumps(payload).replace("<", "\\u003c")


def _inject_scripts(html: str, rows: list[dict], extra_links: str = "") -> str:
    flash = '<script type="text/javascript">var MM_FlashCanPlay = false;</script>\n'
    extra = (
        '<link rel="stylesheet" href="/static/css/forums.css">\n'
        '<link rel="stylesheet" href="/static/css/account-vanilla.css">\n'
        '<link rel="stylesheet" href="/static/css/vanilla-local.css">\n'
        f'<script type="text/javascript">window.VANILLA_PVP = {_ladder_json(rows)};</script>\n'
        '<script type="text/javascript" src="/static/js/vanilla.js"></script>\n'
        '<script type="text/javascript" src="/static/js/site.js"></script>\n'
        f"{extra_links}"
    )
    needle = re.compile(
        r'<script\b[^>]*\bsrc="/new-hp/js/functions\.js"[^>]*>\s*</script>',
        re.I,
    )
    if needle.search(html):
        html = needle.sub(lambda match: flash + match.group(0) + "\n" + extra, html, count=1)
    elif "</head>" in html:
        html = html.replace("</head>", flash + extra + "</head>", 1)
    return html


def patch_document(
    html: str,
    *,
    rows: list[dict],
    ssotd: str,
    dev: bool,
    user: str | None,
    exp: Expansion,
    extra_links: str = "",
) -> str:
    if "<body>" in html:
        html = html.replace("<body>", '<body class="vanilla gen1">', 1)
    html = re.sub(r";jsessionid=[A-Za-z0-9.]+", "", html)
    marker = 'href="http://forums.worldofwarcraft.com/#classes">Class Forums</a>'
    if 'href="/forums/warrior"' not in html and marker in html:
        end = html.find("</div>", html.find(marker))
        if end != -1:
            end += len("</div>")
            html = html[:end] + _class_menu() + html[end:]
    html = re.sub(r"http://shop\.blizzard\.com[^\"'\s<]*", "/shop", html)
    html = re.sub(
        r"http://www\.blizzard\.com/wow/(?:ssotd/)?screenshot\.aspx[^\"'\s<]*",
        "/downloads/screenshots",
        html,
    )
    html = re.sub(
        r"http://www\.blizzard\.com/inblizz/fanart[^\"'\s<]*",
        "/community/fanart",
        html,
    )
    html = re.sub(
        r"http://forums\.worldofwarcraft\.com/thread\.html[^\"'\s<]*",
        "/forums/general",
        html,
    )
    for old, new in _REWRITES:
        html = html.replace(old, new)
    if not (ARCHIVE / "new-hp/images/learnmore.gif").is_file():
        html = re.sub(
            r"<img src = /new-hp/images/learnmore\.gif border=0 alt=([^>]*)>",
            r'<span class="vanilla-redbtn">\1</span>',
            html,
        )
    html = re.sub(
        r"<iframe\b[^>]*ads\.blizzard\.com.*?</iframe>",
        '<a href="/contests/">Contests</a>',
        html,
        flags=re.I | re.S,
    )
    html = re.sub(
        r"<noscript>\s*<a\b[^>]*ads\.blizzard\.com.*?</noscript>",
        "",
        html,
        flags=re.I | re.S,
    )
    html = re.sub(
        r"<script\b[^>]*src=['\"]http://ads\.blizzard\.com[^'\"]*['\"][^>]*>\s*</script>",
        "",
        html,
        flags=re.I,
    )
    safe_shot = ssotd.replace("'", "")
    html = re.sub(
        r'document\.getElementById\("ssotdContainer"\)\.innerHTML\s*=\s*.*?;',
        'document.getElementById("ssotdContainer").innerHTML = '
        f'\'<a href="/downloads/screenshots"><img src="{safe_shot}" width="195" height="151" '
        'border="0" alt="Screenshot of the Day"></a>\';',
        html,
        count=1,
        flags=re.S,
    )
    html = html.replace(
        '<option value="">Select a Realm</option>',
        '<option value="">Select a Realm</option><option value="Vanilla" selected>Vanilla</option>',
        1,
    )
    html = _inject_scripts(html, rows, extra_links)
    if user:
        who = (
            f'<div class="who" style="color:#FCEAC6;font:11px Arial;position:absolute;right:8px;top:0;">'
            f'Signed in as <strong>{escape(user)}</strong> · <a href="/account/logout">Log Out</a></div>'
        )
        html = html.replace('id="countryDropDown"></div>', 'id="countryDropDown"></div>' + who, 1)
    if dev:
        note = (
            f"Last patch {escape(exp.last_patch)} · {escape(exp.last_patch_date)} · "
            f"Local realm {escape(exp.realm_name)} · Visual source {escape(exp.snapshot)} · "
            "Not affiliated with Blizzard Entertainment."
        )
        html = html.replace(
            '<div id="ironFrame">',
            f'<p class="local-note" style="color:#8e8e8e;text-align:center;font:11px Arial">{note}</p>'
            '<div id="ironFrame">',
            1,
        )
    return html


def home_document(exp: Expansion, rows: list[dict], ssotd: str, dev: bool, user: str | None) -> str:
    """April 2006 community home. The archived November shell is not this page."""
    from .era.vanilla import home_body, shell

    realm = {"up": True, "pvp": rows, "ssotd": ssotd}
    body = home_body(exp, [], realm, user)
    return shell(exp, "World of Warcraft Community Site", body, user, "Community Site", dev)


def interior_document(
    exp: Expansion,
    title: str,
    body: str,
    user: str | None = None,
    dev: bool = False,
    rows: list[dict] | None = None,
    ssotd: str = "",
    extra_links: str = "",
    with_rail: bool = True,
) -> str:
    raw = _home_raw()
    prefix, closer = _split_home(raw)
    prefix = prefix.replace(
        "<title>World of Warcraft Community Site</title>",
        f"<title>{escape(title)} — World of Warcraft</title>",
        1,
    )
    shot = ssotd or screenshot_of_the_day(exp)
    middle = _well(title, body, shot, with_rail=with_rail)
    html = prefix + middle + closer
    return patch_document(
        html, rows=rows or [], ssotd=shot, dev=dev, user=user, exp=exp, extra_links=extra_links
    )


def _well(title: str, body: str, ssotd: str, *, with_rail: bool = True) -> str:
    shot = escape(ssotd, quote=True)
    rail = ""
    if with_rail:
        rail = f"""<td valign="top">
<div id="marginal">
<div id="ssotd-container">
<div class="marginal-infoBox-top"><h3><span>Screenshot of the Day</span></h3></div>
<div class="marginal-infoBox"><div class="marginal-infoBox-cnt">
<a href="/downloads/screenshots"><img src="{shot}" width="195" height="151" alt="Screenshot of the Day"></a>
</div></div>
<div class="marginal-infoBox-bottom">&nbsp;</div>
</div>
<p><a href="/support/">Customer Support</a></p>
<p><a href="/wow/realmstatus/">Realm Status</a></p>
</div>
</td>"""
    # The parchment and iron edges of the center column live in this sheet.
    # The homepage links it from inside the column this well replaces.
    return f"""<div id="mainWrapper">
<div id="main">
<div id="main-content-wrapper">
<div id="main-content">
<table cellspacing="0" cellpadding="0" border="0">
<tr><td><div id="main-top"><div><div></div></div></div></td></tr>
<tr><td>
<div id="contentPadding"><div id="cnt"><div id="cnt-wrapper"><div id="contentContainer">
<link rel="stylesheet" href="/new-hp/css/newhp_specific.css" type="text/css">
<table border="0" cellpadding="0" cellspacing="0"><tr>
<td valign="top">
<div id="cntMain">
<div id="cnt-top"><div><div></div></div></div>
<div id="content"><div id="content-left"><div id="content-right"><div id="cnt-wrapper">
<div class="guide-copy">
<h2>{escape(title)}</h2>
{body}
</div>
</div></div></div></div>
<div id="cnt-bot"><div><div>&nbsp;</div></div></div>
</div>
</td>
{rail}
</tr></table>
<div id="copyright"><span class="textlinks"><small>
<a href="/legal/">Online Privacy Policy</a> |
<a href="/legal/">Legal Documents</a> |
<a href="/policy/">Policies</a><br>
&copy;2004-2006 Blizzard Entertainment, Inc. All rights reserved.
</small></span></div>
</div></div></div></div>
</td></tr>
<tr><td><div id="main-bottom"><div><div></div></div></div></td></tr>
</table>
"""


def _archive_file(rel: str) -> Path | None:
    candidate = (ARCHIVE / rel).resolve()
    root = ARCHIVE.resolve()
    if not str(candidate).startswith(str(root)):
        return None
    if candidate.is_file() and candidate.stat().st_size > 0:
        return candidate
    return None


def captured_html(path: str) -> str | None:
    """Saved Wayback document for this path, when it is the November 2006 shell."""
    if path in _SKIP_CAPTURE or path.startswith("/account/"):
        return None
    rel = _INFO_CAPTURES.get(path)
    if rel is None:
        bare = path.lstrip("/")
        guesses = [bare]
        if bare.endswith("/"):
            guesses.append(bare + "index.html")
        else:
            guesses.append(bare + "/index.html")
            if not bare.endswith(".html"):
                guesses.append(bare + ".html")
        for guess in guesses:
            found = _archive_file(guess)
            if found is None:
                continue
            rel = guess
            break
        else:
            return None
    found = _archive_file(rel or "")
    if found is None:
        return None
    text = found.read_text(encoding="utf-8", errors="replace")
    # February 2006 community, the Battle.net login wall, and other
    # off-shell captures are not the 10 Nov page.
    if "loader_screen.css" not in text and "topPlain.js" not in text:
        return None
    if "<html" not in text.lower():
        return None
    return text


def _book_fragment(text: str) -> str | None:
    """The game-guide body from a November 2006 book page.

    Those pages fill the iron frame with script. Chrome never grew the
    ActiveX path, so the book is placed in the homepage frame instead.
    """
    match = re.search(r'<div[^>]*\bid\s*=\s*["\']pageContent["\'][^>]*>', text, re.I)
    if match is None:
        return None
    end = text.lower().rfind("</body>")
    if end < match.end():
        return None
    chunk = text[match.start() : end]
    chunk = re.sub(r"<script\b[^>]*>.*?</script>", "", chunk, flags=re.I | re.S)
    return chunk


def _captured_title(text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    if match is None:
        return "World of Warcraft"
    title = re.sub(r"<[^>]+>", "", match.group(1))
    title = re.sub(r"\s+", " ", title).strip()
    title = title.replace("WoW -> ", "").replace("WoW -&gt; ", "")
    return title or "World of Warcraft"


def captured_document(
    path: str,
    exp: Expansion,
    rows: list[dict],
    ssotd: str,
    dev: bool,
    user: str | None,
) -> str | None:
    text = captured_html(path)
    if text is None:
        return None
    book = _book_fragment(text)
    if book is not None:
        return interior_document(
            exp,
            _captured_title(text),
            book,
            user=user,
            dev=dev,
            rows=rows,
            ssotd=ssotd,
            extra_links='<link rel="stylesheet" href="/shared/wow-com/includes-client/wow.css">\n',
            with_rail=False,
        )
    return patch_document(text, rows=rows, ssotd=ssotd, dev=dev, user=user, exp=exp)
