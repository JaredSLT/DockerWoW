#!/usr/bin/env bash
# extract-data.sh — Build maps / vmaps / mmaps / dbc (and cameras, gt, navs)
# from each expansion's client using that core's extractors.
#
# Usage (from repo root):
#   ./setup.sh [servers]                  # preferred: compile + extract + DB + run
#   ./scripts/extract-data.sh
#   ./scripts/extract-data.sh vanilla
#   ./scripts/extract-data.sh vanilla,tbc,wotlk
#   ./scripts/extract-data.sh --steps maps,vmaps
#   ./scripts/extract-data.sh --steps harvest
#   ./scripts/extract-data.sh --skip-mmaps
#   ./scripts/extract-data.sh --skip-existing
#   ./scripts/extract-data.sh --list
#
# A normal run deletes previous extract data in servers/<short>/ first
# (maps, vmaps, mmaps, dbc, cameras, gt — never bin/sql/etc) so it is
# regenerated. --skip-existing keeps a *complete* extract; leftover
# incomplete data (e.g. mmap tiles without .mmap headers) is always
# deleted and the step is run again. Launch will refuse a partial extract.
#
# Output always lands in that expansion's servers/<short>/ folder
# (DataDir=".") so launch-servers.sh / worldserver can see it:
#   servers/<short>/{dbc,maps,vmaps,mmaps,cameras,gt}
# Alpha writes servers/alpha/etc/{maps,navs}/.
# Leftover extracts sitting next to a client are moved into servers/<short>/.
#
# Extractors run in the matching wow-* Docker image when it exists (needed
# for Legion/BFA OpenSSL and Boost). Otherwise they run on the host.
#
# mmap generation is the slow step (hours per expansion). Maps+vmaps are
# usually minutes to an hour.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "${ROOT}/docker/runtime/catalog.sh"

STEPS="maps,vmaps,mmaps"
SKIP_EXISTING=0
FORCE=1
CLEAN=1
CONTINUE=0
KEEP_BUILDINGS=0
NO_DOCKER=0
ONLY=""
LIST=0
JOBS="${JOBS:-}"

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

usage() {
  awk '
    NR == 1 { next }
    /^#/ { sub(/^# ?/, ""); print; next }
    { exit }
  ' "$0"
  echo
  echo "Expansion → client:"
  local short
  while IFS= read -r short; do
    catalog_load "$short"
    printf '  %-14s  clients/%-28s  %s\n' "$short" "$CATALOG_CLIENT" "$CATALOG_KIND"
  done < <(catalog_shorts)
  exit 0
}

parse_selection() {
  catalog_select "${1:-}" || die "Unknown server in: ${1:-} (try --list)"
}

want_step() {
  [[ ",${STEPS}," == *",$1,"* ]]
}

client_root() {
  local dir="$1"
  [[ -d "${dir}/Data" || -d "${dir}/data" ]] && { printf '%s' "$dir"; return 0; }
  [[ -d "${dir}/World of Warcraft/Data" ]] && { printf '%s' "${dir}/World of Warcraft"; return 0; }
  [[ -d "${dir}/_retail_/Data" ]] && { printf '%s' "${dir}/_retail_"; return 0; }
  [[ -d "${dir}/_classic_/Data" ]] && { printf '%s' "${dir}/_classic_"; return 0; }
  return 1
}

# Extractors link Data and .build.info at /client inside the container.
# Rewrite those to a path relative to the repo so the tree still works
# after it is moved, and so the realm container (which does not mount
# /client) can open the client.
relativize_client_links() {
  local dest="$1" client="$2"
  python3 - "$dest" "$client" <<'PY'
import os, sys
from pathlib import Path

dest, client = Path(sys.argv[1]), Path(sys.argv[2])
pairs = (("Data", client / "Data"), (".build.info", client / ".build.info"))
for name, target in pairs:
    link = dest / name
    if not link.is_symlink() or not target.exists():
        continue
    rel = os.path.relpath(target, dest)
    if os.readlink(link) == rel:
        continue
    link.unlink()
    link.symlink_to(rel)
    print(f"==> {link.name} -> {rel}")
PY
}

