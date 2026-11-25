#!/usr/bin/env bash
# Poll the public upstreams once.
#
# The first run records each revision and does not build. A later change
# rebuilds that one core, extracts it over servers/<short> (maps and the
# live world database stay), and restarts wow-<short> only when that
# container is still running.
#
#   ./scripts/update-from-git.sh
#   ./scripts/update-from-git.sh --built
#   ./scripts/update-from-git.sh --built --only wotlk
#   ./scripts/update-from-git.sh --check
#   ./scripts/update-from-git.sh --check --only wotlk
#   ./scripts/update-from-git.sh --only wotlk
#   ./scripts/update-from-git.sh --baseline
#   ./scripts/update-from-git.sh --catch-up wotlk
#   ./scripts/update-from-git.sh --catch-up all
#
# --built recompiles installed cores whose public revision differs from
# the last successful build. It does not fetch database files or reimport
# MariaDB. A realm that was never built is left alone.
# --check prints drift and does not record a revision or build.
# Operators should use ./setup.sh update, which does not run this on a timer.
#
# --catch-up compiles the named realm even when the recorded revision
# already matches upstream. Installed trees are behind current upstream
# until you do that. A CMaNGOS or TDB database change updates the files
# on disk and does not reimport MariaDB.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "${ROOT}/docker/runtime/catalog.sh"
# shellcheck disable=SC1091
source "${ROOT}/docker/common/repos.sh"

# The poller always uses the public map. A leftover GIT_BASE must not
# point it back at a local mirror.
unset GIT_BASE || true

STATE_DIR="${WOW_STATE_DIR:-${ROOT}/.run/git-revs}"
TDB_PY="${ROOT}/docker/common/github_tdb.py"
MODE="poll"
ONLY=""

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
  awk '
    NR == 1 { next }
    /^#/ { sub(/^# ?/, ""); print; next }
    { exit }
  ' "$0"
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    --baseline) MODE="baseline"; shift ;;
    --built) MODE="built"; shift ;;
    --check) MODE="check"; shift ;;
    --catch-up)
      MODE="catch-up"
      shift
      if [[ $# -gt 0 && "$1" != --* ]]; then
        ONLY="$1"
        shift
      fi
      ;;
    --only) ONLY="${2:?}"; shift 2 ;;
    *)
      if [[ -z "$ONLY" ]]; then
        ONLY="$1"
        shift
      else
        die "Unknown argument: $1 (try --help)"
      fi
      ;;
  esac
done

if [[ "$MODE" == "catch-up" && -z "$ONLY" ]]; then
  die "Name a realm: ./scripts/update-from-git.sh --catch-up wotlk   (or all)"
fi

catalog_select "${ONLY:-all}" || die "No expansions selected"

mkdir -p "$STATE_DIR"
exec 9>"${ROOT}/.run/git-update.lock"
if ! flock -n 9; then
  log "Another git update is already running"
  exit 0
fi

read_state() {
  local file="$1"
  [[ -f "$file" ]] || return 1
  tr -d '\n' <"$file"
}

write_state() {
  local file="$1" value="$2"
  [[ -n "$value" ]] || return 1
  printf '%s\n' "$value" >"${file}.tmp"
  mv "${file}.tmp" "$file"
}

realm_running() {
  if [[ "${WOW_FAKE_RUNNING+x}" == "x" ]]; then
    [[ "$WOW_FAKE_RUNNING" == "1" ]]
    return
  fi
  local state
  state="$(docker inspect -f '{{.State.Running}}' "wow-$1" 2>/dev/null || true)"
  [[ "$state" == "true" ]]
}

install_present() {
  local dest="${WOW_SERVERS_DIR:-${ROOT}/servers}/$1"
  [[ -d "${dest}/bin" ]] && return 0
  [[ -f "${dest}/main.py" || -f "${dest}/run-server.sh" ]] && return 0
  return 1
}

