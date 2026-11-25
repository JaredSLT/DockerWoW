#!/usr/bin/env bash
# build-servers.sh — Build every expansion Docker image and extract installs
# into ./servers/<shorthand>/ (e.g. vanilla, tbc, wotlk, …).
#
# Usage (from repo root):
#   ./setup.sh vanilla
#   ./scripts/build-servers.sh --only vanilla
#   ./scripts/build-servers.sh --extract-only
#   ./scripts/build-servers.sh --build-only
#   ./scripts/build-servers.sh --skip-existing
#   ./scripts/build-servers.sh --list
#
# Environment / flags:
#   GIT_BASE     Optional mirror prefix. Empty uses docker/common/repos.sh.
#   JOBS         Parallel compile jobs passed to docker build (optional)
#   BUILD_TYPE   Release|Debug (optional; Dockerfile default is Release)
#   --network    Docker network mode (default: host)
#   --no-cache   Pass --no-cache to docker build
#   --continue   Continue after a failed core (default: stop on first failure)
#   --force      Re-extract even when servers/<shorthand> already exists
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "${ROOT}/docker/common/repos.sh"
# shellcheck disable=SC1091
source "${ROOT}/docker/runtime/catalog.sh"

GIT_BASE="${GIT_BASE:-}"
NETWORK="${NETWORK:-host}"
JOBS="${JOBS:-}"
BUILD_TYPE="${BUILD_TYPE:-}"
NO_CACHE=0
EXTRACT_ONLY=0
BUILD_ONLY=0
SKIP_EXISTING=0
FORCE=0
CONTINUE=0
ONLY=""
LIST=0

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# Host install folder shorthand for each docker/<core>/ product.
short_name_for() {
  case "$1" in
    alpha-core)                          printf 'alpha' ;;
    cmangos-classic)                     printf 'vanilla' ;;
    cmangos-tbc)                         printf 'tbc' ;;
    azerothcore-wotlk)                   printf 'wotlk' ;;
    The-Cataclysm-Preservation-Project)  printf 'cata' ;;
    WodCore-Reforged)                    printf 'wod' ;;
    SkyFire_548)                         printf 'mop' ;;
    TrinityCore-Legion)                  printf 'legion' ;;
    TrinityCore-BFA)                     printf 'bfa' ;;
    TrinityCore-Shadowlands)             printf 'shadowlands' ;;
    TrinityCore-Dragonflight)            printf 'dragonflight' ;;
    TrinityCore-WarWithin)               printf 'warwithin' ;;
    TrinityCore)                         printf 'midnight' ;;
    *)
      printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr '_' '-'
      ;;
  esac
}

# Realm folder for a core. Alternate cores share the catalog short (vanilla, wotlk, ...).
install_short_for() {
  python3 "${ROOT}/scripts/select-project.py" --install-short "$1"
}

# The core we are about to compile has to be the one selected for that slot.
assert_builds_selected_core() {
  local name="$1" short selected
  short="$(install_short_for "$name")"
  selected="$(python3 "${ROOT}/scripts/select-project.py" --print-core "$short")"
  if [[ "$selected" != "$name" ]]; then
    die "${name} installs into servers/${short}, but ${short} is set to ${selected}. Run: ./scripts/select-project.py --set ${short}=${name}"
  fi
}

