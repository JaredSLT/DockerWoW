#!/usr/bin/env python3
"""Hermetic db-migrate checks. No Docker, no network, no MariaDB."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "docker" / "runtime" / "lib.sh"


def bash(body: str, **env: str) -> subprocess.CompletedProcess[str]:
    script = "set -euo pipefail\nunset WOW_TREE WOW_ROOT MYSQL_PWD\n" + body
    merged = os.environ.copy()
    merged.pop("WOW_TREE", None)
    merged.pop("MYSQL_PWD", None)
    merged.update(env)
    merged["LIB_SH"] = str(LIB)
    return subprocess.run(
        ["bash", "-c", script],
        cwd=ROOT,
        env=merged,
        text=True,
        capture_output=True,
        check=False,
    )


class DbMigrateTests(unittest.TestCase):
    def test_find_sql_dumps_prefers_higher_tdb_and_skips_old(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dumps = Path(tmp) / "sql" / "dumps"
            old = dumps / "old"
            old.mkdir(parents=True)
            (dumps / "TDB1127.26011_world.sql").write_text("older\n")
            (dumps / "TDB1127.26021_world.sql").write_text("newer\n")
            (old / "TDB1127.99999_world.sql").write_text("retired\n")
            proc = bash(
                r'''
source "$LIB_SH"
found="$(find_sql_dumps "$DUMP_ROOT" world)"
printf '%s\n' "$found"
''',
                DUMP_ROOT=tmp,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            chosen = Path(proc.stdout.strip())
            self.assertEqual(chosen.name, "TDB1127.26021_world.sql")
            self.assertNotIn("/old/", proc.stdout.replace("\\", "/"))

    def test_find_sql_dumps_numeric_beats_lexical_short_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dumps = Path(tmp) / "sql" / "dumps"
            dumps.mkdir(parents=True)
            # Lexical order picks ".10" first, which is also numerically newer.
            # ".9" versus ".8" is the case sort|head gets wrong: ".8" sorts first.
            (dumps / "TDB1127.8_world.sql").write_text("eight\n")
            (dumps / "TDB1127.9_world.sql").write_text("nine\n")
            proc = bash(
                r'''
source "$LIB_SH"
find_sql_dumps "$DUMP_ROOT" world
''',
                DUMP_ROOT=tmp,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(proc.stdout.strip().endswith("TDB1127.9_world.sql"))

    def test_find_sql_dumps_unversioned_uses_newest_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dumps = Path(tmp) / "sql" / "dumps"
            dumps.mkdir(parents=True)
            lexical_first = dumps / "a_world_database.sql"
            newest = dumps / "z_world_database.sql"
            lexical_first.write_text("old\n")
            newest.write_text("new\n")
            os.utime(lexical_first, (1000, 1000))
            os.utime(newest, (1000, 5000))
            proc = bash(
                r'''
source "$LIB_SH"
find_sql_dumps "$DUMP_ROOT" world
''',
                DUMP_ROOT=tmp,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(proc.stdout.strip().endswith("z_world_database.sql"), proc.stdout)

    def test_reimport_stamp_predicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stamp = Path(tmp) / ".reimport"
            stamp.write_text("20261126T120000Z\n")
            script = r'''
source "$LIB_SH"
mysql_cmd() {
  printf '%s\n' "${MYSQL_FAKE_ROW-}"
}
AUTH_DB=test_auth
if reimport_selects_importer "$STAMP_FILE"; then
  printf 'import\n'
else
  printf 'skip\n'
fi
'''
            same = bash(script, STAMP_FILE=str(stamp), MYSQL_FAKE_ROW="20261126T120000Z")
            self.assertEqual(same.returncode, 0, same.stderr)
            self.assertEqual(same.stdout.strip(), "skip")

            padded = bash(script, STAMP_FILE=str(stamp), MYSQL_FAKE_ROW="  20261126T120000Z  ")
            self.assertEqual(padded.returncode, 0, padded.stderr)
            self.assertEqual(padded.stdout.strip(), "skip")

            other = bash(script, STAMP_FILE=str(stamp), MYSQL_FAKE_ROW="20261125T000000Z")
            self.assertEqual(other.returncode, 0, other.stderr)
            self.assertEqual(other.stdout.strip(), "import")

            absent = bash(script, STAMP_FILE=str(stamp), MYSQL_FAKE_ROW="")
            self.assertEqual(absent.returncode, 0, absent.stderr)
            self.assertEqual(absent.stdout.strip(), "import")

    def test_cmangos_character_updates_respect_required_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            updates = Path(tmp) / "characters"
            updates.mkdir()
            (updates / "z2700_01_characters_old.sql").write_text("old\n")
            (updates / "z2850_01_characters_same.sql").write_text("same\n")
            (updates / "z2900_01_characters_new.sql").write_text("new\n")
            (updates / "1000_01_characters_lead_old.sql").write_text("lead-old\n")
            (updates / "2860_01_characters_lead_new.sql").write_text("lead-new\n")
            (updates / "notes.sql").write_text("no revision\n")
            proc = bash(
                r'''
source "$LIB_SH"
mysql_cmd() {
  printf '%s\n' 'required_z2850_01_characters_marker'
}
cmangos_pending_updates test_characters "$UPD_DIR"
''',
                UPD_DIR=str(updates),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            names = [Path(line).name for line in proc.stdout.splitlines() if line.strip()]
            self.assertIn("z2900_01_characters_new.sql", names)
            self.assertIn("2860_01_characters_lead_new.sql", names)
            self.assertNotIn("z2700_01_characters_old.sql", names)
            self.assertNotIn("z2850_01_characters_same.sql", names)
            self.assertNotIn("1000_01_characters_lead_old.sql", names)
            self.assertNotIn("notes.sql", names)

    def test_mysql_password_is_not_a_process_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "mysql"
            fake.write_text(
                "#!/bin/bash\n"
                "printf '%s\\n' \"$*\"\n"
                "if [[ -n \"${MYSQL_PWD:-}\" ]]; then printf 'LEAKED_MYSQL_PWD\\n'; fi\n"
            )
            fake.chmod(0o755)
            proc = bash(
                r'''
source "$LIB_SH"
MYSQL_BIN="$FAKE_MYSQL"
MYSQL_PASSWORD='secret-pass'
MYSQL_USER=wow
MYSQL_HOST=db
MYSQL_PORT=3306
export MYSQL_PWD='secret-pass'
out="$(mysql_cmd -e 'SELECT 1')"
printf '%s\n' "$out"
cnf=""
for arg in $out; do
  case "$arg" in
    --defaults-extra-file=*) cnf="${arg#--defaults-extra-file=}" ;;
  esac
done
[[ -n "$cnf" && -f "$cnf" ]]
mode="$(stat -c %a "$cnf")"
printf 'MODE %s\n' "$mode"
grep -q 'secret-pass' "$cnf"
if printf '%s\n' "$out" | grep -q 'secret-pass'; then
  printf 'PASSWORD_ON_ARGV\n'
  exit 1
fi
if printf '%s\n' "$out" | grep -q 'LEAKED_MYSQL_PWD'; then
  printf 'LEAKED_MYSQL_PWD\n'
  exit 1
fi
set -- $out
for arg; do
  if [[ "$arg" == -p || "$arg" == -p* || "$arg" == --password* ]]; then
    printf 'PASSWORD_FLAG %s\n' "$arg"
    exit 1
  fi
done
exit 0
''',
                FAKE_MYSQL=str(fake),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertIn("--defaults-extra-file=", proc.stdout)
            self.assertIn("MODE 600", proc.stdout)
            self.assertNotIn("LEAKED_MYSQL_PWD", proc.stdout)
            self.assertNotIn("secret-pass", proc.stdout.split("MODE", 1)[0])

    def test_realm_ready_does_not_invent_a_tree_suffix(self) -> None:
        text = LIB.read_text(encoding="utf-8")
        self.assertNotIn("/WoW", text)
        with tempfile.TemporaryDirectory() as tmp:
            realm = Path(tmp) / "realm"
            tree = Path(tmp) / "tree"
            (realm / "bin").mkdir(parents=True)
            tree.mkdir()
            proc = bash(
                r'''
source "$LIB_SH"
unset WOW_TREE
if realm_volume_ready "$REALM"; then printf 'bare-ready\n'; else printf 'bare-wait\n'; fi
export WOW_TREE="$TREE"
if realm_volume_ready "$REALM"; then printf 'tree-ready\n'; else printf 'tree-wait\n'; fi
printf 'setup\n' > "$TREE/setup.sh"
if realm_volume_ready "$REALM"; then printf 'setup-ready\n'; else printf 'setup-wait\n'; fi
rmdir "$REALM/bin"
if realm_volume_ready "$REALM"; then printf 'empty-ready\n'; else printf 'empty-wait\n'; fi
printf 'x\n' > "$REALM/main.py"
if realm_volume_ready "$REALM"; then printf 'main-ready\n'; else printf 'main-wait\n'; fi
''',
                REALM=str(realm),
                TREE=str(tree),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            lines = [line for line in proc.stdout.splitlines() if line.endswith(("ready", "wait"))]
            self.assertEqual(
                lines,
                ["bare-ready", "tree-wait", "setup-ready", "empty-wait", "main-ready"],
            )

    def test_import_sql_dir_aborts_unless_best_effort(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sql_dir = Path(tmp) / "updates"
            sql_dir.mkdir()
            (sql_dir / "001_bad.sql").write_text("SELECT 1;\n")
            fake = Path(tmp) / "mysql"
            fake.write_text("#!/bin/bash\nexit 1\n")
            fake.chmod(0o755)
            proc = bash(
                r'''
source "$LIB_SH"
MYSQL_BIN="$FAKE_MYSQL"
MYSQL_PASSWORD=x
MYSQL_USER=wow
if import_sql_dir testdb "$SQL_DIR"; then
  printf 'ABORT_MISSED\n'
else
  printf 'ABORTED\n'
fi
if import_sql_dir_best_effort testdb "$SQL_DIR"; then
  printf 'BEST_EFFORT_OK\n'
else
  printf 'BEST_EFFORT_FAILED\n'
fi
''',
                FAKE_MYSQL=str(fake),
                SQL_DIR=str(sql_dir),
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertIn("ABORTED", proc.stdout)
            self.assertIn("BEST_EFFORT_OK", proc.stdout)
            self.assertNotIn("ABORT_MISSED", proc.stdout)
            self.assertNotIn("BEST_EFFORT_FAILED", proc.stdout)


if __name__ == "__main__":
    unittest.main()
