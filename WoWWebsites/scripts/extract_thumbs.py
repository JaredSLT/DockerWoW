#!/usr/bin/env python3
"""Build client thumbnails for one expansion, or every expansion.

Uses LibWoW to read the lab client (MPQ or CASC) and writes PNGs under
static/img/client/<id>/. Those files are generated game art and are gitignored.

    python3 scripts/extract_thumbs.py vanilla
    python3 scripts/extract_thumbs.py --all
    python3 scripts/extract_thumbs.py wod --listfile /path/to/listfile.csv

--all walks the expansions in patch order. When a CASC client has no
SpellIcon table, the script passes names.txt from the newest earlier
extract so icons that still exist under the same path are written.
Warlords and Legion roots on this lab do not resolve Interface paths;
those two need a community listfile (fdid;path).

LibWoW is expected at ../LibWoW with build/libwow.a. Override with
LIBWOW. The client tree is $WOW_LAB/clients. When WOW_LAB is unset, that
is the parent of this website directory.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBWOW = Path(os.environ.get("LIBWOW", ROOT.parent / "LibWoW"))
BIN = Path(__file__).resolve().parent / "extract_thumbs.bin"
SRC = Path(__file__).resolve().parent / "extract_thumbs.c"


def build() -> None:
    lib = LIBWOW / "build" / "libwow.a"
    inc = LIBWOW / "include"
    if not lib.is_file():
        sys.exit(f"missing {lib}; build LibWoW first (cmake --build build)")
    if BIN.is_file() and BIN.stat().st_mtime >= SRC.stat().st_mtime:
        return
    cmd = [
        "cc",
        "-O2",
        f"-I{inc}",
        str(SRC),
        str(lib),
        "-lpng",
        "-lz",
        "-lbz2",
        "-llzma",
        "-llz4",
        "-ljpeg",
        "-o",
        str(BIN),
    ]
    print(" ".join(cmd), file=sys.stderr)
    subprocess.check_call(cmd)


def clients_root() -> Path:
    lab = Path(os.environ["WOW_LAB"]) if os.environ.get("WOW_LAB") else ROOT.parent
    return lab / "clients"


def expansions():
    sys.path.insert(0, str(ROOT))
    from wowweb.catalog import list_expansions

    return list_expansions()


def newest_names(out_root: Path, before_id: str, order: list[str]) -> Path | None:
    if before_id not in order:
        return None
    for exp_id in reversed(order[: order.index(before_id)]):
        path = out_root / exp_id / "names.txt"
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def run_one(exp, out_root: Path, listfile: str | None, names: Path | None, limit: int | None, force: bool) -> int:
    client = clients_root() / exp.client
    out = out_root / exp.id
    existing = list((out / "icons").glob("*.png")) if (out / "icons").is_dir() else []
    if existing and len(existing) >= 50 and not force and not limit:
        print(f"{exp.id}: {len(existing)} icons already extracted", file=sys.stderr)
        return 0
    if not client.is_dir():
        print(f"{exp.id}: no client at {client}", file=sys.stderr)
        return 1
    cmd = [str(BIN), str(client), str(out)]
    if listfile:
        cmd += ["--listfile", listfile]
    elif names is not None:
        cmd += ["--names", str(names)]
    if limit:
        cmd += ["--limit", str(limit)]
    print(f"{exp.id}: {client}", file=sys.stderr)
    result = subprocess.run(cmd)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("expansion", nargs="?", help="expansion id, or omit with --all")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--listfile", help="community listfile, lines fdid;path")
    parser.add_argument("--names", type=Path, help="icon paths from an earlier extract")
    parser.add_argument("--limit", type=int, help="stop after this many written files")
    parser.add_argument("--force", action="store_true", help="re-extract even if PNGs are already present")
    parser.add_argument("--out", type=Path, default=ROOT / "static" / "img" / "client")
    args = parser.parse_args(argv)

    exps = expansions()
    order = [exp.id for exp in exps]
    chosen = exps if args.all else [exp for exp in exps if exp.id == args.expansion]
    if not chosen:
        parser.error("name an expansion id, or pass --all")
    build()
    rc = 0
    for exp in chosen:
        names = args.names
        if names is None and args.all and not args.listfile:
            names = newest_names(args.out, exp.id, order)
        status = run_one(exp, args.out, args.listfile, names, args.limit, args.force)
        if status != 0:
            rc = status
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
