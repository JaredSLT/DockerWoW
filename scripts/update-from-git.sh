#!/usr/bin/env bash
# Poll the public upstreams once.
#
# The first run records each revision and does not build. A later change
# rebuilds that one core, extracts it over servers/<short> (maps and the
# full world dump stay), and restarts wow-<short> only when that
# container is still running. Init applies incremental SQL either way.
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
# the last successful build. It does not fetch a replacement database dump.
# .built is written as soon as the compile succeeds. Init then applies
# incremental SQL. A realm that was running is restarted and must become
# healthy before the pair and the database revision are recorded. A stopped
# realm is left stopped. A realm that was never built is left alone.
# --check prints drift and does not record a revision or build.
# Operators should use ./setup.sh update, which does not run this on a timer.
#
# --catch-up compiles the named realm even when the recorded revision
# already matches upstream. --no-fetch does not download a replacement dump.
# --no-restart does not start the realm. --stamp records the pair and the
# database revision after SQL has been applied. It does not build.
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
PAIR_PY="${ROOT}/docker/common/release_pair.py"
MODE="poll"
ONLY=""
NO_FETCH=0
NO_RESTART=0
RESOLVED_SHORT=""
RESOLVED_LINE=""

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
    --stamp)
      MODE="stamp"
      shift
      if [[ $# -gt 0 && "$1" != --* ]]; then
        ONLY="$1"
        shift
      fi
      ;;
    --no-fetch) NO_FETCH=1; shift ;;
    --no-restart) NO_RESTART=1; shift ;;
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
if [[ "$MODE" == "stamp" && -z "$ONLY" ]]; then
  die "Name a realm: ./scripts/update-from-git.sh --stamp wotlk"
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
  # A fake health result is the whole container story. Do not call docker.
  if [[ "${WOW_FAKE_HEALTH+x}" == x ]]; then
    return 0
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

resolve_pair() {
  local short="$1" line
  if [[ "$short" == "$RESOLVED_SHORT" ]]; then
    printf '%s' "$RESOLVED_LINE"
    return 0
  fi
  line="$(python3 "$PAIR_PY" --short "$short" --state "$STATE_DIR")" || return 1
  RESOLVED_SHORT="$short"
  RESOLVED_LINE="$line"
  printf '%s' "$line"
}

core_rev() {
  local short="$1" sha ref kind line mode
  catalog_load "$short" || return 1
  if [[ -n "${WOW_FAKE_REVS:-}" ]]; then
    [[ -f "${WOW_FAKE_REVS}/${CATALOG_CORE}" ]] || return 1
    tr -d '\n' < "${WOW_FAKE_REVS}/${CATALOG_CORE}"
    return 0
  fi
  repo_lookup "$CATALOG_CORE" || return 1
  ref="$REPO_REF"
  kind="$REPO_KIND"
  if line="$(resolve_pair "$short")"; then
    IFS=$'\t' read -r mode ref kind _ <<<"$line"
  fi
  sha="$(repo_sha "$REPO_URL" "$ref" "$kind")" || return 1
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
  local short="$1" ref="${2:-}" kind="${3:-}"
  local -a cmd
  WAS_RUNNING=0
  if realm_running "$short"; then
    WAS_RUNNING=1
  fi
  log "Building ${short}"
  if [[ -n "${WOW_BUILD_BIN:-}" ]]; then
    cmd=("${WOW_BUILD_BIN}" "$short")
  else
    cmd=("${ROOT}/scripts/build-servers.sh" --only "$short")
  fi
  if [[ -n "$ref" && -n "$kind" ]]; then
    WOW_CORE_REF="$ref" WOW_CORE_KIND="$kind" "${cmd[@]}"
  elif [[ -n "$ref" ]]; then
    WOW_CORE_REF="$ref" "${cmd[@]}"
  else
    "${cmd[@]}"
  fi
}

# Docker health, or WOW_FAKE_HEALTH. Fake env never calls the daemon.
realm_healthy() {
  local short="$1" status i
  if [[ "${WOW_FAKE_HEALTH+x}" == x ]]; then
    [[ "$WOW_FAKE_HEALTH" == "healthy" ]]
    return
  fi
  if [[ "${WOW_FAKE_RUNNING+x}" == x ]]; then
    return 0
  fi
  for ((i = 0; i < 60; i++)); do
    status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "wow-${short}" 2>/dev/null || true)"
    case "$status" in
      healthy) return 0 ;;
      unhealthy) return 1 ;;
    esac
    sleep 2
  done
  return 1
}

