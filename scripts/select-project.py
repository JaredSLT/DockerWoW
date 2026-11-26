#!/usr/bin/env python3
"""Choose the core and modules for each realm slot.

Missing .run/selection.conf leaves catalog.sh on today's cores. A saved line
is an overlay: catalog_load asks this script for CATALOG_* assignments.
Launch refuses when servers/<short>/.core-id does not match that overlay.

  ./scripts/select-project.py
  ./scripts/select-project.py --list
  ./scripts/select-project.py --set wotlk=TrinityCore-335 --module wotlk:Spells
  ./scripts/select-project.py --module wotlk:mod-playerbots --module wotlk:mod-transmog
  ./scripts/select-project.py --build wotlk
  ./scripts/select-project.py --launch vanilla,wotlk
  ./scripts/select-project.py --reimport wotlk
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS_FILE = ROOT / "docker/runtime/projects.conf"
MODULES_FILE = ROOT / "docker/runtime/modules.conf"
CATALOG_FILE = ROOT / "docker/runtime/catalog.sh"

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
SCRIPT_RE = re.compile(r"^[A-Za-z0-9_]+$")
ASSIGN_RE = re.compile(r"^CATALOG_[A-Z0-9_]+='[^']*'$")
KINDS = {"alpha", "cmangos", "azerothcore", "trinity", "skyfire"}
MODULE_CLASSES = {
    "azerothcore",
    "cmangos-playerbots",
    "trinity-scripts",
    "vmangos-variant",
    "none",
}
OVERLAY_KEYS = (
    "CATALOG_CORE",
    "CATALOG_KIND",
    "CATALOG_IMAGE",
    "CATALOG_AUTH_BIN",
    "CATALOG_WORLD_BIN",
    "CATALOG_PROTO",
    "CATALOG_AUTH_PORT",
    "CATALOG_WORLD_PORT",
    "CATALOG_REST_PORT",
    "CATALOG_DB_REPO",
    "CATALOG_DB_BRANCH",
    "CATALOG_DB_KIND",
    "CATALOG_MODULES",
)


class SelectionError(Exception):
    """The user asked for a core or module this lab will not apply."""


@dataclass(frozen=True)
class Project:
    id: str
    short: str
    label: str
    repo_key: str
    kind: str
    module_class: str
    image: str
    client: str
    expect_build: str
    auth_bin: str
    world_bin: str
    proto: str
    auth_port: str
    world_port: str
    rest_port: str
    db_repo: str
    db_branch: str
    db_kind: str
    selectable: bool
    launch_policy: str
    is_default: bool
    notes: str


@dataclass(frozen=True)
class Module:
    id: str
    module_class: str
    label: str
    url: str
    ref: str
    commit: str
    requires: str
    default_on: bool
    notes: str


@dataclass(frozen=True)
class CatalogRealm:
    short: str
    core: str
    kind: str
    image: str
    client: str
    proto: str
    auth_bin: str
    world_bin: str
    auth_port: str
    world_port: str
    rest_port: str
    loopback: str
    expansion: str
    hotfix: str
    realm_name: str
    db_repo: str
    db_branch: str
    db_kind: str


@dataclass
class Choice:
    project_id: str
    modules: list[str] = field(default_factory=list)


def _rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        rows.append(parts)
        if any("\n" in part for part in parts):
            raise SelectionError(f"{path.name}:{lineno}: newline in a field")
    return rows


def load_projects() -> list[Project]:
    projects: list[Project] = []
    seen: set[str] = set()
    defaults: dict[str, str] = {}
    for parts in _rows(PROJECTS_FILE):
        if len(parts) != 22:
            raise SelectionError(
                f"projects.conf row {parts[0] if parts else '?'} has {len(parts)} fields, expected 22"
            )
        project = Project(
            id=parts[0],
            short=parts[1],
            label=parts[2],
            repo_key=parts[3],
            kind=parts[4],
            module_class=parts[5],
            image=parts[6],
            client=parts[7],
            expect_build=parts[8],
            auth_bin=parts[9],
            world_bin=parts[10],
            proto=parts[11],
            auth_port=parts[12],
            world_port=parts[13],
            rest_port=parts[14],
            db_repo=parts[15],
            db_branch=parts[16],
            db_kind=parts[17],
            selectable=parts[18] == "1",
            launch_policy=parts[19],
            is_default=parts[20] == "1",
            notes=parts[21],
        )
        if project.id in seen:
            raise SelectionError(f"duplicate project id {project.id}")
        seen.add(project.id)
        if project.kind not in KINDS and not (project.kind == "none" and not project.selectable):
            raise SelectionError(f"{project.id}: unknown kind {project.kind}")
        if project.module_class not in MODULE_CLASSES:
            raise SelectionError(f"{project.id}: unknown module class {project.module_class}")
        if project.launch_policy not in {"ok", "warn", "refuse"}:
            raise SelectionError(f"{project.id}: launch_policy must be ok, warn, or refuse")
        if "|" in project.notes:
            raise SelectionError(f"{project.id}: notes contain a pipe")
        if project.is_default:
            if project.short in defaults:
                raise SelectionError(f"{project.short}: two default projects")
            if not project.selectable:
                raise SelectionError(f"{project.id}: the default project must be selectable")
            defaults[project.short] = project.id
        projects.append(project)
    return projects


def load_modules() -> list[Module]:
    modules: list[Module] = []
    seen: set[str] = set()
    for parts in _rows(MODULES_FILE):
        if len(parts) != 9:
            raise SelectionError(
                f"modules.conf row {parts[0] if parts else '?'} has {len(parts)} fields, expected 9"
            )
        module = Module(
            id=parts[0],
            module_class=parts[1],
            label=parts[2],
            url=parts[3],
            ref=parts[4],
            commit=parts[5],
            requires=parts[6],
            default_on=parts[7] == "1",
            notes=parts[8],
        )
        if module.id in seen:
            raise SelectionError(f"duplicate module id {module.id}")
        seen.add(module.id)
        if not SHA_RE.fullmatch(module.commit):
            raise SelectionError(f"{module.id}: commit must be 40 hex characters")
        if module.module_class not in MODULE_CLASSES:
            raise SelectionError(f"{module.id}: unknown module class")
        modules.append(module)
    by_id = {item.id: item for item in modules}
    for module in modules:
        if module.requires and module.requires not in by_id:
            raise SelectionError(f"{module.id}: requires unknown module {module.requires}")
    return modules


def load_catalog() -> list[CatalogRealm]:
    text = CATALOG_FILE.read_text(encoding="utf-8")
    match = re.search(r"catalog_lines\(\) \{\s*cat <<'EOF'\n(.*?\n)EOF", text, re.S)
    if not match:
        raise SelectionError("could not read catalog_lines from catalog.sh")
    realms: list[CatalogRealm] = []
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 18:
            raise SelectionError(f"catalog row {parts[0] if parts else '?'} has {len(parts)} fields")
        realms.append(
            CatalogRealm(
                short=parts[0],
                core=parts[1],
                kind=parts[2],
                image=parts[3],
                client=parts[4],
                proto=parts[5],
                auth_bin=parts[6],
                world_bin=parts[7],
                auth_port=parts[8],
                world_port=parts[9],
                rest_port=parts[10],
                loopback=parts[11],
                expansion=parts[12],
                hotfix=parts[13],
                realm_name=parts[14],
                db_repo=parts[15],
                db_branch=parts[16],
                db_kind=parts[17],
            )
        )
    return realms


def selection_path() -> Path:
    override = os.environ.get("WOW_SELECTION_FILE")
    if override:
        return Path(override)
    return ROOT / ".run" / "selection.conf"


def servers_dir() -> Path:
    override = os.environ.get("WOW_SERVERS_DIR")
    if override:
        return Path(override)
    return ROOT / "servers"


def clients_dir() -> Path:
    override = os.environ.get("WOW_CLIENTS_DIR")
    if override:
        return Path(override)
    return ROOT / "clients"


def backups_dir() -> Path:
    override = os.environ.get("WOW_BACKUP_DIR") or _dotenv().get("BACKUP_DIR", "")
    if override:
        return Path(override)
    return ROOT / "backups"


def load_selection() -> dict[str, Choice]:
    path = selection_path()
    if not path.is_file():
        return {}
    found: dict[str, Choice] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if len(parts) != 3:
            raise SelectionError(f"{path}:{lineno}: expected short|project|modules")
        short, project_id, mods = parts
        modules = [item for item in mods.split(",") if item]
        found[short] = Choice(project_id, modules)
    return found


def save_selection(choices: dict[str, Choice], projects: list[Project]) -> None:
    """Write only rows that differ from the default core with no modules."""
    defaults = {item.short: item.id for item in projects if item.is_default}
    lines: list[str] = []
    for short in sorted(choices):
        choice = choices[short]
        modules = ",".join(choice.modules)
        if choice.project_id == defaults.get(short) and not modules:
            continue
        lines.append(f"{short}|{choice.project_id}|{modules}")
    path = selection_path()
    if not lines:
        if path.is_file() and "WOW_SELECTION_FILE" not in os.environ:
            path.unlink()
        elif path.is_file():
            path.write_text("", encoding="utf-8")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def projects_by_id(projects: list[Project]) -> dict[str, Project]:
    return {item.id: item for item in projects}


def modules_by_id(modules: list[Module]) -> dict[str, Module]:
    return {item.id: item for item in modules}


def active_choice(short: str, projects: list[Project], choices: dict[str, Choice]) -> Choice:
    if short in choices:
        return choices[short]
    for project in projects:
        if project.short == short and project.is_default:
            return Choice(project.id, [])
    raise SelectionError(f"no default project for {short}")


def active_project(short: str, projects: list[Project], choices: dict[str, Choice]) -> Project:
    choice = active_choice(short, projects, choices)
    found = projects_by_id(projects).get(choice.project_id)
    if found is None:
        raise SelectionError(f"{short}: unknown project {choice.project_id}")
    if found.short != short:
        raise SelectionError(f"{choice.project_id} belongs to {found.short}, not {short}")
    return found


def _split_pin(token: str) -> tuple[str, str, str]:
    name, url, commit = token.split("@", 2)
    return name, url, commit


def validate_modules(project: Project, tokens: list[str], modules: list[Module]) -> list[str]:
    if project.module_class == "none" or project.module_class == "vmangos-variant":
        if tokens:
            raise SelectionError(
                f"{project.id} does not take modules ({project.module_class}). "
                "VMaNGOS playerbots is the separate vmangos-playerbots core."
            )
        return []
    known = modules_by_id(modules)
    cleaned: list[str] = []
    for token in tokens:
        if token in cleaned:
            continue
        if project.module_class == "cmangos-playerbots":
            if token != "playerbots":
                raise SelectionError(f"{project.id} only accepts the playerbots module")
            if "playerbots" not in known:
                raise SelectionError("modules.conf is missing playerbots")
            cleaned.append(token)
            continue
        if project.module_class == "trinity-scripts":
            if "@" in token or not SCRIPT_RE.fullmatch(token):
                raise SelectionError(
                    f"{token} is not a TrinityCore script module name. "
                    "Names are applied at build from the 3.3.5 checkout, for example Spells."
                )
            cleaned.append(token)
            continue
        if project.module_class != "azerothcore":
            raise SelectionError(f"{project.id}: unsupported module class")
        if "@" in token:
            if token.count("@") != 2:
                raise SelectionError(f"{token}: extra modules are name@url@commit")
            name, url, commit = _split_pin(token)
            if not NAME_RE.fullmatch(name):
                raise SelectionError(f"{name}: module name must be letters, numbers, _ or -")
            if not url.startswith("https://") or "github.com/" not in url:
                raise SelectionError(f"{name}: pin a public https://github.com URL")
            if not SHA_RE.fullmatch(commit):
                raise SelectionError(f"{name}: commit must be 40 hex characters")
            cleaned.append(f"{name}@{url}@{commit}")
            continue
        module = known.get(token)
        if module is None or module.module_class != "azerothcore":
            raise SelectionError(
                f"unknown module {token}. Curated ids are in modules.conf. "
                "Any other module is name@https://github.com/...git@<40 hex commit>."
            )
        cleaned.append(token)
    selected = set()
    for token in cleaned:
        selected.add(token.split("@", 1)[0])
    for token in cleaned:
        module = known.get(token)
        if module and module.requires and module.requires not in selected:
            raise SelectionError(f"{module.id} requires {module.requires}")
    return sorted(cleaned)


def apply_changes(
    sets: list[tuple[str, str]],
    module_flags: list[tuple[str, str]],
) -> dict[str, Choice]:
    projects = load_projects()
    modules = load_modules()
    by_id = projects_by_id(projects)
    choices = load_selection()
    module_groups: dict[str, list[str]] = {}
    for short, token in module_flags:
        module_groups.setdefault(short, []).append(token)
    touched = set(module_groups)
    for short, project_id in sets:
        project = by_id.get(project_id)
        if project is None:
            raise SelectionError(f"unknown project {project_id}")
        if project.short != short:
            raise SelectionError(f"{project_id} is a {project.short} core, not {short}")
        if not project.selectable:
            raise SelectionError(f"{project_id} is not selectable. {project.notes}")
        tokens = module_groups.get(short, [])
        choices[short] = Choice(project_id, validate_modules(project, tokens, modules))
        touched.discard(short)
    for short in touched:
        current = active_choice(short, projects, choices)
        project = by_id.get(current.project_id)
        if project is None:
            raise SelectionError(f"{short}: saved project {current.project_id} is gone")
        if not project.selectable:
            raise SelectionError(f"{project.id} is not selectable. {project.notes}")
        choices[short] = Choice(project.id, validate_modules(project, module_groups[short], modules))
    save_selection(choices, projects)
    return choices


def bash_assignments(pairs: list[tuple[str, str]]) -> str:
    lines = []
    for key, value in pairs:
        if key not in OVERLAY_KEYS:
            raise SelectionError(f"refusing to export {key}")
        # shlex.quote leaves hyphens bare. catalog.sh only evals single-quoted lines.
        if "'" in value or "\n" in value or "\r" in value:
            raise SelectionError(f"refusing to export unsafe assignment for {key}")
        line = f"{key}='{value}'"
        if not ASSIGN_RE.fullmatch(line):
            raise SelectionError(f"refusing to export unsafe assignment for {key}")
        lines.append(line)
    return "\n".join(lines)


def bash_overlay(short: str) -> str:
    projects = load_projects()
    choices = load_selection()
    if short not in choices:
        return ""
    project = active_project(short, projects, choices)
    choice = choices[short]
    modules = ",".join(choice.modules)
    if project.is_default:
        if not modules:
            return ""
        return bash_assignments([("CATALOG_MODULES", modules)])
    pairs = [
        ("CATALOG_CORE", project.id),
        ("CATALOG_KIND", project.kind),
        ("CATALOG_IMAGE", project.image),
        ("CATALOG_AUTH_BIN", project.auth_bin),
        ("CATALOG_WORLD_BIN", project.world_bin),
        ("CATALOG_PROTO", project.proto),
        ("CATALOG_AUTH_PORT", project.auth_port),
        ("CATALOG_WORLD_PORT", project.world_port),
        ("CATALOG_REST_PORT", project.rest_port),
        ("CATALOG_DB_REPO", project.db_repo),
        ("CATALOG_DB_BRANCH", project.db_branch),
        ("CATALOG_DB_KIND", project.db_kind),
        ("CATALOG_MODULES", modules),
    ]
    return bash_assignments(pairs)


def core_id_path(short: str) -> Path:
    return servers_dir() / short / ".core-id"


def read_core_id(short: str) -> tuple[str, list[str]] | None:
    path = core_id_path(short)
    if not path.is_file():
        return None
    core = ""
    modules: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("core="):
            core = raw.split("=", 1)[1].strip()
        elif raw.startswith("modules="):
            modules = [item for item in raw.split("=", 1)[1].split(",") if item]
    if not core:
        return None
    return core, modules


def write_core_id(short: str, project_id: str, modules: list[str]) -> None:
    path = core_id_path(short)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = f"core={project_id}\nmodules={','.join(sorted(modules))}\n"
    path.write_text(body, encoding="utf-8")


def _build_info_paths(client: str) -> list[Path]:
    root = clients_dir() / client
    direct = root / ".build.info"
    if direct.is_file():
        return [direct]
    if not root.is_dir():
        return []
    # Some installs keep the product one folder down, next to other Blizzard games.
    return sorted(path for path in root.glob("*/.build.info") if path.is_file())


def _versions_in_build_info(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 2:
        return []
    header = lines[0].split("|")
    try:
        column = next(i for i, name in enumerate(header) if name.startswith("Version!"))
    except StopIteration:
        return []
    product_column = next((i for i, name in enumerate(header) if name.startswith("Product!")), None)
    found: list[str] = []
    for line in lines[1:]:
        parts = line.split("|")
        if len(parts) <= column:
            continue
        if product_column is not None and product_column < len(parts):
            product = parts[product_column].strip()
            # An empty product is a sibling Blizzard game, such as Warcraft III.
            if not product.startswith("wow"):
                continue
        version = parts[column].strip()
        if version and version not in found:
            found.append(version)
    return found


def client_versions(client: str) -> list[str]:
    if not client:
        return []
    found: list[str] = []
    for path in _build_info_paths(client):
        for version in _versions_in_build_info(path):
            if version not in found:
                found.append(version)
    return found


def _versions_match(expect: str, versions: list[str]) -> bool:
    return any(version == expect or version.startswith(expect + ".") for version in versions)


def check_client_build(project: Project) -> str | None:
    """Return an error string when launch must stop. Warnings go to stderr and return None."""
    if not project.expect_build or project.launch_policy == "ok":
        return None
    versions = client_versions(project.client)
    matched = _versions_match(project.expect_build, versions)
    shown = ", ".join(versions) if versions else "unreadable"
    if project.launch_policy == "warn":
        if not matched:
            print(
                f"{project.short}: client build {shown} does not match data build {project.expect_build}. "
                "Launch is allowed. The removed Dragonflight 55664 auth seed stays removed.",
                file=sys.stderr,
            )
        return None
    if matched:
        return None
    return (
        f"{project.short}: refusing to launch. Core expects {project.expect_build}; "
        f"client {project.client} is {shown}. {project.notes}"
    )


def install_matches(short: str) -> bool:
    projects = load_projects()
    choices = load_selection()
    project = active_project(short, projects, choices)
    choice = active_choice(short, projects, choices)
    installed = read_core_id(short)
    if installed is None:
        return project.is_default and not choice.modules
    core, modules = installed
    return core == project.id and modules == sorted(choice.modules)


def launch_check(short: str) -> int:
    projects = load_projects()
    catalog = {item.short: item for item in load_catalog()}
    if short not in catalog:
        print(f"{short}: not a realm slot. Nothing to launch.", file=sys.stderr)
        return 1
    choices = load_selection()
    project = active_project(short, projects, choices)
    if not project.selectable:
        print(f"{short}: {project.id} is not selectable. {project.notes}", file=sys.stderr)
        return 1
    build_error = check_client_build(project)
    if build_error:
        print(build_error, file=sys.stderr)
        return 1
    choice = active_choice(short, projects, choices)
    installed = read_core_id(short)
    wanted = sorted(choice.modules)
    if installed is None:
        if project.is_default and not wanted:
            return 0
        print(
            f"{short}: no servers/{short}/.core-id for {project.id}. "
            "Refusing to launch a core that has not been built into this slot.",
            file=sys.stderr,
        )
        _print_switch_help(short, project, catalog[short].core, built=False)
        return 1
    core, modules = installed
    if core == project.id and modules == wanted:
        return 0
    print(
        f"{short}: installed core is {core} (modules: {', '.join(modules) or 'none'}); "
        f"selection is {project.id} (modules: {', '.join(wanted) or 'none'}).",
        file=sys.stderr,
    )
    _print_switch_help(short, project, core, built=True)
    return 1


def _print_switch_help(short: str, project: Project, installed_core: str, built: bool) -> None:
    print(f"  ./scripts/select-project.py --build {short}", file=sys.stderr)
    if installed_core != project.id:
        print(f"  ./scripts/select-project.py --reimport {short}", file=sys.stderr)
        print(
            "Reimport dumps that realm's databases, then drops only those databases. "
            "It does not remove the shared MariaDB volume.",
            file=sys.stderr,
        )
        return
    if not built:
        print("Build before launch. A module change does not need a database reimport.", file=sys.stderr)


def stamp(short: str, built_core: str) -> None:
    projects = load_projects()
    choices = load_selection()
    project = active_project(short, projects, choices)
    if built_core and built_core != project.id:
        raise SelectionError(
            f"not stamping {short}: built {built_core} but the selection is {project.id}"
        )
    choice = active_choice(short, projects, choices)
    validate_modules(project, choice.modules, load_modules())
    write_core_id(short, project.id, choice.modules)


def catalog_databases(short: str) -> list[str]:
    realms = {item.short: item for item in load_catalog()}
    realm = realms.get(short)
    if realm is None:
        raise SelectionError(f"{short} is not a catalog realm")
    names = [f"{short}_auth", f"{short}_characters", f"{short}_world"]
    if realm.hotfix in {"hotfix", "hotfixes"}:
        names.append(f"{short}_{realm.hotfix}")
    return names


def _dotenv() -> dict[str, str]:
    path = ROOT / ".env"
    found: dict[str, str] = {}
    if not path.is_file():
        return found
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        found[key.strip()] = value.strip().strip('"').strip("'")
    return found


def _mysql_client() -> tuple[str, str, str, str, str]:
    env = _dotenv()
    host = "127.0.0.1"
    port = env.get("MYSQL_PUBLISH_PORT", "13306")
    user = env.get("MYSQL_USER", "wow")
    password = env.get("MYSQL_PASSWORD", "wow")
    return host, port, user, password, password


def _cnf_quote(value: str) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\r", "").replace("\n", "")
    return f'"{escaped}"'


def _client_defaults_file(host: str, port: str, user: str, password: str) -> Path:
    """Mode-0600 client defaults. Caller deletes the file."""
    fd, name = tempfile.mkstemp(prefix="wow-my-", suffix=".cnf")
    path = Path(name)
    try:
        os.fchmod(fd, 0o600)
        payload = (
            "[client]\n"
            f"host={_cnf_quote(host)}\n"
            f"port={_cnf_quote(port)}\n"
            f"user={_cnf_quote(user)}\n"
            f"password={_cnf_quote(password)}\n"
        )
        os.write(fd, payload.encode())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        os.close(fd)
    return path


def _mysql_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("MYSQL_PWD", None)
    return env


def dump_databases(names: list[str], dest: Path) -> list[tuple[str, Path]]:
    """Dump the named databases into dest. Raise SelectionError before any drop.

    A database that does not exist is skipped. An empty or failed dump of a
    database that does exist raises, and nothing has been dropped.
    """
    dump_bin = shutil.which("mysqldump") or shutil.which("mariadb-dump")
    if not dump_bin:
        raise SelectionError("mysqldump is required. No databases were dropped.")
    host, port, user, password, _pwd = _mysql_client()
    dest.mkdir(parents=True, exist_ok=True)
    dumped: list[tuple[str, Path]] = []
    defaults = _client_defaults_file(host, port, user, password)
    try:
        child_env = _mysql_env()
        for name in names:
            outfile = dest / f"{name}.sql"
            cmd = [
                dump_bin,
                f"--defaults-extra-file={defaults}",
                "-h",
                host,
                "-P",
                port,
                "-u",
                user,
                "--single-transaction",
                "--routines",
                "--databases",
                name,
            ]
            with outfile.open("wb") as handle:
                result = subprocess.run(cmd, stdout=handle, stderr=subprocess.PIPE, env=child_env)
            if result.returncode != 0:
                err = result.stderr.decode("utf-8", errors="replace")
                if "Unknown database" in err or "ERROR 1049" in err:
                    outfile.unlink(missing_ok=True)
                    print(f"{name}: not present, nothing to dump")
                    continue
                outfile.unlink(missing_ok=True)
                raise SelectionError(f"{name}: mysqldump failed. No databases were dropped.\n{err}")
            if outfile.stat().st_size <= 0:
                outfile.unlink(missing_ok=True)
                raise SelectionError(f"{name}: dump is empty. No databases were dropped.")
            dumped.append((name, outfile))
        return dumped
    finally:
        defaults.unlink(missing_ok=True)


def drop_databases(names: list[str]) -> int:
    """Drop databases that were dumped. Return 0, or 1 after a failed DROP."""
    mysql_bin = shutil.which("mysql") or shutil.which("mariadb")
    if not mysql_bin:
        print("mysql is required. No databases were dropped.", file=sys.stderr)
        return 1
    host, port, user, password, _pwd = _mysql_client()
    defaults = _client_defaults_file(host, port, user, password)
    try:
        child_env = _mysql_env()
        dropped: list[str] = []
        for name in names:
            result = subprocess.run(
                [
                    mysql_bin,
                    f"--defaults-extra-file={defaults}",
                    "-h",
                    host,
                    "-P",
                    port,
                    "-u",
                    user,
                    "-e",
                    f"DROP DATABASE `{name}`",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=child_env,
            )
            if result.returncode != 0:
                print(result.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
                already = ", ".join(dropped) or "none"
                print(
                    f"Stopped after a failed DROP. Databases already dropped: {already}.",
                    file=sys.stderr,
                )
                return 1
            dropped.append(name)
        if dropped:
            print("Dropped: " + ", ".join(dropped))
        return 0
    finally:
        defaults.unlink(missing_ok=True)


def reimport(short: str) -> int:
    """Dump one realm's databases, then drop only those databases."""
    names = catalog_databases(short)
    stamp_name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = backups_dir() / short / stamp_name
    try:
        dumped = dump_databases(names, dest)
    except SelectionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if not dumped:
        print(f"{short}: no databases to dump. Nothing was dropped.")
        return 0
    if drop_databases([name for name, _path in dumped]) != 0:
        print(f"Dumps remain in {dest}. The shared volume was not removed.", file=sys.stderr)
        return 1
    marker = servers_dir() / short / ".reimport"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(stamp_name + "\n", encoding="utf-8")
    host, port, user, _password, _pwd = _mysql_client()
    print(f"Dumped {short} to {dest}")
    print("Restore with the password from .env (the shared volume was not removed):")
    for name, path in dumped:
        print(f"  mysql -h {host} -P {port} -u {user} -p < {path}")
    print(f"Wrote {marker}. The next init imports the selected core and removes that marker.")
    return 0


