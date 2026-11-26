#!/usr/bin/env python3
"""Host layout, MariaDB sizing, and reimport guards. No Docker daemon and no network."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "scripts" / "host-setup.sh"
LAUNCH = ROOT / "scripts" / "launch-servers.sh"
COMPOSE = ROOT / "docker" / "runtime" / "compose.sh"
TUNE = ROOT / "docker" / "runtime" / "mariadb_tune.sh"
OPS = ROOT / "scripts" / "setup_ops.py"


def load_ops():
    spec = importlib.util.spec_from_file_location("host_layout_setup_ops", OPS)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LayoutTests(unittest.TestCase):
    def classify(self, repo: str, target: str, fstype: str, uuid: str = "", mount: str = "") -> dict[str, str]:
        script = f"""
set -euo pipefail
source "{HOST}"
host_classify_layout "$1" "$2" "$3" "$4" "$5"
printf 'LAYOUT=%s\\n' "$HOST_LAYOUT"
printf 'MOUNT=%s\\n' "$HOST_MOUNT"
printf 'TREE=%s\\n' "$HOST_TREE"
printf 'UUID=%s\\n' "$HOST_UUID"
printf 'FSTYPE=%s\\n' "$HOST_FSTYPE"
printf 'FSTAB=%s\\n' "$HOST_FSTAB"
"""
        env = os.environ.copy()
        for key in ("WOW_VOLUME_MOUNT", "WOW_VOLUME_UUID", "WOW_TREE", "WOW_MEDIA_USER"):
            env.pop(key, None)
        proc = subprocess.run(
            ["bash", "-c", script, "bash", repo, target, fstype, uuid, mount],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)

    def test_internal_mount_is_the_repo_and_writes_no_fstab(self):
        got = self.classify("/home/user/games/wow-lab", "/home", "xfs", "", "/mnt/wow-nvme")
        self.assertEqual(got["LAYOUT"], "internal")
        self.assertEqual(got["MOUNT"], "/home/user/games/wow-lab")
        self.assertEqual(got["TREE"], "/home/user/games/wow-lab")
        self.assertEqual(got["FSTAB"], "")
        self.assertNotIn("/mnt/wow-nvme/WoW", got["MOUNT"])
        self.assertNotIn("/mnt/wow-nvme/WoW", got["TREE"])
        self.assertNotIn("ext4", got["FSTAB"])
        root_disk = self.classify("/home/user/games/wow-lab", "/", "btrfs")
        self.assertEqual(root_disk["LAYOUT"], "internal")
        self.assertEqual(root_disk["FSTAB"], "")
        self.assertNotEqual(root_disk["TREE"], "/mnt/wow-nvme/WoW")

    def test_removable_fstab_uses_detected_fstype(self):
        got = self.classify(
            "/run/media/user/NVME/WoW",
            "/run/media/user/NVME",
            "btrfs",
            "abc-uuid",
        )
        self.assertEqual(got["LAYOUT"], "removable")
        self.assertEqual(got["MOUNT"], "/mnt/wow-nvme")
        self.assertEqual(got["TREE"], "/mnt/wow-nvme/WoW")
        self.assertIn("btrfs", got["FSTAB"])
        self.assertNotIn("ext4", got["FSTAB"])
        self.assertIn("UUID=abc-uuid", got["FSTAB"])
        self.assertIn("/mnt/wow-nvme", got["FSTAB"])
        media = self.classify("/media/usb/lab", "/media/usb", "xfs", "disk-1", "/mnt/custom")
        self.assertEqual(media["LAYOUT"], "removable")
        self.assertEqual(media["MOUNT"], "/mnt/custom")
        self.assertEqual(media["TREE"], "/mnt/custom/lab")
        self.assertIn("xfs", media["FSTAB"])
        self.assertNotIn("ext4", media["FSTAB"])

    def test_host_setup_asks_findmnt_for_fstype(self):
        text = HOST.read_text(encoding="utf-8")
        self.assertIn("findmnt -n -o FSTYPE", text)
        self.assertIn("systemctl disable --now wow-git-update.timer", text)
        self.assertNotIn("systemctl enable --now wow-git-update.timer", text)


class BufferPoolTests(unittest.TestCase):
    def tune(self, body: str) -> subprocess.CompletedProcess[str]:
        script = f'set -euo pipefail\nsource "{TUNE}"\n{body}\n'
        return subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=False)

    def pool(self, mem_kb: int) -> str:
        proc = self.tune(f"mariadb_buffer_pool {mem_kb}")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def exceeds(self, mem_kb: int) -> bool:
        proc = self.tune(
            f"if mariadb_pool_exceeds_half {mem_kb}; then echo reject; else echo ok; fi"
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip() == "reject"

    def test_buffer_pool_bounds(self):
        self.assertEqual(self.pool(8 * 1024 * 1024), "2G")
        self.assertEqual(self.pool(1 * 1024 * 1024), "256M")
        self.assertEqual(self.pool(64 * 1024 * 1024), "4G")

    def test_pool_larger_than_half_memory_is_rejected(self):
        self.assertTrue(self.exceeds(256 * 1024))
        self.assertFalse(self.exceeds(8 * 1024 * 1024))
        # 256M is exactly half of 512M, so it is allowed.
        self.assertFalse(self.exceeds(512 * 1024))

    def test_flush_method_follows_docker_filesystem(self):
        for fstype in ("zfs", "fuse", "9p", "virtiofs", "overlay", "fuse.sshfs"):
            proc = self.tune(f"mariadb_flush_method {fstype}")
            self.assertEqual(proc.stdout.strip(), "fsync", fstype)
        for fstype in ("ext4", "xfs", "btrfs", ""):
            proc = self.tune(f'mariadb_flush_method "{fstype}"')
            self.assertEqual(proc.stdout.strip(), "O_DIRECT", fstype)


class ComposeTests(unittest.TestCase):
    def test_mariadb_is_loopback_and_tree_is_not_suffixed(self):
        text = COMPOSE.read_text(encoding="utf-8")
        self.assertIn("127.0.0.1:", text)
        self.assertNotIn("/WoW", text)
        self.assertNotIn("innodb-buffer-pool-size", text)
        self.assertNotIn("innodb-flush-method", text)
        self.assertIn(".run/haproxy.cfg", text)
        self.assertIn(".run/mariadb.cnf", text)


class CoreGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ops = load_ops()

    def test_reimport_refuses_vmangos_before_a_drop(self):
        for kind in ("vmangos", "mangosthree", "none", ""):
            with self.assertRaises(self.ops.OpsError) as caught:
                self.ops.assert_core_reimport_allowed(kind)
            self.assertIn("the core has no importer", str(caught.exception))
        self.ops.assert_core_reimport_allowed("cmangos")
        self.assertEqual(self.ops.decide_core_action("players", "reimport", False, False), "reimport")
        env = os.environ.copy()
        env["WOW_PLAYER_STATE"] = "players"
        env.pop("WOW_CORE_DRY", None)
        with tempfile.TemporaryDirectory() as tmp:
            env["WOW_SELECTION_FILE"] = str(Path(tmp) / "selection.conf")
            env["WOW_SERVERS_DIR"] = str(Path(tmp) / "servers")
            env["WOW_BACKUP_DIR"] = str(Path(tmp) / "backups")
            proc = subprocess.run(
                [sys.executable, str(OPS), "core-set", "vanilla", "vmangos", "--on-data", "reimport"],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("the core has no importer", proc.stderr)
        self.assertNotIn("Dropped", proc.stdout + proc.stderr)

    def test_published_access_refuses_default_passwords_before_write(self):
        ops = self.ops
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            access = Path(tmp) / "access.conf"
            env_path.write_text("MYSQL_PASSWORD=wow\nACCOUNT_PASSWORD=secret\nACCESS=loopback\n", encoding="utf-8")
            old_env, old_access = ops.ENV_FILE, ops.ACCESS_FILE
            ops.ENV_FILE = env_path
            ops.ACCESS_FILE = access
            try:
                with self.assertRaises(ops.OpsError) as caught:
                    ops.cmd_access_set("ports", "203.0.113.10", [])
                self.assertIn("MYSQL_PASSWORD", str(caught.exception))
                self.assertFalse(access.exists())
                self.assertIn("ACCESS=loopback", env_path.read_text(encoding="utf-8"))
                with self.assertRaises(ops.OpsError):
                    ops.cmd_access_set(
                        "public",
                        "",
                        [("vanilla", "vanilla.example.com", "203.0.113.10")],
                    )
                self.assertFalse(access.exists())
                env_path.write_text(
                    "MYSQL_PASSWORD=s3cret-db\nACCOUNT_PASSWORD=s3cret-acct\nACCESS=loopback\n",
                    encoding="utf-8",
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(ops.cmd_access_set("ports", "203.0.113.10", []), 0)
                text = env_path.read_text(encoding="utf-8")
                self.assertIn("ACCESS=ports", text)
                self.assertIn("REALM_ADDRESS=203.0.113.10", text)
            finally:
                ops.ENV_FILE = old_env
                ops.ACCESS_FILE = old_access

    def test_volume_tree_must_be_this_checkout(self):
        ops = self.ops
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.env"
            self.assertTrue(ops.volume_tree_status(missing)[0])
            path = Path(tmp) / "volume.env"
            path.write_text(f"WOW_TREE={ROOT}\n", encoding="utf-8")
            self.assertTrue(ops.volume_tree_status(path)[0])
            path.write_text("WOW_TREE=/tmp/not-this-repo-wow-layout\n", encoding="utf-8")
            ok, detail = ops.volume_tree_status(path)
            self.assertFalse(ok)
            self.assertIn("/tmp/not-this-repo-wow-layout", detail)

    def test_resource_warnings_are_under_the_thresholds(self):
        ops = self.ops
        self.assertIn("memory", ops.resource_warnings(1024 * 1024, 30 * 1024**3))
        self.assertNotIn("memory", ops.resource_warnings(2 * 1024 * 1024, 30 * 1024**3))
        self.assertIn("disk", ops.resource_warnings(8 * 1024 * 1024, 19 * 1024**3))
        self.assertNotIn("disk", ops.resource_warnings(8 * 1024 * 1024, 20 * 1024**3))

    def test_volume_env_replaces_the_dotenv_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            vol = Path(tmp) / "volume.env"
            tree = "/home/user/games/wow-lab"
            vol.write_text(
                f"WOW_VOLUME_UUID=\nWOW_VOLUME_MOUNT={tree}\nWOW_TREE={tree}\nWOW_MEDIA_USER=user\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            for key in ("WOW_VOLUME_UUID", "WOW_VOLUME_MOUNT", "WOW_TREE", "WOW_MEDIA_USER"):
                env.pop(key, None)
            dotenv = ROOT / ".env"
            preset = ""
            if dotenv.is_file():
                for line in dotenv.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.startswith("WOW_VOLUME_MOUNT="):
                        preset = line.split("=", 1)[1].strip().strip('"').strip("'")
            if preset:
                env["WOW_VOLUME_MOUNT"] = preset
            env["WOW_VOLUME_ENV"] = str(vol)
            script = f"""
set -euo pipefail
source "{LAUNCH}"
load_volume_env
printf 'MOUNT=%s\\n' "$WOW_VOLUME_MOUNT"
printf 'TREE=%s\\n' "$WOW_TREE"
"""
            proc = subprocess.run(
                ["bash", "-c", script],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        got = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
        self.assertEqual(got["MOUNT"], tree)
        self.assertEqual(got["TREE"], tree)
        self.assertNotEqual(got["TREE"], "/mnt/wow-nvme/WoW")


if __name__ == "__main__":
    unittest.main()
