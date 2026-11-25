#!/usr/bin/env python3
"""Point realmlist at the host-visible address and ensure the lab GM login.

Username realms use ACCOUNT_NAME / ACCOUNT_PASSWORD (admin / admin).
WoD and Battle.net realms log in as <name>@<expansion>.local, for example
admin@midnight.local. ACCOUNT_EMAIL is ignored so one address cannot be
applied to every realm.
"""
from __future__ import annotations

import hashlib
import http.client
import os
import secrets
import shutil
import subprocess
import sys
import time


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def mysql_bin() -> str:
    for name in ("mysql", "mariadb"):
        found = shutil.which(name)
        if found:
            return found
    return "mysql"


def mysql(*args: str, sql: str) -> str:
    cmd = [
        mysql_bin(),
        "--protocol=TCP",
        "-h", env("MYSQL_HOST", "db"),
        "-P", env("MYSQL_PORT", "3306"),
        "-u", env("MYSQL_USER", "wow"),
        "--batch",
        "--raw",
        "--skip-column-names",
        *args,
    ]
    password = env("MYSQL_PASSWORD")
    if password:
        cmd.insert(6, f"-p{password}")
    proc = subprocess.run(cmd, input=sql, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "mysql failed")
    return proc.stdout


def mysql_ok(sql: str) -> bool:
    try:
        mysql(sql=sql)
        return True
    except RuntimeError:
        return False


def sql_quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def sql_hex(data: bytes) -> str:
    return "0x" + data.hex()


def ident(name: str) -> str:
    if not name.replace("_", "").isalnum():
        raise RuntimeError(f"unexpected SQL name {name!r}")
    return f"`{name}`"


def first_value(sql: str) -> str:
    text = mysql(sql=sql).strip()
    if not text:
        return ""
    value = text.splitlines()[0].split("\t", 1)[0].strip()
    if value in {"", "NULL", r"\N"}:
        return ""
    return value


def column_names(db: str, table: str) -> set[str]:
    text = mysql(sql=f"SHOW COLUMNS FROM {ident(db)}.{ident(table)}")
    return {line.split("\t", 1)[0] for line in text.splitlines() if line}


def table_exists(db: str, table: str) -> bool:
    text = mysql(sql=f"SHOW TABLES FROM {ident(db)} LIKE {sql_quote(table)}")
    return table in {line.strip() for line in text.splitlines()}


# --- SRP6 -----------------------------------------------------------------

# Game-account (realmd / authserver) — SHA1, g=7, 256-bit N used by MaNGOS/TC/AC.
GAME_N = int("894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7", 16)
GAME_G = 7

# Battle.net SRP v2 (Dragonflight and later) — g=2, RFC 5054 2048-bit group.
BNET_N = int(
    "AC6BDB41324A9A9BF166DE5E1389582FAF72B6651987EE07FC3192943DB56050"
    "A37329CBB4A099ED8193E0757767A13DD52312AB4B03310DCD7F48A9DA04FD50"
    "E8083969EDB767B0CF6095179A163AB3661A05FBD5FAAAE82918A9962F0B93B8"
    "55F97993EC975EEAA80D740ADBF4FF747359D041D5C33EA71D281E446B14773B"
    "CA97B43A23FB801676BD207A436C6481F1D2B9078717461A5B9D32E688F87748"
    "544523B524B0D57D5EA77A2775D2ECFA032CFBDBF52FB3786160279004E57AE6"
    "AF874E7303CE53299CCC041C7BC308D82A5698F3A8D0C38271AE35F8E9DBFBB6"
    "94B5C803D89F7AE435DE236D525F54759B65E372FCD68EF20FA7111F9E4AFF73",
    16,
)
BNET_G = 2
BNET_V2_ITERATIONS = 15000

