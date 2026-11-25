#!/usr/bin/env python3
"""Point each WoW client at the local Docker realm for its expansion.

Reads docker/runtime/catalog.sh and .env (BIND_MODE, REALM_ADDRESS).
BIND_MODE=haproxy serves vanilla.local, tbc.local, and the other realm names
on stock ports (3724 / 1119, world 8085, REST 8081), so no port bridge is
required. ports mode still publishes unique host ports and this script
bridges the stock client sockets onto them. loopback mode does the same for
world and REST.

Re-run after BIND_MODE or REALM_ADDRESS changes. The forwarder stops on
reboot; run this script again to bring it back.

Examples:
  ./scripts/connect-client.py
  ./scripts/connect-client.py wotlk legion
  ./scripts/connect-client.py clients/World-of-Warcraft-7.3.5
  ./scripts/connect-client.py --dry-run --all
  ./scripts/connect-client.py --status
  ./scripts/connect-client.py --stop
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "docker" / "runtime" / "catalog.sh"
ENV_PATH = ROOT / ".env"
RUN_DIR = ROOT / ".run"
STATE_PATH = RUN_DIR / "client-forward.json"
PID_PATH = RUN_DIR / "client-forward.pid"
READY_PATH = RUN_DIR / "client-forward.ready"
LOG_PATH = RUN_DIR / "client-forward.log"

STOCK_REST_PORT = 8081
HEAVY_DIRS = {
    "cache",
    "interface",
    "wdb",
    "logs",
    "errors",
    "fonts",
    "utils",
    "documentation",
    "optional dlls",
    "buildings",
}
EXE_NAMES = {"wow.exe", "wow-64.exe", "wowclient.exe"}
ALIASES = {
    "bc": "tbc",
    "burningcrusade": "tbc",
    "wrath": "wotlk",
    "lichking": "wotlk",
    "cataclysm": "cata",
    "pandaria": "mop",
    "draenor": "wod",
    "bfa": "bfa",
    "battleforazeroth": "bfa",
    "sl": "shadowlands",
    "df": "dragonflight",
    "tww": "warwithin",
    "thewarwithin": "warwithin",
    "classic": "vanilla",
}


@dataclass(frozen=True)
class Expansion:
    short: str
    core: str
    kind: str
    image: str
    client: str
    proto: str
    auth_port: int
    world_port: int
    rest_port: int
    loopback: str
    realm_name: str
    host_auth: int
    host_world: int
    host_rest: int

    @property
    def uses_portal(self) -> bool:
        # 6.x and later read SET portal. WoD's server is still legacy auth.
        return self.proto == "bnet" or self.short == "wod"

    @property
    def client_dir(self) -> Path:
        return ROOT / "clients" / self.client


@dataclass(frozen=True)
class Forward:
    short: str
    listen_host: str
    listen_port: int
    dest_host: str
    dest_port: int
    role: str

    def as_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, raw: dict) -> Forward:
        return cls(
            short=raw["short"],
            listen_host=raw["listen_host"],
            listen_port=int(raw["listen_port"]),
            dest_host=raw["dest_host"],
            dest_port=int(raw["dest_port"]),
            role=raw["role"],
        )


def log(message: str) -> None:
    print(f"==> {message}")


def warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_dotenv(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def env_value(name: str, file_env: dict[str, str], default: str = "") -> str:
    if os.environ.get(name):
        return os.environ[name]
    return file_env.get(name, default)


def load_catalog(path: Path) -> list[Expansion]:
    text = path.read_text(encoding="utf-8")
    rows = re.search(r"catalog_lines\(\) \{\s*cat <<'EOF'\n(.*?\n)EOF", text, re.S)
    ports = re.search(r"catalog_fallback_ports\(\) \{(.*?\n\s*)esac", text, re.S)
    if not rows or not ports:
        die(f"Could not parse {path}")
    host_ports: dict[str, tuple[int, int, int]] = {}
    for match in re.finditer(
        r"^\s*([A-Za-z0-9-]+)\)\s+FB_AUTH=(\d+);\s*FB_WORLD=(\d+);\s*FB_REST=(\d+)",
        ports.group(1),
        re.M,
    ):
        host_ports[match.group(1)] = (
            int(match.group(2)),
            int(match.group(3)),
            int(match.group(4)),
        )
    found: list[Expansion] = []
    for line in rows.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) < 15:
            die(f"Short catalog line: {line}")
        short = parts[0]
        if short not in host_ports:
            die(f"No host ports for {short} in catalog.sh")
        host_auth, host_world, host_rest = host_ports[short]
        found.append(
            Expansion(
                short=short,
                core=parts[1],
                kind=parts[2],
                image=parts[3],
                client=parts[4],
                proto=parts[5],
                auth_port=int(parts[8]),
                world_port=int(parts[9]),
                rest_port=int(parts[10]),
                loopback=parts[11],
                realm_name=parts[14],
                host_auth=host_auth,
                host_world=host_world,
                host_rest=host_rest,
            )
        )
    if not found:
        die(f"No expansions in {path}")
    return found


def client_host(expansion: Expansion, bind_mode: str, realm_address: str) -> str:
    """Address written into realmlist.wtf / Config.wtf."""
    if bind_mode == "haproxy":
        return f"{expansion.short}.local"
    if bind_mode == "loopback":
        return expansion.loopback
    return realm_address


def published_endpoint(expansion: Expansion, bind_mode: str, role: str) -> tuple[str, int]:
    """Host and port Docker actually listens on for this role."""
    if bind_mode == "haproxy":
        ports = {
            "auth": expansion.auth_port,
            "world": expansion.world_port,
            "rest": expansion.rest_port,
        }
        if role not in ports:
            die(f"Unknown port role {role}")
        return expansion.loopback, ports[role]
    if role == "auth":
        port = expansion.auth_port if bind_mode == "loopback" else expansion.host_auth
    elif role == "world":
        port = expansion.host_world
    elif role == "rest":
        port = expansion.host_rest
    else:
        die(f"Unknown port role {role}")
    host = expansion.loopback if bind_mode == "loopback" else "127.0.0.1"
    return host, port


def forwards_for(
    expansion: Expansion, bind_mode: str, realm_address: str
) -> list[Forward]:
    """Stock client sockets that do not already land on the published port."""
    if bind_mode == "haproxy":
        return []
    planned: list[Forward] = []
    auth_host, auth_port = published_endpoint(expansion, bind_mode, "auth")
    if (expansion.loopback, expansion.auth_port) != (auth_host, auth_port):
        planned.append(
            Forward(
                expansion.short,
                expansion.loopback,
                expansion.auth_port,
                auth_host,
                auth_port,
                "auth",
            )
        )
    if expansion.uses_portal and expansion.proto == "bnet" and expansion.host_rest:
        rest_host, rest_port = published_endpoint(expansion, bind_mode, "rest")
        if (expansion.loopback, STOCK_REST_PORT) != (rest_host, rest_port):
            planned.append(
                Forward(
                    expansion.short,
                    expansion.loopback,
                    STOCK_REST_PORT,
                    rest_host,
                    rest_port,
                    "rest",
                )
            )
    world_host, world_port = published_endpoint(expansion, bind_mode, "world")
    # Alpha sends the in-container world port. Everyone else sends the host port
    # written into realmlist (REALM_ADDRESS:host world port).
    if expansion.short == "alpha":
        advertised = (realm_address, expansion.world_port)
    else:
        advertised = (realm_address, expansion.host_world)
    if advertised != (world_host, world_port):
        # ports mode publishes world on 0.0.0.0, so REALM_ADDRESS:host_world is
        # already reachable when the port matches.
        if not (bind_mode == "ports" and advertised[1] == world_port):
            planned.append(
                Forward(
                    expansion.short,
                    advertised[0],
                    advertised[1],
                    world_host,
                    world_port,
                    "world",
                )
            )
    return planned


def normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9]", "", token.lower())


def expansion_by_client_path(path: Path, catalog: list[Expansion]) -> Expansion | None:
    try:
        relative = path.resolve().relative_to((ROOT / "clients").resolve())
    except ValueError:
        return None
    if not relative.parts:
        return None
    folder = relative.parts[0]
    for expansion in catalog:
        if expansion.client == folder:
            return expansion
    return None


def resolve_targets(tokens: list[str], catalog: list[Expansion], select_all: bool) -> list[Expansion]:
    if select_all or not tokens:
        return [item for item in catalog if item.client_dir.is_dir()]
    by_short = {item.short: item for item in catalog}
    chosen: list[Expansion] = []
    seen: set[str] = set()

    def add(expansion: Expansion) -> None:
        if expansion.short not in seen:
            seen.add(expansion.short)
            chosen.append(expansion)

    for token in tokens:
        key = normalize_token(token)
        alias = ALIASES.get(key, key)
        if alias in by_short:
            add(by_short[alias])
            continue
        for expansion in catalog:
            names = {
                normalize_token(expansion.short),
                normalize_token(expansion.core),
                normalize_token(expansion.client),
                normalize_token(expansion.realm_name),
            }
            if key in names:
                add(expansion)
                break
        else:
            candidate = Path(token)
            if not candidate.is_absolute():
                for base in (Path.cwd(), ROOT):
                    if (base / token).exists():
                        candidate = base / token
                        break
            matched = expansion_by_client_path(candidate, catalog) if candidate.exists() else None
            if matched is None:
                die(
                    f"Unknown client or expansion {token!r}. "
                    "Use a catalog name (wotlk, legion, …) or a path under clients/."
                )
            add(matched)
    return chosen


def read_text(path: Path) -> tuple[str, str, bool]:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    if bom:
        raw = raw[3:]
    newline = "\r\n" if b"\r\n" in raw else "\n"
    return raw.decode("utf-8", errors="replace"), newline, bom


def write_text(path: Path, text: str, newline: str, bom: bool) -> None:
    body = text.replace("\r\n", "\n").replace("\n", newline)
    if body and not body.endswith(("\n", "\r\n")):
        body += newline
    data = body.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def split_lines(text: str) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for line in text.splitlines(keepends=True):
        ending = ""
        body = line
        if body.endswith("\r\n"):
            ending = "\r\n"
            body = body[:-2]
        elif body.endswith("\n"):
            ending = "\n"
            body = body[:-1]
        lines.append((body, ending))
    return lines


def join_lines(lines: list[tuple[str, str]]) -> str:
    return "".join(body + ending for body, ending in lines)


def terminate(lines: list[tuple[str, str]]) -> None:
    """A following line must not be glued onto a file that has no trailing newline."""
    if lines and lines[-1][1] == "":
        body, _ending = lines[-1]
        lines[-1] = (body, "\n")


REALMLIST_LINE = re.compile(
    r'^([ \t]*set[ \t]+realmlist[ \t]+)("?)([^"\s]*)("?)([ \t]*)$',
    re.IGNORECASE,
)
REALMNAME_LINE = re.compile(
    r'^([ \t]*set[ \t]+realmname[ \t]+)"?([^"]*)"?[ \t]*$',
    re.IGNORECASE,
)
WTF_LINE = re.compile(
    r'^([ \t]*SET[ \t]+)(portal|realmlist|realmname)([ \t]+)"?([^"]*)"?[ \t]*$',
    re.IGNORECASE,
)


def update_realmlist_text(text: str, host: str, realm_name: str) -> str:
    lines = split_lines(text)
    saw_list = False
    saw_name = False
    updated: list[tuple[str, str]] = []
    for body, ending in lines:
        list_match = REALMLIST_LINE.match(body)
        name_match = REALMNAME_LINE.match(body)
        if list_match:
            saw_list = True
            quote = '"' if list_match.group(2) or list_match.group(4) else ""
            body = f"{list_match.group(1)}{quote}{host}{quote}"
        elif name_match:
            saw_name = True
            body = f'{name_match.group(1)}"{realm_name}"'
        updated.append((body, ending))
    if not saw_list:
        updated.insert(0, (f"set realmlist {host}", "\n"))
    if not saw_name:
        terminate(updated)
        updated.append((f'set realmname "{realm_name}"', "\n"))
    return join_lines(updated)


def update_wtf_text(text: str, *, portal: bool, host: str, realm_name: str) -> str:
    key_name = "portal" if portal else "realmlist"
    lines = split_lines(text)
    saw_key = False
    updated: list[tuple[str, str]] = []
    for body, ending in lines:
        match = WTF_LINE.match(body)
        if not match:
            updated.append((body, ending))
            continue
        kind = match.group(2).lower()
        if kind == key_name:
            saw_key = True
            body = f'{match.group(1)}{match.group(2)}{match.group(3)}"{host}"'
        elif kind == "realmname":
            body = f'{match.group(1)}{match.group(2)}{match.group(3)}"{realm_name}"'
        updated.append((body, ending))
    if not saw_key:
        terminate(updated)
        keyword = "portal" if portal else "realmList"
        updated.append((f'SET {keyword} "{host}"', "\n"))
    return join_lines(updated)


def apply_text(path: Path, new_text: str, *, create_newline: str = "\n") -> str:
    if path.is_file():
        old, newline, bom = read_text(path)
        if old.replace("\r\n", "\n").strip() == new_text.replace("\r\n", "\n").strip():
            return "unchanged"
        write_text(path, new_text, newline, bom)
        return "updated"
    write_text(path, new_text, create_newline, False)
    return "created"


def iter_client_files(client_dir: Path) -> tuple[list[Path], list[Path], list[Path]]:
    """Return realmlist.wtf files, WTF configs, and directories that contain an exe."""
    realmlists: list[Path] = []
    wtfs: list[Path] = []
    exe_dirs: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(client_dir):
        base = os.path.basename(dirpath).lower()
        if base in HEAVY_DIRS or base == "account":
            dirnames[:] = []
            continue
        if base == "data":
            for name in filenames:
                if name.lower() == "realmlist.wtf":
                    realmlists.append(Path(dirpath) / name)
            for child in dirnames:
                candidate = Path(dirpath) / child / "realmlist.wtf"
                if candidate.is_file():
                    realmlists.append(candidate)
            dirnames[:] = []
            continue
        lower_names = {name.lower() for name in filenames}
        if lower_names & EXE_NAMES:
            exe_dirs.append(Path(dirpath))
        if base == "wtf":
            dirnames[:] = [name for name in dirnames if name.lower() != "account"]
            for name in filenames:
                if name.lower().endswith(".wtf") and not name.lower().endswith(".wtf.bak"):
                    wtfs.append(Path(dirpath) / name)
    return realmlists, wtfs, exe_dirs


def plan_file_writes(expansion: Expansion, host: str | None = None) -> list[tuple[Path, str]]:
    client_dir = expansion.client_dir
    realmlists, wtfs, exe_dirs = iter_client_files(client_dir)
    host = host or expansion.loopback
    writes: list[tuple[Path, str]] = []
    anchor = exe_dirs[0] if exe_dirs else client_dir
    classic_file = expansion.short in {"alpha", "vanilla", "tbc", "wotlk"}

    # 1.12 through 3.3.5 read realmlist.wtf. Later clients read WTF/Config.wtf.
    if classic_file and not realmlists:
        realmlists = [anchor / "realmlist.wtf"]
    for path in realmlists:
        current = read_text(path)[0] if path.is_file() else ""
        writes.append((path, update_realmlist_text(current, host, expansion.realm_name)))

    config_paths = [path for path in wtfs if path.name.lower() == "config.wtf"]
    if not classic_file and not config_paths:
        config_paths = [anchor / "WTF" / "Config.wtf"]
    for path in config_paths:
        current = read_text(path)[0] if path.is_file() else ""
        writes.append(
            (
                path,
                update_wtf_text(
                    current,
                    portal=expansion.uses_portal,
                    host=host,
                    realm_name=expansion.realm_name,
                ),
            )
        )
    for path in wtfs:
        if path.name.lower() == "config.wtf":
            continue
        current = read_text(path)[0]
        if expansion.uses_portal:
            carries = re.search(r"(?im)^[ \t]*SET[ \t]+portal\b", current)
        else:
            carries = re.search(r"(?im)^[ \t]*SET[ \t]+realmlist\b", current)
        if not carries:
            continue
        writes.append(
            (
                path,
                update_wtf_text(
                    current,
                    portal=expansion.uses_portal,
                    host=host,
                    realm_name=expansion.realm_name,
                ),
            )
        )
    return writes


def ensure_loopback(ip: str) -> bool:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind((ip, 0))
        return True
    except OSError:
        pass
    finally:
        probe.close()
    for command in (
        ["ip", "addr", "add", f"{ip}/32", "dev", "lo"],
        ["sudo", "-n", "ip", "addr", "add", f"{ip}/32", "dev", "lo"],
    ):
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True)
        except OSError:
            continue
        if result.returncode == 0:
            log(f"Added loopback address {ip}")
            return True
    warn(f"Cannot bind {ip}. Add it with: sudo ip addr add {ip}/32 dev lo")
    return False


def load_state() -> dict[str, list[dict]]:
    if not STATE_PATH.is_file():
        return {}
    try:
        raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    forwards = raw.get("forwards", {})
    return forwards if isinstance(forwards, dict) else {}


def save_state(forwards: dict[str, list[dict]]) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps({"forwards": forwards}, indent=2) + "\n",
        encoding="utf-8",
    )


def pid_is_daemon(pid: int) -> bool:
    cmdline = Path(f"/proc/{pid}/cmdline")
    try:
        raw = cmdline.read_bytes()
    except OSError:
        return False
    return b"connect-client.py" in raw and b"--daemon" in raw


def read_daemon_pid() -> int | None:
    if not PID_PATH.is_file():
        return None
    try:
        pid = int(PID_PATH.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    if pid > 0 and pid_is_daemon(pid):
        return pid
    return None


def stop_daemon() -> None:
    pid = read_daemon_pid()
    if pid is None:
        PID_PATH.unlink(missing_ok=True)
        READY_PATH.unlink(missing_ok=True)
        return
    os.kill(pid, signal.SIGTERM)
    for _ in range(50):
        if not Path(f"/proc/{pid}").exists():
            break
        time.sleep(0.05)
    else:
        os.kill(pid, signal.SIGKILL)
    PID_PATH.unlink(missing_ok=True)
    READY_PATH.unlink(missing_ok=True)


def flatten_state(state: dict[str, list[dict]]) -> list[Forward]:
    found: list[Forward] = []
    for items in state.values():
        for item in items:
            found.append(Forward.from_json(item))
    return found


def spawn_daemon(forwards: list[Forward]) -> list[str]:
    stop_daemon()
    if not forwards:
        return []
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    READY_PATH.unlink(missing_ok=True)
    log_handle = LOG_PATH.open("a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--daemon", str(STATE_PATH)],
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        cwd=str(ROOT),
    )
    PID_PATH.write_text(f"{proc.pid}\n", encoding="utf-8")
    deadline = time.time() + 3
    while time.time() < deadline:
        if READY_PATH.is_file():
            ready = json.loads(READY_PATH.read_text(encoding="utf-8"))
            errors = ready.get("errors") or []
            for message in errors:
                warn(message)
            if proc.poll() not in (None, 0):
                die(f"Forwarder exited. See {LOG_PATH}")
            return errors
        if proc.poll() not in (None, 0):
            die(f"Forwarder exited. See {LOG_PATH}")
        time.sleep(0.05)
    die(f"Forwarder did not report ready. See {LOG_PATH}")
    return []


def one_way(source: socket.socket, dest: socket.socket) -> None:
    try:
        while True:
            data = source.recv(65536)
            if not data:
                break
            dest.sendall(data)
    except OSError:
        pass
    finally:
        try:
            dest.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def bridge_connection(client: socket.socket, remote: socket.socket) -> None:
    left = threading.Thread(target=one_way, args=(client, remote), daemon=True)
    right = threading.Thread(target=one_way, args=(remote, client), daemon=True)
    left.start()
    right.start()
    left.join()
    right.join()
    for sock in (client, remote):
        try:
            sock.close()
        except OSError:
            pass


def serve_forward(item: Forward, errors: list[str]) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((item.listen_host, item.listen_port))
        server.listen(64)
    except OSError as exc:
        errors.append(
            f"{item.short} {item.role}: cannot listen on "
            f"{item.listen_host}:{item.listen_port} ({exc.strerror})"
        )
        server.close()
        return
    log(
        f"forward {item.short} {item.role} "
        f"{item.listen_host}:{item.listen_port} -> {item.dest_host}:{item.dest_port}"
    )

    def accept_loop() -> None:
        while True:
            try:
                client, _addr = server.accept()
            except OSError:
                return
            try:
                remote = socket.create_connection((item.dest_host, item.dest_port), timeout=5)
            except OSError:
                client.close()
                continue
            remote.settimeout(None)
            client.settimeout(None)
            threading.Thread(target=bridge_connection, args=(client, remote), daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()


def daemon_main(state_path: str) -> None:
    raw = json.loads(Path(state_path).read_text(encoding="utf-8"))
    forwards = flatten_state(raw.get("forwards", {}))
    errors: list[str] = []
    for item in forwards:
        serve_forward(item, errors)
    ready = {
        "ok": not errors,
        "listening": [item.as_json() for item in forwards],
        "errors": errors,
    }
    READY_PATH.write_text(json.dumps(ready, indent=2) + "\n", encoding="utf-8")
    if errors and len(errors) == len(forwards):
        raise SystemExit(1)
    stop = threading.Event()

    def handle(_signum: int, _frame: object) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, handle)
    signal.signal(signal.SIGINT, handle)
    stop.wait()


def cmd_status() -> None:
    pid = read_daemon_pid()
    state = load_state()
    forwards = flatten_state(state)
    if pid is None:
        print("Forwarder is not running.")
    else:
        print(f"Forwarder pid {pid}")
    if not forwards:
        print("No forwards configured.")
        return
    print(f"{'SERVER':<14} {'ROLE':<6} {'CLIENT DIALS':<24} DESTINATION")
    for item in forwards:
        dials = f"{item.listen_host}:{item.listen_port}"
        dest = f"{item.dest_host}:{item.dest_port}"
        print(f"{item.short:<14} {item.role:<6} {dials:<24} {dest}")


def cmd_stop() -> None:
    stop_daemon()
    if STATE_PATH.is_file():
        STATE_PATH.unlink()
    log("Stopped client forwarder")


def configure(args: argparse.Namespace) -> None:
    file_env = load_dotenv(ENV_PATH)
    bind_mode = args.bind_mode or env_value("BIND_MODE", file_env, "ports")
    if bind_mode not in {"ports", "loopback", "haproxy"}:
        die(f"BIND_MODE must be ports, loopback, or haproxy, got {bind_mode!r}")
    realm_address = env_value("REALM_ADDRESS", file_env) or env_value(
        "PUBLIC_HOST", file_env, "127.0.0.1"
    )
    account = env_value("ACCOUNT_NAME", file_env, "admin")
    password = env_value("ACCOUNT_PASSWORD", file_env, "admin")
    catalog = load_catalog(CATALOG_PATH)
    targets = resolve_targets(args.targets, catalog, args.all)
    if not targets:
        die(f"No catalog clients found under {ROOT / 'clients'}")

    print(f"Bind mode {bind_mode}. Realm address {realm_address}.")
    print(f"Password {password}.")
    print()

    state = load_state()
    needed_ips: set[str] = set()
    any_forward = False
    for expansion in targets:
        if not expansion.client_dir.is_dir():
            warn(f"No client at {expansion.client_dir.relative_to(ROOT)}")
            continue
        dial_host = client_host(expansion, bind_mode, realm_address)
        writes = plan_file_writes(expansion, dial_host)
        forwards = forwards_for(expansion, bind_mode, realm_address)
        print(f"{expansion.short}  {expansion.realm_name}")
        local = account.split("@", 1)[0].lower()
        if expansion.proto == "bnet" or expansion.short == "wod":
            print(f"  login   {local}@{expansion.short}.local / {password}")
        else:
            print(f"  login   {account} / {password}")
        print(f"  client  {expansion.client_dir.relative_to(ROOT)}")
        print(f"  portal  {dial_host}  ({'SET portal' if expansion.uses_portal else 'realmlist'})")
        auth_host, auth_port = published_endpoint(expansion, bind_mode, "auth")
        print(f"  auth    {auth_host}:{auth_port}")
        if expansion.proto == "bnet" and expansion.host_rest:
            rest_host, rest_port = published_endpoint(expansion, bind_mode, "rest")
            print(f"  rest    {rest_host}:{rest_port}  (client dials {expansion.loopback}:{STOCK_REST_PORT})")
        world_host, world_port = published_endpoint(expansion, bind_mode, "world")
        print(f"  world   {world_host}:{world_port}")
        for path, _text in writes:
            try:
                shown = path.relative_to(ROOT)
            except ValueError:
                shown = path
            print(f"  file    {shown}")
        if args.no_forward:
            print("  bridge  left unchanged (--no-forward)")
        elif not forwards:
            print("  bridge  none (published ports already match the client)")
        else:
            for item in forwards:
                print(
                    f"  bridge  {item.role:<5} {item.listen_host}:{item.listen_port}"
                    f" -> {item.dest_host}:{item.dest_port}"
                )
                needed_ips.add(item.listen_host)
        print()
        if args.dry_run:
            continue
        for path, text in writes:
            status = apply_text(path, text)
            log(f"{status} {path.relative_to(ROOT)}")
        if not args.no_forward:
            state[expansion.short] = [item.as_json() for item in forwards]
            any_forward = any_forward or bool(forwards)
            needed_ips.add(expansion.loopback)

    if args.dry_run:
        log("Dry run. No files were written.")
        return
    if args.no_forward:
        log("Client files updated. Forwarder left unchanged.")
        return

    for ip in sorted(needed_ips):
        if ip != "127.0.0.1":
            ensure_loopback(ip)
    save_state(state)
    errors = spawn_daemon(flatten_state(state))
    if errors:
        die("One or more forwards failed to listen")
    if any_forward or flatten_state(state):
        log(f"Forwarder is running. Status: {Path(__file__).name} --status")
    else:
        log("Client files updated. No port bridge is required.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Point a local WoW client at the Docker realm for its expansion."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Expansion name, client folder, or path. Default: every catalog client on disk.",
    )
    parser.add_argument("--all", action="store_true", help="Every catalog client that exists.")
    parser.add_argument("--dry-run", action="store_true", help="Show edits and bridges without writing.")
    parser.add_argument(
        "--no-forward",
        action="store_true",
        help="Only edit client files. Leave the port forwarder unchanged.",
    )
    parser.add_argument(
        "--bind-mode",
        choices=("ports", "loopback", "haproxy"),
        help="Override BIND_MODE from the environment and .env.",
    )
    parser.add_argument("--status", action="store_true", help="Show the running port forwarder.")
    parser.add_argument("--stop", action="store_true", help="Stop the port forwarder.")
    parser.add_argument("--daemon", metavar="STATE", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "--daemon":
        if len(argv) != 2:
            die("--daemon needs a state file")
        daemon_main(argv[1])
        return
    args = build_parser().parse_args(argv)
    if args.status:
        cmd_status()
        return
    if args.stop:
        cmd_stop()
        return
    configure(args)


if __name__ == "__main__":
    main()
