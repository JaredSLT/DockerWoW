#!/usr/bin/env python3
"""Hermetic update apply, pair check, and GitHub asset filter tests.

No Docker daemon and no network. GitHub is monkeypatched or replaced by
WOW_FAKE_PAIRS.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
UPDATE = ROOT / "scripts" / "update-from-git.sh"
PAIR = ROOT / "docker" / "common" / "release_pair.py"
COMMON = ROOT / "docker" / "common"
sys.path.insert(0, str(COMMON))

github_tdb = importlib.import_module("github_tdb")
release_pair = importlib.import_module("release_pair")


def _git_trap(tmp: Path, env: dict[str, str]) -> Path:
    bindir = tmp / "bin"
    bindir.mkdir()
    log = tmp / "git.log"
    git = bindir / "git"
    git.write_text(
        "#!/bin/sh\nprintf '%s\\n' git >> \"$GIT_LOG\"\nexit 1\n",
        encoding="utf-8",
    )
    git.chmod(0o755)
    env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
    env["GIT_LOG"] = str(log)
    return log


class UpdateBuiltTests(unittest.TestCase):
    def _env(self, tmp: str) -> tuple[dict[str, str], Path, Path]:
        fake = Path(tmp) / "revs"
        state = Path(tmp) / "state"
        servers = Path(tmp) / "servers"
        fake.mkdir()
        state.mkdir()
        (servers / "vanilla" / "bin").mkdir(parents=True)
        (fake / "cmangos-classic").write_text(
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n",
            encoding="utf-8",
        )
        marker = Path(tmp) / "built"
        build = Path(tmp) / "build.sh"
        build.write_text(
            "#!/bin/sh\nprintf '%s\\n' \"$1\" >> \"$MARKER\"\n",
            encoding="utf-8",
        )
        build.chmod(0o755)
        env = os.environ.copy()
        env["WOW_FAKE_REVS"] = str(fake)
        env["WOW_STATE_DIR"] = str(state)
        env["WOW_SERVERS_DIR"] = str(servers)
        env["WOW_BUILD_BIN"] = str(build)
        env["WOW_FAKE_RUNNING"] = "0"
        env["WOW_SELECTION_FILE"] = str(Path(tmp) / "no-selection")
        env.pop("WOW_FAKE_PAIRS", None)
        env.pop("WOW_FAKE_HEALTH", None)
        env["MARKER"] = str(marker)
        return env, marker, state

    def test_built_records_built_and_does_not_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, marker, state = self._env(tmp)
            (state / "vanilla.built").write_text(
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [str(UPDATE), "--built", "--only", "vanilla"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("core moved", proc.stdout)
            self.assertNotIn("fetch-db", proc.stdout)
            self.assertEqual(marker.read_text(encoding="utf-8").strip(), "vanilla")
            self.assertEqual(
                (state / "vanilla.built").read_text(encoding="utf-8").strip(),
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            )
            self.assertEqual(
                (state / "vanilla.pair").read_text(encoding="utf-8").strip(),
                "float\tmaster\tbranch\tmaster",
            )

    def test_unhealthy_keeps_built_and_does_not_record_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, _marker, state = self._env(tmp)
            env["WOW_FAKE_RUNNING"] = "1"
            env["WOW_FAKE_HEALTH"] = "unhealthy"
            (state / "vanilla.built").write_text(
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
                encoding="utf-8",
            )
            (state / "vanilla.pair").write_text("float\told\tbranch\tmaster\n", encoding="utf-8")
            (state / "vanilla.db").write_text("old-db\n", encoding="utf-8")
            proc = subprocess.run(
                [str(UPDATE), "--built", "--only", "vanilla"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout)
            self.assertNotIn("fetch-db", proc.stdout)
            self.assertEqual(
                (state / "vanilla.built").read_text(encoding="utf-8").strip(),
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            )
            self.assertEqual(
                (state / "vanilla.pair").read_text(encoding="utf-8").strip(),
                "float\told\tbranch\tmaster",
            )
            self.assertEqual((state / "vanilla.db").read_text(encoding="utf-8").strip(), "old-db")

    def test_healthy_records_pair_and_database_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, _marker, state = self._env(tmp)
            fake = Path(env["WOW_FAKE_REVS"])
            (fake / "db-cmangos-classic-db").write_text("new-db\n", encoding="utf-8")
            env["WOW_FAKE_RUNNING"] = "1"
            env["WOW_FAKE_HEALTH"] = "healthy"
            (state / "vanilla.built").write_text(
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
                encoding="utf-8",
            )
            (state / "vanilla.pair").write_text("float\told\tbranch\tmaster\n", encoding="utf-8")
            (state / "vanilla.db").write_text("old-db\n", encoding="utf-8")
            proc = subprocess.run(
                [str(UPDATE), "--built", "--only", "vanilla"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn("fetch-db", proc.stdout)
            self.assertEqual(
                (state / "vanilla.pair").read_text(encoding="utf-8").strip(),
                "float\tmaster\tbranch\tmaster",
            )
            self.assertEqual((state / "vanilla.db").read_text(encoding="utf-8").strip(), "new-db")


class UpdateCheckTests(unittest.TestCase):
    def test_check_prints_pair_moved(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "revs"
            state = Path(tmp) / "state"
            pairs = Path(tmp) / "pairs"
            fake.mkdir()
            state.mkdir()
            pairs.mkdir()
            (fake / "cmangos-classic").write_text(
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n",
                encoding="utf-8",
            )
            (fake / "db-cmangos-classic-db").write_text("new-db\n", encoding="utf-8")
            (state / "vanilla.core").write_text(
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
                encoding="utf-8",
            )
            (state / "vanilla.db").write_text("old-db\n", encoding="utf-8")
            (state / "vanilla.pair").write_text("float\toldref\tbranch\tmaster\n", encoding="utf-8")
            (pairs / "vanilla").write_text("float\tnewref\tbranch\tmaster\n", encoding="utf-8")
            env = os.environ.copy()
            env["WOW_FAKE_REVS"] = str(fake)
            env["WOW_STATE_DIR"] = str(state)
            env["WOW_FAKE_PAIRS"] = str(pairs)
            env["WOW_SELECTION_FILE"] = str(Path(tmp) / "no-selection")
            proc = subprocess.run(
                [str(UPDATE), "--check", "--only", "vanilla"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("pair moved", proc.stdout)
            self.assertIn("core moved", proc.stdout)
            self.assertNotIn("fetch-db", proc.stdout)


class ReleasePairTests(unittest.TestCase):
    def test_fake_pairs_print_the_line_and_do_not_call_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pairs = root / "pairs"
            pairs.mkdir()
            line = "pair\tTDB837.20999\ttag\tTDB837.20999"
            (pairs / "bfa").write_text(line + "\n", encoding="utf-8")
            env = os.environ.copy()
            env["WOW_FAKE_PAIRS"] = str(pairs)
            log = _git_trap(root, env)
            proc = subprocess.run(
                [sys.executable, str(PAIR), "--short", "bfa"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout.strip(), line)
            self.assertFalse(log.exists(), proc.stderr)

    def test_wod_and_float_do_not_call_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = os.environ.copy()
            env.pop("WOW_FAKE_PAIRS", None)
            env["WOW_SELECTION_FILE"] = str(root / "no-selection")
            log = _git_trap(root, env)
            wod = subprocess.run(
                [sys.executable, str(PAIR), "--short", "wod"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            vanilla = subprocess.run(
                [sys.executable, str(PAIR), "--short", "vanilla"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            unknown = subprocess.run(
                [sys.executable, str(PAIR), "--short", "not-a-realm"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(wod.stdout.strip(), "wod\treforged\tbranch\twod-local")
            self.assertEqual(wod.returncode, 0, wod.stderr)
            self.assertEqual(vanilla.stdout.strip(), "float\tmaster\tbranch\tmaster")
            self.assertEqual(vanilla.returncode, 0, vanilla.stderr)
            self.assertEqual(unknown.returncode, 1)
            self.assertFalse(log.exists())

    def test_newest_tag_without_core_tag_stays_pinned(self):
        original_tag = github_tdb.newest_tag
        original_has = release_pair.core_has_tag
        try:
            github_tdb.newest_tag = lambda spec, prefix: "TDB837.20999"
            release_pair.core_has_tag = lambda url, tag: False
            with tempfile.TemporaryDirectory() as tmp:
                state = Path(tmp)
                os.environ["WOW_SELECTION_FILE"] = str(state / "no-selection")
                os.environ.pop("WOW_FAKE_PAIRS", None)
                (state / "bfa.pair").write_text(
                    "pair\tTDB837.20101\ttag\tTDB837.20101\n",
                    encoding="utf-8",
                )
                self.assertEqual(
                    release_pair.resolve("bfa", state),
                    "pinned\tTDB837.20101\ttag\tTDB837.20101",
                )
                empty = state / "empty"
                empty.mkdir()
                self.assertEqual(
                    release_pair.resolve("bfa", empty),
                    "pinned\tTDB837.20101\ttag\tTDB837.20101",
                )
                github_tdb.newest_tag = lambda spec, prefix: "TDB735.99999"
                self.assertEqual(
                    release_pair.resolve("legion", empty),
                    "pinned\t7.3.5/26972\ttag\tTDB735",
                )
                release_pair.core_has_tag = lambda url, tag: tag == "TDB735.99999"
                self.assertEqual(
                    release_pair.resolve("legion", empty),
                    "pair\tTDB735.99999\ttag\tTDB735.99999",
                )
        finally:
            github_tdb.newest_tag = original_tag
            release_pair.core_has_tag = original_has
            os.environ.pop("WOW_SELECTION_FILE", None)


class GithubAssetsTests(unittest.TestCase):
    def test_assets_named_uses_the_newest_release_with_the_prefix(self):
        releases = [
            {
                "published_at": "2020-01-01T00:00:00Z",
                "tag_name": "old",
                "assets": [
                    {
                        "name": "SFDB_full_old.zip",
                        "browser_download_url": "http://example/old.zip",
                    }
                ],
            },
            {
                "published_at": "2024-06-01T00:00:00Z",
                "tag_name": "new",
                "assets": [
                    {
                        "name": "notes.txt",
                        "browser_download_url": "http://example/notes.txt",
                    }
                ],
            },
            {
                "published_at": "2024-01-01T00:00:00Z",
                "tag_name": "mid",
                "assets": [
                    {
                        "name": "SFDB_full_mid.zip",
                        "browser_download_url": "http://example/mid.zip",
                    }
                ],
            },
        ]
        assets = github_tdb.assets_named(releases, "SFDB_full_")
        self.assertEqual([item["name"] for item in assets], ["SFDB_full_mid.zip"])
        self.assertEqual(github_tdb.assets_named(releases, "missing"), [])
        self.assertEqual(github_tdb.assets_named(releases, ""), [])

    def test_assets_rejects_a_missing_prefix_without_github(self):
        payload = json.dumps(
            [
                {
                    "published_at": "2024-01-01T00:00:00Z",
                    "tag_name": "v1",
                    "assets": [
                        {
                            "name": "other.zip",
                            "browser_download_url": "http://example/other.zip",
                        }
                    ],
                }
            ]
        ).encode()

        class Resp:
            def read(self):
                return payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(req, timeout=30):
            self.assertNotIn("super-secret-token", req.full_url)
            return Resp()

        with mock.patch.object(github_tdb.urllib.request, "urlopen", fake_urlopen):
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = github_tdb.main(
                    ["github_tdb.py", "--assets", "ProjectSkyfire/SkyFire_548", "SFDB_full_"]
                )
        self.assertEqual(code, 2)
        self.assertIn("no assets", stderr.getvalue())
        self.assertNotIn("super-secret-token", stdout.getvalue() + stderr.getvalue())

    def test_assets_sends_bearer_and_retries_429(self):
        calls = {"n": 0}
        payload = json.dumps(
            [
                {
                    "published_at": "2024-01-01T00:00:00Z",
                    "tag_name": "sf",
                    "assets": [
                        {
                            "name": "SFDB_full_1.zip",
                            "browser_download_url": "http://example/sf.zip",
                        }
                    ],
                }
            ]
        ).encode()

        class Resp:
            def read(self):
                return payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(req, timeout=30):
            calls["n"] += 1
            calls["auth"] = req.get_header("Authorization")
            if calls["n"] < 3:
                raise urllib.error.HTTPError(
                    "https://api.github.com/repos/o/r/releases",
                    429,
                    "rate",
                    None,
                    None,
                )
            return Resp()

        os.environ["GITHUB_TOKEN"] = "super-secret-token"
        try:
            with mock.patch.object(github_tdb.urllib.request, "urlopen", fake_urlopen):
                with mock.patch.object(github_tdb.time, "sleep", lambda _seconds: None):
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        code = github_tdb.main(
                            ["github_tdb.py", "--assets", "owner/repo", "SFDB_full_"]
                        )
        finally:
            os.environ.pop("GITHUB_TOKEN", None)
        self.assertEqual(code, 0)
        self.assertEqual(calls["n"], 3)
        self.assertEqual(calls["auth"], "Bearer super-secret-token")
        self.assertIn("http://example/sf.zip\tSFDB_full_1.zip", stdout.getvalue())
        self.assertNotIn("super-secret-token", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
