#!/usr/bin/env python3
"""Select a TrinityCore-style TDB GitHub release.

Usage:
  github_tdb.py [--id] owner/repo [prefix]
  github_tdb.py --assets owner/repo name_prefix

Prints download_url<TAB>filename lines, or with --id one identity line
(tag plus asset names). --assets prints the same columns for assets whose
names start with name_prefix on the newest release (published_at) that has
one. Exit 0 when a release matches, 2 when none does.

GITHUB_TOKEN or GH_TOKEN, when set, is sent as Authorization: Bearer.
The token is never printed. HTTP 403 and 429 are retried three times.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def _token():
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def get(url):
    headers = {"User-Agent": "wow-setup", "Accept": "application/vnd.github+json"}
    tok = _token()
    if tok:
        headers["Authorization"] = "Bearer " + tok
    # One attempt plus three retries. Sleep stays short; tests can replace it.
    delays = (1, 2, 4)
    attempt = 0
    while True:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            if code in (403, 429) and attempt < len(delays):
                time.sleep(delays[attempt])
                attempt += 1
                continue
            if code == 404:
                return None
            print(f"WARNING: GitHub {url}: HTTP {code}", file=sys.stderr)
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


def fetch_releases(spec, pages=10):
    if "/" not in spec:
        return []
    owner, repo = spec.split("/", 1)
    base = f"https://api.github.com/repos/{owner}/{repo}"
    found = []
    for page in range(1, pages + 1):
        batch = get(f"{base}/releases?per_page=100&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        found.extend(batch)
        if len(batch) < 100:
            break
    return found


def assets_named(releases, name_prefix):
    """Assets on the newest release that has a name starting with name_prefix.

    published_at picks the release. An empty prefix matches nothing.
    """
    if not name_prefix:
        return []
    best_at = ""
    best = []
    for rel in releases:
        if not isinstance(rel, dict):
            continue
        published = rel.get("published_at") or ""
        if not published:
            continue
        found = []
        for asset in rel.get("assets") or []:
            name = asset.get("name") or ""
            url = asset.get("browser_download_url") or ""
            if url and name.startswith(name_prefix):
                found.append(asset)
        if found and published >= best_at:
            best_at = published
            best = found
    return best


def newest_tag(spec, prefix):
    """Newest published release tag that starts with prefix, or None."""
    if not prefix:
        return None
    best_at = ""
    best = ""
    for rel in fetch_releases(spec):
        if not isinstance(rel, dict):
            continue
        tag = rel.get("tag_name") or ""
        published = rel.get("published_at") or ""
        if tag.startswith(prefix) and published >= best_at:
            best_at = published
            best = tag
    return best or None


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


def _print_assets(assets):
    for asset in assets:
        print(f"{asset['browser_download_url']}\t{asset['name']}")


def main(argv):
    args = argv[1:]
    if args and args[0] == "--assets":
        if len(args) != 3 or not args[1] or not args[2]:
            print(
                "usage: github_tdb.py --assets owner/repo name_prefix",
                file=sys.stderr,
            )
            return 1
        assets = assets_named(fetch_releases(args[1]), args[2])
        if not assets:
            print(
                f"WARNING: no assets named {args[2]}* in {args[1]}",
                file=sys.stderr,
            )
            return 2
        _print_assets(assets)
        return 0

    ident = False
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
    _print_assets(assets)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