# WoD bnet2 modulus. Little-endian bytes in BNet2::SRP6a_N; this is the integer.
# g is 2. Same 1024-bit group Trinity later called BnetSRP6v1.
WOD_N = int(
    "86A7F6DEEB306CE519770FE37D556F29944132554DED0BD68205E27F3231FEF5"
    "A10108238A3150C59CAF7B0B6478691C13A6ACF5E1B5ADAFD4A943D4A21A142B"
    "800E8A55F8BFBAC700EB77A7235EE5A609E350EA9FC19F10D921C2FA832E4461"
    "B7125D38D254A0BE873DFC27858ACB3F8B9F258461E4373BC3A6C2A9634324AB",
    16,
)
WOD_G = 2


def sha1_pass_hash(username: str, password: str) -> str:
    """Trinity/WoD CalculateShaPassHash. Hex digits are uppercase."""
    raw = f"{username.upper()}:{password.upper()}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest().upper()


def bnet_sha256_pass(email: str, password: str) -> str:
    """Legion, BFA, and Shadowlands battlenet_accounts.sha_pass_hash."""
    raw = f"{email.upper()}:{password.upper()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest().upper()


def srp6_sha1(username: str, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """GruntSRP6: little-endian SHA1 salt and verifier. Password is uppercased."""
    if salt is None:
        salt = secrets.token_bytes(32)
    inner = hashlib.sha1(f"{username.upper()}:{password.upper()}".encode("utf-8")).digest()
    x = int.from_bytes(hashlib.sha1(salt + inner).digest(), "little")
    verifier = pow(GAME_G, x, GAME_N).to_bytes(32, "little")
    return salt, verifier


def srp6_cmangos_hex(username: str, password: str, salt_le: bytes | None = None) -> tuple[str, str]:
    """CMaNGOS stores v and s with BN_bn2hex (big-endian).

    realmd loads that hex with SetHexStr, then hashes the little-endian salt
    bytes. A hex dump of the little-endian bytes does not log in.
    Pass salt_le to recompute a verifier for a password check.
    """
    identity = hashlib.sha1(f"{username.upper()}:{password.upper()}".encode("utf-8")).digest()
    if salt_le is None:
        salt_le = secrets.token_bytes(32)
        while salt_le[-1] == 0:
            salt_le = secrets.token_bytes(32)
    x = int.from_bytes(hashlib.sha1(salt_le + identity).digest(), "little")
    verifier = pow(GAME_G, x, GAME_N)
    salt_hex = format(int.from_bytes(salt_le, "little"), "X")
    verifier_hex = format(verifier, "X")
    return verifier_hex, salt_hex


def bnet_srp_identity(email: str) -> str:
    """Uppercase hex of SHA256(UPPER(email)). That string is the SRP username."""
    return hashlib.sha256(email.upper().encode("utf-8")).hexdigest().upper()


def bnet_srp_v2(email: str, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    """Trinity BnetSRP6v2<SHA256>.

    x is PBKDF2-HMAC-SHA512(identity + ":" + password, salt, 15000, 64).
    The password is not uppercased. The high bit of the digest makes x
    negative in the same way BigNumber(bytes, littleEndian=false) does.
    The verifier is g^x mod N as minimal little-endian bytes.
    Pass salt to recompute a verifier for a password check.
    """
    if salt is None:
        salt = secrets.token_bytes(32)
    material = f"{bnet_srp_identity(email)}:{password}".encode("utf-8")
    x_bytes = hashlib.pbkdf2_hmac("sha512", material, salt, BNET_V2_ITERATIONS, dklen=64)
    x = int.from_bytes(x_bytes, "big")
    if x_bytes[0] & 0x80:
        x -= 1 << 512
    x %= BNET_N - 1
    verifier = pow(BNET_G, x, BNET_N)
    length = (verifier.bit_length() + 7) // 8 or 1
    return salt, verifier.to_bytes(length, "little")


def _le_hex(value: int) -> str:
    if value == 0:
        return "00"
    length = (value.bit_length() + 7) // 8
    return value.to_bytes(length, "little").hex().upper()


def wod_bnet2(email: str, password: str, salt: bytes | None = None) -> tuple[str, str]:
    """WodCore SRP6aCalculatePasswordVerifier.

    The verifier hashes the lowercase email. The password is already uppercase.
    Salt and verifier are ByteArrayToHexStr of the raw bytes (uppercase hex).
    Pass salt to recompute a verifier for a password check.
    """
    email_l = email.lower()
    password_u = password.upper()
    identity = hashlib.sha256(email_l.encode("utf-8")).hexdigest().upper()
    p = hashlib.sha256(f"{identity}:{password_u}".encode("utf-8")).digest()
    if salt is None:
        salt = secrets.token_bytes(32)
    x = int.from_bytes(hashlib.sha256(salt + p).digest(), "little")
    verifier = pow(WOD_G, x, WOD_N)
    return _le_hex(verifier), salt.hex().upper()


def login_email(username: str, short: str) -> str:
    local = username.split("@", 1)[0].lower() or "admin"
    return f"{local}@{short}.local"


PASSWORD_COLUMNS = frozenset(
    {
        "salt",
        "verifier",
        "sha_pass_hash",
        "v",
        "s",
        "bnet2_pass_hash",
        "bnet2_salt",
        "password",
        "srp_version",
    }
)


def apply_password_policy(fields: dict[str, str], existed: bool, force: bool) -> dict[str, str]:
    """Keep an existing verifier. The first create, and an explicit password change, write it."""
    if existed and not force:
        return {key: value for key, value in fields.items() if key not in PASSWORD_COLUMNS}
    return dict(fields)


def seal_gm() -> None:
    root = env("WOW_ROOT", "")
    if not root:
        return
    path = os.path.join(root, ".gm-created")
    if os.path.exists(path):
        return
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("sealed\n")
    except OSError as exc:
        print(f"WARNING: could not write {path}: {exc}", file=sys.stderr)


# --- SOAP -----------------------------------------------------------------

def soap_command(command: str, port: int = 7878, timeout: float = 8.0) -> bool:
    bodies = []
    for ns in ("urn:TC", "urn:AC", "urn:MaNGOS", "urn:SF", "urn:SKYFIRE"):
        bodies.append(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            f'<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="{ns}">'
            "<SOAP-ENV:Body>"
            f"<ns1:executeCommand><command>{command}</command></ns1:executeCommand>"
            "</SOAP-ENV:Body></SOAP-ENV:Envelope>"
        )
    for body in bodies:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
            conn.request(
                "POST",
                "/",
                body=body.encode("utf-8"),
                headers={"Content-Type": "text/xml", "Content-Length": str(len(body))},
            )
            resp = conn.getresponse()
            data = resp.read().decode("utf-8", errors="replace")
            conn.close()
            if resp.status == 200 and "fault" not in data.lower():
                return True
        except OSError:
            return False
    return False


def wait_soap(seconds: int) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if soap_command("server info"):
            print("==> SOAP is up")
            return True
        time.sleep(3)
    return False


# --- realmlist ------------------------------------------------------------

def update_realmlist(auth_db: str, address: str, port: int, name: str) -> None:
    cols = column_names(auth_db, "realmlist")
    if "realm_id" in cols:
        mysql(
            sql=(
                f"UPDATE {ident(auth_db)}.realmlist SET "
                f"realm_name={sql_quote(name)}, proxy_address='0.0.0.0', proxy_port=9090, "
                f"realm_address='0.0.0.0', realm_port=9100 WHERE realm_id=1"
            )
        )
        print(f"==> alpha realmlist bind 0.0.0.0 (FORWARD_ADDRESS_OVERRIDE={address})")
        return

    assignments = [
        f"address={sql_quote(address)}",
        f"port={int(port)}",
        f"name={sql_quote(name)}",
    ]
    if "localAddress" in cols:
        assignments.append(f"localAddress={sql_quote(address)}")
    # AzerothCore auth exits when flag is OFFLINE | VERSION_MISMATCH.
    # World clears the offline bit later; do not leave the mismatch bit set.
    if "flag" in cols:
        assignments.append("flag=0")
    mysql(sql=f"UPDATE {ident(auth_db)}.realmlist SET {', '.join(assignments)} WHERE id=1")
    print(f"==> realmlist {name} -> {address}:{port}")


# --- accounts -------------------------------------------------------------

def _account_id(auth_db: str, table: str, column: str, username: str) -> str:
    return first_value(
        f"SELECT id FROM {ident(auth_db)}.{ident(table)} "
        f"WHERE UPPER({ident(column)})=UPPER({sql_quote(username)}) LIMIT 1"
    )


def _write_row(db: str, table: str, row_id: str, fields: dict[str, str], floors: set[str]) -> None:
    assignments = []
    for name, value in fields.items():
        if name in floors:
            assignments.append(f"{ident(name)}=GREATEST({ident(name)}, {value})")
        else:
            assignments.append(f"{ident(name)}={value}")
    if row_id:
        mysql(
            sql=(
                f"UPDATE {ident(db)}.{ident(table)} SET {', '.join(assignments)} "
                f"WHERE id={int(row_id)}"
            )
        )
        return
    columns = ", ".join(ident(name) for name in fields)
    values = ", ".join(fields.values())
    mysql(sql=f"INSERT INTO {ident(db)}.{ident(table)} ({columns}) VALUES ({values})")


def _claim_bnet_index(auth_db: str, bnet_id: str, keep_id: str) -> int:
    """Return a free battlenet_index, preferring 1.

    Trinity's bnetaccount create names the game account '<id>#1' at index 1.
    Drop that generated link so the lab GM can take index 1. If some other
    account already holds it, use the next free index instead.
    """
    text = mysql(
        sql=(
            f"SELECT id, username FROM {ident(auth_db)}.account "
            f"WHERE battlenet_account={int(bnet_id)} AND battlenet_index=1"
        )
    )
    for line in text.splitlines():
        if not line.strip():
            continue
        row_id, _, name = line.partition("\t")
        if not row_id or row_id == keep_id:
            continue
        if "#" not in name:
            nxt = first_value(
                f"SELECT COALESCE(MAX(battlenet_index), 0) + 1 FROM {ident(auth_db)}.account "
                f"WHERE battlenet_account={int(bnet_id)}"
            )
            return int(nxt or "1")
        mysql(
            sql=(
                f"UPDATE {ident(auth_db)}.account "
                f"SET battlenet_account=NULL, battlenet_index=NULL WHERE id={int(row_id)}"
            )
        )
    return 1


def grant_gm(auth_db: str, account_id: str) -> None:
    if not account_id or not table_exists(auth_db, "account_access"):
        return
    cols = column_names(auth_db, "account_access")
    if "AccountID" in cols and "SecurityLevel" in cols:
        id_col, level_col = "AccountID", "SecurityLevel"
    elif "id" in cols and "gmlevel" in cols:
        id_col, level_col = "id", "gmlevel"
    else:
        return
    realm = "RealmID" if "RealmID" in cols else ""
    if realm:
        mysql(
            sql=(
                f"INSERT INTO {ident(auth_db)}.account_access "
                f"({ident(id_col)}, {ident(level_col)}, {ident(realm)}) "
                f"VALUES ({int(account_id)}, 3, -1) "
                f"ON DUPLICATE KEY UPDATE {ident(level_col)}=IF({ident(level_col)} < 3, 3, {ident(level_col)})"
            )
        )
    else:
        mysql(
            sql=(
                f"INSERT INTO {ident(auth_db)}.account_access "
                f"({ident(id_col)}, {ident(level_col)}) VALUES ({int(account_id)}, 3) "
                f"ON DUPLICATE KEY UPDATE {ident(level_col)}=IF({ident(level_col)} < 3, 3, {ident(level_col)})"
            )
        )


def _unlock(names: set[str], fields: dict[str, str]) -> None:
    if "locked" in names:
        fields["locked"] = "0"
    if "failed_logins" in names:
        fields["failed_logins"] = "0"


def ensure_bnet_account(auth_db: str, email: str, password: str, linked_id: str) -> str:
    if not table_exists(auth_db, "battlenet_accounts"):
        return ""
    names = column_names(auth_db, "battlenet_accounts")
    fields: dict[str, str] = {"email": sql_quote(email)}
    if {"srp_version", "salt", "verifier"} <= names:
        salt, verifier = bnet_srp_v2(email, password)
        fields["srp_version"] = "2"
        fields["salt"] = sql_hex(salt)
        fields["verifier"] = sql_hex(verifier)
    elif "sha_pass_hash" in names:
        fields["sha_pass_hash"] = sql_quote(bnet_sha256_pass(email, password))
    else:
        raise RuntimeError(f"unknown battlenet_accounts schema in {auth_db}")
    _unlock(names, fields)

    row_id = _account_id(auth_db, "battlenet_accounts", "email", email)
    renamed = False
    if not row_id:
        for legacy in ("admin@localhost", f"{email.split('@', 1)[0]}@localhost"):
            row_id = _account_id(auth_db, "battlenet_accounts", "email", legacy)
            if row_id:
                renamed = True
                break
    if not row_id and linked_id:
        current = first_value(
            f"SELECT email FROM {ident(auth_db)}.battlenet_accounts WHERE id={int(linked_id)} LIMIT 1"
        )
        if current.lower() in {"admin@localhost", f"{email.split('@', 1)[0]}@localhost"}:
            row_id = linked_id
            renamed = True

    existed = bool(row_id)
    fields = apply_password_policy(fields, existed, env("WOW_FORCE_GM_PASSWORD") == "1")
    _write_row(auth_db, "battlenet_accounts", row_id, fields, set())
    if not row_id:
        row_id = _account_id(auth_db, "battlenet_accounts", "email", email)
    if existed or renamed:
        print(f"==> bnet account {email}")
    else:
        print(f"==> created bnet account {email}")
    return row_id


def ensure_game_account(
    auth_db: str,
    username: str,
    password: str,
    expansion: int,
    email: str,
    bnet_id: str,
) -> str:
    names = column_names(auth_db, "account")
    email_login = "bnet2_pass_hash" in names and "bnet2_salt" in names
    login = email if email_login else username.upper()
    fields: dict[str, str] = {"username": sql_quote(login)}
    floors: set[str] = set()

    if email_login:
        # WoD: the account name is the email. sha_pass_hash is the uppercase
        # pair; the bnet2 verifier is the lowercase email. v/s are cleared.
        fields["sha_pass_hash"] = sql_quote(sha1_pass_hash(login, password))
        verifier_hex, salt_hex = wod_bnet2(login, password)
        fields["bnet2_pass_hash"] = sql_quote(verifier_hex)
        fields["bnet2_salt"] = sql_quote(salt_hex)
        if "v" in names:
            fields["v"] = sql_quote("0")
        if "s" in names:
            fields["s"] = sql_quote("0")
        if "admin" in names:
            fields["admin"] = "1"
            floors.add("admin")
    elif "salt" in names and "verifier" in names:
        salt, verifier = srp6_sha1(login, password)
        fields["salt"] = sql_hex(salt)
        fields["verifier"] = sql_hex(verifier)
        if "sha_pass_hash" in names:
            fields["sha_pass_hash"] = sql_quote(sha1_pass_hash(login, password))
    elif "sha_pass_hash" in names:
        fields["sha_pass_hash"] = sql_quote(sha1_pass_hash(login, password))
        if "v" in names:
            fields["v"] = sql_quote("0")
        if "s" in names:
            fields["s"] = sql_quote("0")
    elif "v" in names and "s" in names:
        verifier_hex, salt_hex = srp6_cmangos_hex(login, password)
        fields["v"] = sql_quote(verifier_hex)
        fields["s"] = sql_quote(salt_hex)
    else:
        raise RuntimeError(f"unknown account schema in {auth_db}")

    if "gmlevel" in names:
        fields["gmlevel"] = "3"
        floors.add("gmlevel")
    if "expansion" in names:
        fields["expansion"] = str(int(expansion))
        floors.add("expansion")
    _unlock(names, fields)

    mail = email if (email_login or bnet_id) else ""
    if mail:
        if "email" in names:
            fields["email"] = sql_quote(mail)
        if "reg_mail" in names:
            fields["reg_mail"] = sql_quote(mail)
    row_id = _account_id(auth_db, "account", "username", login)
    if not row_id and email_login:
        local = login.split("@", 1)[0]
        for legacy in (f"{local}@localhost", "admin@localhost"):
            row_id = _account_id(auth_db, "account", "username", legacy)
            if row_id:
                break
    if bnet_id and "battlenet_account" in names:
        fields["battlenet_account"] = str(int(bnet_id))
        if "battlenet_index" in names:
            # Trinity's first game account on a bnet login is index 1.
            fields["battlenet_index"] = str(_claim_bnet_index(auth_db, bnet_id, row_id))
    fields = apply_password_policy(fields, bool(row_id), env("WOW_FORCE_GM_PASSWORD") == "1")
    _write_row(auth_db, "account", row_id, fields, floors)
    if not row_id:
        row_id = _account_id(auth_db, "account", "username", login)
    grant_gm(auth_db, row_id)
    print(f"==> GM account {login}")
    return row_id


def ensure_alpha_account(auth_db: str, username: str, password: str) -> None:
    if not table_exists(auth_db, "accounts"):
        return
    # Alpha stores SHA256(password) and a GruntSRP6 verifier. The client
    # compares the hash directly, and the SRP proof uses the verifier.
    salt, verifier = srp6_sha1(username, password)
    pw_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    names = column_names(auth_db, "accounts")
    fields = {
        "name": sql_quote(username),
        "password": sql_quote(pw_hash),
        "salt": sql_quote(salt.hex()),
        "verifier": sql_quote(verifier.hex()),
    }
    floors: set[str] = set()
    if "gmlevel" in names:
        fields["gmlevel"] = "3"
        floors.add("gmlevel")
    if "ip" in names:
        fields["ip"] = sql_quote("127.0.0.1")
    if "sessionkey" in names:
        fields["sessionkey"] = sql_quote("")
    row_id = first_value(
        f"SELECT id FROM {ident(auth_db)}.accounts "
        f"WHERE UPPER(name)=UPPER({sql_quote(username)}) LIMIT 1"
    )
    # sessionkey is cleared only when creating. Keep a live alpha session key.
    if row_id:
        fields.pop("sessionkey", None)
        fields.pop("ip", None)
    fields = apply_password_policy(fields, bool(row_id), env("WOW_FORCE_GM_PASSWORD") == "1")
    _write_row(auth_db, "accounts", row_id, fields, floors)
    print(f"==> alpha GM account {username}")


def linked_bnet_id(auth_db: str, username: str) -> str:
    if not table_exists(auth_db, "account"):
        return ""
    names = column_names(auth_db, "account")
    if "battlenet_account" not in names:
        return ""
    account_id = _account_id(auth_db, "account", "username", username.upper())
    if not account_id:
        return ""
    return first_value(
        f"SELECT battlenet_account FROM {ident(auth_db)}.account WHERE id={int(account_id)} LIMIT 1"
    )


def set_password_main() -> int:
    """Write the GM verifier and leave realmlist alone."""
    short = env("WOW_SHORT")
    kind = env("WOW_KIND")
    proto = env("WOW_PROTO", "legacy")
    username = env("ACCOUNT_NAME", "admin") or "admin"
    password = env("ACCOUNT_PASSWORD", "")
    if not short or not kind or not password:
        print("ERROR: WOW_SHORT, WOW_KIND, and a password are required", file=sys.stderr)
        return 1
    os.environ["WOW_FORCE_GM_PASSWORD"] = "1"
    auth_db = f"{short}_auth"
    expansion = int(env("WOW_EXPANSION", "0") or 0)
    email = login_email(username, short)
    if kind == "alpha":
        ensure_alpha_account(auth_db, username, password)
    else:
        bnet_id = ""
        if proto == "bnet" or table_exists(auth_db, "battlenet_accounts"):
            bnet_id = ensure_bnet_account(
                auth_db, email, password, linked_bnet_id(auth_db, username)
            )
        ensure_game_account(auth_db, username, password, expansion, email, bnet_id)
    seal_gm()
    print(f"==> updated GM password for {short}")
    return 0


def main() -> int:
    if env("WOW_SET_PASSWORD") == "1":
        return set_password_main()
    short = env("WOW_SHORT")
    kind = env("WOW_KIND")
    proto = env("WOW_PROTO", "legacy")
    address = env("WOW_PUBLIC_HOST", "127.0.0.1")
    world_port = int(env("WOW_PUBLIC_WORLD_PORT") or env("WOW_WORLD_PORT", "8085"))
    realm_name = env("WOW_REALM_NAME") or short
    username = env("ACCOUNT_NAME", "admin") or "admin"
    password = env("ACCOUNT_PASSWORD", "admin") or "admin"
    email = login_email(username, short)
    expansion = int(env("WOW_EXPANSION", "0") or 0)
    auth_db = f"{short}_auth"
    wait_secs = int(env("WOW_SOAP_WAIT", "0") or 0)

    if not short:
        print("ERROR: WOW_SHORT is required", file=sys.stderr)
        return 1

    if wait_secs:
        wait_soap(wait_secs)

    deadline = time.time() + int(env("WOW_DB_WAIT", "1800") or 1800)
    while time.time() < deadline:
        try:
            if table_exists(auth_db, "realmlist"):
                break
        except RuntimeError:
            pass
        time.sleep(5)
    else:
        print(f"ERROR: {auth_db}.realmlist never appeared", file=sys.stderr)
        return 1

    update_realmlist(auth_db, address, world_port, realm_name)

    if kind == "alpha":
        ensure_alpha_account(auth_db, username, password)
        seal_gm()
        return 0

    bnet_id = ""
    bnet_ok = False
    if proto == "bnet" or table_exists(auth_db, "battlenet_accounts"):
        try:
            bnet_id = ensure_bnet_account(
                auth_db, email, password, linked_bnet_id(auth_db, username)
            )
            bnet_ok = bool(bnet_id)
        except RuntimeError as exc:
            print(f"WARNING: bnet account SQL failed: {exc}", file=sys.stderr)
            if soap_command(f"bnetaccount create {email} {password}"):
                print(f"==> created bnet account {email} via SOAP")
                bnet_ok = True
                bnet_id = linked_bnet_id(auth_db, username) or _account_id(
                    auth_db, "battlenet_accounts", "email", email
                )

    try:
        ensure_game_account(auth_db, username, password, expansion, email, bnet_id)
    except RuntimeError as exc:
        print(f"WARNING: game account SQL failed: {exc}", file=sys.stderr)
        login = username
        try:
            if "bnet2_pass_hash" in column_names(auth_db, "account"):
                login = email
        except RuntimeError:
            pass
        if soap_command(f"account create {login} {password}"):
            soap_command(f"account set gmlevel {login} 3 -1")
            print(f"==> created account {login} via SOAP")

    if proto == "bnet" and not bnet_ok and soap_command(f"bnetaccount create {email} {password}"):
        print(f"==> created bnet account {email} via SOAP")

    soap_command(f"account set gmlevel {username} 3 -1")
    seal_gm()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: post-setup failed: {exc}", file=sys.stderr)
        sys.exit(1)