def _module_summary(choice: Choice) -> str:
    if not choice.modules:
        return "-"
    names = []
    for token in choice.modules:
        names.append(token.split("@", 1)[0])
    return ",".join(names)


def _row_text(columns: list[str], widths: list[int]) -> str:
    return "  ".join(text.ljust(width) for text, width in zip(columns, widths))


def render_list() -> str:
    projects = load_projects()
    choices = load_selection()
    catalog = load_catalog()
    catalog_shorts = {item.short for item in catalog}
    header = ["SHORT", "CLIENT", "BUILD", "CORE", "MODULES", "INSTALL"]
    rows = [header]
    for realm in catalog:
        project = active_project(realm.short, projects, choices)
        choice = active_choice(realm.short, projects, choices)
        versions = client_versions(project.client or realm.client)
        build = versions[0] if versions else "-"
        if project.expect_build and not _versions_match(project.expect_build, versions):
            build = f"{build}!={project.expect_build}"
        rows.append(
            [
                realm.short,
                realm.client,
                build,
                project.label,
                _module_summary(choice),
                "match" if install_matches(realm.short) else "rebuild",
            ]
        )
    rows.append(["---", "unavailable classic clients", "", "", "", ""])
    for project in projects:
        if project.short in catalog_shorts or project.selectable:
            continue
        rows.append([project.short, project.client or "-", project.expect_build or "-", project.label, "-", "no"])
    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    lines = [_row_text(row, widths) for row in rows]
    lines.append("")
    lines.append("Unavailable rows have no build or launch. Enter the menu to read why.")
    for project in projects:
        if not project.selectable:
            lines.append(f"  {project.short}: {project.notes}")
    return "\n".join(lines)


