"""Realm account create, login, and password change.

Credential math is the same code the realm image runs in post-setup.py.
A password saved here is the password the game client accepts.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import os
import re
import secrets
from pathlib import Path

from .catalog import Expansion
from .lab import LabConfig, mysql, mysql_rows

USER_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 4
_RUNTIME = None

CLASS_NAMES = {
    1: "Warrior",
    2: "Paladin",
    3: "Hunter",
    4: "Rogue",
    5: "Priest",
    6: "Death Knight",
    7: "Shaman",
    8: "Mage",
    9: "Warlock",
    10: "Monk",
    11: "Druid",
    12: "Demon Hunter",
    13: "Evoker",
}


def email_login(exp: Expansion) -> bool:
    """WoD and Battle.net realms sign in with an email address."""
    return exp.proto == "bnet" or exp.id == "wod"


def _runtime():
    global _RUNTIME
    if _RUNTIME is not None:
        return _RUNTIME
    candidates = [
        Path("/opt/runtime/post-setup.py"),
        Path(__file__).resolve().parents[2] / "docker" / "runtime" / "post-setup.py",
    ]
    path = next((item for item in candidates if item.is_file()), None)
    if path is None:
        raise RuntimeError("post-setup.py is not available")
    spec = importlib.util.spec_from_file_location("wow_post_setup", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _RUNTIME = module
    return module


def srp6_sha1(username: str, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    return _runtime().srp6_sha1(username, password, salt)


def srp6_sha1_verifier(username: str, password: str, salt: bytes) -> bytes:
    return _runtime().srp6_sha1(username, password, salt)[1]


def srp6_sha256(identity: str, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Battle.net SRP version 2 (PBKDF2), not a raw SHA256 verifier."""
    return _runtime().bnet_srp_v2(identity, password, salt)


def srp6_sha256_verifier(identity: str, password: str, salt: bytes) -> bytes:
    return _runtime().bnet_srp_v2(identity, password, salt)[1]


def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "''").replace("\x00", "")


def _hex_bytes(value: str) -> bytes:
    raw = (value or "").strip()
    if raw in {"NULL", "\\N", "None"}:
        return b""
    if raw.lower().startswith("0x"):
        raw = raw[2:]
    raw = raw.replace(" ", "")
    if not raw:
        return b""
    if len(raw) % 2:
        raw = "0" + raw
    try:
        return bytes.fromhex(raw)
    except ValueError:
        return b""


def _sql_hex(data: bytes) -> str:
    return "0x" + data.hex()


