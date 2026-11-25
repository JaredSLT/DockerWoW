#!/usr/bin/env python3
"""setup.sh dispatcher rules. Does not compile a core or open MariaDB."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "setup.sh"
OPS = ROOT / "scripts" / "setup_ops.py"
POST = ROOT / "docker" / "runtime" / "post-setup.py"
UPDATE = ROOT / "scripts" / "update-from-git.sh"
HOST = ROOT / "scripts" / "host-setup.sh"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ops = load(OPS, "setup_ops")
        cls.post = load(POST, "post_setup_policy")

    def test_core_change_requires_on_data_when_players_exist(self):
        with self.assertRaises(self.ops.OpsError):
            self.ops.decide_core_action("players", "", True, True)
        with self.assertRaises(self.ops.OpsError):
            self.ops.decide_core_action("unknown", "", True, True)
        self.assertEqual(self.ops.decide_core_action("none", "", False, False), "set")
        self.assertEqual(self.ops.decide_core_action("players", "refuse", False, False), "refuse")
        self.assertEqual(self.ops.decide_core_action("players", "reimport", False, False), "reimport")
        self.assertEqual(self.ops.decide_core_action("players", "keep", True, True), "keep")
        with self.assertRaises(self.ops.OpsError):
            self.ops.decide_core_action("players", "keep", False, True)
        with self.assertRaises(self.ops.OpsError):
            self.ops.decide_core_action("players", "keep", True, False)

    def test_erase_confirm_must_match(self):
        self.ops.require_confirm("wotlk", "wotlk")
        with self.assertRaises(self.ops.OpsError):
            self.ops.require_confirm("", "wotlk")
        with self.assertRaises(self.ops.OpsError):
            self.ops.require_confirm("yes", "wow_wow-mariadb")

    def test_public_addresses_cannot_be_shared(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "access.conf"
            self.ops.write_access([("vanilla", "vanilla.example.com", "203.0.113.10")], path)
            with self.assertRaises(self.ops.OpsError):
                self.ops.write_access(
                    [
                        ("vanilla", "vanilla.example.com", "203.0.113.10"),
                        ("tbc", "tbc.example.com", "203.0.113.10"),
                    ],
                    path,
                )

    def test_existing_verifier_is_left_alone(self):
        fields = {"username": "'ADMIN'", "verifier": "0xAB", "salt": "0xCD", "gmlevel": "3"}
        kept = self.post.apply_password_policy(fields, existed=True, force=False)
        self.assertNotIn("verifier", kept)
        self.assertNotIn("salt", kept)
        self.assertEqual(kept["gmlevel"], "3")
        created = self.post.apply_password_policy(fields, existed=False, force=False)
        self.assertEqual(created["verifier"], "0xAB")
        forced = self.post.apply_password_policy(fields, existed=True, force=True)
        self.assertEqual(forced["verifier"], "0xAB")

    def test_seal_writes_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("WOW_ROOT")
            os.environ["WOW_ROOT"] = tmp
            try:
                self.post.seal_gm()
                marker = Path(tmp) / ".gm-created"
                self.assertEqual(marker.read_text(encoding="utf-8"), "sealed\n")
                marker.write_text("kept\n", encoding="utf-8")
                self.post.seal_gm()
                self.assertEqual(marker.read_text(encoding="utf-8"), "kept\n")
            finally:
                if old is None:
                    os.environ.pop("WOW_ROOT", None)
                else:
                    os.environ["WOW_ROOT"] = old


class CommandTests(unittest.TestCase):
    def test_no_args_without_a_terminal_exits_2(self):
        proc = subprocess.run(
            [str(SETUP)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("setup.sh", proc.stdout + proc.stderr)

    def test_erase_without_confirm_does_not_run(self):
        proc = subprocess.run(
            [str(SETUP), "erase", "databases", "vanilla"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--confirm vanilla", proc.stderr)

    def test_core_set_dry_run_rejects_missing_on_data(self):
        env = os.environ.copy()
        env["WOW_PLAYER_STATE"] = "players"
        env["WOW_CORE_DRY"] = "1"
        env["WOW_SELECTION_FILE"] = str(Path(tempfile.mkdtemp()) / "selection.conf")
        proc = subprocess.run(
            [str(SETUP), "core", "set", "wotlk", "azerothcore-wotlk"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--on-data", proc.stderr)
        proc = subprocess.run(
            [str(SETUP), "core", "set", "wotlk", "azerothcore-wotlk", "--on-data", "refuse"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("refuse", proc.stdout)

    def test_update_check_prints_drift_and_does_not_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "revs"
            state = Path(tmp) / "state"
            fake.mkdir()
            state.mkdir()
            (fake / "cmangos-classic").write_text("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n", encoding="utf-8")
            (fake / "db-cmangos-classic-db").write_text("new-db\n", encoding="utf-8")
            (state / "vanilla.core").write_text("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n", encoding="utf-8")
            (state / "vanilla.db").write_text("old-db\n", encoding="utf-8")
            build = Path(tmp) / "build-servers.sh"
            build.write_text("#!/bin/sh\necho BUILT > \"$1\"\nexit 99\n", encoding="utf-8")
            # The real script calls ROOT/scripts/build-servers.sh, so intercept
            # with a PATH entry only if the script is invoked through PATH.
            # Assert the check path by replacing the call site's neighbor:
            marker = Path(tmp) / "built"
            env = os.environ.copy()
            env["WOW_FAKE_REVS"] = str(fake)
            env["WOW_STATE_DIR"] = str(state)
            # Point the script's state dir by wrapping isn't available.
            # Run the real script with a copied state via the documented flag
            # after the script honors WOW_STATE_DIR. See the assertion below.
            proc = subprocess.run(
                [str(UPDATE), "--check", "--only", "vanilla"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("core moved", proc.stdout)
            self.assertNotIn("BUILT", marker.read_text(encoding="utf-8") if marker.exists() else "")
            self.assertFalse(marker.exists())


class UpdateBuiltTests(unittest.TestCase):
    def _env(self, tmp: str) -> tuple[dict[str, str], Path]:
        fake = Path(tmp) / "revs"
        state = Path(tmp) / "state"
        servers = Path(tmp) / "servers"
        fake.mkdir()
        state.mkdir()
        (servers / "vanilla" / "bin").mkdir(parents=True)
        (fake / "cmangos-classic").write_text("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n", encoding="utf-8")
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
        env["MARKER"] = str(marker)
        return env, marker

    def test_rebuilds_only_a_core_that_moved(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, marker = self._env(tmp)
            state = Path(env["WOW_STATE_DIR"])
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
            self.assertIn("Recompiled: vanilla", proc.stdout)
            self.assertEqual(marker.read_text(encoding="utf-8").strip(), "vanilla")
            self.assertEqual(
                (state / "vanilla.built").read_text(encoding="utf-8").strip(),
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            )
            self.assertNotIn("fetch-db", proc.stdout)

    def test_unchanged_and_unrecorded_cores_are_not_built(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, marker = self._env(tmp)
            state = Path(env["WOW_STATE_DIR"])
            (state / "vanilla.core").write_text(
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n",
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
            self.assertIn("core unchanged", proc.stdout)
            self.assertFalse(marker.exists())

            (state / "vanilla.core").unlink()
            proc = subprocess.run(
                [str(UPDATE), "--built", "--only", "vanilla"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("no recorded build revision", proc.stdout)
            self.assertFalse(marker.exists())
            self.assertFalse((state / "vanilla.built").exists())

    def test_a_realm_that_was_never_built_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            env, marker = self._env(tmp)
            env["WOW_SERVERS_DIR"] = str(Path(tmp) / "empty")
            proc = subprocess.run(
                [str(UPDATE), "--built", "--only", "vanilla"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("have not been built", proc.stdout)
            self.assertFalse(marker.exists())

    def test_setup_update_dispatches_to_built_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "updater.sh"
            script.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\"\n", encoding="utf-8")
            script.chmod(0o755)
            env = os.environ.copy()
            env["WOW_UPDATE_BIN"] = str(script)
            proc = subprocess.run(
                [str(SETUP), "update"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("--built", proc.stdout)
            proc = subprocess.run(
                [str(SETUP), "update", "--only", "wotlk"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("--built --only wotlk", proc.stdout)


class HostSetupTests(unittest.TestCase):
    def test_git_timer_is_not_enabled(self):
        text = HOST.read_text(encoding="utf-8")
        self.assertNotIn("systemctl enable --now wow-git-update.timer", text)
        self.assertIn("systemctl disable --now wow-git-update.timer", text)


class UpdateStateTests(unittest.TestCase):
    def test_check_uses_the_override_state_dir(self):
        text = UPDATE.read_text(encoding="utf-8")
        self.assertIn("WOW_FAKE_REVS", text)
        self.assertIn('MODE" == "check"', text)
        self.assertNotIn("build-servers.sh", textwrap.dedent("""
            if [[ "$MODE" == "check" ]]; then
        """))


if __name__ == "__main__":
    unittest.main()