apply_core_restart() {
  local short="$1"
  if [[ "$NO_RESTART" -eq 1 ]]; then
    log "wow-${short} restart left to the caller"
    return 0
  fi
  # Fake env is the whole container story. Do not call Docker or init.
  if [[ "${WOW_FAKE_RUNNING+x}" == x || "${WOW_FAKE_HEALTH+x}" == x ]]; then
    if [[ "$WAS_RUNNING" -ne 1 ]]; then
      log "wow-${short} was not running; binaries updated, container left stopped"
      return 0
    fi
    log "Restarting wow-${short}"
    realm_healthy "$short"
    return
  fi
  if [[ "$WAS_RUNNING" -eq 1 ]] && ! realm_running "$short"; then
    log "wow-${short} stopped during the build; leaving it stopped"
    return 1
  fi
  # Incremental SQL only. prepare-db does not fetch or replace a full dump.
  # launch-servers.sh restart uses --no-deps, so init has to run first.
  log "Applying incremental SQL for ${short}"
  if [[ "$WAS_RUNNING" -eq 1 ]]; then
    "${ROOT}/scripts/launch-servers.sh" stop "$short" || return 1
  fi
  "${ROOT}/scripts/launch-servers.sh" prepare-db "$short" || return 1
  if [[ "$WAS_RUNNING" -ne 1 ]]; then
    log "wow-${short} was not running; binaries updated, container left stopped"
    return 0
  fi
  log "Restarting wow-${short}"
  "${ROOT}/scripts/launch-servers.sh" restart "$short" || return 1
  realm_healthy "$short"
}

# Pair plus database revision. Used after a healthy restart or a finished apply.
# Does not write either file when the database revision cannot be read.
stamp_revision() {
  local short="$1" line db pair_file db_file
  catalog_load "$short" || return 1
  line="$(resolve_pair "$short")" || return 1
  pair_file="${STATE_DIR}/${short}.pair"
  db_file="${STATE_DIR}/${short}.db"
  case "$CATALOG_DB_KIND" in
    cmangos|mangosthree|tdb-github)
      db="$(db_rev "$short")" || return 1
      printf '%s\n' "$db" >"${db_file}.tmp"
      printf '%s\n' "$line" >"${pair_file}.tmp"
      mv "${db_file}.tmp" "$db_file"
      mv "${pair_file}.tmp" "$pair_file"
      ;;
    *)
      write_state "$pair_file" "$line"
      ;;
  esac
}

