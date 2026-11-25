"""Community-site search behind the November 2006 search box."""

from __future__ import annotations

from pathlib import Path

from . import content, forums
from .catalog import Expansion
from .lab import LabConfig, mysql_rows

_LIMIT = 25

# slug, title, summary, body, audience, minimum expansion_level
_ARTICLES: tuple[tuple[str, str, str, str, str, int], ...] = (
    (
        "stuck-character",
        "Stuck Character",
        "Free a character who cannot move, has fallen through the world, or is trapped in a wall.",
        "If your character is stuck and cannot move, type /stuck and wait while the game tries to "
        "place you at a nearby safe spot. Should you still be trapped, log out completely, wait a "
        "minute, and log back in. You may also open the Help Request menu and ask a Game Master to "
        "move the character. Do not delete the character to fix a stuck position.",
        "game",
        0,
    ),
    (
        "forgot-password",
        "Forgot Password",
        "This realm does not email a password reset. Create the account again only if it is yours.",
        "If you have forgotten your password, this realm does not email a reset. Create the account "
        "again only if it is yours, and choose a new password you will remember. Do not create an "
        "account that belongs to someone else. Account names and passwords are case sensitive, so "
        "check the Caps Lock key before you try the old password once more.",
        "game",
        0,
    ),
    (
        "addons-and-macros",
        "Addons and Macros",
        "Install interface addons beside the game client, and write macros with the /macro command.",
        "Addons are interface files you place in the Interface folder next to the game client. "
        "Restart the game after you add or remove one, then enable it from the AddOns button on the "
        "character screen. Macros are written in the game: type /macro, create a macro, and drag it "
        "to your bars. Trade tips on the UI and Macros forum.",
        "game",
        0,
    ),
    (
        "talent-reset",
        "Talent Reset",
        "Unlearn your talents at a class trainer. The gold cost rises each time you reset.",
        "To reset your talents, speak with your class trainer in a capital or major city and choose "
        "to unlearn them. The trainer charges gold, and the price rises with every reset. You "
        "receive every spent talent point back and may place them again. Read the build before you "
        "pay, because the next visit will cost more.",
        "game",
        0,
    ),
    (
        "honor-and-battlegrounds",
        "Honor and Battlegrounds",
        "Queue for battlegrounds at a battlemaster and earn honor toward your rank.",
        "Honor is the standing you earn from ranked player-versus-player combat. Queue for "
        "battlegrounds by speaking with the battlemasters in your faction's capital. Wins, "
        "objectives, and honorable kills add honor for the current period, and your rank is tallied "
        "from that honor. Leave civilian townsfolk alone; dishonorable kills lower your standing.",
        "game",
        0,
    ),
    (
        "arena",
        "Arena",
        "Register an arena team and queue for rated matches with your teammates.",
        "Arenas are rated matches played by a team you create in the game. Register the team with an "
        "arena organizer, then queue once every member is present. Wins raise the team's rating and "
        "losses lower it. Your personal rating is tracked apart from the team. Skirmishes let you "
        "practice without changing that rating.",
        "game",
        1,
    ),
    (
        "dungeon-finder",
        "Dungeon Finder",
        "Queue for a five-player dungeon with the Dungeon Finder and choose a role.",
        "The Dungeon Finder assembles a group for a five-player dungeon. Open it from the dungeon "
        "button, choose a role, and tick the dungeons you are willing to enter. You must meet each "
        "dungeon's level requirement. When the group is ready, accept the invitation and you will be "
        "summoned to the instance. Leaving early can keep you from queueing again for a while. Need "
        "and Greed rolls decide who receives the loot.",
        "game",
        2,
    ),
    (
        "connection-failed",
        "Connection Failed",
        "What to do when the game says the connection to the realm failed.",
        "If the login screen reports that the connection failed, check the Realm Status page to see "
        "whether the realm is up. Confirm that the account name and password are correct, then try "
        "the realm again after a short wait. A full restart of the game clears a login that stopped "
        "halfway. If other players are online and you still cannot connect, ask on the realm forum "
        "before you change any game files.",
        "tech",
        0,
    ),
    (
        "patching",
        "Patching",
        "Let the patcher finish, and start it again if a file is reported corrupt.",
        "The patcher must finish before you can enter the realm. If it stops, closes early, or "
        "reports a corrupt file, shut it down and start it again so it can resume. Do not copy files "
        "from a different version of the game over this client. Give the patcher time on a slow "
        "connection, and do not log in until it says the game is ready to play.",
        "tech",
        0,
    ),
    (
        "graphics-performance",
        "Graphics and Performance",
        "Raise your frame rate from the System menu when the game stutters or the machine runs hot.",
        "Open the System menu in game and lower the graphics options if the world stutters or the "
        "machine grows hot. Reduce view distance, shadows, and spell detail first, then lower the "
        "resolution if you still need frames. Windowed mode can be steadier when other programs are "
        "open. Vertical sync limits the frame rate to the display and can smooth a picture that "
        "tears. Apply the changes, then return to the character before you judge the result.",
        "tech",
        0,
    ),
)

_PAGES: tuple[tuple[str, str, str, str], ...] = (
    (
        "Game Guide",
        "/wow/info/",
        "guide",
        "Introduction to races, classes, professions, and how to get started in the world.",
    ),
    (
        "Realm Status",
        "/wow/realmstatus",
        "realm",
        "See whether the realm is online and how many adventurers are in the world.",
    ),
    (
        "Forums",
        "/forums/",
        "forum",
        "Community boards for discussion, guild recruitment, and realm talk.",
    ),
    (
        "Screenshots",
        "/wow/media/screenshots",
        "media",
        "Screenshot of the Day and pictures sent in from the world.",
    ),
)


