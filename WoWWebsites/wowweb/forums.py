"""Local SQLite forums, logged in with realm account names."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from .catalog import Expansion

def _classes(*extra: str) -> list[tuple[str, str]]:
    names = {
        "deathknight": "Death Knight",
        "demonhunter": "Demon Hunter",
        "druid": "Druid",
        "evoker": "Evoker",
        "hunter": "Hunter",
        "mage": "Mage",
        "monk": "Monk",
        "paladin": "Paladin",
        "priest": "Priest",
        "rogue": "Rogue",
        "shaman": "Shaman",
        "warlock": "Warlock",
        "warrior": "Warrior",
    }
    order = [
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
        "evoker",
    ]
    wanted = set(extra) | {
        "warrior",
        "paladin",
        "hunter",
        "rogue",
        "priest",
        "shaman",
        "mage",
        "warlock",
        "druid",
    }
    return [(slug, names[slug]) for slug in order if slug in wanted]


_VANILLA_BOARDS = [
    ("general", "General Discussion"),
    ("suggestions", "General Suggestions"),
    ("pvp", "PvP Discussion"),
    ("quests", "Quest Discussion"),
    ("guilds", "Guild Recruitment"),
    ("rp", "Role-Playing"),
    ("ui", "UI & Macros"),
    ("bugs", "Bug Report"),
    ("support", "Customer Service"),
    ("realm", "Realm Forum"),
    *_classes(),
    ("professions", "Professions"),
]

_CATA_BOARDS = [
    ("general", "General Discussion"),
    ("pvp", "PvP"),
    ("dungeons", "Dungeons & Raids"),
    ("professions", "Professions"),
    ("ui", "UI & Macros"),
    ("guilds", "Guild Recruitment"),
    ("realm", "Realm Forum"),
    ("bugs", "Bug Report"),
    *_classes("deathknight"),
]

def _topic_boards(topics: list[tuple[str, str]], *extra_classes: str) -> list[tuple[str, str]]:
    return [
        ("general", "General Discussion"),
        ("pvp", "PvP"),
        *topics,
        ("professions", "Professions"),
        ("ui", "UI & Macros"),
        ("guilds", "Guild Recruitment"),
        ("realm", "Realm Forum"),
        ("bugs", "Bug Report"),
        *_classes(*extra_classes),
    ]


BOARDS_BY_ID = {
    "alpha": [
        ("general", "General"),
        ("quests", "Quest Discussion"),
        ("pvp", "PvP Discussion"),
        ("offtopic", "Off-topic"),
        ("guilds", "Guild Recruitment"),
        ("trading", "Trading Post"),
        ("rp", "Role-playing"),
        ("ui", "UI Customization"),
        ("suggestions", "Suggestions"),
        ("professions", "Trade Skills"),
        ("classes", "Classes"),
        ("realm", "Server Status"),
        ("support", "Support Forum"),
        ("bugs", "Bug Report"),
    ],
    "vanilla": list(_VANILLA_BOARDS) + [("guildrelations", "Guild Relations")],
    "tbc": list(_VANILLA_BOARDS),
    "wotlk": _topic_boards(
        [("quests", "Quest Discussion"), ("dungeons", "Dungeons & Raids")],
        "deathknight",
    ),
    "cata": list(_CATA_BOARDS),
    "mop": _topic_boards(
        [("dungeons", "Dungeons & Raids"), ("scenarios", "Scenarios")],
        "deathknight",
        "monk",
    ),
    "wod": _topic_boards(
        [("dungeons", "Dungeons & Raids"), ("garrisons", "Garrisons")],
        "deathknight",
        "monk",
    ),
    "legion": _topic_boards(
        [("dungeons", "Dungeons & Raids"), ("classhalls", "Class Halls")],
        "deathknight",
        "monk",
        "demonhunter",
    ),
    "bfa": _topic_boards(
        [("dungeons", "Dungeons & Raids"), ("islands", "Island Expeditions")],
        "deathknight",
        "monk",
        "demonhunter",
    ),
    "shadowlands": _topic_boards(
        [("dungeons", "Dungeons & Raids"), ("covenants", "Covenants")],
        "deathknight",
        "monk",
        "demonhunter",
    ),
    "dragonflight": _topic_boards(
        [("dungeons", "Dungeons & Raids")],
        "deathknight",
        "monk",
        "demonhunter",
        "evoker",
    ),
    "warwithin": _topic_boards(
        [("dungeons", "Dungeons & Raids"), ("delves", "Delves"), ("housing", "Housing")],
        "deathknight",
        "monk",
        "demonhunter",
        "evoker",
    ),
    "midnight": _topic_boards(
        [("dungeons", "Dungeons & Raids"), ("delves", "Delves"), ("housing", "Housing")],
        "deathknight",
        "monk",
        "demonhunter",
        "evoker",
    ),
}


def connect(data_dir: Path) -> sqlite3.Connection:
    data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(data_dir / "forums.sqlite")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expansion TEXT NOT NULL,
            board TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            created INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            created INTEGER NOT NULL,
            FOREIGN KEY(thread_id) REFERENCES threads(id)
        );
        CREATE INDEX IF NOT EXISTS idx_threads_board ON threads(expansion, board);
        """
    )
    conn.commit()
    return conn


