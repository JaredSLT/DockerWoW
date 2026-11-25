#!/usr/bin/env python3
"""Selector rules, catalog overlay, and module pins. Does not compile cores."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTOR = ROOT / "scripts" / "select-project.py"
CATALOG = ROOT / "docker" / "runtime" / "catalog.sh"


def load_selector():
    spec = importlib.util.spec_from_file_location("select_project", SELECTOR)
    module = importlib.util.module_from_spec(spec)
    # Python 3.14 dataclasses look the class up in sys.modules during decoration.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ConfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_selector()

    def test_module_pins_are_40_hex_and_ah_bot_is_public(self):
        modules = {item.id: item for item in self.mod.load_modules()}
        self.assertNotIn("mod-ah-bot-plus", modules)
        self.assertIn("mod-ah-bot", modules)
        self.assertEqual(modules["mod-dungeon-clear"].requires, "mod-playerbots")
        self.assertFalse(modules["mod-playerbots"].default_on)
        for module in modules.values():
            self.assertRegex(module.commit, r"^[0-9a-f]{40}$")

    def test_defaults_match_the_catalog(self):
        projects = self.mod.load_projects()
        defaults = {item.short: item for item in projects if item.is_default}
        for realm in self.mod.load_catalog():
            project = defaults[realm.short]
            self.assertEqual(project.id, realm.core, realm.short)
            self.assertEqual(project.kind, realm.kind, realm.short)
            self.assertEqual(project.image, realm.image, realm.short)
            self.assertEqual(project.db_kind, realm.db_kind, realm.short)
            self.assertEqual(project.db_repo, realm.db_repo, realm.short)
            self.assertEqual(project.db_branch, realm.db_branch, realm.short)
            self.assertTrue(project.selectable, realm.short)

    def test_selectable_cores_have_dockerfiles_and_matching_image_names(self):
        for project in self.mod.load_projects():
            if not project.selectable:
                continue
            self.assertTrue(project.repo_key, project.id)
            dockerfile = ROOT / "docker" / project.repo_key / "Dockerfile"
            self.assertTrue(dockerfile.is_file(), dockerfile)
            image = "wow-" + project.repo_key.lower().replace("_", "-")
            self.assertEqual(project.image, image, project.id)

    def test_unavailable_classics_are_not_catalog_realms(self):
        shorts = {realm.short for realm in self.mod.load_catalog()}
        blocked = [item for item in self.mod.load_projects() if not item.selectable]
        self.assertGreaterEqual(len(blocked), 4)
        for project in blocked:
            if project.short not in shorts:
                self.assertFalse(project.repo_key, project.id)
        self.assertIn("classic-era", shorts)
        self.assertIn("wotlk-classic", shorts)
        for short in ("tbc-classic", "tbc-anniversary", "mop-classic"):
            self.assertNotIn(short, shorts)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.selection = root / "selection.conf"
        self.servers = root / "servers"
        self.clients = root / "clients"
        self.env = os.environ.copy()
        self.env["WOW_SELECTION_FILE"] = str(self.selection)
        self.env["WOW_SERVERS_DIR"] = str(self.servers)
        self.env["WOW_CLIENTS_DIR"] = str(self.clients)
        self.env["WOW_BACKUP_DIR"] = str(root / "backups")

    def run_selector(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SELECTOR), *args],
            cwd=ROOT,
            env=self.env,
            text=True,
            capture_output=True,
        )

    def test_rejects_unknown_core_modules_on_none_and_bad_pins(self):
        unknown = self.run_selector("--set", "wotlk=not-a-core")
        self.assertNotEqual(unknown.returncode, 0)
        self.assertIn("unknown project", unknown.stderr)

        sylcore = self.run_selector("--set", "wotlk=sylcore")
        self.assertNotEqual(sylcore.returncode, 0)
        self.assertIn("not selectable", sylcore.stderr)

        skyfire = self.run_selector("--set", "mop=SkyFire_548", "--module", "mop:mod-playerbots")
        self.assertNotEqual(skyfire.returncode, 0)
        self.assertIn("does not take modules", skyfire.stderr)

        bots = self.run_selector("--module", "wotlk:mod-dungeon-clear")
        self.assertNotEqual(bots.returncode, 0)
        self.assertIn("requires mod-playerbots", bots.stderr)

        short = self.run_selector(
            "--module",
            "wotlk:mod-extra@https://github.com/azerothcore/mod-extra.git@abc",
        )
        self.assertNotEqual(short.returncode, 0)
        self.assertIn("40 hex", short.stderr)

    def test_overlay_changes_kind_and_launch_check_asks_for_reimport(self):
        both = self.run_selector(
            "--set",
            "wotlk=azerothcore-wotlk",
            "--module",
            "wotlk:mod-playerbots",
            "--module",
            "wotlk:mod-dungeon-clear",
        )
        self.assertEqual(both.returncode, 0, both.stderr)
        self.assertIn("mod-dungeon-clear", self.selection.read_text())
        self.assertIn("mod-playerbots", self.selection.read_text())

        switched = self.run_selector("--set", "wotlk=TrinityCore-335")
        self.assertEqual(switched.returncode, 0, switched.stderr)
        overlay = self.run_selector("--bash-overlay", "wotlk")
        self.assertEqual(overlay.returncode, 0, overlay.stderr)
        self.assertIn("CATALOG_KIND='trinity'", overlay.stdout)
        self.assertIn("CATALOG_CORE='TrinityCore-335'", overlay.stdout)
        self.assertNotIn("CATALOG_LOOPBACK", overlay.stdout)

        bare = self.run_selector("--bash-overlay", "vanilla")
        self.assertEqual(bare.returncode, 0, bare.stderr)
        self.assertEqual(bare.stdout, "")

        slot = self.servers / "wotlk"
        slot.mkdir(parents=True)
        (slot / ".core-id").write_text("core=azerothcore-wotlk\nmodules=\n", encoding="utf-8")
        check = self.run_selector("--launch-check", "wotlk")
        self.assertNotEqual(check.returncode, 0)
        self.assertIn("reimport", check.stderr)
        self.assertNotIn("compose", check.stderr.lower())
        self.assertNotIn("down -v", check.stderr)


class CatalogBashTests(unittest.TestCase):
    def test_missing_selection_keeps_today_cores(self):
        script = r"""