def support_articles(exp: Expansion) -> list[dict]:
    """Help articles this expansion's patch would have offered."""
    level = exp.expansion_level
    articles = []
    for slug, title, summary, body, audience, min_level in _ARTICLES:
        if level < min_level:
            continue
        articles.append(
            {
                "slug": slug,
                "title": title,
                "summary": summary,
                "body": body,
                "audience": audience,
            }
        )
    return articles


def search(cfg: LabConfig, exp: Expansion, data_dir: Path, query: str, search_type: str) -> list[dict]:
    """Each hit is {title, href, kind, summary}. Empty or whitespace query returns []."""
    text = (query or "").strip()
    if not text:
        return []
    kind = (search_type or "").strip().lower()
    if kind in ("", "site"):
        hits = _site_hits(exp, data_dir)
    elif kind == "encyclopedia":
        hits = _encyclopedia_hits(cfg, exp, text)
    elif kind == "ingamesupport":
        hits = _article_hits(exp, "game")
    elif kind == "techsupport":
        hits = _article_hits(exp, "tech")
    else:
        return []
    return _filter(text, hits, _LIMIT)


def _hit(title: str, href: str, kind: str, summary: str) -> dict:
    return {"title": title, "href": href, "kind": kind, "summary": summary}


def _filter(query: str, hits: list[dict], limit: int) -> list[dict]:
    needle = query.casefold()
    found = []
    for hit in hits:
        title = hit["title"]
        summary = hit["summary"]
        if needle in title.casefold() or needle in summary.casefold():
            found.append(hit)
            if len(found) >= limit:
                break
    return found


def _site_hits(exp: Expansion, data_dir: Path) -> list[dict]:
    hits = []
    for index, (title, date, body) in enumerate(content.news_for(exp)):
        hits.append(_hit(title, f"/wow/news/{index}", "news", f"{date}. {body}"))
    hits.extend(_race_hits(exp))
    hits.extend(_class_hits(exp))
    for name, desc in content.professions_for(exp):
        hits.append(_hit(name, "/wow/info/professions", "profession", desc))
    for title, href, kind, summary in _PAGES:
        hits.append(_hit(title, href, kind, summary))
    hits.extend(_forum_hits(exp, data_dir))
    return hits


def _race_hits(exp: Expansion) -> list[dict]:
    hits = []
    for slug in content.races_for(exp):
        name, faction, capital, blurb = content.race_facts(exp, slug)
        hits.append(_hit(name, f"/wow/info/races/{slug}", "race", f"{faction}. {capital}. {blurb}"))
    return hits


def _class_hits(exp: Expansion) -> list[dict]:
    hits = []
    for slug in content.classes_for(exp):
        name, armor, specs, blurb = content.class_facts(exp, slug)
        hits.append(_hit(name, f"/wow/info/classes/{slug}", "class", f"{armor}. {specs}. {blurb}"))
    return hits


def _encyclopedia_hits(cfg: LabConfig, exp: Expansion, query: str) -> list[dict]:
    # Races and classes stay even when item_template cannot be read.
    hits = _race_hits(exp) + _class_hits(exp)
    hits.extend(_item_hits(cfg, exp, query))
    return hits


def _esc(value: str) -> str:
    flat = value.replace("\x00", "").replace("\r", " ").replace("\n", " ")
    return flat.replace("\\", "\\\\").replace("'", "''")


def _item_hits(cfg: LabConfig, exp: Expansion, query: str) -> list[dict]:
    db = f"{exp.lab_short}_world"
    sql = (
        f"SELECT entry, name FROM `{db}`.`item_template` "
        f"WHERE name LIKE '%{_esc(query)}%' LIMIT 25;"
    )
    hits = []
    for row in mysql_rows(cfg, sql):
        if not row:
            continue
        if len(row) == 1:
            entry, name = "", row[0]
        else:
            entry, name = row[0], row[1]
        name = (name or "").strip()
        if not name:
            continue
        href = f"/armory/item/{entry}" if entry else "/armory/"
        hits.append(_hit(name, href, "item", "Item"))
        if len(hits) >= _LIMIT:
            break
    return hits


def _article_hits(exp: Expansion, audience: str) -> list[dict]:
    kind = "support" if audience == "game" else "tech"
    return [
        _hit(article["title"], f"/support/{article['slug']}", kind, article["summary"])
        for article in support_articles(exp)
        if article["audience"] == audience
    ]


def _forum_hits(exp: Expansion, data_dir: Path) -> list[dict]:
    # connect creates the file when it can; a missing or unreadable sqlite is skipped.
    try:
        conn = forums.connect(data_dir)
    except Exception:
        return []
    try:
        try:
            rows = conn.execute(
                """
                SELECT t.id, t.board, t.title,
                       COALESCE(
                         (SELECT p.body FROM posts p
                          WHERE p.thread_id = t.id ORDER BY p.id LIMIT 1),
                         ''
                       )
                FROM threads t
                WHERE t.expansion = ?
                ORDER BY t.id DESC
                """,
                (exp.id,),
            ).fetchall()
        except Exception:
            return []
    finally:
        conn.close()
    hits = []
    for row in rows:
        title = str(row[2] or "").strip()
        if not title:
            continue
        board = str(row[1] or "")
        body = " ".join(str(row[3] or "").split())
        summary = body[:240] if body else (f"Forum thread on {board}." if board else "Forum thread.")
        hits.append(_hit(title, f"/forums/{board}/{row[0]}", "thread", summary))
    return hits