core_rev() {
  local short="$1" sha
  catalog_load "$short" || return 1
  if [[ -n "${WOW_FAKE_REVS:-}" ]]; then
    [[ -f "${WOW_FAKE_REVS}/${CATALOG_CORE}" ]] || return 1
    tr -d '\n' < "${WOW_FAKE_REVS}/${CATALOG_CORE}"
    return 0
  fi
  sha="$(repo_sha_for "$CATALOG_CORE")" || return 1
  # Module pins are part of the revision. A module change rebuilds that realm.
  if [[ -n "${CATALOG_MODULES:-}" ]]; then
    printf '%s+%s' "$sha" "$CATALOG_MODULES"
  else
    printf '%s' "$sha"
  fi
}

db_rev() {
  local short="$1"
  catalog_load "$short" || return 1
  if [[ -n "${WOW_FAKE_REVS:-}" ]]; then
    [[ -f "${WOW_FAKE_REVS}/db-${CATALOG_DB_REPO}" ]] || return 1
    tr -d '\n' < "${WOW_FAKE_REVS}/db-${CATALOG_DB_REPO}"
    return 0
  fi
  case "$CATALOG_DB_KIND" in
    cmangos|mangosthree)
      [[ -n "$CATALOG_DB_REPO" ]] || return 1
      repo_sha_for "$CATALOG_DB_REPO"
      ;;
    tdb-github)
      if ! python3 "$TDB_PY" --id "$CATALOG_DB_REPO" "${CATALOG_DB_BRANCH:-}"; then
        printf 'none'
      fi
      ;;
    *)
      return 1
      ;;
  esac
}

WAS_RUNNING=0

apply_core_build() {
  local short="$1"
  WAS_RUNNING=0
  if realm_running "$short"; then
    WAS_RUNNING=1
  fi
  log "Building ${short}"
  if [[ -n "${WOW_BUILD_BIN:-}" ]]; then
    "${WOW_BUILD_BIN}" "$short"
  else
    "${ROOT}/scripts/build-servers.sh" --only "$short"
  fi
}

apply_core_restart() {
  local short="$1"
  if [[ "$WAS_RUNNING" -eq 1 ]] && realm_running "$short"; then
    log "Restarting wow-${short}"
    "${ROOT}/scripts/launch-servers.sh" restart "$short"
  elif [[ "$WAS_RUNNING" -eq 1 ]]; then
    log "wow-${short} stopped during the build; leaving it stopped"
  else
    log "wow-${short} was not running; binaries updated, container left stopped"
  fi
}

apply_db() {
  local short="$1"
  log "Refreshing database files for ${short}"
  "${ROOT}/docker/runtime/fetch-db.sh" --force "$short"
  log "${short}: database files updated. The live MariaDB world was not reimported."
}

# Last successful compile. Fall back to the poller's recorded revision
# when this tree was built before .built existed.
last_built_rev() {
  local short="$1" built_file="$2" core_file="$3"
  if [[ -f "$built_file" ]]; then
    tr -d '\n' <"$built_file"
    return 0
  fi
  if [[ -f "$core_file" ]]; then
    tr -d '\n' <"$core_file"
    return 0
  fi
  return 1
}

