#!/usr/bin/env bash
# fetch-db.sh — Download / unpack world-content databases for selected expansions.
#
# CMaNGOS clones classic-db / tbc-db from the public URLs in repos.sh
# into servers/<short>/db. An existing clone is retargeted, not replaced.
# Trinity cores download a matching GitHub TDB release into sql/dumps/.
# WoD unpacks the Firestorm rar/zip already shipped in sql/base/.
#
# Usage (from repo root, or via setup.sh):
#   ./docker/runtime/fetch-db.sh                  # all
#   ./docker/runtime/fetch-db.sh vanilla,tbc,bfa
#   ./docker/runtime/fetch-db.sh --force vanilla
#
set -euo pipefail

RUNTIME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${RUNTIME}/../.." && pwd)"
# shellcheck disable=SC1091
source "${RUNTIME}/catalog.sh"
# shellcheck disable=SC1091
source "${ROOT}/docker/common/repos.sh"
# shellcheck disable=SC1091
source "${RUNTIME}/lib.sh"

GIT_BASE="${GIT_BASE:-}"
FORCE="${FORCE:-0}"
ONLY=""
TDB_PY="${ROOT}/docker/common/github_tdb.py"

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

dumps_dir() { printf '%s/servers/%s/sql/dumps' "$ROOT" "$1"; }
db_dir()    { printf '%s/servers/%s/db' "$ROOT" "$1"; }

has_world_dump() {
  local dest="$1"
  local dumps sql
  dumps="$(dumps_dir "$dest")"
  sql="${ROOT}/servers/${dest}/sql"
  [[ -d "$(db_dir "$dest")/Full_DB" ]] && return 0
  [[ -d "$dumps" ]] && find "$dumps" -maxdepth 1 -type f -size +1M \( \
      -iname 'TDB*.sql' -o -iname 'TDB*.sql.gz' -o -iname '*world*.sql' \
    \) | grep -q . && return 0
  [[ -d "$sql" ]] && find "$sql" -maxdepth 2 -type f -size +1M \( \
      -iname 'TDB*.sql' -o -iname 'TDB*.sql.gz' -o -iname '*world_database*.sql' \
    \) | grep -q . && return 0
  return 1
}

# --force retires the world/hotfix dumps find_sql_dumps would choose.
# Files already under sql/dumps/old stay there.
retire_sql_dumps() {
  local short="$1"
  local root dumps f dest base
  root="${ROOT}/servers/${short}"
  dumps="$(dumps_dir "$short")"
  [[ -d "$dumps" ]] || return 0
  mkdir -p "${dumps}/old"
  while IFS= read -r f; do
    [[ -n "$f" && -f "$f" ]] || continue
    case "$f" in
      "${dumps}/old/"*) continue ;;
      "${dumps}/"*) ;;
      *) continue ;;
    esac
    base="$(basename "$f")"
    dest="${dumps}/old/${base}"
    if [[ -e "$dest" ]]; then
      dest="${dumps}/old/$(date +%s%N)-${base}"
    fi
    log "Retiring ${f#"${ROOT}/"} -> servers/${short}/sql/dumps/old/"
    mv -- "$f" "$dest"
  done < <(
    list_sql_dump_candidates "$root" world || true
    list_sql_dump_candidates "$root" hotfix || true
  )
}

skyfire_dump_present() {
  local dumps="$1" f
  [[ -d "$dumps" ]] || return 1
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    return 0
  done < <(find "$dumps" -maxdepth 1 -type f \( \
      -iname 'SFDB*.sql' -o -iname 'SFDB*.sql.gz' -o -iname 'SFDB*.zip' \
      -o -iname '*world*.sql' -o -iname '*world*.sql.gz' \
    \))
  return 1
}

download() {
  local url="$1" dest="$2"
  local tmp="${dest}.part"
  mkdir -p "$(dirname "$dest")"
  log "Download $(basename "$dest")  ($(printf '%s' "$url" | sed 's#https\?://##'))"
  curl -fL --retry 4 --retry-delay 2 -C - --progress-bar -o "$tmp" "$url"
  mv "$tmp" "$dest"
}