report_pair() {
  local short="$1" new_line="$2"
  local old_line old_ref old_db
  local new_mode new_ref new_db
  IFS=$'\t' read -r new_mode new_ref _ new_db <<<"$new_line"
  if [[ "$new_mode" == "wod" ]]; then
    log "${short}: wod local dump; no public newer release"
  fi
  old_line="$(read_state "${STATE_DIR}/${short}.pair" || true)"
  [[ -n "$old_line" ]] || return 0
  IFS=$'\t' read -r _ old_ref _ old_db <<<"$old_line"
  if [[ "$old_ref" != "$new_ref" || "$old_db" != "$new_db" ]]; then
    log "${short}: pair moved ${old_ref} -> ${new_ref}"
  elif [[ "$new_mode" == "pinned" ]]; then
    log "${short}: no newer core+database pair"
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
  local pair_line pair_ref pair_kind
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
    pair_line=""
    pair_ref=""
    pair_kind=""
    RESOLVED_SHORT=""
    RESOLVED_LINE=""
    if pair_line="$(resolve_pair "$short")"; then
      IFS=$'\t' read -r _ pair_ref pair_kind _ <<<"$pair_line"
    else
      warn "${short}: cannot resolve the core and database pair"
      pair_line=""
    fi
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
      # A failed init leaves .built in place and does not write .pair.
      # The next update must apply SQL again without recompiling.
      saved_pair="$(read_state "${STATE_DIR}/${short}.pair" || true)"
      if [[ -n "$pair_line" && "$saved_pair" != "$pair_line" ]]; then
        log "${short}: database pair is not applied. Applying incremental SQL."
        WAS_RUNNING=0
        if realm_running "$short"; then
          WAS_RUNNING=1
        fi
        if apply_core_restart "$short"; then
          if ! stamp_revision "$short"; then
            warn "${short}: incremental SQL ran but the database revision was not recorded"
            # Hermetic tests have no database revision file. A real host
            # must fail so the next update tries this pair again.
            if [[ -z "${WOW_FAKE_REVS:-}" ]]; then
              failed+=("$short")
            fi
          fi
        else
          warn "${short}: incremental SQL was not applied. Database revision was not recorded."
          failed+=("$short")
        fi
      fi
      continue
    fi
    log "${short}: core moved ${old_core} -> ${new_core}"
    if apply_core_build "$short" "$pair_ref" "$pair_kind"; then
      # Record the compile before the health check so a failed restart is not rebuilt.
      record_built_rev "$short" "$new_core"
      if apply_core_restart "$short"; then
        if [[ "$WAS_RUNNING" -eq 1 ]]; then
          if stamp_revision "$short"; then
            rebuilt+=("$short")
          else
            warn "${short}: core is healthy but the database revision was not recorded"
            failed+=("$short")
          fi
        else
          if [[ -n "$pair_line" ]]; then
            write_state "${STATE_DIR}/${short}.pair" "$pair_line" || true
          fi
          rebuilt+=("$short")
        fi
      else
        warn "${short}: core built but the realm is not healthy. Database revision was not recorded."
        failed+=("$short")
      fi
    else
      warn "Update failed for ${short}"
      failed+=("$short")
    fi
  done
  if [[ "$skipped" -gt 0 ]]; then
    log "Skipped ${skipped} realms that have not been built"
  fi
  if [[ ${#rebuilt[@]} -eq 0 && ${#failed[@]} -eq 0 ]]; then
    log "No cores had moved"
  elif [[ ${#rebuilt[@]} -gt 0 ]]; then
    log "Recompiled: ${rebuilt[*]}"
  fi
  log "No full world dump was replaced."
  if [[ ${#failed[@]} -gt 0 ]]; then
    die "Git update failed: ${failed[*]}"
  fi
}

if [[ "$MODE" == "built" ]]; then
  update_built_cores
  exit 0
fi

if [[ "$MODE" == "stamp" ]]; then
  failed=()
  for short in "${SELECTED[@]}"; do
    RESOLVED_SHORT=""
    RESOLVED_LINE=""
    if ! stamp_revision "$short"; then
      warn "${short}: database revision was not recorded"
      failed+=("$short")
    fi
  done
  if [[ ${#failed[@]} -gt 0 ]]; then
    die "Git update failed: ${failed[*]}"
  fi
  exit 0
fi

failed=()
for short in "${SELECTED[@]}"; do
  catalog_load "$short" || { failed+=("$short"); continue; }
  core_file="${STATE_DIR}/${short}.core"
  db_file="${STATE_DIR}/${short}.db"
  pair_line=""
  pair_ref=""
  pair_kind=""
  RESOLVED_SHORT=""
  RESOLVED_LINE=""
  if pair_line="$(resolve_pair "$short")"; then
    IFS=$'\t' read -r _ pair_ref pair_kind _ <<<"$pair_line"
  else
    warn "${short}: cannot resolve the core and database pair"
    pair_line=""
  fi

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
    if [[ -n "$pair_line" ]]; then
      report_pair "$short" "$pair_line"
    fi
    continue
  fi

  core_changed=0
  db_changed=0
  if [[ "$MODE" == "catch-up" ]]; then
    core_changed=1
    if [[ "$NO_FETCH" -eq 0 && "$has_db" -eq 1 ]]; then
      db_changed=1
    fi
  elif [[ "$MODE" == "baseline" || -z "$old_core" ]]; then
    write_state "$core_file" "$new_core"
    log "Baseline ${short} core ${new_core} (not building)"
    if [[ "$MODE" == "baseline" && -n "$pair_line" ]]; then
      write_state "${STATE_DIR}/${short}.pair" "$pair_line"
    fi
  elif [[ "$old_core" != "$new_core" ]]; then
    core_changed=1
  else
    log "${short} core unchanged (${new_core:0:12})"
  fi

  if [[ "$has_db" -eq 1 && "$MODE" != "catch-up" ]]; then
    if [[ "$MODE" == "baseline" || -z "$old_db" ]]; then
      write_state "$db_file" "$new_db"
      log "Baseline ${short} database ${new_db}"
      db_changed=0
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
    if apply_core_build "$short" "$pair_ref" "$pair_kind"; then
      record_built_rev "$short" "$new_core"
      if [[ "$NO_RESTART" -eq 0 ]]; then
        apply_core_restart "$short" || ok=0
      fi
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
  # --no-fetch leaves the pair for setup.sh, which stamps only after prepare-db.
  # A failed restart leaves ok=0, so a running realm does not record the pair.
  if [[ "$ok" -eq 1 && "$NO_FETCH" -eq 0 && -n "$pair_line" ]]; then
    write_state "${STATE_DIR}/${short}.pair" "$pair_line" || ok=0
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