def _le_salt(stored_hex: str) -> bytes:
    """CMaNGOS s is BN_bn2hex of the little-endian salt integer."""
    number = int(stored_hex or "0", 16)
    width = max(32, (number.bit_length() + 7) // 8 or 1)
    raw = number.to_bytes(width, "little")
    if len(raw) < 32:
        return raw.ljust(32, b"\x00")
    return raw[:32]


def _same_int(stored: bytes, expected: bytes) -> bool:
    if not stored or not expected:
        return False
    return int.from_bytes(stored, "little") == int.from_bytes(expected, "little")


def _query(cfg: LabConfig, sql: str) -> tuple[bool, list[list[str]]]:
    ok, out = mysql(cfg, sql)
    if not ok:
        return False, []
    rows = []
    for line in out.splitlines():
        if line == "":
            continue
        rows.append(line.split("\t"))
    return True, rows


def _columns(cfg: LabConfig, db: str, table: str) -> tuple[bool, set[str]]:
    ok, rows = _query(cfg, f"SHOW COLUMNS FROM `{db}`.`{table}`;")
    return ok, {row[0] for row in rows if row}


def _cell(value: str) -> str:
    if value in {"NULL", "\\N", "None"}:
        return ""
    return value


def session_secret(data_dir: Path) -> bytes:
    path = data_dir / "secret.bin"
    if path.is_file():
        return path.read_bytes()
    data_dir.mkdir(parents=True, exist_ok=True)
    val = secrets.token_bytes(32)
    path.write_bytes(val)
    return val


def sign_session(secret: bytes, expansion_id: str, username: str) -> str:
    msg = f"{expansion_id}|{username}".encode("utf-8")
    sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()
    return f"{expansion_id}|{username}|{sig}"


def verify_session(secret: bytes, cookie: str) -> tuple[str, str] | None:
    parts = (cookie or "").split("|")
    if len(parts) != 3:
        return None
    exp_id, username, sig = parts
    expected = hmac.new(secret, f"{exp_id}|{username}".encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    return exp_id, username


def _password_ok(password: str) -> str:
    if len(password) < MIN_PASSWORD:
        return f"Password must be at least {MIN_PASSWORD} characters."
    if len(password) > 128:
        return "Password must be 128 characters or fewer."
    return ""


def _save_error(err: str) -> str:
    if "Duplicate" in (err or ""):
        return "That account already exists on this realm."
    for part in (err or "").splitlines():
        text = part.strip()
        if text.startswith("ERROR") or "Unknown column" in text or "doesn't exist" in text:
            return f"Could not save that account. {text}"
    return "Could not save that account."


def _game_password_sql(exp: Expansion, login: str, password: str, cols: set[str]) -> list[str]:
    """Column assignments for the game account. Does not change GM level."""
    ps = _runtime()
    assigns: list[str] = []
    email_row = "bnet2_pass_hash" in cols and "bnet2_salt" in cols
    if email_row:
        verifier_hex, salt_hex = ps.wod_bnet2(login, password)
        assigns.append(f"sha_pass_hash='{_esc(ps.sha1_pass_hash(login, password))}'")
        assigns.append(f"bnet2_pass_hash='{_esc(verifier_hex)}'")
        assigns.append(f"bnet2_salt='{_esc(salt_hex)}'")
        if "v" in cols:
            assigns.append("v='0'")
        if "s" in cols:
            assigns.append("s='0'")
    elif "salt" in cols and "verifier" in cols:
        salt, verifier = ps.srp6_sha1(login, password)
        assigns.append(f"salt={_sql_hex(salt)}")
        assigns.append(f"verifier={_sql_hex(verifier)}")
        if "sha_pass_hash" in cols:
            assigns.append(f"sha_pass_hash='{_esc(ps.sha1_pass_hash(login, password))}'")
    elif "sha_pass_hash" in cols:
        assigns.append(f"sha_pass_hash='{_esc(ps.sha1_pass_hash(login, password))}'")
        if "v" in cols:
            assigns.append("v='0'")
        if "s" in cols:
            assigns.append("s='0'")
    elif "v" in cols and "s" in cols:
        verifier_hex, salt_hex = ps.srp6_cmangos_hex(login, password)
        assigns.append(f"v='{_esc(verifier_hex)}'")
        assigns.append(f"s='{_esc(salt_hex)}'")
    else:
        raise RuntimeError(f"unknown account schema for {exp.id}")
    if "locked" in cols:
        assigns.append("locked=0")
    if "failed_logins" in cols:
        assigns.append("failed_logins=0")
    return assigns


def _bnet_password_sql(email: str, password: str, cols: set[str]) -> list[str]:
    ps = _runtime()
    assigns: list[str] = []
    if {"srp_version", "salt", "verifier"} <= cols:
        salt, verifier = ps.bnet_srp_v2(email, password)
        assigns.append("srp_version=2")
        assigns.append(f"salt={_sql_hex(salt)}")
        assigns.append(f"verifier={_sql_hex(verifier)}")
    elif "sha_pass_hash" in cols:
        assigns.append(f"sha_pass_hash='{_esc(ps.bnet_sha256_pass(email, password))}'")
    else:
        raise RuntimeError("unknown battlenet_accounts schema")
    if "locked" in cols:
        assigns.append("locked=0")
    if "failed_logins" in cols:
        assigns.append("failed_logins=0")
    return assigns


def _game_password_matches(login: str, password: str, cols: set[str], row: dict[str, str]) -> bool:
    ps = _runtime()
    if "bnet2_pass_hash" in cols and "bnet2_salt" in cols:
        expect = ps.sha1_pass_hash(login, password)
        if (row.get("sha_pass_hash") or "").upper() == expect:
            return True
        salt = _hex_bytes(row.get("bnet2_salt", ""))
        stored = _hex_bytes(row.get("bnet2_pass_hash", ""))
        if salt and stored:
            verifier_hex, _salt_hex = ps.wod_bnet2(login, password, salt)
            return _same_int(stored, _hex_bytes(verifier_hex))
        return False
    if "salt" in cols and "verifier" in cols and row.get("salt") and row.get("verifier"):
        salt = _hex_bytes(row["salt"])
        _salt, verifier = ps.srp6_sha1(login, password, salt)
        return _same_int(_hex_bytes(row["verifier"]), verifier)
    if "sha_pass_hash" in cols and row.get("sha_pass_hash"):
        return (row["sha_pass_hash"] or "").upper() == ps.sha1_pass_hash(login, password)
    if "v" in cols and "s" in cols and row.get("s") and row.get("v"):
        try:
            verifier_hex, _salt_hex = ps.srp6_cmangos_hex(login, password, _le_salt(row["s"]))
            return int(verifier_hex, 16) == int(row["v"], 16)
        except ValueError:
            return False
    return False


def _bnet_password_matches(email: str, password: str, cols: set[str], row: dict[str, str]) -> bool:
    ps = _runtime()
    if "srp_version" in cols and row.get("salt") and row.get("verifier"):
        salt = _hex_bytes(row["salt"])
        _salt, verifier = ps.bnet_srp_v2(email, password, salt)
        return _same_int(_hex_bytes(row["verifier"]), verifier)
    if "sha_pass_hash" in cols and row.get("sha_pass_hash"):
        return (row["sha_pass_hash"] or "").upper() == ps.bnet_sha256_pass(email, password)
    return False


def _select_game(cfg: LabConfig, auth: str, where: str) -> tuple[bool, dict[str, str], set[str]]:
    ok, cols = _columns(cfg, auth, "account")
    if not ok:
        return False, {}, set()
    bits = ["id", "username"]
    for name in ("email", "sha_pass_hash", "v", "s", "bnet2_pass_hash", "bnet2_salt", "battlenet_account"):
        if name in cols:
            if name in {"bnet2_salt"}:
                bits.append(name)
            else:
                bits.append(name)
    if "salt" in cols:
        bits.append("HEX(salt) AS salt")
    if "verifier" in cols:
        bits.append("HEX(verifier) AS verifier")
    ok, rows = _query(cfg, f"SELECT {', '.join(bits)} FROM `{auth}`.`account` WHERE {where} LIMIT 1;")
    if not ok or not rows:
        return ok, {}, cols
    # Map by re-querying names. HEX aliases keep the column name.
    header = []
    for bit in bits:
        if " AS " in bit:
            header.append(bit.split(" AS ", 1)[1])
        else:
            header.append(bit)
    row = {header[i]: _cell(rows[0][i]) if i < len(rows[0]) else "" for i in range(len(header))}
    return True, row, cols


def _select_bnet(cfg: LabConfig, auth: str, where: str) -> tuple[bool, dict[str, str], set[str]]:
    ok, tables = _query(cfg, f"SHOW TABLES FROM `{auth}` LIKE 'battlenet_accounts';")
    if not ok:
        return False, {}, set()
    if not tables:
        return True, {}, set()
    ok, cols = _columns(cfg, auth, "battlenet_accounts")
    if not ok:
        return False, {}, set()
    bits = ["id", "email"]
    if "sha_pass_hash" in cols:
        bits.append("sha_pass_hash")
    if "srp_version" in cols:
        bits.append("srp_version")
    if "salt" in cols:
        bits.append("HEX(salt) AS salt")
    if "verifier" in cols:
        bits.append("HEX(verifier) AS verifier")
    ok, rows = _query(
        cfg, f"SELECT {', '.join(bits)} FROM `{auth}`.`battlenet_accounts` WHERE {where} LIMIT 1;"
    )
    if not ok or not rows:
        return ok, {}, cols
    header = [("salt" if bit.startswith("HEX(salt)") else "verifier" if bit.startswith("HEX(verifier)") else bit) for bit in bits]
    row = {header[i]: _cell(rows[0][i]) if i < len(rows[0]) else "" for i in range(len(header))}
    return True, row, cols


def _linked_username(cfg: LabConfig, auth: str, bnet_id: str, email: str) -> str:
    ok, cols = _columns(cfg, auth, "account")
    if not ok:
        return ""
    if "battlenet_account" in cols and bnet_id:
        ok, rows = _query(
            cfg,
            "SELECT username FROM `{db}`.`account` WHERE battlenet_account={bid} "
            "AND username NOT LIKE '%#%' ORDER BY battlenet_index, id LIMIT 1;".format(
                db=auth, bid=int(bnet_id)
            ),
        )
        if ok and rows and rows[0][0]:
            return rows[0][0]
        ok, rows = _query(
            cfg,
            f"SELECT username FROM `{auth}`.`account` WHERE battlenet_account={int(bnet_id)} "
            "ORDER BY id LIMIT 1;",
        )
        if ok and rows and rows[0][0]:
            return rows[0][0]
    if email and "email" in cols:
        ok, rows = _query(
            cfg,
            f"SELECT username FROM `{auth}`.`account` WHERE LOWER(email)=LOWER('{_esc(email)}') "
            "ORDER BY id LIMIT 1;",
        )
        if ok and rows and rows[0][0]:
            return rows[0][0]
    return ""


def authenticate(cfg: LabConfig, exp: Expansion, identity: str, password: str) -> tuple[bool, str]:
    """Check a site login. On success the second value is the game-account name."""
    identity = (identity or "").strip()
    if not identity or not password:
        return False, "Enter the account and password."
    if exp.kind == "alpha":
        return _auth_alpha(cfg, exp, identity, password)
    if email_login(exp):
        return _auth_email(cfg, exp, identity, password)
    return _auth_username(cfg, exp, identity, password)


def _auth_username(cfg: LabConfig, exp: Expansion, identity: str, password: str) -> tuple[bool, str]:
    if not USER_RE.match(identity):
        return False, "No such account on this realm. Create one first."
    auth = cfg.auth_db(exp)
    ok, row, cols = _select_game(cfg, auth, f"UPPER(username)=UPPER('{_esc(identity)}')")
    if not ok:
        return False, "The realm database is not reachable."
    if not row:
        return False, "No such account on this realm. Create one first."
    if not _game_password_matches(row["username"], password, cols, row):
        return False, "That password does not match this account."
    return True, row["username"]


def _auth_email(cfg: LabConfig, exp: Expansion, identity: str, password: str) -> tuple[bool, str]:
    if not EMAIL_RE.match(identity):
        return False, "Enter the email address for this account."
    auth = cfg.auth_db(exp)
    safe = _esc(identity)
    if exp.id == "wod":
        ok, row, cols = _select_game(cfg, auth, f"LOWER(username)=LOWER('{safe}')")
        if not ok:
            return False, "The realm database is not reachable."
        if not row:
            return False, "No such account on this realm. Create one first."
        if not _game_password_matches(row["username"], password, cols, row):
            return False, "That password does not match this account."
        return True, row["username"]
    ok, row, cols = _select_bnet(cfg, auth, f"LOWER(email)=LOWER('{safe}')")
    if not ok:
        return False, "The realm database is not reachable."
    if not row:
        return False, "No such account on this realm. Create one first."
    if not _bnet_password_matches(row.get("email") or identity, password, cols, row):
        return False, "That password does not match this account."
    game = _linked_username(cfg, auth, row.get("id", ""), row.get("email") or identity)
    if not game:
        return False, "That Battle.net login has no game account on this realm."
    return True, game


def _auth_alpha(cfg: LabConfig, exp: Expansion, identity: str, password: str) -> tuple[bool, str]:
    if not USER_RE.match(identity):
        return False, "No such account on this realm. Create one first."
    auth = cfg.auth_db(exp)
    ok, rows = _query(
        cfg,
        "SELECT name, password, salt, verifier FROM `{db}`.`accounts` "
        "WHERE UPPER(name)=UPPER('{name}') LIMIT 1;".format(db=auth, name=_esc(identity)),
    )
    if not ok:
        return False, "The realm database is not reachable."
    if not rows or len(rows[0]) < 4:
        return False, "No such account on this realm. Create one first."
    name, stored, salt_hex, verifier_hex = (_cell(rows[0][0]), _cell(rows[0][1]), _cell(rows[0][2]), _cell(rows[0][3]))
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if stored.lower() == digest or stored == password:
        return True, name
    salt = _hex_bytes(salt_hex)
    if salt:
        verifier = srp6_sha1_verifier(name, password, salt)
        if _same_int(_hex_bytes(verifier_hex), verifier):
            return True, name
    return False, "That password does not match this account."


CLOSED_ACCOUNT = "Account creation is closed."


def registration_open() -> bool:
    """Read the per-realm flag on each request. A missing file leaves creation on."""
    path = os.environ.get("WOW_ACCOUNT_CREATE_FILE", "")
    if not path:
        root = os.environ.get("WOW_ROOT", "")
        if not root:
            return True
        path = os.path.join(root, "account-create")
    if not os.path.isfile(path):
        return True
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read().strip().lower()
    except OSError:
        return True
    return text not in {"off", "0", "no", "closed"}


def create_account(
    cfg: LabConfig,
    exp: Expansion,
    username: str,
    password: str,
    email: str = "",
    game_name: str = "",
) -> tuple[bool, str, str]:
    """Create a realm login. The third value is the game-account name."""
    if not registration_open():
        return False, CLOSED_ACCOUNT, ""
    problem = _password_ok(password)
    if problem:
        return False, problem, ""
    if exp.kind == "alpha":
        return _create_alpha(cfg, exp, username or game_name, password)
    if exp.id == "wod":
        return _create_wod(cfg, exp, email or username, password)
    if exp.proto == "bnet":
        return _create_bnet(cfg, exp, email or username, game_name or username, password)
    return _create_username(cfg, exp, username, password)


def _create_username(cfg: LabConfig, exp: Expansion, username: str, password: str) -> tuple[bool, str, str]:
    if not USER_RE.match(username or ""):
        return False, "Username must be 3–16 letters, numbers, or underscore.", ""
    auth = cfg.auth_db(exp)
    user = username.upper()
    ok, cols = _columns(cfg, auth, "account")
    if not ok:
        return False, "The realm database is not reachable.", ""
    existing = mysql_rows(cfg, f"SELECT id FROM `{auth}`.`account` WHERE UPPER(username)=UPPER('{_esc(user)}') LIMIT 1;")
    if existing:
        return False, "That account already exists on this realm.", ""
    try:
        assigns = _game_password_sql(exp, user, password, cols)
    except RuntimeError:
        return False, "This realm's account table has no password field.", ""
    cols_sql = ["username"]
    vals_sql = [f"'{_esc(user)}'"]
    for item in assigns:
        col, _, val = item.partition("=")
        cols_sql.append(col)
        vals_sql.append(val)
    if "expansion" in cols:
        cols_sql.append("expansion")
        vals_sql.append(str(int(exp.expansion_level)))
    ok, err = mysql(cfg, f"INSERT INTO `{auth}`.`account` ({', '.join(cols_sql)}) VALUES ({', '.join(vals_sql)})")
    if not ok:
        return False, _save_error(err), ""
    return True, "Account created. You can log in with the game client and on this site.", user


def _create_wod(cfg: LabConfig, exp: Expansion, email: str, password: str) -> tuple[bool, str, str]:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email):
        return False, "Enter the email address for this account.", ""
    return _create_username_email(cfg, exp, email, password)


def _create_username_email(cfg: LabConfig, exp: Expansion, email: str, password: str) -> tuple[bool, str, str]:
    auth = cfg.auth_db(exp)
    ok, cols = _columns(cfg, auth, "account")
    if not ok:
        return False, "The realm database is not reachable.", ""
    existing = mysql_rows(
        cfg, f"SELECT id FROM `{auth}`.`account` WHERE LOWER(username)=LOWER('{_esc(email)}') LIMIT 1;"
    )
    if existing:
        return False, "That account already exists on this realm.", ""
    try:
        assigns = _game_password_sql(exp, email, password, cols)
    except RuntimeError:
        return False, "This realm's account table has no password field.", ""
    cols_sql = ["username"]
    vals_sql = [f"'{_esc(email)}'"]
    for item in assigns:
        col, _, val = item.partition("=")
        cols_sql.append(col)
        vals_sql.append(val)
    if "email" in cols:
        cols_sql.append("email")
        vals_sql.append(f"'{_esc(email)}'")
    if "reg_mail" in cols:
        cols_sql.append("reg_mail")
        vals_sql.append(f"'{_esc(email)}'")
    if "expansion" in cols:
        cols_sql.append("expansion")
        vals_sql.append(str(int(exp.expansion_level)))
    ok, err = mysql(cfg, f"INSERT INTO `{auth}`.`account` ({', '.join(cols_sql)}) VALUES ({', '.join(vals_sql)})")
    if not ok:
        return False, _save_error(err), ""
    return True, "Account created. Log in with this email in the game client and on this site.", email


def _create_bnet(
    cfg: LabConfig, exp: Expansion, email: str, game_name: str, password: str
) -> tuple[bool, str, str]:
    email = (email or "").strip()
    game_name = (game_name or "").strip()
    if not EMAIL_RE.match(email):
        return False, "Enter the email address for this account.", ""
    if not USER_RE.match(game_name):
        return False, "Choose a World of Warcraft account name: 3–16 letters, numbers, or underscore.", ""
    auth = cfg.auth_db(exp)
    ok, bcols = _columns(cfg, auth, "battlenet_accounts")
    if not ok:
        return False, "The realm database is not reachable.", ""
    if not bcols:
        return False, "This realm has no Battle.net account table.", ""
    taken = mysql_rows(
        cfg,
        f"SELECT id FROM `{auth}`.`battlenet_accounts` WHERE LOWER(email)=LOWER('{_esc(email)}') LIMIT 1;",
    )
    if taken:
        return False, "That email is already registered on this realm.", ""
    user = game_name.upper()
    taken = mysql_rows(
        cfg, f"SELECT id FROM `{auth}`.`account` WHERE UPPER(username)=UPPER('{_esc(user)}') LIMIT 1;"
    )
    if taken:
        return False, "That World of Warcraft account name is already in use.", ""
    try:
        assigns = _bnet_password_sql(email, password, bcols)
    except RuntimeError:
        return False, "This realm's Battle.net table has no password field.", ""
    cols_sql = ["email"]
    vals_sql = [f"'{_esc(email)}'"]
    for item in assigns:
        col, _, val = item.partition("=")
        cols_sql.append(col)
        vals_sql.append(val)
    ok, err = mysql(
        cfg,
        f"INSERT INTO `{auth}`.`battlenet_accounts` ({', '.join(cols_sql)}) VALUES ({', '.join(vals_sql)})",
    )
    if not ok:
        return False, _save_error(err), ""
    found = mysql_rows(
        cfg,
        f"SELECT id FROM `{auth}`.`battlenet_accounts` WHERE LOWER(email)=LOWER('{_esc(email)}') LIMIT 1;",
    )
    if not found:
        return False, "Could not save that account.", ""
    bnet_id = int(found[0][0])
    ok, gcols = _columns(cfg, auth, "account")
    if not ok:
        return False, "The realm database is not reachable.", ""
    try:
        gassigns = _game_password_sql(exp, user, password, gcols)
    except RuntimeError:
        return False, "This realm's account table has no password field.", ""
    cols_sql = ["username"]
    vals_sql = [f"'{_esc(user)}'"]
    for item in gassigns:
        col, _, val = item.partition("=")
        cols_sql.append(col)
        vals_sql.append(val)
    if "email" in gcols:
        cols_sql.append("email")
        vals_sql.append(f"'{_esc(email)}'")
    if "reg_mail" in gcols:
        cols_sql.append("reg_mail")
        vals_sql.append(f"'{_esc(email)}'")
    if "expansion" in gcols:
        cols_sql.append("expansion")
        vals_sql.append(str(int(exp.expansion_level)))
    if "battlenet_account" in gcols:
        cols_sql.append("battlenet_account")
        vals_sql.append(str(bnet_id))
    if "battlenet_index" in gcols:
        cols_sql.append("battlenet_index")
        vals_sql.append("1")
    ok, err = mysql(cfg, f"INSERT INTO `{auth}`.`account` ({', '.join(cols_sql)}) VALUES ({', '.join(vals_sql)})")
    if not ok:
        return False, _save_error(err), ""
    return True, "Account created. Log in with this email in the game client and on this site.", user


def _create_alpha(cfg: LabConfig, exp: Expansion, username: str, password: str) -> tuple[bool, str, str]:
    if not USER_RE.match(username or ""):
        return False, "Username must be 3–16 letters, numbers, or underscore.", ""
    auth = cfg.auth_db(exp)
    existing = mysql_rows(
        cfg, f"SELECT id FROM `{auth}`.`accounts` WHERE UPPER(name)=UPPER('{_esc(username)}') LIMIT 1;"
    )
    if existing:
        return False, "That account already exists on this realm.", ""
    salt, verifier = srp6_sha1(username, password)
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
    ok, err = mysql(
        cfg,
        "INSERT INTO `{db}`.`accounts` (name, password, ip, gmlevel, salt, verifier, sessionkey) "
        "VALUES ('{name}', '{pw}', '127.0.0.1', 0, '{salt}', '{ver}', '')".format(
            db=auth,
            name=_esc(username),
            pw=_esc(digest),
            salt=_esc(salt.hex()),
            ver=_esc(verifier.hex()),
        ),
    )
    if not ok:
        return False, _save_error(err), ""
    return True, "Account created for this realm.", username


def change_password(
    cfg: LabConfig, exp: Expansion, username: str, current: str, new_password: str
) -> tuple[bool, str]:
    """Replace the password on the signed-in game account and its Battle.net login."""
    problem = _password_ok(new_password)
    if problem:
        return False, problem
    if not current:
        return False, "Enter the current password."
    if new_password == current:
        return False, "Choose a different password."
    if exp.kind == "alpha":
        return _change_alpha(cfg, exp, username, current, new_password)
    auth = cfg.auth_db(exp)
    ok, row, cols = _select_game(cfg, auth, f"UPPER(username)=UPPER('{_esc(username)}')")
    if not ok:
        return False, "The realm database is not reachable."
    if not row:
        return False, "That account is not on this realm."
    login = row["username"]
    bnet_row: dict[str, str] = {}
    bnet_cols: set[str] = set()
    bnet_id = row.get("battlenet_account") or ""
    if bnet_id and bnet_id not in {"0", "NULL"}:
        ok, bnet_row, bnet_cols = _select_bnet(cfg, auth, f"id={int(bnet_id)}")
        if not ok:
            return False, "The realm database is not reachable."
    matched = False
    if bnet_row:
        matched = _bnet_password_matches(bnet_row.get("email") or "", current, bnet_cols, bnet_row)
    if not matched:
        matched = _game_password_matches(login, current, cols, row)
    if not matched:
        return False, "That password does not match this account."
    try:
        assigns = _game_password_sql(exp, login, new_password, cols)
    except RuntimeError:
        return False, "This realm's account table has no password field."
    ok, err = mysql(
        cfg,
        f"UPDATE `{auth}`.`account` SET {', '.join(assigns)} WHERE id={int(row['id'])}",
    )
    if not ok:
        return False, _save_error(err)
    if bnet_row:
        email = bnet_row.get("email") or ""
        try:
            bassigns = _bnet_password_sql(email, new_password, bnet_cols)
        except RuntimeError:
            return False, "This realm's Battle.net table has no password field."
        ok, err = mysql(
            cfg,
            f"UPDATE `{auth}`.`battlenet_accounts` SET {', '.join(bassigns)} WHERE id={int(bnet_row['id'])}",
        )
        if not ok:
            return False, _save_error(err)
    return True, "Password changed. Use it the next time you log into the game."


def _change_alpha(
    cfg: LabConfig, exp: Expansion, username: str, current: str, new_password: str
) -> tuple[bool, str]:
    ok, name = _auth_alpha(cfg, exp, username, current)
    if not ok:
        return False, name
    auth = cfg.auth_db(exp)
    salt, verifier = srp6_sha1(name, new_password)
    digest = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
    ok, err = mysql(
        cfg,
        "UPDATE `{db}`.`accounts` SET password='{pw}', salt='{salt}', verifier='{ver}', sessionkey='' "
        "WHERE UPPER(name)=UPPER('{name}')".format(
            db=auth,
            pw=_esc(digest),
            salt=_esc(salt.hex()),
            ver=_esc(verifier.hex()),
            name=_esc(name),
        ),
    )
    if not ok:
        return False, _save_error(err)
    return True, "Password changed. Use it the next time you log into the game."


def account_summary(cfg: LabConfig, exp: Expansion, username: str) -> dict:
    """Email and characters for the signed-in game account. Empty when unknown."""
    summary = {"email": "", "characters": []}
    if not username:
        return summary
    auth = cfg.auth_db(exp)
    account_id = ""
    if exp.kind == "alpha":
        ok, rows = _query(
            cfg,
            f"SELECT id, name FROM `{auth}`.`accounts` WHERE UPPER(name)=UPPER('{_esc(username)}') LIMIT 1;",
        )
        if ok and rows:
            account_id = rows[0][0]
    else:
        ok, row, cols = _select_game(cfg, auth, f"UPPER(username)=UPPER('{_esc(username)}')")
        if ok and row:
            account_id = row.get("id", "")
            summary["email"] = row.get("email") or ""
            bnet_id = row.get("battlenet_account") or ""
            if bnet_id and bnet_id not in {"0"}:
                _ok, brow, _bcols = _select_bnet(cfg, auth, f"id={int(bnet_id)}")
                if brow.get("email"):
                    summary["email"] = brow["email"]
            if exp.id == "wod" and not summary["email"]:
                summary["email"] = row.get("username") or ""
    if not account_id:
        return summary
    chars = cfg.chars_db(exp)
    ok, rows = _query(
        cfg,
        f"SELECT name, level, `class` FROM `{chars}`.`characters` WHERE account={int(account_id)} "
        "ORDER BY level DESC LIMIT 12;",
    )
    if not ok:
        return summary
    characters = []
    for name, level, class_id in rows:
        try:
            label = CLASS_NAMES.get(int(class_id), "Adventurer")
            shown_level = int(level)
        except (TypeError, ValueError):
            label = "Adventurer"
            shown_level = 0
        characters.append({"name": _cell(name), "level": shown_level, "class_name": label})
    summary["characters"] = characters
    return summary


def account_exists(cfg: LabConfig, exp: Expansion, username: str) -> bool:
    auth = cfg.auth_db(exp)
    if exp.kind == "alpha":
        rows = mysql_rows(
            cfg, f"SELECT id FROM `{auth}`.`accounts` WHERE UPPER(name)=UPPER('{_esc(username)}') LIMIT 1;"
        )
        return bool(rows)
    user = username.upper()
    rows = mysql_rows(cfg, f"SELECT id FROM `{auth}`.`account` WHERE UPPER(username)=UPPER('{_esc(user)}') LIMIT 1;")
    return bool(rows)