extract_archive() {
  local archive="$1" outdir="$2"
  mkdir -p "$outdir"
  case "$archive" in
    *.sql|*.SQL) return 0 ;;
    *.gz)
      if [[ "$archive" == *.sql.gz ]]; then
        return 0
      fi
      gzip -dkf "$archive"
      ;;
    *.rar)
      if command -v unrar >/dev/null; then
        unrar x -o+ "$archive" "$outdir"
      elif command -v 7z >/dev/null; then
        7z x -y -o"$outdir" "$archive"
      else
        die "Need unrar or 7z to extract $(basename "$archive")"
      fi
      ;;
    *.zip)
      if command -v unzip >/dev/null; then
        unzip -o "$archive" -d "$outdir"
      elif command -v 7z >/dev/null; then
        7z x -y -o"$outdir" "$archive"
      else
        die "Need unzip or 7z to extract $(basename "$archive")"
      fi
      ;;
    *)
      if command -v 7z >/dev/null; then
        7z x -y -o"$outdir" "$archive"
      else
        die "Need 7z to extract $(basename "$archive")"
      fi
      ;;
  esac
}

clone_cmangos_db() {
  local short="$1" repo="$2" branch="$3"
  local dest url ref current
  dest="$(db_dir "$short")"
  mkdir -p "$(dirname "$dest")"
  if [[ -n "$GIT_BASE" ]]; then
    url="${GIT_BASE%/}/${repo}.git"
    ref="$branch"
  elif repo_lookup "$repo"; then
    url="$REPO_URL"
    ref="$REPO_REF"
  else
    die "${short}: no public database repo for ${repo}"
  fi
  if [[ -d "${dest}/.git" ]]; then
    current="$(git -C "$dest" remote get-url origin 2>/dev/null || true)"
    if [[ "$current" != "$url" ]]; then
      log "Pointing servers/${short}/db at ${url}"
      git -C "$dest" remote set-url origin "$url"
    fi
    if [[ "$FORCE" -eq 1 ]]; then
      log "Updating ${repo} (${ref}) in servers/${short}/db"
      git -C "$dest" fetch --depth 1 origin "+refs/heads/${ref}:refs/remotes/origin/${ref}"
      git -C "$dest" checkout -f "origin/${ref}"
    else
      log "CMaNGOS db already cloned at servers/${short}/db"
    fi
    return 0
  fi
  if [[ -d "$dest" && "$FORCE" -eq 0 ]]; then
    log "servers/${short}/db exists (not a git clone) — leave it"
    return 0
  fi
  rm -rf "$dest"
  log "Cloning ${url} -> servers/${short}/db"
  git clone --depth 1 --branch "$ref" "$url" "$dest"
}

download_github_assets() {
  local short="$1" spec="$2" prefix="${3:-}"
  local dumps url name out list got=0
  dumps="$(dumps_dir "$short")"
  mkdir -p "$dumps"
  list="$(mktemp)"
  if ! python3 "$TDB_PY" "$spec" "$prefix" >"$list"; then
    rm -f "$list"
    return 1
  fi
  if [[ "$FORCE" -eq 1 ]] && grep -q $'\t' "$list"; then
    retire_sql_dumps "$short"
  fi
  while IFS=$'\t' read -r url name; do
    [[ -n "$url" && -n "$name" ]] || continue
    got=1
    out="${dumps}/${name}"
    if [[ -f "$out" && "$FORCE" -eq 0 ]]; then
      log "Have ${out#"$ROOT"/}"
      continue
    fi
    download "$url" "$out"
    extract_archive "$out" "$dumps"
  done <"$list"
  rm -f "$list"
  [[ "$got" -eq 1 ]]
}