# Extracted client data only — never bin/, sql/, etc/, lib/.
wipe_dirs_for_steps() {
  local kind="$1"
  local dirs=()
  if [[ "$kind" == "alpha" ]]; then
    [[ ",${STEPS}," == *",maps,"* ]] && dirs+=(etc/maps etc/mdx etc/wmo_liquids etc/wmo_geometry)
    { [[ ",${STEPS}," == *",vmaps,"* ]] || [[ ",${STEPS}," == *",mmaps,"* ]]; } && dirs+=(etc/navs)
  else
    [[ ",${STEPS}," == *",maps,"* ]] && dirs+=(maps dbc cameras Cameras gt)
    [[ ",${STEPS}," == *",vmaps,"* ]] && dirs+=(vmaps Buildings)
    [[ ",${STEPS}," == *",mmaps,"* ]] && dirs+=(mmaps)
  fi
  [[ ${#dirs[@]} -gt 0 ]] || return 0
  printf '%s\n' "${dirs[@]}"
}

wipe_extract_data() {
  local dest="$1" kind="$2" d
  local dirs=()
  mapfile -t dirs < <(wipe_dirs_for_steps "$kind")
  [[ ${#dirs[@]} -gt 0 ]] || return 0
  log "Removing previous extract data in ${dest#"$ROOT"/} so it can be regenerated"
  for d in "${dirs[@]}"; do
    [[ -n "$d" ]] || continue
    if [[ -e "${dest}/${d}" || -L "${dest}/${d}" ]]; then
      rm -rf "${dest:?}/${d}"
      log "  removed ${d}/"
    fi
  done
}

has_extractors() {
  local dest="$1" kind="$2"
  if [[ "$kind" == "alpha" ]]; then
    [[ -f "${dest}/main.py" ]] && return 0
    return 1
  fi
  [[ -x "${dest}/bin/tools/ad" || -x "${dest}/bin/mapextractor" || -x "${dest}/bin/map_extractor" ]]
}

cmd_list() {
  printf '%-14s %-12s %-28s %-10s %-10s %s\n' \
    "SHORT" "KIND" "CLIENT" "CLIENT?" "TOOLS?" "DATA?"
  local short dest client okc okt maps
  while IFS= read -r short; do
    catalog_load "$short"
    dest="${ROOT}/servers/${short}"
    client="${ROOT}/clients/${CATALOG_CLIENT}"
    okc="no"
    client_root "$client" >/dev/null && okc="ok"
    okt="no"
    has_extractors "$dest" "$CATALOG_KIND" && okt="ok"
    maps="none"
    if extract_data_complete "$dest" "$CATALOG_KIND"; then
      maps="complete"
    elif [[ "$CATALOG_KIND" == "alpha" && -d "${dest}/etc/maps" ]] \
        && [[ "$(find "${dest}/etc/maps" -type f -name '*.map' | wc -l)" -gt 0 ]]; then
      maps="incomplete"
    elif [[ -d "${dest}/maps" ]]; then
      local n
      n="$(find "${dest}/maps" -type f -name '*.map' | wc -l)"
      [[ "$n" -gt 0 ]] && maps="incomplete (${n} maps)"
    fi
    printf '%-14s %-12s %-28s %-10s %-10s %s\n' \
      "$short" "$CATALOG_KIND" "$CATALOG_CLIENT" "$okc" "$okt" "$maps"
  done < <(catalog_shorts)
}

run_host() {
  local short="$1"
  env \
    WOW_SHORT="$short" \
    WOW_KIND="$CATALOG_KIND" \
    CORE_NAME="$CATALOG_CORE" \
    CLIENT="$CLIENT_PATH" \
    DEST="${ROOT}/servers/${short}" \
    STEPS="$STEPS" \
    JOBS="$JOBS" \
    FORCE="$FORCE" \
    CLEAN="$CLEAN" \
    KEEP_BUILDINGS="$KEEP_BUILDINGS" \
    bash "${ROOT}/docker/runtime/extract-one.sh"
}

# Namigator Python .so files (pathfind.so / mapbuild.so) used by alpha .nav extract.
prefetch_namigator() {
  local dest="$1" pyver="$2"
  local dir="${dest}/namigator"
  mkdir -p "$dir"
  if [[ -f "${dir}/pathfind.so" && -f "${dir}/mapbuild.so" ]]; then
    log "Namigator bindings already in ${dir#"$ROOT"/}"
    return 0
  fi
  local url="https://github.com/The-Alpha-Project/alpha-core/releases/download/Namigator/namigator_nix_${pyver}.zip"
  local zip="${dir}/.namigator.zip"
  log "Download Namigator bindings for CPython ${pyver}"
  if ! curl -fL --retry 4 --retry-delay 2 --progress-bar -o "$zip" "$url"; then
    warn "Could not download Namigator from GitHub (${url})"
    rm -f "$zip"
    return 1
  fi
  python3 - "$zip" "$dir" <<'PY'
import sys, zipfile
from pathlib import Path
zf_path, dest = Path(sys.argv[1]), Path(sys.argv[2])
with zipfile.ZipFile(zf_path) as zf:
    zf.extractall(dest)
PY
  rm -f "$zip"
  [[ -f "${dir}/pathfind.so" && -f "${dir}/mapbuild.so" ]] || {
    warn "Namigator zip did not contain pathfind.so / mapbuild.so"
    return 1
  }
  log "Installed ${dir#"$ROOT"/}/{pathfind,mapbuild}.so"
}

python_ver_for_extract() {
  local image="$1"
  if [[ -n "$image" ]] && command -v docker >/dev/null && docker image inspect "$image" &>/dev/null; then
    docker run --rm --entrypoint python3 "$image" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null && return 0
  fi
  python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")'
}

run_docker() {
  local short="$1" image="$2"
  local dest="${ROOT}/servers/${short}"
  local uid gid common net
  uid="$(id -u)"
  gid="$(id -g)"
  # Alpha Namigator fetches GitHub releases and talks to wow-db.
  net=(--network none)
  if [[ "$CATALOG_KIND" == "alpha" ]]; then
    net=(--network wow-net)
  fi
  common=(
    --rm
    "${net[@]}"
    --ulimit "nofile=1048576:1048576"
    -e HOME=/tmp
    -e WOW_SHORT="$short"
    -e WOW_KIND="$CATALOG_KIND"
    -e CORE_NAME="$CATALOG_CORE"
    -e CLIENT=/client
    -e DEST=/opt/wow
    -e STEPS="$STEPS"
    -e JOBS="$JOBS"
    -e FORCE="$FORCE"
    -e CLEAN="$CLEAN"
    -e KEEP_BUILDINGS="$KEEP_BUILDINGS"
    -e MYSQL_HOST="${MYSQL_HOST:-db}"
    -e MYSQL_PORT="${MYSQL_PORT:-3306}"
    -e MYSQL_USER="${MYSQL_USER:-wow}"
    -e MYSQL_PASSWORD="${MYSQL_PASSWORD:-wow}"
    -e WOW_ROOT=/opt/wow
    -e LD_LIBRARY_PATH="/opt/wow/lib:/servers/${CATALOG_CORE}/lib"
    -v "${CLIENT_PATH}:/client"
    -v "${dest}:/opt/wow"
    -v "${ROOT}/docker/runtime:/opt/runtime:ro"
    -w /opt/wow
  )
  local rc=0
  docker run -u "${uid}:${gid}" "${common[@]}" "$image" bash /opt/runtime/extract-one.sh || rc=$?
  if [[ "$rc" -eq 0 ]]; then
    return 0
  fi
  if [[ "$rc" -eq 130 || "$rc" -eq 137 || "$rc" -eq 143 ]]; then
    die "Extract interrupted"
  fi
  return "$rc"
}

# A different extractor must not reuse the previous core's maps. Move them
# aside and leave them on disk until a later extract succeeds.
stash_previous_extractor() {
  local short="$1" dest="$2" selected installed stamp aside dir
  selected="$(python3 "${ROOT}/scripts/select-project.py" --print-core "$short" 2>/dev/null || true)"
  [[ -n "$selected" ]] || return 0
  if [[ -f "${dest}/.core-id" ]]; then
    installed="$(sed -n 's/^core=//p' "${dest}/.core-id" | head -1)"
    [[ "$installed" == "$selected" ]] && return 0
    [[ -n "$installed" ]] || installed="previous"
  else
    # No stamp and the default core: the maps already belong to this extractor.
    python3 "${ROOT}/scripts/select-project.py" --install-matches "$short" >/dev/null 2>&1 && return 0
    installed="unstamped"
  fi
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  aside="${dest}/.maps-aside-${installed}-${stamp}"
  local moved=0
  for dir in maps vmaps mmaps dbc cameras Cameras gt Buildings; do
    if [[ -d "${dest}/${dir}" ]]; then
      mkdir -p "$aside"
      mv "${dest}/${dir}" "${aside}/"
      moved=1
    fi
  done
  if [[ "$moved" -eq 1 ]]; then
    log "${short}: moved previous extractor output to ${aside} (not deleted)"
  fi
}

extract_one() {
  local short="$1"
  catalog_load "$short" || die "Unknown short: $short"
  local dest="${ROOT}/servers/${short}"
  local client="${ROOT}/clients/${CATALOG_CLIENT}"
  local image="${CATALOG_IMAGE}:latest"
  stash_previous_extractor "$short" "$dest"

  CLIENT_PATH="$(client_root "$client")" || {
    warn "No client Data/ at clients/${CATALOG_CLIENT} — skip ${short}"
    return 0
  }

  mkdir -p "${dest}/logs"

  local have_tools=0 have_image=0
  has_extractors "$dest" "$CATALOG_KIND" && have_tools=1
  if [[ "$NO_DOCKER" -eq 0 ]] && command -v docker >/dev/null && docker image inspect "$image" &>/dev/null; then
    have_image=1
  fi

  if [[ "$have_tools" -eq 0 && "$have_image" -eq 0 ]]; then
    warn "No extractors in servers/${short} and no image ${image} — harvest leftover client data only"
    local saved_steps="$STEPS"
    STEPS=harvest
    run_host "$short"
    STEPS="$saved_steps"
    return 0
  fi

  if [[ "$STEPS" != "harvest" ]] && extract_data_complete "$dest" "$CATALOG_KIND" && [[ "$FORCE" -eq 0 ]]; then
    relativize_client_links "$dest" "$CLIENT_PATH"
    log "Extract already complete for ${short} — skip"
    return 0
  fi

  if [[ "$CLEAN" -eq 1 && "$STEPS" != "harvest" ]]; then
    wipe_extract_data "$dest" "$CATALOG_KIND"
  elif [[ "$STEPS" != "harvest" ]] && ! extract_data_complete "$dest" "$CATALOG_KIND"; then
    log "Incomplete extract for ${short} (${EXTRACT_GAP:-unknown}) — deleting leftover data and starting again"
    # Only wipe the layers that are actually incomplete so good maps are kept
    # when only mmaps were cut short.
    if ! extract_step_complete "$dest" "$CATALOG_KIND" maps; then
      wipe_extract_data "$dest" "$CATALOG_KIND"
    else
      if want_step vmaps && ! extract_step_complete "$dest" "$CATALOG_KIND" vmaps; then
        rm -rf "${dest}/vmaps" "${dest}/Buildings"
        log "  removed vmaps/ Buildings/"
      fi
      if want_step mmaps && ! extract_step_complete "$dest" "$CATALOG_KIND" mmaps; then
        rm -rf "${dest}/mmaps"
        mkdir -p "${dest}/mmaps"
        log "  removed mmaps/"
      fi
      if [[ "$CATALOG_KIND" == "alpha" ]] && { want_step vmaps || want_step mmaps; } \
          && ! extract_step_complete "$dest" "$CATALOG_KIND" navs; then
        rm -rf "${dest}/etc/navs"
        log "  removed etc/navs/"
      fi
    fi
  fi

  if [[ "$CATALOG_KIND" == "alpha" ]]; then
    local pyver
    pyver="$(python_ver_for_extract "$([[ "$have_image" -eq 1 ]] && echo "$image")")" || pyver="3.12"
    prefetch_namigator "$dest" "$pyver" || warn "Namigator prefetch failed — extract will try inside the container"
  fi

  if [[ "$have_image" -eq 1 ]]; then
    log "Extract ${short} via ${image} -> servers/${short}"
    run_docker "$short" "$image"
  else
    log "Extract ${short} on host -> servers/${short}"
    run_host "$short"
  fi
  relativize_client_links "$dest" "$CLIENT_PATH"
}

# --- args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    --list) LIST=1; shift ;;
    --skip-existing) SKIP_EXISTING=1; FORCE=0; CLEAN=0; shift ;;
    --force) FORCE=1; CLEAN=1; shift ;;
    --clean|--fresh) CLEAN=1; FORCE=1; shift ;;
    --continue) CONTINUE=1; shift ;;
    --keep-buildings) KEEP_BUILDINGS=1; shift ;;
    --no-docker) NO_DOCKER=1; shift ;;
    --skip-mmaps) STEPS="maps,vmaps"; shift ;;
    --steps) STEPS="${2:?}"; shift 2 ;;
    --jobs|-j) JOBS="${2:?}"; shift 2 ;;
    --only) ONLY="${2:?}"; shift 2 ;;
    all) ONLY="all"; shift ;;
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