set -euo pipefail
export WOW_SELECTION_FILE=/tmp/wow-selection-missing-$$
source "$1"
for short in alpha vanilla tbc wotlk cata mop wod legion bfa shadowlands dragonflight warwithin midnight; do
  catalog_load "$short"
  case "$short" in
    alpha) expect=alpha-core ;;
    vanilla) expect=cmangos-classic ;;
    tbc) expect=cmangos-tbc ;;
    wotlk) expect=azerothcore-wotlk ;;
    cata) expect=The-Cataclysm-Preservation-Project ;;
    mop) expect=SkyFire_548 ;;
    wod) expect=WodCore-Reforged ;;
    legion) expect=TrinityCore-Legion ;;
    bfa) expect=TrinityCore-BFA ;;
    shadowlands) expect=TrinityCore-Shadowlands ;;
    dragonflight) expect=TrinityCore-Dragonflight ;;
    warwithin) expect=TrinityCore-WarWithin ;;
    midnight) expect=TrinityCore ;;
  esac
  [[ "$CATALOG_CORE" == "$expect" ]] || { echo "$short core $CATALOG_CORE"; exit 1; }
  [[ -z "${CATALOG_MODULES}" ]] || { echo "$short modules leaked"; exit 1; }
done
catalog_load cata-classic
[[ "$CATALOG_CORE" == "TrinityCore-Cata-Classic" ]]
[[ "$CATALOG_LOOPBACK" == "127.0.0.15" ]]
[[ "$CATALOG_DB_KIND" == "bundled" ]]
catalog_fallback_ports cata-classic
[[ "$FB_AUTH" == "11126" && "$FB_WORLD" == "18097" && "$FB_REST" == "18887" && "$FB_WEB" == "19093" ]]
catalog_load classic-era
[[ "$CATALOG_CORE" == "TrinityCore-Classic" ]]
[[ "$CATALOG_LOOPBACK" == "127.0.0.16" ]]
[[ "$CATALOG_DB_KIND" == "bundled" ]]
[[ -z "$CATALOG_DB_REPO" && -z "$CATALOG_DB_BRANCH" ]]
catalog_fallback_ports classic-era
[[ "$FB_AUTH" == "11127" && "$FB_WORLD" == "18098" && "$FB_REST" == "18888" && "$FB_WEB" == "19094" ]]
catalog_load wotlk-classic
[[ "$CATALOG_CORE" == "TrinityCore-WotLK-Classic" ]]
[[ "$CATALOG_LOOPBACK" == "127.0.0.17" ]]
[[ "$CATALOG_DB_KIND" == "tdb-github" ]]
[[ "$CATALOG_DB_REPO" == "TrinityCore/TrinityCore" ]]
[[ "$CATALOG_DB_BRANCH" == "TDB343.24081" ]]
catalog_fallback_ports wotlk-classic
[[ "$FB_AUTH" == "11128" && "$FB_WORLD" == "18099" && "$FB_REST" == "18889" && "$FB_WEB" == "19095" ]]
catalog_select all
printf '%s\n' "${SELECTED[@]}" | grep -qx wotlk-classic
if printf '%s\n' "${SELECTED[@]}" | grep -qx classic-era; then
  echo "classic-era was selected"
  exit 1
fi
"""
        result = subprocess.run(["bash", "-c", script, "bash", str(CATALOG)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_saved_row_overlays_kind_without_moving_the_loopback(self):
        with tempfile.TemporaryDirectory() as tmp:
            selection = Path(tmp) / "selection.conf"
            selection.write_text("wotlk|TrinityCore-335|\n", encoding="utf-8")
            script = r"""
set -euo pipefail
export WOW_SELECTION_FILE="$2"
source "$1"
catalog_load wotlk
[[ "$CATALOG_CORE" == "TrinityCore-335" ]]
[[ "$CATALOG_KIND" == "trinity" ]]
[[ "$CATALOG_IMAGE" == "wow-trinitycore-335" ]]
[[ "$CATALOG_LOOPBACK" == "127.0.0.5" ]]
[[ "$CATALOG_DB_KIND" == "tdb-github" ]]
catalog_load vanilla
[[ "$CATALOG_CORE" == "cmangos-classic" ]]
[[ "$CATALOG_KIND" == "cmangos" ]]
"""
            result = subprocess.run(
                ["bash", "-c", script, "bash", str(CATALOG), str(selection)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