update_built_cores() {
  local short old_core new_core core_file built_file
  local rebuilt=() skipped=0
  failed=()
  for short in "${SELECTED[@]}"; do
    if ! install_present "$short"; then
      skipped=$((skipped + 1))
      continue
    fi
    catalog_load "$short" || { failed+=("$short"); continue; }
    core_file="${STATE_DIR}/${short}.core"
    built_file="${STATE_DIR}/${short}.built"
    if ! new_core="$(core_rev "$short")"; then
      warn "${short}: cannot read the public core revision"
      failed+=("$short")
      continue
    fi
    old_core="$(last_built_rev "$short" "$built_file" "$core_file" || true)"
    if [[ -z "$old_core" ]]; then
      log "${short}: no recorded build revision. Not rebuilding."
      continue
    fi
    if [[ "$old_core" == "$new_core" ]]; then
      log "${short}: core unchanged (${new_core:0:12})"
      continue
    fi
    log "${short}: core moved ${old_core} -> ${new_core}"
    if apply_core_build "$short"; then
      record_built_rev "$short" "$new_core"
      apply_core_restart "$short" || failed+=("$short")
      rebuilt+=("$short")
    else
      warn "Update failed for ${short}"
      failed+=("$short")
    fi
  done
  if [[ "$skipped" -gt 0 ]]; then
    log "Skipped ${skipped} realms that have not been built"
  fi
  if [[ ${#rebuilt[@]} -eq 0 ]]; then
    log "No cores had moved"
  else
    log "Recompiled: ${rebuilt[*]}"
  fi
  log "Database files and MariaDB were not changed."
  if [[ ${#failed[@]} -gt 0 ]]; then
    die "Git update failed: ${failed[*]}"
  fi
}

if [[ "$MODE" == "built" ]]; then
  update_built_cores
  exit 0
fi

failed=()
for short in "${SELECTED[@]}"; do
  catalog_load "$short" || { failed+=("$short"); continue; }
  core_file="${STATE_DIR}/${short}.core"
  db_file="${STATE_DIR}/${short}.db"

  if ! new_core="$(core_rev "$short")"; then
    warn "${short}: cannot read the public core revision"
    failed+=("$short")
    continue
  fi

  new_db=""
  has_db=0
  case "$CATALOG_DB_KIND" in
    cmangos|mangosthree|tdb-github)
      has_db=1
      if ! new_db="$(db_rev "$short")"; then
        warn "${short}: cannot read the public database revision"
        failed+=("$short")
        new_db=""
        has_db=0
      fi
      ;;
  esac

  old_core="$(read_state "$core_file" || true)"
  old_db="$(read_state "$db_file" || true)"

  if [[ "$MODE" == "check" ]]; then
    if [[ -z "$old_core" ]]; then
      log "${short}: core ${new_core} is not recorded"
    elif [[ "$old_core" != "$new_core" ]]; then
      log "${short}: core moved ${old_core} -> ${new_core}"
    else
      log "${short}: core unchanged (${new_core:0:12})"
    fi
    if [[ "$has_db" -eq 1 ]]; then
      if [[ -z "$old_db" ]]; then
        log "${short}: database ${new_db} is not recorded"
      elif [[ "$old_db" != "$new_db" ]]; then
        log "${short}: database moved ${old_db} -> ${new_db}"
      else
        log "${short}: database unchanged"
      fi
    fi
    continue
  fi

  core_changed=0
  db_changed=0
  if [[ "$MODE" == "catch-up" ]]; then
    core_changed=1
    [[ "$has_db" -eq 1 ]] && db_changed=1
  elif [[ "$MODE" == "baseline" || -z "$old_core" ]]; then
    write_state "$core_file" "$new_core"
    log "Baseline ${short} core ${new_core} (not building)"
  elif [[ "$old_core" != "$new_core" ]]; then
    core_changed=1
  else
    log "${short} core unchanged (${new_core:0:12})"
  fi

  if [[ "$has_db" -eq 1 ]]; then
    if [[ "$MODE" == "baseline" || -z "$old_db" ]]; then
      write_state "$db_file" "$new_db"
      log "Baseline ${short} database ${new_db}"
      [[ "$MODE" != "catch-up" ]] && db_changed=0
    elif [[ "$old_db" != "$new_db" ]]; then
      db_changed=1
    fi
  fi

  if [[ "$core_changed" -eq 0 && "$db_changed" -eq 0 ]]; then
    continue
  fi

  if [[ "$MODE" == "catch-up" ]]; then
    log "Catch-up ${short}: core ${old_core:-unrecorded} -> ${new_core}"
  elif [[ "$core_changed" -eq 1 ]]; then
    log "${short} core moved ${old_core} -> ${new_core}"
  fi
  if [[ "$db_changed" -eq 1 && "$MODE" != "catch-up" ]]; then
    log "${short} database moved ${old_db} -> ${new_db}"
  fi

  ok=1
  if [[ "$core_changed" -eq 1 ]]; then
    if apply_core_build "$short"; then
      record_built_rev "$short" "$new_core"
      apply_core_restart "$short" || ok=0
    else
      ok=0
    fi
  fi
  if [[ "$ok" -eq 1 && "$db_changed" -eq 1 ]]; then
    if apply_db "$short"; then
      write_state "$db_file" "$new_db"
    else
      ok=0
    fi
  fi
  if [[ "$ok" -eq 0 ]]; then
    warn "Update failed for ${short}"
    failed+=("$short")
  fi
done

if [[ ${#failed[@]} -gt 0 ]]; then
  die "Git update failed: ${failed[*]}"
fi
log "Git update check complete"
