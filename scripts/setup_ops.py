#!/usr/bin/env python3
"""Operator actions for setup.sh.

The menu collects choices and runs setup.sh. setup.sh runs this module for
the actions that need the catalog, MariaDB, or a saved file. Importing this
module does not connect to a database or change a file.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTOR = ROOT / "scripts" / "select-project.py"
ENV_FILE = ROOT / ".env"
ACCESS_FILE = ROOT / ".run" / "access.conf"
VOLUME_NAME = "wow_wow-mariadb"
NAME_RE = re.compile(r"^[a-z0-9-]+$")
HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$")
KEEP_ROOT = {
    "maps",
    "vmaps",
    "mmaps",
    "dbc",
    "cameras",
    "Cameras",
    "gt",
    "Buildings",
    "logs",
    "db",
    "account-create",
    ".gm-created",
}
KEEP_ETC = {"maps", "navs", "mdx", "wmo_liquids", "wmo_geometry"}
UNSAFE_WORLD = {"vmangos", "mangosthree", "none", ""}


class OpsError(Exception):
    """The operator asked for something this command will not do."""


def load_selector():
    spec = importlib.util.spec_from_file_location("select_project", SELECTOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def decide_core_action(state: str, on_data: str, same_kind: bool, world_safe: bool) -> str:
    """Choose what a core change may do with an existing realm.

    state is "none", "players", or "unknown". "set" records the core and
    leaves every database alone. The other return values are the operator's
    --on-data choice after it has been checked.
    """
    if state == "none":
        return "set"
    if state not in {"players", "unknown"}:
        raise OpsError(f"unknown player state {state}")
    if on_data not in {"refuse", "reimport", "keep"}:
        raise OpsError(
            "This realm has player data, or MariaDB could not be checked. "
            "Pass --on-data refuse, reimport, or keep."
        )
    if on_data == "keep" and not same_kind:
        raise OpsError(
            "Cannot keep accounts and characters: the cores do not use the same database kind."
        )
    if on_data == "keep" and not world_safe:
        raise OpsError(
            "Cannot keep accounts and characters: this core has no safe world reimport."
        )
    return on_data


def require_confirm(got: str, expected: str) -> None:
    if got != expected:
        raise OpsError(f"Refusing. Pass --confirm {expected}")


def world_safe(project) -> bool:
    return project.kind in {"cmangos", "trinity", "azerothcore", "skyfire", "alpha"} and (
        project.db_kind not in UNSAFE_WORLD
    )


def read_env(path: Path | None = None) -> dict[str, str]:
    target = path or ENV_FILE
    found: dict[str, str] = {}
    if not target.is_file():
        return found
    for raw in target.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        found[key.strip()] = value.strip().strip('"').strip("'")
    return found


def update_env(updates: dict[str, str], path: Path | None = None) -> None:
    target = path or ENV_FILE
    if not target.exists():
        example = ROOT / ".env.example"
        text = example.read_text(encoding="utf-8") if example.is_file() else ""
        target.write_text(text, encoding="utf-8")
    lines = target.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    target.write_text("\n".join(out) + "\n", encoding="utf-8")


def backup_dir(create: bool = False) -> Path:
    raw = os.environ.get("WOW_BACKUP_DIR") or read_env().get("BACKUP_DIR", "")
    if not raw:
        raise OpsError(
            "Set a backup directory first: ./setup.sh backup path /path/on/another/disk"
        )
    path = Path(raw).expanduser()
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if create and not os.access(path, os.W_OK):
        raise OpsError(f"Cannot write {path}")
    return path


def valid_ipv4(text: str) -> bool:
    parts = text.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 and str(int(part)) == part for part in parts)
    except ValueError:
        return False


def read_access(path: Path | None = None) -> list[tuple[str, str, str]]:
    target = path or ACCESS_FILE
    rows: list[tuple[str, str, str]] = []
    if not target.is_file():
        return rows
    for lineno, raw in enumerate(target.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 3:
            raise OpsError(f"{target}:{lineno}: expected short|hostname|ip")
        rows.append((parts[0], parts[1], parts[2]))
    return rows


def write_access(rows: list[tuple[str, str, str]], path: Path | None = None) -> None:
    seen_ip: dict[str, str] = {}
    seen_short: set[str] = set()
    for short, host, ip in rows:
        if not NAME_RE.fullmatch(short):
            raise OpsError(f"bad realm name {short}")
        if not HOST_RE.fullmatch(host) or "." not in host:
            raise OpsError(f"{short}: {host} is not a DNS name")
        if not valid_ipv4(ip):
            raise OpsError(f"{short}: {ip} is not an IPv4 address")
        if short in seen_short:
            raise OpsError(f"{short} is listed twice")
        seen_short.add(short)
        if ip in seen_ip:
            raise OpsError(
                f"{short} and {seen_ip[ip]} both use {ip}. "
                "Stock ports can be bound once per address."
            )
        seen_ip[ip] = short
    target = path or ACCESS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(f"{short}|{host}|{ip}\n" for short, host, ip in rows)
    target.write_text(body, encoding="utf-8")


def client_present(path: Path) -> bool:
    return any(
        (path / name).is_dir()
        for name in ("Data", "data", "World of Warcraft/Data", "_retail_/Data", "_classic_/Data")
    )


def mysql_base() -> list[str]:
    binary = shutil.which("mysql") or shutil.which("mariadb")
    if not binary:
        raise OpsError("mysql or mariadb client is required. No databases were changed.")
    env = read_env()
    return [
        binary,
        "--protocol=TCP",
        "--connect-timeout=3",
        "-h",
        "127.0.0.1",
        "-P",
        env.get("MYSQL_PUBLISH_PORT", "13306"),
        "-u",
        env.get("MYSQL_USER", "wow"),
        "--batch",
        "--raw",
        "--skip-column-names",
    ]


def mysql_query(sql: str) -> tuple[bool, str]:
    env = read_env()
    child = os.environ.copy()
    child["MYSQL_PWD"] = env.get("MYSQL_PASSWORD", "wow")
    try:
        result = subprocess.run(
            [*mysql_base(), "-e", sql],
            capture_output=True,
            text=True,
            env=child,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired, OpsError) as exc:
        return False, str(exc)
    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip()
    return True, result.stdout.strip()


def player_state(short: str) -> str:
    """Return none, players, or unknown without changing a database."""
    forced = os.environ.get("WOW_PLAYER_STATE", "")
    if forced in {"none", "players", "unknown"}:
        return forced
    if not NAME_RE.fullmatch(short):
        raise OpsError(f"bad realm name {short}")
    mod = load_selector()
    realms = {item.short: item for item in mod.load_catalog()}
    realm = realms.get(short)
    if realm is None:
        raise OpsError(f"{short} is not a catalog realm")
    char_db = f"{short}_realm" if realm.kind == "alpha" else f"{short}_characters"
    auth_db = f"{short}_auth"
    ok, text = mysql_query("SELECT 1")
    if not ok:
        return "unknown"
    chars = _count(char_db, "characters")
    accounts = _count(auth_db, "account")
    if accounts == 0:
        named = _count(auth_db, "accounts")
        if named < 0:
            return "unknown"
        accounts = named
    if chars < 0 or accounts < 0:
        return "unknown"
    if chars > 0 or accounts > 1:
        return "players"
    return "none"


def _count(database: str, table: str) -> int:
    ok, text = mysql_query(
        "SELECT COUNT(*) FROM information_schema.tables "
        f"WHERE table_schema='{database}' AND table_name='{table}'"
    )
    if not ok or text.strip() != "1":
        return 0 if ok else -1
    ok, text = mysql_query(f"SELECT COUNT(*) FROM `{database}`.`{table}`")
    if not ok:
        return -1
    try:
        return int(text.strip() or "0")
    except ValueError:
        return -1


def forget_init(short: str) -> None:
    if os.environ.get("WOW_CORE_DRY") == "1":
        return
    subprocess.run(
        ["docker", "rm", "-f", f"wow-{short}", f"wow-{short}-init"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def close_account_creation(short: str) -> None:
    path = ROOT / "servers" / short / "account-create"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("off\n", encoding="utf-8")


def cmd_doctor() -> int:
    problems = 0

    def check(ok: bool, label: str, detail: str = "") -> None:
        nonlocal problems
        mark = "ok" if ok else "missing"
        if not ok:
            problems += 1
        suffix = f" — {detail}" if detail else ""
        print(f"  {mark:8} {label}{suffix}")

    print("Tools")
    check(shutil.which("docker") is not None, "docker")
    compose = subprocess.run(
        ["docker", "compose", "version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    check(compose.returncode == 0 or shutil.which("docker-compose") is not None, "docker compose")
    for name in ("rsync", "git", "python3", "curl"):
        check(shutil.which(name) is not None, name)
    check(
        shutil.which("mysqldump") is not None or shutil.which("mariadb-dump") is not None,
        "mysqldump",
    )
    check(shutil.which("sudo") is not None, "sudo")
    print("Config")
    check(ENV_FILE.is_file(), ".env", "copy .env.example if this is a new tree")
    env = read_env()
    check(bool(env.get("ACCESS") or env.get("BIND_MODE")), "how players connect", env.get("ACCESS") or env.get("BIND_MODE") or "not chosen")
    print("Clients")
    mod = load_selector()
    for realm in mod.load_catalog():
        path = ROOT / "clients" / realm.client
        check(client_present(path), realm.short, str(path))
    timer = subprocess.run(
        ["systemctl", "is-enabled", "wow-git-update.timer"],
        capture_output=True,
        text=True,
        check=False,
    )
    if timer.stdout.strip() == "enabled":
        print("The 30-minute git timer is enabled. ./setup.sh host disables it.")
        problems += 1
    if problems:
        print(f"{problems} check(s) need attention. ./setup.sh host installs packages and the host files.")
        return 1
    print("Doctor found nothing missing.")
    return 0


def cmd_clients() -> int:
    mod = load_selector()
    missing = 0
    print(f"{'SHORT':<16} {'CLIENT':<36} DATA")
    for realm in mod.load_catalog():
        path = ROOT / "clients" / realm.client
        present = client_present(path)
        if not present:
            missing += 1
        print(f"{realm.short:<16} {realm.client:<36} {'ok' if present else 'missing'}")
    if missing:
        print("Place the client so Data/ is inside clients/<name>. This command does not download a client.")
        return 1
    return 0


def cmd_players(short: str) -> int:
    state = player_state(short)
    print(state)
    return {"none": 0, "players": 10, "unknown": 11}[state]


def _prepare_modules(mod, project, modules: list[str] | None, short: str) -> list[str]:
    projects = mod.load_projects()
    choices = mod.load_selection()
    if modules is None:
        modules = list(mod.active_choice(short, projects, choices).modules)
    mod.validate_modules(project, modules, mod.load_modules())
    return modules


def cmd_core_set(short: str, project_id: str, on_data: str, modules: list[str] | None) -> int:
    mod = load_selector()
    projects = mod.load_projects()
    by_id = {item.id: item for item in projects}
    project = by_id.get(project_id)
    if project is None:
        raise OpsError(f"unknown project {project_id}")
    if project.short != short:
        raise OpsError(f"{project_id} is a {project.short} core, not {short}")
    if not project.selectable:
        raise OpsError(f"{project_id} is not selectable. {project.notes}")
    current = mod.active_project(short, projects, mod.load_selection())
    chosen = _prepare_modules(mod, project, modules, short)
    state = player_state(short)
    action = decide_core_action(
        state,
        on_data,
        current.kind == project.kind,
        world_safe(project),
    )
    if os.environ.get("WOW_CORE_DRY") == "1":
        print(action)
        return 0
    if action == "refuse":
        print(f"{short}: left the selection and the databases unchanged.")
        return 0
    if action in {"reimport", "keep"}:
        os.environ["WOW_BACKUP_DIR"] = str(backup_dir(create=True))
        forget_init(short)
        if action == "reimport":
            code = mod.reimport(short)
            if code != 0:
                return code
        else:
            realms = {item.short: item for item in mod.load_catalog()}
            names = [f"{short}_world"]
            hotfix = realms[short].hotfix
            if hotfix in {"hotfix", "hotfixes"}:
                names.append(f"{short}_{hotfix}")
            dest = backup_dir(create=True) / short / "world"
            dumped = mod.dump_databases(names, dest)
            if dumped and mod.drop_databases([name for name, _path in dumped]) != 0:
                return 1
            print(f"{short}: world database replaced. Accounts and characters were left in place.")
    flags = [(short, name) for name in chosen]
    mod.apply_changes([(short, project_id)], flags)
    print(f"{short}: selection is {project_id}.")
    installed = mod.read_core_id(short)
    if installed and installed[0] == project_id and action == "set":
        print("The installed core already matches. Start it with ./setup.sh up " + short)
    else:
        print(
            "Build this core before the next start: "
            f"./setup.sh setup --skip-extract {short}"
        )
    if action in {"reimport", "keep"}:
        print("The next start imports the databases that were emptied.")
    return 0


def cmd_modules(short: str, modules: list[str]) -> int:
    mod = load_selector()
    projects = mod.load_projects()
    project = mod.active_project(short, projects, mod.load_selection())
    mod.validate_modules(project, modules, mod.load_modules())
    if os.environ.get("WOW_CORE_DRY") == "1":
        print(",".join(modules) or "-")
        return 0
    mod.apply_changes([], [(short, name) for name in modules])
    print(f"{short}: modules {', '.join(modules) or 'none'}. Build before the next start.")
    return 0


def cmd_password(short: str, save_env: bool) -> int:
    password = os.environ.get("ACCOUNT_PASSWORD", "")
    if not password:
        raise OpsError("the password was empty")
    if os.environ.get("WOW_CORE_DRY") == "1":
        print(f"{short}: password would be updated")
        return 0
    env = read_env()
    child = os.environ.copy()
    child.update(
        {
            "WOW_SET_PASSWORD": "1",
            "WOW_FORCE_GM_PASSWORD": "1",
            "WOW_SHORT": short,
            "WOW_ROOT": str(ROOT / "servers" / short),
            "ACCOUNT_PASSWORD": password,
            "ACCOUNT_NAME": env.get("ACCOUNT_NAME", "admin"),
            "MYSQL_HOST": "127.0.0.1",
            "MYSQL_PORT": env.get("MYSQL_PUBLISH_PORT", "13306"),
            "MYSQL_USER": env.get("MYSQL_USER", "wow"),
            "MYSQL_PASSWORD": env.get("MYSQL_PASSWORD", "wow"),
        }
    )
    # Kind and proto are supplied by setup.sh from the catalog.
    result = subprocess.run([sys.executable, str(ROOT / "docker" / "runtime" / "post-setup.py")], env=child)
    if result.returncode != 0:
        return result.returncode
    if save_env:
        update_env({"ACCOUNT_PASSWORD": password})
        print("Saved ACCOUNT_PASSWORD in .env.")
    return 0


def cmd_website(short: str, state: str) -> int:
    if not NAME_RE.fullmatch(short):
        raise OpsError(f"bad realm name {short}")
    if state not in {"on", "off"}:
        raise OpsError("website create expects on or off")
    path = ROOT / "servers" / short / "account-create"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state + "\n", encoding="utf-8")
    print(f"{short}: account creation is {state}. The world server was not restarted.")
    return 0


def cmd_access_show() -> int:
    env = read_env()
    mode = env.get("ACCESS") or "loopback"
    print(f"ACCESS={mode}")
    print(f"BIND_MODE={env.get('BIND_MODE', 'haproxy')}")
    if mode == "ports":
        print(f"REALM_ADDRESS={env.get('REALM_ADDRESS', '')}")
    if mode == "public":
        for short, host, ip in read_access():
            print(f"  {short} {host} {ip}")
    return 0


def cmd_access_set(mode: str, address: str, rows: list[tuple[str, str, str]]) -> int:
    if mode == "loopback":
        update_env({"ACCESS": "loopback", "BIND_MODE": "haproxy"})
        print("Players on this machine use vanilla.local and the other loopback names.")
        return 0
    if mode == "ports":
        if not valid_ipv4(address):
            raise OpsError("--address must be an IPv4 address")
        update_env({"ACCESS": "ports", "BIND_MODE": "ports", "REALM_ADDRESS": address})
        print(f"Players use {address} and the unique port for each realm.")
        print("Run ./setup.sh list to see those ports. Websites use the site port on that address.")
        return 0
    if mode == "public":
        if not rows:
            raise OpsError("public access needs at least one short=hostname,ip row")
        write_access(rows)
        update_env({"ACCESS": "public", "BIND_MODE": "haproxy"})
        for short, _host, _ip in rows:
            close_account_creation(short)
        print("Each realm below has its own address. Stock ports and port 80 are published there.")
        print("Account creation is off until you run ./setup.sh website <short> create on.")
        print("The site is HTTP. A password crosses the network in the clear.")
        print("Create these DNS records:")
        for short, host, ip in rows:
            print(f"  {host}  A  {ip}")
        return 0
    raise OpsError("access set expects loopback, ports, or public")


def _dump_existing(mod, short: str, names: list[str]) -> list[tuple[str, Path]]:
    os.environ["WOW_BACKUP_DIR"] = str(backup_dir(create=True))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = backup_dir() / short / stamp
    return mod.dump_databases(names, dest)


def cmd_world_drop(short: str, confirm: str) -> int:
    require_confirm(confirm, short)
    mod = load_selector()
    realms = {item.short: item for item in mod.load_catalog()}
    realm = realms.get(short)
    if realm is None:
        raise OpsError(f"{short} is not a catalog realm")
    project = mod.active_project(short, mod.load_projects(), mod.load_selection())
    if not world_safe(project):
        raise OpsError(f"{short}: this core has no safe world reimport. Nothing was dropped.")
    names = [f"{short}_world"]
    if realm.hotfix in {"hotfix", "hotfixes"}:
        names.append(f"{short}_{realm.hotfix}")
    forget_init(short)
    dumped = _dump_existing(mod, short, names)
    if dumped and mod.drop_databases([name for name, _path in dumped]) != 0:
        return 1
    print(f"{short}: world database emptied. Accounts and characters were left in place.")
    print(f"Import on the next start: ./setup.sh up {short}")
    return 0


def _character_names(mod, short: str) -> list[str]:
    realms = {item.short: item for item in mod.load_catalog()}
    realm = realms.get(short)
    if realm is None:
        raise OpsError(f"{short} is not a catalog realm")
    if realm.kind == "alpha":
        return [f"{short}_realm"]
    return [f"{short}_characters"]


def remove_tree(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def erase_maps(short: str) -> None:
    dest = ROOT / "servers" / short
    if not dest.is_dir():
        print(f"{short}: no servers/{short} directory")
        return
    for name in ("maps", "vmaps", "mmaps", "dbc", "cameras", "Cameras", "gt", "Buildings"):
        path = dest / name
        if path.exists():
            remove_tree(path)
            print(f"removed {path}")
    etc = dest / "etc"
    if etc.is_dir():
        for name in KEEP_ETC:
            path = etc / name
            if path.exists():
                remove_tree(path)
                print(f"removed {path}")


def erase_install(short: str) -> None:
    dest = ROOT / "servers" / short
    if not dest.is_dir():
        print(f"{short}: no servers/{short} directory")
        return
    for child in list(dest.iterdir()):
        if child.name in KEEP_ROOT:
            continue
        if child.name == "sql" and child.is_dir():
            for sub in list(child.iterdir()):
                if sub.name != "dumps":
                    remove_tree(sub)
                    print(f"removed {sub}")
            continue
        if child.name == "etc" and child.is_dir():
            for sub in list(child.iterdir()):
                if sub.name not in KEEP_ETC:
                    remove_tree(sub)
                    print(f"removed {sub}")
            continue
        remove_tree(child)
        print(f"removed {child}")
    core_id = dest / ".core-id"
    if core_id.exists():
        core_id.unlink()
        print(f"removed {core_id}")


def cmd_erase(scope: str, short: str, confirm: str) -> int:
    if scope == "volume":
        require_confirm(confirm, VOLUME_NAME)
        return erase_volume()
    require_confirm(confirm, short)
    if not NAME_RE.fullmatch(short):
        raise OpsError(f"bad realm name {short}")
    mod = load_selector()
    if scope == "container":
        forget_init(short)
        print(f"{short}: container removed. Databases, maps, and binaries were left in place.")
        return 0
    if scope == "databases":
        os.environ["WOW_BACKUP_DIR"] = str(backup_dir(create=True))
        forget_init(short)
        return mod.reimport(short)
    if scope == "characters":
        forget_init(short)
        names = _character_names(mod, short)
        dumped = _dump_existing(mod, short, names)
        if dumped and mod.drop_databases([name for name, _path in dumped]) != 0:
            return 1
        print(f"{short}: character database emptied. Accounts and the world were left in place.")
        print(f"The next start creates an empty character schema: ./setup.sh up {short}")
        return 0
    if scope == "maps":
        erase_maps(short)
        return 0
    if scope == "install":
        erase_install(short)
        return 0
    if scope == "realm":
        forget_init(short)
        os.environ["WOW_BACKUP_DIR"] = str(backup_dir(create=True))
        code = mod.reimport(short)
        if code != 0:
            return code
        erase_maps(short)
        erase_install(short)
        print(f"{short}: realm erased. Other realms and the shared volume were left in place.")
        return 0
    raise OpsError(f"unknown erase scope {scope}")


def erase_volume() -> int:
    print(f"This deletes Docker volume {VOLUME_NAME}. Every realm's accounts and characters go with it.")
    ok, text = mysql_query("SHOW DATABASES")
    if ok:
        print(text)
    else:
        print("MariaDB is not answering. The volume is still removed if it exists.")
    names = subprocess.run(
        ["docker", "ps", "-aq", "--filter", "name=wow-", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    containers = [line for line in names.stdout.splitlines() if line]
    if containers:
        subprocess.run(["docker", "rm", "-f", *containers], check=False)
    result = subprocess.run(["docker", "volume", "rm", VOLUME_NAME], check=False)
    return result.returncode


def cmd_backup_path(path: str) -> int:
    target = Path(path).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    if not os.access(target, os.W_OK):
        raise OpsError(f"Cannot write {target}")
    update_env({"BACKUP_DIR": str(target)})
    print(f"Backups will be written under {target}. They are kept until you delete them.")
    return 0


def cmd_backup_now(shorts: list[str]) -> int:
    mod = load_selector()
    os.environ["WOW_BACKUP_DIR"] = str(backup_dir(create=True))
    if not shorts:
        shorts = [item.short for item in mod.load_catalog()]
    start = subprocess.run(["docker", "start", "wow-db"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if start.returncode != 0:
        ok, _text = mysql_query("SELECT 1")
        if not ok:
            print("wow-db is not running and could not be started. Nothing was dumped.")
            return 1
    failed = 0
    for short in shorts:
        names = mod.catalog_databases(short)
        try:
            dumped = _dump_existing(mod, short, names)
        except OpsError as exc:
            print(f"{short}: {exc}", file=sys.stderr)
            failed += 1
            continue
        if dumped:
            print(f"{short}: {len(dumped)} database(s) dumped")
        else:
            print(f"{short}: no databases to dump")
    return 1 if failed else 0


def cmd_backup_list() -> int:
    path = backup_dir(create=False)
    if not path.is_dir():
        print(f"No dumps in {path}")
        return 0
    total = 0
    for short_dir in sorted(p for p in path.iterdir() if p.is_dir()):
        for stamp in sorted(p for p in short_dir.iterdir() if p.is_dir()):
            size = sum(f.stat().st_size for f in stamp.rglob("*") if f.is_file())
            total += size
            print(f"{short_dir.name}  {stamp.name}  {size} bytes")
    print(f"Total {total} bytes under {path}")
    return 0


def cmd_backup_delete(short: str, stamp: str, confirm: str) -> int:
    require_confirm(confirm, stamp)
    path = backup_dir(create=False) / short / stamp
    if not path.is_dir():
        raise OpsError(f"no dump {path}")
    shutil.rmtree(path)
    print(f"removed {path}")
    return 0


def cmd_backup_restore(short: str, stamp: str, confirm: str) -> int:
    require_confirm(confirm, short)
    path = backup_dir(create=False) / short / stamp
    if not path.is_dir():
        raise OpsError(f"no dump {path}")
    files = sorted(path.glob("*.sql"))
    if not files:
        raise OpsError(f"{path} has no sql dumps")
    forget_init(short)
    binary = shutil.which("mysql") or shutil.which("mariadb")
    if not binary:
        raise OpsError("mysql client is required. Nothing was restored.")
    env = read_env()
    child = os.environ.copy()
    child["MYSQL_PWD"] = env.get("MYSQL_PASSWORD", "wow")
    for sql in files:
        print(f"restoring {sql.name}")
        with sql.open("rb") as handle:
            result = subprocess.run(
                [
                    binary,
                    "--protocol=TCP",
                    "-h",
                    "127.0.0.1",
                    "-P",
                    env.get("MYSQL_PUBLISH_PORT", "13306"),
                    "-u",
                    env.get("MYSQL_USER", "wow"),
                ],
                stdin=handle,
                env=child,
                check=False,
            )
        if result.returncode != 0:
            raise OpsError(f"restore stopped at {sql.name}. {short} was left stopped.")
    print(f"{short} was restored and left stopped. Start it with ./setup.sh up {short}")
    return 0


def parse_public(items: list[str]) -> list[tuple[str, str, str]]:
    rows = []
    for item in items:
        if "=" not in item or "," not in item:
            raise OpsError(f"expected short=hostname,ip, got {item}")
        short, rest = item.split("=", 1)
        host, ip = rest.split(",", 1)
        rows.append((short.strip(), host.strip(), ip.strip()))
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operator actions for setup.sh")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("clients")
    players = sub.add_parser("players")
    players.add_argument("short")
    core = sub.add_parser("core-set")
    core.add_argument("short")
    core.add_argument("project")
    core.add_argument("--on-data", default="")
    core.add_argument("--module", action="append", default=None)
    modules = sub.add_parser("modules")
    modules.add_argument("short")
    modules.add_argument("module", nargs="*")
    password = sub.add_parser("password")
    password.add_argument("short")
    password.add_argument("--save-env", action="store_true")
    website = sub.add_parser("website")
    website.add_argument("short")
    website.add_argument("state")
    sub.add_parser("access-show")
    access = sub.add_parser("access-set")
    access.add_argument("mode")
    access.add_argument("--address", default="")
    access.add_argument("--realm", action="append", default=[])
    world = sub.add_parser("world-drop")
    world.add_argument("short")
    world.add_argument("--confirm", default="")
    erase = sub.add_parser("erase")
    erase.add_argument("scope")
    erase.add_argument("short", nargs="?", default="")
    erase.add_argument("--confirm", default="")
    path = sub.add_parser("backup-path")
    path.add_argument("path")
    now = sub.add_parser("backup-now")
    now.add_argument("short", nargs="*")
    sub.add_parser("backup-list")
    delete = sub.add_parser("backup-delete")
    delete.add_argument("short")
    delete.add_argument("stamp")
    delete.add_argument("--confirm", default="")
    restore = sub.add_parser("backup-restore")
    restore.add_argument("short")
    restore.add_argument("stamp")
    restore.add_argument("--confirm", default="")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "doctor":
            return cmd_doctor()
        if args.cmd == "clients":
            return cmd_clients()
        if args.cmd == "players":
            return cmd_players(args.short)
        if args.cmd == "core-set":
            return cmd_core_set(args.short, args.project, args.on_data, args.module)
        if args.cmd == "modules":
            return cmd_modules(args.short, args.module)
        if args.cmd == "password":
            return cmd_password(args.short, args.save_env)
        if args.cmd == "website":
            return cmd_website(args.short, args.state)
        if args.cmd == "access-show":
            return cmd_access_show()
        if args.cmd == "access-set":
            return cmd_access_set(args.mode, args.address, parse_public(args.realm))
        if args.cmd == "world-drop":
            return cmd_world_drop(args.short, args.confirm)
        if args.cmd == "erase":
            return cmd_erase(args.scope, args.short, args.confirm)
        if args.cmd == "backup-path":
            return cmd_backup_path(args.path)
        if args.cmd == "backup-now":
            return cmd_backup_now(args.short)
        if args.cmd == "backup-list":
            return cmd_backup_list()
        if args.cmd == "backup-delete":
            return cmd_backup_delete(args.short, args.stamp, args.confirm)
        if args.cmd == "backup-restore":
            return cmd_backup_restore(args.short, args.stamp, args.confirm)
    except OpsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        if exc.__class__.__name__ == "SelectionError":
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        raise
    print(f"ERROR: unknown command {args.cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
