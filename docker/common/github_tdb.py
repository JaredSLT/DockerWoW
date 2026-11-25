#!/usr/bin/env python3
"""Select a TrinityCore-style TDB GitHub release.

Usage:
  github_tdb.py owner/repo [prefix]
  github_tdb.py --id owner/repo [prefix]

Prints download_url<TAB>filename lines, or with --id one identity line
(tag plus asset names). Exit 0 when a release matches, 2 when none does.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def get(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "wow-setup", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        print(f"WARNING: GitHub {url}: {exc}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"WARNING: GitHub {url}: {exc}", file=sys.stderr)
        return None


def wanted(name):
    low = name.lower()
    if not any(low.endswith(ext) for ext in (".sql", ".sql.gz", ".7z", ".zip")):
        return False
    return low.startswith("tdb") or "world" in low or "hotfix" in low


def picked(rel):
    return [a for a in (rel.get("assets") or []) if wanted(a.get("name") or "")]


def matches(rel, prefix):
    if not prefix:
        return True
    tag = rel.get("tag_name") or ""
    title = rel.get("name") or ""
    return tag.startswith(prefix) or title.startswith(prefix)


def choose(spec, prefix):
    if "/" not in spec:
        return None
    owner, repo = spec.split("/", 1)
    base = f"https://api.github.com/repos/{owner}/{repo}"
    if prefix:
        quoted = urllib.parse.quote(prefix, safe="")
        rel = get(f"{base}/releases/tags/{quoted}")
        if rel and matches(rel, prefix) and picked(rel):
            return rel
    for page in (1, 2):
        releases = get(f"{base}/releases?per_page=100&page={page}") or []
        if not isinstance(releases, list):
            return None
        for rel in releases:
            if matches(rel, prefix) and picked(rel):
                return rel
        if len(releases) < 100:
            break
    return None


def main(argv):
    ident = False
    args = argv[1:]
    if args and args[0] == "--id":
        ident = True
        args = args[1:]
    if not args:
        print("usage: github_tdb.py [--id] owner/repo [prefix]", file=sys.stderr)
        return 1
    spec = args[0]
    prefix = args[1] if len(args) > 1 else ""
    rel = choose(spec, prefix)
    if not rel:
        hint = f" matching {prefix}" if prefix else ""
        print(f"WARNING: no TDB release{hint} in {spec}", file=sys.stderr)
        return 2
    assets = picked(rel)
    if ident:
        names = " ".join(sorted(a.get("name") or "" for a in assets))
        print(f"{rel.get('tag_name') or ''} {names}".rstrip())
        return 0
    for asset in assets:
        print(f"{asset['browser_download_url']}\t{asset['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