unpack_wod() {
  local short="$1"
  local base="${ROOT}/servers/${short}/sql/base"
  local dumps
  dumps="$(dumps_dir "$short")"
  mkdir -p "$dumps"
  if [[ "$FORCE" -eq 0 ]] \
     && [[ -f "${dumps}/world_database.sql" ]] \
     && find "$dumps" -maxdepth 1 -type f -iname '*hotfix*.sql' | grep -q .; then
    log "WoD dumps already unpacked in sql/dumps"
    return 0
  fi
  if [[ "$FORCE" -eq 1 ]]; then
    retire_sql_dumps "$short"
  fi
  local f
  for f in "${base}"/*; do
    [[ -f "$f" ]] || continue
    case "$(basename "$f")" in
      *.rar|*.zip|*.7z)
        log "Unpack $(basename "$f") -> servers/${short}/sql/dumps"
        extract_archive "$f" "$dumps"
        ;;
    esac
  done
}

fetch_one() {
  local short="$1"
  catalog_load "$short" || die "Unknown short: $short"
  local dest="${ROOT}/servers/${short}"
  mkdir -p "$dest"

  # Retarget an existing CMaNGOS clone even when Full_DB is already on disk.
  if [[ "$CATALOG_DB_KIND" == "cmangos" || "$CATALOG_DB_KIND" == "mangosthree" ]]; then
    [[ -n "$CATALOG_DB_REPO" ]] || die "${short}: missing db_repo"
    if [[ "$CATALOG_DB_KIND" == "mangosthree" ]]; then
      log "${short}: cloning MaNGOS Three database. It is not imported automatically."
    fi
    clone_cmangos_db "$short" "$CATALOG_DB_REPO" "${CATALOG_DB_BRANCH:-master}"
    return 0
  fi

  if [[ "$CATALOG_DB_KIND" == "vmangos" ]]; then
    die "${short}: VMaNGOS has no full-world git dump in this lab. Refusing to fetch so classic-db is not reused. Build can still compile the core."
  fi

  if [[ "$FORCE" -eq 0 ]] && has_world_dump "$short"; then
    log "World dump already present for ${short} — skip (pass --force to refetch)"
    return 0
  fi

  case "${CATALOG_DB_KIND}" in
    bundled|none|"")
      log "${short}: world SQL ships with the core (AutoSetup / bundled)"
      ;;
    tdb)
      die "${short}: db_kind tdb was the local mirror. Use tdb-github and a public owner/repo."
      ;;
    tdb-github)
      [[ -n "$CATALOG_DB_REPO" ]] || die "${short}: missing GitHub owner/repo"
      if ! download_github_assets "$short" "$CATALOG_DB_REPO" "${CATALOG_DB_BRANCH:-}"; then
        if has_world_dump "$short"; then
          warn "${short}: no matching GitHub TDB release; keeping the existing dump"
          return 0
        fi
        return 1
      fi
      ;;
    wod)
      unpack_wod "$short"
      ;;
    skyfire)
      sf_dumps="$(dumps_dir "$short")"
      mkdir -p "$sf_dumps"
      if [[ "$FORCE" -eq 0 ]] && skyfire_dump_present "$sf_dumps"; then
        log "${short}: SkyFire dump already present"
        return 0
      fi
      log "${short}: downloading SkyFire SFDB_full assets"
      sf_list="$(mktemp)"
      sf_rc=0
      python3 "$TDB_PY" --assets ProjectSkyfire/SkyFire_548 SFDB_full >"$sf_list" || sf_rc=$?
      if [[ "$sf_rc" -ne 0 ]]; then
        rm -f "$sf_list"
        if [[ "$sf_rc" -eq 2 ]]; then
          die "${short}: no SFDB_full asset from github_tdb.py --assets ProjectSkyfire/SkyFire_548 SFDB_full. Not using a hardcoded URL."
        fi
        die "${short}: github_tdb.py --assets ProjectSkyfire/SkyFire_548 SFDB_full failed (exit ${sf_rc}). Not using a hardcoded URL."
      fi
      if ! grep -q $'\t' "$sf_list"; then
        rm -f "$sf_list"
        die "${short}: github_tdb.py --assets returned no SkyFire files. Not using a hardcoded URL."
      fi
      if [[ "$FORCE" -eq 1 ]]; then
        retire_sql_dumps "$short"
      fi
      sf_got=0
      while IFS=$'\t' read -r sf_url sf_name; do
        [[ -n "$sf_url" && -n "$sf_name" ]] || continue
        sf_got=1
        sf_out="${sf_dumps}/${sf_name}"
        if [[ -f "$sf_out" && "$FORCE" -eq 0 ]]; then
          log "Have ${sf_out#"${ROOT}/"}"
          continue
        fi
        download "$sf_url" "$sf_out"
        extract_archive "$sf_out" "$sf_dumps"
      done <"$sf_list"
      rm -f "$sf_list"
      [[ "$sf_got" -eq 1 ]] || die "${short}: github_tdb.py --assets returned no SkyFire files. Not using a hardcoded URL."
      ;;
    *)
      warn "${short}: unknown db kind ${CATALOG_DB_KIND}"
      ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    --force) FORCE=1; shift ;;
    --git-base) GIT_BASE="${2:?}"; shift 2 ;;
    --only) ONLY="${2:?}"; shift 2 ;;
    *)
      if [[ -z "$ONLY" ]]; then
        ONLY="$1"
        shift
      else
        die "Unknown argument: $1"
      fi
      ;;
  esac
done

catalog_select "${ONLY}" || die "No expansions selected (try a name from setup.sh --list)"
[[ ${#SELECTED[@]} -gt 0 ]] || die "No expansions selected"

if [[ -n "$GIT_BASE" ]]; then
  log "GIT_BASE=${GIT_BASE} (mirror override)"
else
  log "Database sources: public repos"
fi
failed=()
for short in "${SELECTED[@]}"; do
  if ! fetch_one "$short"; then
    warn "Failed to fetch DB for ${short}"
    failed+=("$short")
  fi
done

if [[ ${#failed[@]} -gt 0 ]]; then
  die "Database fetch failed: ${failed[*]}"
fi
log "World-database fetch complete"