def _run(cmd: list[str]) -> int:
    print("+ " + " ".join(shlex.quote(part) for part in cmd))
    return subprocess.call(cmd)


def build_short(short: str) -> int:
    projects = load_projects()
    choices = load_selection()
    project = active_project(short, projects, choices)
    if not project.selectable or not project.repo_key:
        print(f"{short}: {project.notes}", file=sys.stderr)
        return 1
    dockerfile = ROOT / "docker" / project.repo_key / "Dockerfile"
    if not dockerfile.is_file():
        print(f"Missing Dockerfile: {dockerfile}", file=sys.stderr)
        return 1
    return _run(
        [
            str(ROOT / "scripts" / "build-servers.sh"),
            "--only",
            project.repo_key,
            "--force",
        ]
    )


def launch_shorts(spec: str) -> int:
    shorts = [item.strip() for item in spec.split(",") if item.strip()]
    for short in shorts:
        if launch_check(short) != 0:
            return 1
    return _run([str(ROOT / "scripts" / "launch-servers.sh"), "up", ",".join(shorts)])


def _read_key() -> str:
    if not sys.stdin.isatty():
        return "q"
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x03":
            raise KeyboardInterrupt
        if char == "\x1b":
            return char + sys.stdin.read(2)
        return char
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _prompt(text: str) -> str:
    print(text, end="", flush=True)
    return sys.stdin.readline().rstrip("\n")


