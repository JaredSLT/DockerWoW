#!/usr/bin/env python3
"""Save a homepage screenshot for every expansion.

Writes one PNG per expansion into screenshots/ at the repository root.
Each file is named for the expansion id, for example screenshots/vanilla.png.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wowweb.catalog import list_expansions, resolve
from wowweb.http import make_server

HOME = "/wow/"


def find_chrome() -> str:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit("No Chrome or Chromium binary is on PATH.")


def wait_until_up(url: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last = "connection refused"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
                last = f"HTTP {resp.status}"
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = str(exc)
        time.sleep(0.2)
    raise TimeoutError(last)


def shoot(chrome: str, url: str, dest: Path, width: int, height: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wow-home-shot-") as profile:
        cmd = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--virtual-time-budget=8000",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            f"--screenshot={dest}",
            url,
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not dest.is_file() or dest.stat().st_size == 0:
        raise RuntimeError(f"Chrome wrote no image to {dest}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "expansions",
        nargs="*",
        help="expansion ids to shoot (default: every expansion, in catalog order)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "screenshots",
        help="directory for the PNG files (default: screenshots/)",
    )
    parser.add_argument("--port", type=int, default=18980, help="first port for the temporary servers")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1800)
    parser.add_argument("--timeout", type=float, default=20, help="seconds to wait for each server")
    args = parser.parse_args(argv)

    chrome = find_chrome()
    if args.expansions:
        chosen = []
        for token in args.expansions:
            exp = resolve(token)
            if exp is None:
                print(f"Unknown expansion: {token}", file=sys.stderr)
                return 2
            chosen.append(exp)
    else:
        chosen = list_expansions()

    args.out.mkdir(parents=True, exist_ok=True)
    failed: list[str] = []
    for index, exp in enumerate(chosen):
        dest = args.out / f"{exp.id}.png"
        port = args.port + index
        httpd = make_server(exp, "127.0.0.1", port, None, ROOT / "data")
        httpd.RequestHandlerClass.log_message = lambda *args: None
        url = f"http://127.0.0.1:{port}{HOME}"
        thread = threading.Thread(target=httpd.serve_forever, name=f"shot-{exp.id}", daemon=True)
        thread.start()
        try:
            wait_until_up(url, args.timeout)
            shoot(chrome, url, dest, args.width, args.height)
        except (OSError, subprocess.CalledProcessError, TimeoutError, RuntimeError) as exc:
            failed.append(exp.id)
            print(f"{exp.id}: {exc}", file=sys.stderr)
        else:
            try:
                print(dest.relative_to(ROOT))
            except ValueError:
                print(dest)
        finally:
            httpd.shutdown()
            httpd.server_close()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
