#!/usr/bin/env python3
"""Write server configs from .dist using environment variables."""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def set_conf_key(text: str, key: str, value: str) -> str:
    """Replace the first assignment of `key` (comment lines ignored)."""
    pattern = re.compile(
        rf"^([ \t]*{re.escape(key)}[ \t]*=[ \t]*).*$",
        re.MULTILINE,
    )
    if pattern.search(text):
        return pattern.sub(rf"\g<1>{value}", text, count=1)
    return text.rstrip() + f"\n{key} = {value}\n"


def copy_dist(src: Path, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    return dest.read_text(encoding="utf-8", errors="replace")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    print(f"==> wrote {path}")


def db_info(db: str) -> str:
    host = env("MYSQL_HOST", "db")
    port = env("MYSQL_PORT", "3306")
    user = env("MYSQL_USER", "wow")
    password = env("MYSQL_PASSWORD", "wow")
    return f'"{host};{port};{user};{password};{db}"'


def q(value: str) -> str:
    if value.startswith('"') or value.startswith("'"):
        return value
    return f'"{value}"'


def mysql_exe() -> str:
    for path in ("/usr/bin/mysql", "/usr/bin/mariadb"):
        if Path(path).is_file():
            return path
    return "/usr/bin/mysql"


def patch_common(text: str, *, is_world: bool, kind: str, short: str) -> str:
    auth_db = f"{short}_auth"
    world_db = f"{short}_world"
    chars_db = f"{short}_characters"
    hotfix = env("WOW_HOTFIX", "none")
    logs_db = f"{short}_logs"

    text = set_conf_key(text, "LoginDatabaseInfo", db_info(auth_db))
    if is_world:
        text = set_conf_key(text, "WorldDatabaseInfo", db_info(world_db))
        text = set_conf_key(text, "CharacterDatabaseInfo", db_info(chars_db))
        if kind == "cmangos":
            text = set_conf_key(text, "LogsDatabaseInfo", db_info(logs_db))
            text = set_conf_key(text, "mmap.enabled", env("WOW_MMAP_ENABLED", "1"))
        if hotfix not in ("", "none"):
            text = set_conf_key(text, "HotfixDatabaseInfo", db_info(f"{short}_{hotfix}"))
        text = set_conf_key(text, "WorldServerPort", env("WOW_WORLD_PORT", "8085"))
        text = set_conf_key(text, "DataDir", q(env("WOW_DATA_DIR", ".")))
        text = set_conf_key(text, "LogsDir", q("logs"))
        # 0: no CLI (stdin EOF would shut the world down). Process stays in Master::Run.
        text = set_conf_key(text, "Console.Enable", "0")
        text = set_conf_key(text, "SOAP.Enabled", "1")
        text = set_conf_key(text, "SOAP.IP", q("0.0.0.0"))
        text = set_conf_key(text, "SOAP.Port", "7878")
        text = set_conf_key(text, "Ra.Enable", "0")
        if kind in ("trinity", "azerothcore", "skyfire"):
            text = set_conf_key(text, "SourceDirectory", q(env("WOW_ROOT", "/opt/wow")))
            text = set_conf_key(text, "MySQLExecutable", q(mysql_exe()))
            text = set_conf_key(text, "Updates.AutoSetup", "1")
            enable = "15" if hotfix not in ("", "none") else "7"
            if kind == "azerothcore":
                enable = "7"
                # Re-assert the realm online within a minute if auth restarts
                # and sets REALM_FLAG_OFFLINE again. The default is 10 minutes.
                text = set_conf_key(text, "UpdateUptimeInterval", "1")
            text = set_conf_key(text, "Updates.EnableDatabases", enable)
    else:
        text = set_conf_key(text, "RealmServerPort", env("WOW_AUTH_PORT", "3724"))
        text = set_conf_key(text, "BattlenetPort", env("WOW_AUTH_PORT", "1119"))
        rest = env("WOW_REST_PORT", "0")
        if rest not in ("", "0"):
            text = set_conf_key(text, "LoginREST.Port", rest)
            public = env("WOW_PUBLIC_HOST", "127.0.0.1")
            text = set_conf_key(text, "LoginREST.ExternalAddress", public)
            text = set_conf_key(text, "LoginREST.LocalAddress", public)
        root = env("WOW_ROOT", "/opt/wow")
        cert = Path(root) / "bin" / "bnetserver.cert.pem"
        key = Path(root) / "bin" / "bnetserver.key.pem"
        if cert.is_file():
            text = set_conf_key(text, "CertificatesFile", q(str(cert)))
        if key.is_file():
            text = set_conf_key(text, "PrivateKeyFile", q(str(key)))
        text = set_conf_key(text, "LogsDir", q("logs"))
        if kind in ("trinity", "azerothcore", "skyfire"):
            text = set_conf_key(text, "SourceDirectory", q(env("WOW_ROOT", "/opt/wow")))
            text = set_conf_key(text, "MySQLExecutable", q(mysql_exe()))
            # worldserver applies schema; auth process only needs a live DB
            text = set_conf_key(text, "Updates.EnableDatabases", "0")
    text = set_conf_key(text, "BindIP", q("0.0.0.0"))
    return text


def gen_conf_pair(etc: Path, auth_name: str, world_name: str, kind: str, short: str) -> None:
    auth_dist = etc / f"{auth_name}.conf.dist"
    world_dist = etc / f"{world_name}.conf.dist"
    if auth_dist.is_file():
        dest = etc / f"{auth_name}.conf"
        text = copy_dist(auth_dist, dest)
        write(dest, patch_common(text, is_world=False, kind=kind, short=short))
    if world_dist.is_file():
        dest = etc / f"{world_name}.conf"
        text = copy_dist(world_dist, dest)
        write(dest, patch_common(text, is_world=True, kind=kind, short=short))


def gen_alpha(root: Path, short: str) -> None:
    src = root / "etc" / "config" / "config.yml.dist"
    dest = root / "etc" / "config" / "config.yml"
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    text = copy_dist(src, dest)
    host = env("MYSQL_HOST", "db")
    port = env("MYSQL_PORT", "3306")
    user = env("MYSQL_USER", "wow")
    password = env("MYSQL_PASSWORD", "wow")

    def block(name: str, db: str) -> str:
        return (
            f"    {name}:\n"
            f"        db_name: {db}\n"
            f"        host: {host}\n"
            f"        port: {port}\n"
            f"        username: {user}\n"
            f"        password: {password}\n"
        )

    text = re.sub(
        r"    Auth:\n(?:        .*\n){5}",
        block("Auth", f"{short}_auth"),
        text,
        count=1,
    )
    text = re.sub(
        r"    Realm:\n(?:        .*\n){5}",
        block("Realm", f"{short}_realm"),
        text,
        count=1,
    )
    text = re.sub(
        r"    World:\n(?:        .*\n){5}",
        block("World", f"{short}_world"),
        text,
        count=1,
    )
    text = re.sub(
        r"    DBC:\n(?:        .*\n){5}",
        block("DBC", f"{short}_dbc"),
        text,
        count=1,
    )
    text = re.sub(
        r"(console_mode:\s*)True",
        r"\1False",
        text,
        count=1,
    )
    write(dest, text)


def main() -> None:
    root = Path(env("WOW_ROOT", "/opt/wow"))
    short = env("WOW_SHORT")
    kind = env("WOW_KIND")
    proto = env("WOW_PROTO", "legacy")
    if not short or not kind:
        raise SystemExit("WOW_SHORT and WOW_KIND are required")
    (root / "logs").mkdir(parents=True, exist_ok=True)
    (root / "etc").mkdir(parents=True, exist_ok=True)

    if kind == "alpha":
        gen_alpha(root, short)
        return

    etc = root / "etc"
    if kind == "cmangos":
        gen_conf_pair(etc, "realmd", "mangosd", kind, short)
        return
    if proto == "bnet":
        gen_conf_pair(etc, "bnetserver", "worldserver", kind, short)
        return
    gen_conf_pair(etc, "authserver", "worldserver", kind, short)


if __name__ == "__main__":
    main()