def menu() -> int:
    if not sys.stdin.isatty():
        print(render_list())
        print("No terminal attached. Use --set, --module, --build, and --launch.")
        return 0
    projects = load_projects()
    modules = load_modules()
    catalog = load_catalog()
    choices = load_selection()
    catalog_shorts = [item.short for item in catalog]
    extras = [
        project.short
        for project in projects
        if project.short not in catalog_shorts and not project.selectable
    ]
    rows = catalog_shorts + extras
    index = 0
    while True:
        os.system("clear")
        print("Realm cores. j/k move, Enter cycle core, m modules, b build, l launch, q save.")
        print()
        for pos, short in enumerate(rows):
            mark = ">" if pos == index else " "
            if short in catalog_shorts:
                project = active_project(short, projects, choices)
                choice = active_choice(short, projects, choices)
                state = "match" if install_matches(short) else "rebuild"
                print(f"{mark} {short:<16} {project.label:<32} {_module_summary(choice):<24} {state}")
            else:
                project = next(item for item in projects if item.short == short)
                print(f"{mark} {short:<16} not buildable")
                print(f"    {project.notes}")
        short = rows[index]
        key = _read_key()
        if key in {"q", "Q"}:
            save_selection(choices, projects)
            print(f"Saved {selection_path()}")
            return 0
        if key in {"j", "\x1b[B"}:
            index = (index + 1) % len(rows)
        elif key in {"k", "\x1b[A"}:
            index = (index - 1) % len(rows)
        elif key in {"\r", "\n"}:
            if short not in catalog_shorts:
                continue
            options = [item for item in projects if item.short == short and item.selectable]
            current = active_project(short, projects, choices)
            pos = next((i for i, item in enumerate(options) if item.id == current.id), 0)
            nxt = options[(pos + 1) % len(options)]
            choices[short] = Choice(nxt.id, [])
            save_selection(choices, projects)
        elif key in {"m", "M"}:
            if short not in catalog_shorts:
                continue
            project = active_project(short, projects, choices)
            print()
            if project.module_class in {"none", "vmangos-variant"}:
                print(project.notes or "This core has no module checkboxes.")
                if project.module_class == "vmangos-variant":
                    print("Playerbots for VMaNGOS is the vmangos-playerbots core, not a checkbox.")
                _prompt("Press Enter. ")
                continue
            if project.module_class == "trinity-scripts":
                print("TrinityCore 3.3.5 script names are read from the checkout at build time.")
                print("Enter names separated by commas, for example Spells,World. Empty clears them.")
            elif project.module_class == "cmangos-playerbots":
                print("Enter playerbots to enable CMaNGOS playerbots, or empty to disable.")
            else:
                print("Curated AzerothCore modules (all off unless you name them):")
                for module in modules:
                    if module.module_class != "azerothcore":
                        continue
                    need = f" requires {module.requires}" if module.requires else ""
                    print(f"  {module.id:<28} {module.label}{need}")
                print("Or pin another module as name@https://github.com/org/mod-name.git@<40 hex commit>.")
            raw = _prompt("Modules: ")
            tokens = [item.strip() for item in raw.split(",") if item.strip()]
            try:
                choices[short] = Choice(project.id, validate_modules(project, tokens, modules))
            except SelectionError as exc:
                print(exc)
                _prompt("Press Enter. ")
                continue
            save_selection(choices, projects)
        elif key in {"b", "B"}:
            if short not in catalog_shorts:
                continue
            save_selection(choices, projects)
            build_short(short)
            _prompt("Press Enter. ")
        elif key in {"l", "L"}:
            if short not in catalog_shorts:
                continue
            save_selection(choices, projects)
            launch_shorts(short)
            _prompt("Press Enter. ")


