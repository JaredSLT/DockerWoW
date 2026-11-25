#!/usr/bin/env python3
"""Serve a last-patch World of Warcraft community site for one expansion."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wowweb.catalog import list_expansions, resolve
from wowweb.lab import load_lab, mysql_reachable, realm_status
from wowweb.http import ROOT, make_server


def cmd_list(lab_root: Path | None) -> int:
    cfg = load_lab(lab_root)
    db = mysql_reachable(cfg)
    print(f"{'id':14} {'patch':8} {'lab':12} {'world':6} {'maria':5} {'realm'}")
    for exp in list_expansions():
        st = realm_status(cfg, exp) if db else {"up": False, "db": False}
        print(
            f"{exp.id:14} {exp.last_patch:8} {exp.lab_short:12} {exp.world_port:<6} "
            f"{'yes' if st.get('db') else 'no':5} {'up' if st.get('up') else 'down'}"
        )
    if not db:
        print("\nMariaDB is not reachable at 127.0.0.1:13306. Static pages still serve.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("expansion", nargs="?", help="expansion id (vanilla, tbc, wotlk, …)")
    p.add_argument("--list", action="store_true", help="list expansions and lab status")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=18765)
    p.add_argument("--lab", type=Path, default=None, help="path to the private-server lab")
    p.add_argument("--data", type=Path, default=ROOT / "data", help="forum/session data directory")
    args = p.parse_args(argv)

    if args.list or args.expansion == "list":
        return cmd_list(args.lab)
    if args.expansion is None:
        p.print_help()
        print("\nExpansions:")
        for exp in list_expansions():
            print(f"  {exp.id:14} {exp.name} ({exp.last_patch})")
        return 2

    exp = resolve(args.expansion or "")
    if not exp:
        print(f"Unknown expansion: {args.expansion}", file=sys.stderr)
        print("Use --list to see ids.", file=sys.stderr)
        return 2

    httpd = make_server(exp, args.host, args.port, args.lab, args.data)
    print(f"Serving {exp.name} ({exp.last_patch}) at http://{args.host}:{args.port}/wow/")
    print(f"Lab short={exp.lab_short} world=127.0.0.1:{exp.world_port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