# Discover expansion Dockerfiles (skip helpers that are not cores).
discover_cores() {
  local dir name
  for dir in "$ROOT"/docker/*/; do
    name="$(basename "$dir")"
    [[ "$name" == "common" || "$name" == "runtime" ]] && continue
    [[ -f "${dir}Dockerfile" ]] || continue
    printf '%s\n' "$name"
  done | sort
}

# Image tag: wow-<lowercase-name-with-underscores-to-dashes>
image_tag_for() {
  local name="$1"
  local tag
  tag="$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]' | tr '_' '-')"
  printf 'wow-%s' "$tag"
}

# Resolve a user token (core name or shorthand) back to the docker core name.
resolve_core_name() {
  local token="$1" name short
  token="${token// /}"
  for name in "${ALL_CORES[@]:-}"; do
    [[ "$token" == "$name" ]] && { printf '%s' "$name"; return 0; }
    short="$(short_name_for "$name")"
    [[ "$token" == "$short" ]] && { printf '%s' "$name"; return 0; }
  done
  local tlow
  tlow="$(printf '%s' "$token" | tr '[:upper:]' '[:lower:]')"
  for name in "${ALL_CORES[@]:-}"; do
    short="$(short_name_for "$name")"
    [[ "$tlow" == "$short" ]] && { printf '%s' "$name"; return 0; }
    [[ "$tlow" == "$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')" ]] && { printf '%s' "$name"; return 0; }
  done
  return 1
}

usage() {
  awk '
    NR == 1 { next }
    /^#/ { sub(/^# ?/, ""); print; next }
    { exit }
  ' "$0"
  echo
  echo "Expansion shorthand map (docker core → servers/ folder):"
  local name
  while IFS= read -r name; do
    printf '  %-40s → servers/%s\n' "$name" "$(short_name_for "$name")"
  done < <(discover_cores)
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    --list) LIST=1; shift ;;
    --extract-only) EXTRACT_ONLY=1; shift ;;
    --build-only) BUILD_ONLY=1; shift ;;
    --skip-existing) SKIP_EXISTING=1; shift ;;
    --force) FORCE=1; shift ;;
    --continue) CONTINUE=1; shift ;;
    --no-cache) NO_CACHE=1; shift ;;
    --network) NETWORK="${2:?}"; shift 2 ;;
    --git-base) GIT_BASE="${2:?}"; shift 2 ;;
    --jobs|-j) JOBS="${2:?}"; shift 2 ;;
    --build-type) BUILD_TYPE="${2:?}"; shift 2 ;;
    --only) ONLY="${2:?}"; shift 2 ;;
    *) die "Unknown argument: $1 (try --help)" ;;
  esac
done

if [[ "$EXTRACT_ONLY" -eq 1 && "$BUILD_ONLY" -eq 1 ]]; then
  die "Cannot use --extract-only and --build-only together"
fi

core_selected() {
  local name="$1" item short
  if [[ -z "$ONLY" ]]; then
    while IFS= read -r short; do
      catalog_load "$short" || continue
      [[ "$CATALOG_CORE" == "$name" ]] && return 0
    done < <(catalog_shorts)
    return 1
  fi
  IFS=',' read -ra items <<<"$ONLY"
  for item in "${items[@]}"; do
    item="${item// /}"
    [[ -z "$item" ]] && continue
    [[ "$item" == "$name" ]] && return 0
    if catalog_load "$item" 2>/dev/null; then
      [[ "$CATALOG_CORE" == "$name" ]] && return 0
    fi
  done
  return 1
}

install_present() {
  local dest="$1"
  # Treat as present if we have binaries or (alpha-core style) main entrypoints.
  [[ -d "${dest}/bin" ]] && return 0
  [[ -f "${dest}/main.py" || -f "${dest}/run-server.sh" ]] && return 0
  return 1
}

build_core() {
  local name="$1"
  local dockerfile="$ROOT/docker/${name}/Dockerfile"
  local tag
  tag="$(image_tag_for "$name")"

  [[ -f "$dockerfile" ]] || die "Missing Dockerfile: $dockerfile"

  local rev url ref kind short modules
  short="$(install_short_for "$name")"
  assert_builds_selected_core "$name"
  modules=""
  if catalog_load "$short" 2>/dev/null; then
    modules="${CATALOG_MODULES:-}"
  fi
  if [[ -n "$GIT_BASE" ]]; then
    repo_lookup "$name" || die "No repo map entry for ${name}"
    url="${GIT_BASE%/}/${name}.git"
    ref="$REPO_REF"
    kind="$REPO_KIND"
  else
    repo_lookup "$name" || die "No public repo for ${name}"
    url="$REPO_URL"
    ref="$REPO_REF"
    kind="$REPO_KIND"
  fi
  rev="$(repo_sha "$url" "$ref" "$kind")" || die "Cannot resolve ${ref} from ${url}"
  BUILT_CORE_REV="$rev"
  if [[ -n "$modules" ]]; then
    BUILT_CORE_REV="${rev}+${modules}"
  fi

  local args=(
    build
    --network="$NETWORK"
    --build-arg "SOURCE_REV=${rev}"
    --build-arg "CORE_BRANCH=${ref}"
    -f "$dockerfile"
    -t "${tag}:latest"
  )
  [[ -n "$GIT_BASE" ]] && args+=(--build-arg "GIT_BASE=${GIT_BASE}")
  [[ -n "$modules" ]] && args+=(--build-arg "WOW_MODULES=${modules}")
  [[ -n "$JOBS" ]] && args+=(--build-arg "JOBS=${JOBS}")
  [[ -n "$BUILD_TYPE" ]] && args+=(--build-arg "BUILD_TYPE=${BUILD_TYPE}")
  [[ "$NO_CACHE" -eq 1 ]] && args+=(--no-cache)

  log "Building ${name} -> ${tag}:latest (${ref} ${rev})"
  log "  docker ${args[*]} ."
  docker "${args[@]}" "$ROOT" || die "docker build failed for ${name}"
}

extract_core() {
  local name="$1"
  local short tag cname src dest
  short="$(install_short_for "$name")"
  tag="$(image_tag_for "$name")"
  cname="${short}-extract"
  # Image always installs under the full core name; host folder is the shorthand.
  src="/servers/${name}"
  dest="$ROOT/servers/${short}"

  if ! docker image inspect "${tag}:latest" &>/dev/null; then
    die "Image ${tag}:latest not found — build first (omit --extract-only)"
  fi

  if install_present "$dest" && [[ "$FORCE" -eq 0 ]]; then
    if [[ "$SKIP_EXISTING" -eq 1 ]]; then
      log "Skip extract ${name} (servers/${short} already present; use --force to overwrite)"
      return 0
    fi
    log "Replacing existing servers/${short}"
  fi

  log "Extracting ${tag}:latest -> servers/${short}  (core: ${name})"
  docker rm -f "$cname" &>/dev/null || true
  docker create --name "$cname" "${tag}:latest" >/dev/null

  local tmp="$ROOT/servers/.extracting-${short}"
  rm -rf "$tmp"
  # Prefer the documented path; fall back to first /servers/* entry.
  if ! docker cp "$cname:${src}" "$tmp" 2>/dev/null; then
    local found
    found="$(docker run --rm "${tag}:latest" bash -lc 'ls -d /servers/* 2>/dev/null | head -1' || true)"
    [[ -n "$found" ]] || { docker rm -f "$cname" &>/dev/null || true; die "No /servers/* product in ${tag}"; }
    rm -rf "$tmp"
    docker cp "$cname:${found}" "$tmp"
  fi
  docker rm -f "$cname" &>/dev/null || true

  mkdir -p "$dest"
  # Keep extracted client data / dumps / logs when replacing binaries.
  # Patterns are rooted at dest/ so we do not skip source trees like database/dbc/.
  rsync -a --delete \
    --exclude /maps/ --exclude /vmaps/ --exclude /mmaps/ \
    --exclude /dbc/ --exclude /cameras/ --exclude /Cameras/ \
    --exclude /gt/ --exclude /Buildings/ --exclude /logs/ \
    --exclude /db/ --exclude /sql/dumps/ \
    --exclude /etc/maps/ --exclude /etc/navs/ \
    --exclude /etc/mdx/ --exclude /etc/wmo_liquids/ --exclude /etc/wmo_geometry/ \
    "${tmp}/" "${dest}/"
  rm -rf "$tmp"

  local size
  size="$(du -sh "$dest" 2>/dev/null | cut -f1 || echo '?')"
  log "Installed servers/${short} (${size})"
  if [[ -d "${dest}/bin" ]]; then
    log "  bin/: $(ls "${dest}/bin" 2>/dev/null | tr '\n' ' ')"
  fi
}

# --- main ---
command -v docker >/dev/null || die "docker is required"
command -v rsync >/dev/null || die "rsync is required to extract installs without wiping maps/dumps"

mapfile -t ALL_CORES < <(discover_cores)
[[ ${#ALL_CORES[@]} -gt 0 ]] || die "No docker/*/Dockerfile found under $ROOT/docker"

CORES=()
for name in "${ALL_CORES[@]}"; do
  core_selected "$name" || continue
  CORES+=("$name")
done
[[ ${#CORES[@]} -gt 0 ]] || die "No cores matched --only=${ONLY}"

if [[ "$LIST" -eq 1 ]]; then
  printf 'Available cores (%d):\n' "${#ALL_CORES[@]}"
  printf '  %-40s  %-14s  %-45s  %-10s  %s\n' "CORE" "SHORTHAND" "IMAGE" "IMAGE?" "servers/"
  for name in "${ALL_CORES[@]}"; do
    short="$(short_name_for "$name")"
    tag="$(image_tag_for "$name")"
    status="no"
    docker image inspect "${tag}:latest" &>/dev/null && status="ok"
    host="missing"
    install_present "$ROOT/servers/${short}" && host="present"
    # Also note legacy full-name folder if still around
    legacy=""
    [[ -d "$ROOT/servers/${name}" && "$name" != "$short" ]] && legacy=" (legacy: servers/${name})"
    sel=""
    core_selected "$name" && sel="*"
    printf '  %-40s  %-14s  %-45s  %-10s  %s%s %s\n' \
      "$name" "$short" "$tag" "$status" "$host" "$legacy" "$sel"
  done
  exit 0
fi

mkdir -p "$ROOT/servers"

log "Repo root:   $ROOT"
if [[ -n "$GIT_BASE" ]]; then
  log "GIT_BASE:    $GIT_BASE (mirror override)"
else
  log "Sources:     public repos (docker/common/repos.sh)"
fi
log "Network:     $NETWORK"
log "Cores:       ${#CORES[@]} selected (${#ALL_CORES[@]} total)"
[[ -n "$JOBS" ]] && log "JOBS:        $JOBS"
[[ -n "$BUILD_TYPE" ]] && log "BUILD_TYPE:  $BUILD_TYPE"
log "Mode:        $(
  if [[ "$EXTRACT_ONLY" -eq 1 ]]; then echo extract-only
  elif [[ "$BUILD_ONLY" -eq 1 ]]; then echo build-only
  else echo build+extract
  fi
)"
echo "  shorthand mapping:"
for name in "${CORES[@]}"; do
  printf '    %s → servers/%s\n' "$name" "$(install_short_for "$name")"
done
echo

failed=()
succeeded=()
skipped=()

for name in "${CORES[@]}"; do
  short="$(install_short_for "$name")"
  assert_builds_selected_core "$name"
  if [[ "$SKIP_EXISTING" -eq 1 ]] && install_present "$ROOT/servers/${short}" && [[ "$FORCE" -eq 0 ]] \
      && python3 "${ROOT}/scripts/select-project.py" --install-matches "$short"; then
    log "Skip ${name} (--skip-existing and servers/${short} matches the selection)"
    skipped+=("${name}→${short}")
    continue
  fi

  if (
    set -e
    if [[ "$EXTRACT_ONLY" -eq 0 ]]; then
      build_core "$name"
    fi
    if [[ "$BUILD_ONLY" -eq 0 ]]; then
      # The loop already decided this install is stale. Copy the new tree
      # even when --skip-existing was set for cores that still match.
      FORCE=1 extract_core "$name"
    fi
    if [[ "$EXTRACT_ONLY" -eq 0 && "$BUILD_ONLY" -eq 0 ]]; then
      python3 "${ROOT}/scripts/select-project.py" --stamp "$short" --built-core "$name"
      if [[ -n "${BUILT_CORE_REV:-}" ]]; then
        record_built_rev "$short" "$BUILT_CORE_REV"
      fi
    fi
  ); then
    succeeded+=("${name}→${short}")
  else
    warn "Failed: ${name} → servers/${short}"
    failed+=("${name}→${short}")
    if [[ "$CONTINUE" -eq 0 ]]; then
      die "Stopping after failure on ${name} (pass --continue to keep going)"
    fi
  fi
  echo
done

echo "========================================"
log "Summary"
echo "  succeeded: ${#succeeded[@]}"
for n in "${succeeded[@]:-}"; do [[ -n "$n" ]] && echo "    + $n"; done
echo "  skipped:   ${#skipped[@]}"
for n in "${skipped[@]:-}"; do [[ -n "$n" ]] && echo "    ~ $n"; done
echo "  failed:    ${#failed[@]}"
for n in "${failed[@]:-}"; do [[ -n "$n" ]] && echo "    - $n"; done
echo

if [[ ${#failed[@]} -gt 0 ]]; then
  exit 1
fi

if [[ "$BUILD_ONLY" -eq 0 ]]; then
  log "servers/ tree:"
  du -sh "$ROOT"/servers/*/ 2>/dev/null | sort -h || true
fi

log "Done."