def boards_for(exp: Expansion) -> list[tuple[str, str]]:
    return list(BOARDS_BY_ID.get(exp.id, BOARDS_BY_ID["vanilla"]))


def board_title(exp: Expansion, slug: str) -> str | None:
    for s, title in boards_for(exp):
        if s == slug:
            if s == "realm" and title == "Realm Forum":
                return f"{exp.realm_name} Realm Forum"
            return title
    return None


def list_threads(conn: sqlite3.Connection, exp: Expansion, board: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT t.id, t.title, t.author, t.created,
               (SELECT COUNT(*) FROM posts p WHERE p.thread_id = t.id) AS replies,
               (SELECT MAX(created) FROM posts p WHERE p.thread_id = t.id) AS last
        FROM threads t
        WHERE t.expansion = ? AND t.board = ?
        ORDER BY last DESC, t.id DESC
        """,
        (exp.id, board),
    ).fetchall()
    return [dict(r) for r in rows]


def get_thread(conn: sqlite3.Connection, exp: Expansion, thread_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM threads WHERE id = ? AND expansion = ?",
        (thread_id, exp.id),
    ).fetchone()
    if not row:
        return None
    posts = conn.execute(
        "SELECT * FROM posts WHERE thread_id = ? ORDER BY id ASC",
        (thread_id,),
    ).fetchall()
    data = dict(row)
    data["posts"] = [dict(p) for p in posts]
    return data


def create_thread(
    conn: sqlite3.Connection, exp: Expansion, board: str, author: str, title: str, body: str
) -> int:
    now = int(time.time())
    cur = conn.execute(
        "INSERT INTO threads (expansion, board, title, author, created) VALUES (?, ?, ?, ?, ?)",
        (exp.id, board, title.strip()[:120], author, now),
    )
    tid = int(cur.lastrowid)
    conn.execute(
        "INSERT INTO posts (thread_id, author, body, created) VALUES (?, ?, ?, ?)",
        (tid, author, body.strip()[:8000], now),
    )
    conn.commit()
    return tid


def add_post(conn: sqlite3.Connection, thread_id: int, author: str, body: str) -> None:
    conn.execute(
        "INSERT INTO posts (thread_id, author, body, created) VALUES (?, ?, ?, ?)",
        (thread_id, author, body.strip()[:8000], int(time.time())),
    )
    conn.commit()


def seed_if_empty(conn: sqlite3.Connection, exp: Expansion) -> None:
    n = conn.execute(
        "SELECT COUNT(*) FROM threads WHERE expansion = ?", (exp.id,)
    ).fetchone()[0]
    if n:
        return
    samples = [
        (
            "general",
            "Welcome to the community forums",
            "Blizzard Poster",
            "These forums are for players of this realm. Be excellent to each other, and keep spoilers out of thread titles.",
        ),
        (
            "realm",
            f"Welcome to {exp.realm_name}",
            "Blizzard Poster",
            f"This board is the realm forum for {exp.realm_name}. Coordinate groups, trade, and talk about life on this server.",
        ),
        (
            "pvp",
            "Looking for more for Warsong Gulch",
            "Thaddeus",
            "Need a healer for evening premades. Bring a sense of humor and a bandage.",
        ),
    ]
    for board, title, author, body in samples:
        if board_title(exp, board):
            create_thread(conn, exp, board, author, title, body)