def install_short_for(core: str) -> str:
    for project in load_projects():
        if project.id == core or project.repo_key == core:
            return project.short
    raise SelectionError(f"unknown core {core}")


def print_core(short: str) -> str:
    projects = load_projects()
    return active_project(short, projects, load_selection()).id


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Select a core and modules per realm slot.")
    parser.add_argument("--list", action="store_true", help="print realms, cores, and classic rows that cannot build")
    parser.add_argument("--set", action="append", default=[], metavar="SHORT=PROJECT")
    parser.add_argument("--module", action="append", default=[], metavar="SHORT:MODULE")
    parser.add_argument("--build", metavar="SHORT", help="build the selected core for this realm")
    parser.add_argument("--launch", metavar="SHORTS", help="launch after the core-id check")
    parser.add_argument("--reimport", metavar="SHORT", help="dump then drop only this realm's databases")
    parser.add_argument("--bash-overlay", metavar="SHORT", help="print CATALOG_* assignments for eval")
    parser.add_argument("--launch-check", metavar="SHORT", help="exit 1 when the install does not match")
    parser.add_argument("--install-matches", metavar="SHORT", help="exit 1 when .core-id does not match")
    parser.add_argument("--stamp", metavar="SHORT", help="write servers/<short>/.core-id for the selection")
    parser.add_argument("--built-core", default="", help="core directory just compiled; must match the selection")
    parser.add_argument("--print-core", metavar="SHORT", help="print the selected project id")
    parser.add_argument("--install-short", metavar="CORE", help="print the realm slot for a core id")
    args = parser.parse_args(argv)

    try:
        if args.set or args.module:
            sets: list[tuple[str, str]] = []
            for item in args.set:
                if "=" not in item:
                    raise SelectionError(f"--set expects short=project, got {item}")
                short, project_id = item.split("=", 1)
                sets.append((short.strip(), project_id.strip()))
            modules: list[tuple[str, str]] = []
            for item in args.module:
                if ":" not in item:
                    raise SelectionError(f"--module expects short:name, got {item}")
                short, token = item.split(":", 1)
                modules.append((short.strip(), token.strip()))
            apply_changes(sets, modules)
        if args.bash_overlay:
            text = bash_overlay(args.bash_overlay)
            if text:
                sys.stdout.write(text + "\n")
            return 0
        if args.launch_check:
            return launch_check(args.launch_check)
        if args.install_matches:
            return 0 if install_matches(args.install_matches) else 1
        if args.stamp:
            stamp(args.stamp, args.built_core)
            return 0
        if args.print_core:
            print(print_core(args.print_core))
            return 0
        if args.install_short:
            print(install_short_for(args.install_short))
            return 0
        if args.reimport:
            return reimport(args.reimport)
        if args.build:
            return build_short(args.build)
        if args.launch:
            return launch_shorts(args.launch)
        if args.list or not sys.stdin.isatty():
            print(render_list())
            return 0
        return menu()
    except SelectionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