if [[ "$LIST" -eq 1 ]]; then
  cmd_list
  exit 0
fi

[[ -n "$JOBS" ]] || JOBS="$(nproc 2>/dev/null || echo 4)"

# Harvest only collects leftovers — never delete what is already in servers/.
if [[ "$STEPS" == "harvest" ]]; then
  CLEAN=0
  FORCE=0
fi

# --skip-existing keeps previous extract data and skips those steps.
if [[ "$SKIP_EXISTING" -eq 1 ]]; then
  FORCE=0
  CLEAN=0
fi

parse_selection "${ONLY}"
[[ ${#SELECTED[@]} -gt 0 ]] || die "No expansions selected"

log "Repo:   $ROOT"
log "Steps:  $STEPS"
log "Jobs:   $JOBS"
log "Force:  $FORCE"
log "Clean:  $CLEAN  ($([[ "$CLEAN" -eq 1 ]] && echo 'wipe existing extract data' || echo 'keep existing'))"
log "Docker: $([[ "$NO_DOCKER" -eq 1 ]] && echo off || echo on)"
echo "  selected:"
local_short=""
for local_short in "${SELECTED[@]}"; do
  catalog_load "$local_short"
  printf '    %s  (%s ← clients/%s)\n' "$local_short" "$CATALOG_KIND" "$CATALOG_CLIENT"
done
echo

failed=()
succeeded=()
skipped=()

for local_short in "${SELECTED[@]}"; do
  if (
    set -e
    extract_one "$local_short"
  ); then
    succeeded+=("$local_short")
  else
    warn "Failed: ${local_short}"
    failed+=("$local_short")
    if [[ "$CONTINUE" -eq 0 ]]; then
      die "Stopping after failure on ${local_short} (pass --continue to keep going)"
    fi
  fi
  echo
done

echo "========================================"
log "Summary"
echo "  succeeded: ${#succeeded[@]}"
for n in "${succeeded[@]:-}"; do [[ -n "$n" ]] && echo "    + $n"; done
echo "  failed:    ${#failed[@]}"
for n in "${failed[@]:-}"; do [[ -n "$n" ]] && echo "    - $n"; done
echo

if [[ ${#failed[@]} -gt 0 ]]; then
  exit 1
fi
log "Done. Each expansion's data is in servers/<short>/{dbc,maps,vmaps,mmaps} (alpha: servers/alpha/etc/maps)."
