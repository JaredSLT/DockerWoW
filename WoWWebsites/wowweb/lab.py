"""Read-only (plus account insert) adapter for the private-server lab MariaDB."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .catalog import Expansion

# This file lives at <lab>/WoWWebsites/wowweb/lab.py. WOW_LAB overrides it.
DEFAULT_LAB = Path(__file__).resolve().parents[2]


@dataclass
class LabConfig:
    root: Path
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 13306
    mysql_user: str = "wow"
    mysql_password: str = "wow"

    def auth_db(self, exp: Expansion) -> str:
        return f"{exp.lab_short}_auth"

    def world_db(self, exp: Expansion) -> str:
        return f"{exp.lab_short}_world"

    def chars_db(self, exp: Expansion) -> str:
        if exp.kind == "alpha":
            return f"{exp.lab_short}_realm"
        return f"{exp.lab_short}_characters"


def load_lab(root: Optional[Path] = None) -> LabConfig:
    path = Path(root or os.environ.get("WOW_LAB") or DEFAULT_LAB)
    cfg = LabConfig(root=path)
    env_file = path / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            val = val.strip().strip('"').strip("'")
            key = key.strip()
            if key == "MYSQL_PUBLISH_PORT":
                try:
                    cfg.mysql_port = int(val)
                except ValueError:
                    pass
            elif key == "MYSQL_USER":
                cfg.mysql_user = val
            elif key == "MYSQL_PASSWORD":
                cfg.mysql_password = val
            elif key == "MYSQL_HOST":
                cfg.mysql_host = val
    cfg.mysql_host = os.environ.get("MYSQL_HOST", cfg.mysql_host)
    cfg.mysql_user = os.environ.get("MYSQL_USER", cfg.mysql_user)
    cfg.mysql_password = os.environ.get("MYSQL_PASSWORD", cfg.mysql_password)
    if os.environ.get("MYSQL_PORT"):
        cfg.mysql_port = int(os.environ["MYSQL_PORT"])
    if os.environ.get("MYSQL_PUBLISH_PORT"):
        cfg.mysql_port = int(os.environ["MYSQL_PUBLISH_PORT"])
    return cfg


def _mysql_bin() -> str:
    for name in ("mysql", "mariadb"):
        found = shutil.which(name)
        if found:
            return found
    return "mysql"


def mysql(cfg: LabConfig, sql: str, db: str = "", timeout: int = 8) -> tuple[bool, str]:
    cmd = [
        _mysql_bin(),
        "--protocol=TCP",
        "-h",
        cfg.mysql_host,
        "-P",
        str(cfg.mysql_port),
        "-u",
        cfg.mysql_user,
        "--batch",
        "--raw",
        "--skip-column-names",
    ]
    if cfg.mysql_password:
        cmd.insert(6, f"-p{cfg.mysql_password}")
    if db:
        cmd += [db]
    try:
        proc = subprocess.run(
            cmd,
            input=sql,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "mysql failed").strip()
    return True, proc.stdout


def mysql_rows(cfg: LabConfig, sql: str, db: str = "", timeout: int = 8) -> list[list[str]]:
    ok, out = mysql(cfg, sql, db, timeout=timeout)
    if not ok:
        return []
    rows = []
    for line in out.splitlines():
        if line == "":
            continue
        rows.append(line.split("\t"))
    return rows


def _stock_world_port(exp: Expansion) -> int:
    """Port the client uses on the realm loopback. Alpha is 8100. Later realms are 8085."""
    if exp.id == "alpha":
        return 8100
    return 8085


def _world_endpoint(exp: Expansion) -> tuple[str, int]:
    """World port inside a realm container is the stock listen port, not the host publish.

    On the host, HAProxy publishes that stock port on the realm loopback.
    The fallback host port in the catalog is only used when the loopback is closed.
    """
    if os.environ.get("WOW_SHORT") == exp.lab_short and os.environ.get("WOW_WORLD_PORT"):
        try:
            return "127.0.0.1", int(os.environ["WOW_WORLD_PORT"])
        except ValueError:
            pass
    stock = _stock_world_port(exp)
    if exp.loopback and port_open(exp.loopback, stock):
        return exp.loopback, stock
    return "127.0.0.1", exp.world_port


def port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


# realmlist.icon is the core realm type (same codes as GameType), not a graphic.
_ICON_REALM_TYPES = {
    0: "Normal",
    1: "PvP",
    4: "Normal",
    6: "RP",
    8: "RP PvP",
    16: "FFA PvP",
}


def realm_type_label(value: str | int | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        code = int(value)
    except (TypeError, ValueError):
        return None
    return _ICON_REALM_TYPES.get(code)


def realm_status(cfg: LabConfig, exp: Expansion) -> dict:
    status = {
        "name": exp.realm_name,
        "address": "127.0.0.1",
        "port": exp.world_port,
        "up": False,
        "db": False,
        "population": "",
        "type": "",
        "timezone": "PST",
        "error": "",
    }
    auth = cfg.auth_db(exp)
    table = "realmlist"
    if exp.kind == "alpha":
        rows = mysql_rows(cfg, "SHOW TABLES LIKE 'realmlist';", auth)
        if not rows:
            # alpha uses realm db
            rows = mysql_rows(
                cfg,
                f"SHOW TABLES FROM `{exp.lab_short}_realm` LIKE 'realmlist';",
            )
            if rows:
                auth = f"{exp.lab_short}_realm"
    ok, out = mysql(cfg, f"SHOW TABLES FROM `{auth}` LIKE 'realmlist';")
    if not ok:
        status["error"] = "MariaDB unreachable"
        host, port = _world_endpoint(exp)
        status["up"] = port_open(host, port)
        return status
    status["db"] = True
    cols = mysql_rows(cfg, f"SHOW COLUMNS FROM `{auth}`.`{table}`;")
    colset = {c[0] for c in cols if c}
    if "realm_name" in colset:
        rows = mysql_rows(
            cfg,
            f"SELECT realm_name, realm_address, realm_port FROM `{auth}`.`{table}` LIMIT 1;",
        )
        if rows:
            status["name"] = rows[0][0] or status["name"]
            status["address"] = rows[0][1] or status["address"]
            try:
                status["port"] = int(rows[0][2])
            except (TypeError, ValueError):
                pass
    elif "name" in colset:
        select = f"SELECT name, address, port, population FROM `{auth}`.`{table}` LIMIT 1;"
        if "population" not in colset:
            select = f"SELECT name, address, port FROM `{auth}`.`{table}` LIMIT 1;"
        rows = mysql_rows(cfg, select)
        if rows:
            status["name"] = rows[0][0] or status["name"]
            status["address"] = rows[0][1] or status["address"]
            try:
                status["port"] = int(rows[0][2])
            except (TypeError, ValueError):
                pass
            if len(rows[0]) > 3:
                status["population"] = rows[0][3]
    if "icon" in colset:
        icon_rows = mysql_rows(cfg, f"SELECT icon FROM `{auth}`.`{table}` LIMIT 1;")
        if icon_rows and icon_rows[0]:
            label = realm_type_label(icon_rows[0][0])
            if label:
                status["type"] = label
    host, port = _world_endpoint(exp)
    status["up"] = port_open(host, port)
    playing = _online_players(cfg, exp)
    if playing is not None:
        status["population"] = playing
    return status


def _online_players(cfg: LabConfig, exp: Expansion) -> str | None:
    db = cfg.chars_db(exp)
    cols = mysql_rows(cfg, f"SHOW COLUMNS FROM `{db}`.`characters`;")
    names = {c[0] for c in cols if c}
    if "online" not in names:
        return None
    rows = mysql_rows(cfg, f"SELECT COUNT(*) FROM `{db}`.`characters` WHERE online<>0;")
    if not rows or not rows[0]:
        return None
    return rows[0][0]


def mysql_reachable(cfg: LabConfig) -> bool:
    ok, _ = mysql(cfg, "SELECT 1;")
    return ok
