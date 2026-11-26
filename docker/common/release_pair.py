#!/usr/bin/env python3
"""Print the core ref and database identity that belong together.

Usage:
  release_pair.py --short SHORT [--state DIR]

stdout: <mode>\\t<core_ref>\\t<kind>\\t<db_id>
mode is float, pair, pinned, or wod. kind is branch or tag.
Exit 1 on an unknown short. Exit 0 otherwise.

WOW_FAKE_PAIRS is a directory of <short> files. When <short> exists, that
line is printed and GitHub is not called. Network goes through github_tdb.py
and git ls-remote (repos.sh repo_sha).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import github_tdb  # noqa: E402

CATALOG = ROOT / "docker" / "runtime" / "catalog.sh"
REPOS = HERE / "repos.sh"

# Frozen expansions. The catalog stores the prefix. Legion's core tag and
# TDB735 advance only when the same release tag exists on the core repo.
FROZEN_PREFIXES = (
    "TDB1127",
    "TDB1027",
    "TDB927",
    "TDB837",
    "TDB735",
    "TDB343",
)


def frozen_prefix(db_branch: str) -> str | None:
    for prefix in FROZEN_PREFIXES:
        if db_branch == prefix or db_branch.startswith(prefix + "."):
            return prefix
    return None


def load_realm(short: str) -> dict[str, str] | None:
    script = r"""
set -euo pipefail
source "$1"
source "$2"
catalog_load "$3"
repo_lookup "$CATALOG_CORE"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "$CATALOG_CORE" \
  "$CATALOG_DB_KIND" \
  "$CATALOG_DB_REPO" \
  "$CATALOG_DB_BRANCH" \
  "$REPO_URL" \
  "$REPO_REF" \
  "$REPO_KIND"
"""
    proc = subprocess.run(
        ["bash", "-c", script, "bash", str(CATALOG), str(REPOS), short],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    parts = proc.stdout.rstrip("\n").split("\t")
    if len(parts) != 7 or not parts[0] or not parts[4] or not parts[5] or not parts[6]:
        return None
    return {
        "core": parts[0],
        "db_kind": parts[1],
        "db_repo": parts[2],
        "db_branch": parts[3],
        "url": parts[4],
        "ref": parts[5],
        "kind": parts[6],
    }


def core_has_tag(url: str, tag: str) -> bool:
    proc = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1" && repo_sha "$2" "$3" tag >/dev/null',
            "bash",
            str(REPOS),
            url,
            tag,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _fake_line(short: str) -> str | None:
    root = os.environ.get("WOW_FAKE_PAIRS")
    if not root:
        return None
    path = Path(root) / short
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return ""
    return text.splitlines()[0].strip()


def _saved(state_dir: Path, short: str) -> tuple[str, str, str, str] | None:
    path = state_dir / f"{short}.pair"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    parts = text.splitlines()[0].split("\t")
    if len(parts) != 4 or not parts[1] or not parts[2] or not parts[3]:
        return None
    return parts[0], parts[1], parts[2], parts[3]


def _pinned_fallback(info: dict[str, str], prefix: str, state_dir: Path, short: str) -> str:
    saved = _saved(state_dir, short)
    if saved is not None:
        _mode, ref, kind, db_id = saved
        return f"pinned\t{ref}\t{kind}\t{db_id}"
    db_id = info["ref"] if info["ref"].startswith(prefix) else prefix
    return f"pinned\t{info['ref']}\t{info['kind']}\t{db_id}"


def resolve(short: str, state_dir: Path) -> str:
    """Return one pair line. Raise KeyError when short is unknown."""
    fake = _fake_line(short)
    if fake is not None:
        return fake
    info = load_realm(short)
    if info is None:
        raise KeyError(short)
    if info["db_kind"] == "wod":
        return f"wod\t{info['ref']}\t{info['kind']}\twod-local"
    prefix = None
    if info["db_kind"] == "tdb-github":
        prefix = frozen_prefix(info["db_branch"])
    if prefix:
        # Newest database tag only. An older tag is not a reason to move,
        # and Legion does not advance the core tag without that database tag.
        tag = ""
        if info["db_repo"]:
            tag = github_tdb.newest_tag(info["db_repo"], prefix) or ""
        if tag and core_has_tag(info["url"], tag):
            return f"pair\t{tag}\ttag\t{tag}"
        return _pinned_fallback(info, prefix, state_dir, short)
    if info["kind"] == "branch":
        db_id = info["db_branch"] or "none"
        return f"float\t{info['ref']}\tbranch\t{db_id}"
    db_id = info["db_branch"] or "none"
    return f"pinned\t{info['ref']}\t{info['kind']}\t{db_id}"


def main(argv: list[str]) -> int:
    short = ""
    state = ROOT / ".run" / "git-revs"
    args = argv[1:]
    index = 0
    while index < len(args):
        item = args[index]
        if item == "--short" and index + 1 < len(args):
            short = args[index + 1]
            index += 2
            continue
        if item == "--state" and index + 1 < len(args):
            state = Path(args[index + 1])
            index += 2
            continue
        print(
            "usage: release_pair.py --short SHORT [--state DIR]",
            file=sys.stderr,
        )
        return 1
    if not short:
        print(
            "usage: release_pair.py --short SHORT [--state DIR]",
            file=sys.stderr,
        )
        return 1
    try:
        print(resolve(short, state))
    except KeyError:
        print(f"unknown short: {short}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
