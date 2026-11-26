#!/usr/bin/env bash
# setup.sh — Install and run this tree. A terminal with no arguments opens
# the menu. The same actions are subcommands, so a boot unit or a backup
# timer never opens the menu.
#
#   ./setup.sh                         # menu
#   ./setup.sh help
#   ./setup.sh doctor                  # tools, config, and client folders
#   ./setup.sh host                    # packages, mount, loopback, HAProxy
#   ./setup.sh setup vanilla           # compile, fetch SQL, extract, start
#   ./setup.sh setup --skip-build vanilla
#   ./setup.sh up vanilla,tbc
#   ./setup.sh down vanilla            # stop one realm; the database volume stays
#   ./setup.sh status
#   ./setup.sh logs vanilla
#   ./setup.sh list
#   ./setup.sh core set wotlk TrinityCore-335 --on-data refuse
#   ./setup.sh core modules wotlk mod-playerbots
#   ./setup.sh update                       # rebuild built cores whose source moved
#   ./setup.sh update --only wotlk
#   ./setup.sh update check wotlk
#   ./setup.sh update apply wotlk --db skip
#   ./setup.sh update apply wotlk --db world --confirm wotlk
#   ./setup.sh access show
#   ./setup.sh access set loopback
#   ./setup.sh access set ports --address 203.0.113.10
#   ./setup.sh access set public --realm vanilla=vanilla.example.com,203.0.113.10
#   ./setup.sh password wotlk          # prompts; does not print the password
#   ./setup.sh website wotlk create off
#   ./setup.sh clients
#   ./setup.sh backup path /var/backups/wow
#   ./setup.sh backup now wotlk
#   ./setup.sh backup list
#   ./setup.sh backup delete wotlk STAMP --confirm STAMP
#   ./setup.sh backup restore wotlk STAMP --confirm wotlk
#   ./setup.sh backup schedule on --hour 04
#   ./setup.sh boot enable vanilla,wotlk
#   ./setup.sh erase databases wotlk --confirm wotlk
#   ./setup.sh erase volume --confirm wow_wow-mariadb
#
# Erase scopes: container, databases, characters, maps, install, realm, volume.
# A dump that fails stops the command before anything is dropped.
#
# With no arguments and no terminal, this prints help and exits 2.
# It does not build every expansion. That is: ./setup.sh setup all
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "${ROOT}/docker/runtime/catalog.sh"

OPS=(python3 "${ROOT}/scripts/setup_ops.py")

SKIP_BUILD=0
SKIP_EXTRACT=0
SKIP_DB=0
SKIP_MMAPS=0
REBUILD=0
REEXTRACT=0
REFETCH_DB=0
NO_START=0
CONTINUE=0
DRY_RUN=0
NO_CACHE=0
JOBS="${JOBS:-}"
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
}

ensure_env() {
  if [[ ! -f "${ROOT}/.env" && -f "${ROOT}/.env.example" ]]; then
    cp "${ROOT}/.env.example" "${ROOT}/.env"
    log "Wrote .env from .env.example"
  fi
  if [[ -f "${ROOT}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${ROOT}/.env"
    set +a
  fi
}

parse_only() {
  catalog_select "${ONLY}" || die "Unknown server in: ${ONLY:-} (try ./setup.sh list)"
  [[ ${#SELECTED[@]} -gt 0 ]] || die "No expansions selected"
}

run_or_print() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf 'DRY-RUN: %s\n' "$*"
    return 0
  fi
  "$@"
}

client_present() {
  local dir="$1"
  [[ -d "${dir}/Data" || -d "${dir}/data" ]] && return 0
  [[ -d "${dir}/World of Warcraft/Data" ]] && return 0
  [[ -d "${dir}/_retail_/Data" || -d "${dir}/_classic_/Data" ]] && return 0
  return 1
}

preflight() {
  command -v docker >/dev/null || die "docker is required. Run ./setup.sh host"
  docker info >/dev/null 2>&1 || die "Cannot talk to the Docker daemon. Run ./setup.sh host, then open a new login if you were just added to the docker group."
  if ! docker compose version &>/dev/null && ! command -v docker-compose >/dev/null; then
    die "docker compose is required. Run ./setup.sh host"
  fi
  command -v python3 >/dev/null || die "python3 is required. Run ./setup.sh host"
  command -v rsync >/dev/null || die "rsync is required. Run ./setup.sh host"

  local short dest client
  for short in "${SELECTED[@]}"; do
    catalog_load "$short"
    dest="${ROOT}/servers/${short}"
    client="${ROOT}/clients/${CATALOG_CLIENT}"
    if [[ "$SKIP_EXTRACT" -eq 0 ]] && ! client_present "$client"; then
      warn "${short}: no client Data/ at clients/${CATALOG_CLIENT} — extract will skip it. Place the client; this tree does not download one."
    fi
    if [[ "$SKIP_BUILD" -eq 1 ]]; then
      docker image inspect "${CATALOG_IMAGE}:latest" &>/dev/null \
        || die "${short}: image ${CATALOG_IMAGE}:latest missing (omit --skip-build)"
      install_present "$dest" \
        || die "${short}: servers/${short} has no binaries (omit --skip-build)"
    fi
  done
}

step_build() {
  [[ "$SKIP_BUILD" -eq 1 ]] && { log "Skip compile"; return 0; }
  local args=(--only "$(IFS=','; echo "${SELECTED[*]}")")
  [[ "$REBUILD" -eq 0 ]] && args+=(--skip-existing)
  [[ "$REBUILD" -eq 1 ]] && args+=(--force)
  [[ "$CONTINUE" -eq 1 ]] && args+=(--continue)
  [[ "$NO_CACHE" -eq 1 ]] && args+=(--no-cache)
  [[ -n "$JOBS" ]] && args+=(--jobs "$JOBS")
  log "Compile ${#SELECTED[@]} core(s) in Docker. This can take hours."
  run_or_print "${ROOT}/scripts/build-servers.sh" "${args[@]}"
}

step_fetch_db() {
  [[ "$SKIP_DB" -eq 1 ]] && { log "Skip world-database fetch"; return 0; }
  local args=()
  [[ "$REFETCH_DB" -eq 1 ]] && args+=(--force)
  args+=(--only "$(IFS=','; echo "${SELECTED[*]}")")
  log "Fetch world databases"
  run_or_print bash "${ROOT}/docker/runtime/fetch-db.sh" "${args[@]}"
}

step_prepare_db() {
  [[ "$SKIP_DB" -eq 1 && "$SKIP_EXTRACT" -eq 1 ]] && return 0
  log "Start shared MariaDB and load ${SELECTED[*]} schema"
  run_or_print "${ROOT}/scripts/launch-servers.sh" prepare-db "$(IFS=','; echo "${SELECTED[*]}")"
}

step_extract() {
  [[ "$SKIP_EXTRACT" -eq 1 ]] && { log "Skip client-data extract"; return 0; }
  local args=()
  [[ "$REEXTRACT" -eq 0 ]] && args+=(--skip-existing)
  [[ "$REEXTRACT" -eq 1 ]] && args+=(--force)
  [[ "$SKIP_MMAPS" -eq 1 ]] && args+=(--skip-mmaps)
  [[ "$CONTINUE" -eq 1 ]] && args+=(--continue)
  [[ -n "$JOBS" ]] && args+=(--jobs "$JOBS")
  args+=(--only "$(IFS=','; echo "${SELECTED[*]}")")
  log "Extract client data (maps/vmaps/mmaps/dbc). Map generation can take hours."
  run_or_print "${ROOT}/scripts/extract-data.sh" "${args[@]}"
}

step_launch() {
  [[ "$NO_START" -eq 1 ]] && { log "Skip launch (--no-start)"; return 0; }
  log "Start shared MariaDB + ${#SELECTED[@]} realm(s)"
  run_or_print "${ROOT}/scripts/launch-servers.sh" up "$(IFS=','; echo "${SELECTED[*]}")"
}

cmd_status() {
  parse_only
  printf '%-14s %-8s %-8s %-10s %-10s %-10s %s\n' \
    "SHORT" "IMAGE" "BINS" "MAPS" "WORLD DB" "RUNNING" "DB KIND"
  local short dest image bins maps dump running
  for short in "${SELECTED[@]}"; do
    catalog_load "$short"
    dest="${ROOT}/servers/${short}"
    image="no"
    docker image inspect "${CATALOG_IMAGE}:latest" &>/dev/null && image="ok"
    bins="no"
    install_present "$dest" && bins="ok"
    maps="no"
    if extract_data_complete "$dest" "$CATALOG_KIND"; then
      maps="ok"
    elif [[ "$CATALOG_KIND" == "alpha" ]] \
        && [[ "$(find "${dest}/etc/maps" -type f -name '*.map' 2>/dev/null | wc -l)" -gt 0 ]]; then
      maps="incomplete"
    elif [[ "$(find "${dest}/maps" -type f -name '*.map' 2>/dev/null | wc -l)" -gt 0 ]]; then
      maps="incomplete"
    fi
    dump="no"
    if [[ "$CATALOG_DB_KIND" == "bundled" || "$CATALOG_DB_KIND" == "none" || -z "$CATALOG_DB_KIND" ]]; then
      dump="bundled"
    elif [[ -d "${dest}/db/Full_DB" ]]; then
      dump="ok"
    elif find "${dest}/sql/dumps" -maxdepth 1 -type f \( \
        -iname 'TDB*.sql' -o -iname '*world*.sql' \) 2>/dev/null | grep -q .; then
      dump="ok"
    elif find "${dest}/sql" -maxdepth 2 -type f \( \
        -iname 'TDB*.sql' -o -iname '*world_database*.sql' -o -iname '*world_database*.rar' \
        -o -iname '*world*.7z' -o -iname '*world*.zip' \) 2>/dev/null | grep -q .; then
      dump="packed"
    fi
    running="no"
    docker inspect -f '{{.State.Running}}' "wow-${short}" 2>/dev/null | grep -qx true && running="yes"
    printf '%-14s %-8s %-8s %-10s %-10s %-10s %s\n' \
      "$short" "$image" "$bins" "$maps" "$dump" "$running" "$CATALOG_DB_KIND"
  done
  echo
  if docker inspect -f '{{.State.Status}}' wow-db &>/dev/null; then
    log "Shared MariaDB wow-db: $(docker inspect -f '{{.State.Status}}' wow-db)"
  else
    log "Shared MariaDB wow-db: not created"
  fi
}

cmd_setup() {
  ensure_env
  parse_only
  preflight
  log "Repo:     $ROOT"
  log "Selected: ${SELECTED[*]}"
  log "Steps:    compile=$([[ $SKIP_BUILD -eq 1 ]] && echo skip || echo yes)  db=$([[ $SKIP_DB -eq 1 ]] && echo skip || echo yes)  extract=$([[ $SKIP_EXTRACT -eq 1 ]] && echo skip || echo yes)  launch=$([[ $NO_START -eq 1 ]] && echo skip || echo yes)"
  echo
  local all=("${SELECTED[@]}") short
  local failed=()
  for short in "${all[@]}"; do
    SELECTED=("$short")
    log "==== ${short} ===="
    if [[ "$CONTINUE" -eq 1 ]]; then
      step_build || { warn "${short}: compile failed"; failed+=("$short"); continue; }
      step_fetch_db || { warn "${short}: world-db fetch failed"; failed+=("$short"); continue; }
      step_prepare_db || { warn "${short}: database init failed"; failed+=("$short"); continue; }
      step_extract || { warn "${short}: extract failed"; failed+=("$short"); continue; }
      step_launch || { warn "${short}: launch failed"; failed+=("$short"); continue; }
    else
      step_build
      step_fetch_db
      step_prepare_db
      step_extract
      step_launch
    fi
  done
  echo
  if [[ ${#failed[@]} -gt 0 ]]; then
    die "Failed: ${failed[*]}"
  fi
  log "Done. Selected realms share the wow-db MariaDB container."
  log "Status:  ./setup.sh status"
  log "Logs:    ./setup.sh logs <short>"
  log "Stop:    ./setup.sh down <short>"
}

parse_setup_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help) usage; exit 0 ;;
      --list) exec "${ROOT}/scripts/launch-servers.sh" list ;;
      --skip-build) SKIP_BUILD=1; shift ;;
      --skip-extract) SKIP_EXTRACT=1; shift ;;
      --skip-db|--skip-databases) SKIP_DB=1; shift ;;
      --skip-mmaps) SKIP_MMAPS=1; shift ;;
      --rebuild) REBUILD=1; shift ;;
      --reextract) REEXTRACT=1; shift ;;
      --refetch-db) REFETCH_DB=1; shift ;;
      --no-start) NO_START=1; shift ;;
      --stop-on-error) CONTINUE=0; shift ;;
      --continue) CONTINUE=1; shift ;;
      --dry-run) DRY_RUN=1; shift ;;
      --no-cache) NO_CACHE=1; shift ;;
      --jobs|-j) JOBS="${2:?}"; shift 2 ;;
      --only) ONLY="${2:?}"; shift 2 ;;
      *)
        if [[ -z "$ONLY" ]]; then
          ONLY="$1"
          shift
        else
          die "Unknown argument: $1 (try ./setup.sh help)"
        fi
        ;;
    esac
  done
}

realm_was_running() {
  if [[ "${WOW_FAKE_RUNNING+x}" == x ]]; then
    [[ "$WOW_FAKE_RUNNING" == 1 ]]
    return
  fi
  if [[ "${WOW_FAKE_HEALTH+x}" == x ]]; then
    return 0
  fi
  docker inspect -f '{{.State.Running}}' "wow-$1" 2>/dev/null | grep -qx true
}

# Fake health or running never calls the docker daemon.
realm_became_healthy() {
  local short="$1" status i
  if [[ "${WOW_FAKE_HEALTH+x}" == x || "${WOW_FAKE_RUNNING+x}" == x ]]; then
    [[ "${WOW_FAKE_HEALTH:-healthy}" == healthy ]]
    return
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

stop_realm_for_update() {
  local short="$1"
  if [[ "${WOW_FAKE_RUNNING+x}" == x || "${WOW_FAKE_HEALTH+x}" == x ]]; then
    log "Stopping wow-${short}"
    return 0
  fi
  "${ROOT}/scripts/launch-servers.sh" stop "$short" || true
}

start_realm_after_update() {
  local short="$1"
  if [[ "${WOW_FAKE_RUNNING+x}" == x || "${WOW_FAKE_HEALTH+x}" == x ]]; then
    log "Starting wow-${short}"
    return 0
  fi
  "${ROOT}/scripts/launch-servers.sh" up "$short"
}

cmd_core() {
  local sub="${1:-}"
  shift || true
  case "$sub" in
    set)
      local short="${1:-}" project="${2:-}" on_data="" modules=()
      [[ -n "$short" && -n "$project" ]] || die "usage: ./setup.sh core set SHORT PROJECT [--on-data refuse|reimport|keep]"
      shift 2
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --on-data) on_data="${2:?}"; shift 2 ;;
          --module) modules+=(--module "$2"); shift 2 ;;
          *) die "Unknown argument: $1" ;;
        esac
      done
      local args=(core-set "$short" "$project")
      [[ -n "$on_data" ]] && args+=(--on-data "$on_data")
      "${OPS[@]}" "${args[@]}" "${modules[@]}"
      ;;
    modules)
      local short="${1:-}"
      [[ -n "$short" ]] || die "usage: ./setup.sh core modules SHORT [MODULE ...]"
      shift
      "${OPS[@]}" modules "$short" "$@"
      ;;
    *) die "usage: ./setup.sh core set|modules ..." ;;
  esac
}

cmd_update() {
  local sub="${1:-}"
  local updater="${WOW_UPDATE_BIN:-${ROOT}/scripts/update-from-git.sh}"
  if [[ -z "$sub" || "$sub" == --* ]]; then
    log "Recompiling built cores whose source moved since the last build. This can take hours."
    "$updater" --built "$@"
    return
  fi
  shift
  case "$sub" in
    check)
      "$updater" --check "$@"
      ;;
    apply)
      local db="" confirm="" only=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --db) db="${2:?}"; shift 2 ;;
          --confirm) confirm="${2:?}"; shift 2 ;;
          *)
            [[ -z "$only" ]] || die "Unknown argument: $1"
            only="$1"
            shift
            ;;
        esac
      done
      [[ -n "$only" ]] || die "usage: ./setup.sh update apply SHORT --db skip|world|full"
      [[ "$db" == "skip" || "$db" == "world" || "$db" == "full" ]] || die "--db must be skip, world, or full"
      local was=0
      if [[ "$db" != "skip" ]]; then
        [[ "$confirm" == "$only" ]] || die "Refusing. Pass --confirm ${only}"
      fi
      if realm_was_running "$only"; then
        was=1
        stop_realm_for_update "$only"
      fi
      # Core catch-up does not fetch a dump and does not restart. SQL apply
      # is prepare-db. The pair is stamped only after that succeeds.
      "$updater" --catch-up "$only" --no-fetch --no-restart
      if [[ "$db" == "world" ]]; then
        "${ROOT}/docker/runtime/fetch-db.sh" --force "$only"
        "${OPS[@]}" world-drop "$only" --confirm "$only"
      elif [[ "$db" == "full" ]]; then
        "${ROOT}/docker/runtime/fetch-db.sh" --force "$only"
        "${OPS[@]}" erase databases "$only" --confirm "$only"
      fi
      "${ROOT}/scripts/launch-servers.sh" prepare-db "$only"
      if [[ "$was" -eq 1 ]]; then
        start_realm_after_update "$only"
        if ! realm_became_healthy "$only"; then
          die "${only}: restarted core is not healthy. Database revision was not recorded."
        fi
      fi
      "$updater" --stamp "$only"
      ;;
    *) die "usage: ./setup.sh update [check|apply] ..." ;;
  esac
}

cmd_access() {
  local sub="${1:-show}"
  shift || true
  case "$sub" in
    show) "${OPS[@]}" access-show ;;
    set)
      local mode="${1:-}"
      shift || true
      case "$mode" in
        loopback) "${OPS[@]}" access-set loopback ;;
        ports)
          local address=""
          while [[ $# -gt 0 ]]; do
            case "$1" in
              --address) address="${2:?}"; shift 2 ;;
              *) die "Unknown argument: $1" ;;
            esac
          done
          [[ -n "$address" ]] || die "usage: ./setup.sh access set ports --address IP"
          "${OPS[@]}" access-set ports --address "$address"
          ;;
        public)
          local args=()
          while [[ $# -gt 0 ]]; do
            case "$1" in
              --realm) args+=(--realm "$2"); shift 2 ;;
              *) die "Unknown argument: $1" ;;
            esac
          done
          [[ ${#args[@]} -gt 0 ]] || die "usage: ./setup.sh access set public --realm short=hostname,ip"
          "${OPS[@]}" access-set public "${args[@]}"
          ;;
        *) die "usage: ./setup.sh access set loopback|ports|public" ;;
      esac
      ;;
    firewall)
      local confirm=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --confirm) confirm="${2:?}"; shift 2 ;;
          *) die "Unknown argument: $1" ;;
        esac
      done
      [[ "$confirm" == "open" ]] || die "Refusing. Pass --confirm open"
      "${ROOT}/scripts/open-firewall.sh"
      ;;
    *) die "usage: ./setup.sh access show|set|firewall" ;;
  esac
}

cmd_password() {
  local short="${1:-}" save=0
  [[ -n "$short" ]] || die "usage: ./setup.sh password SHORT [--save-env]"
  shift
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --save-env) save=1; shift ;;
      *) die "Unknown argument: $1" ;;
    esac
  done
  local password
  if [[ -t 0 ]]; then
    read -r -s -p "New GM password: " password
    echo
  else
    IFS= read -r password
  fi
  catalog_load "$short" || die "Unknown realm ${short}"
  local args=(password "$short")
  [[ "$save" -eq 1 ]] && args+=(--save-env)
  WOW_KIND="$CATALOG_KIND" \
    WOW_PROTO="$CATALOG_PROTO" \
    WOW_EXPANSION="$CATALOG_EXPANSION" \
    ACCOUNT_PASSWORD="$password" \
    "${OPS[@]}" "${args[@]}"
}

cmd_website() {
  local short="${1:-}" verb="${2:-}" state="${3:-}"
  [[ -n "$short" && "$verb" == "create" && -n "$state" ]] || die "usage: ./setup.sh website SHORT create on|off"
  "${OPS[@]}" website "$short" "$state"
}

cmd_backup() {
  local sub="${1:-}"
  shift || true
  case "$sub" in
    path)
      [[ -n "${1:-}" ]] || die "usage: ./setup.sh backup path DIRECTORY"
      "${OPS[@]}" backup-path "$1"
      ;;
    now) "${OPS[@]}" backup-now "$@" ;;
    list) "${OPS[@]}" backup-list ;;
    delete)
      local short="${1:-}" stamp="${2:-}" confirm=""
      shift 2 || true
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --confirm) confirm="${2:?}"; shift 2 ;;
          *) die "Unknown argument: $1" ;;
        esac
      done
      "${OPS[@]}" backup-delete "$short" "$stamp" --confirm "$confirm"
      ;;
    restore)
      local short="${1:-}" stamp="${2:-}" confirm=""
      shift 2 || true
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --confirm) confirm="${2:?}"; shift 2 ;;
          *) die "Unknown argument: $1" ;;
        esac
      done
      "${OPS[@]}" backup-restore "$short" "$stamp" --confirm "$confirm"
      ;;
    schedule)
      local state="${1:-}" hour="04"
      shift || true
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --hour) hour="${2:?}"; shift 2 ;;
          *) die "Unknown argument: $1" ;;
        esac
      done
      case "$state" in
        on)
          [[ "$hour" =~ ^[0-9]{2}$ && 10#$hour -le 23 ]] || die "--hour expects 00 through 23"
          python3 - "$ROOT/.env" "$hour" <<'PY'
import pathlib, sys
path, hour = sys.argv[1], sys.argv[2]
file = pathlib.Path(path)
text = file.read_text(encoding="utf-8") if file.exists() else ""
updates = {"BACKUP_SCHEDULE": "on", "BACKUP_HOUR": hour}
lines = text.splitlines()
seen = set()
out = []
for line in lines:
    stripped = line.strip()
    if stripped and not stripped.startswith("#") and "=" in line:
        key = line.split("=", 1)[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
            continue
    out.append(line)
for key, value in updates.items():
    if key not in seen:
        out.append(f"{key}={value}")
file.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
          log "Daily backups at ${hour}:00. Installing the timer."
          "${ROOT}/scripts/host-setup.sh"
          ;;
        off)
          python3 - "$ROOT/.env" <<'PY'
import pathlib, sys
file = pathlib.Path(sys.argv[1])
text = file.read_text(encoding="utf-8") if file.exists() else ""
lines = []
seen = False
for line in text.splitlines():
    if line.startswith("BACKUP_SCHEDULE="):
        lines.append("BACKUP_SCHEDULE=off")
        seen = True
    else:
        lines.append(line)
if not seen:
    lines.append("BACKUP_SCHEDULE=off")
file.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
          "${ROOT}/scripts/host-setup.sh"
          ;;
        *) die "usage: ./setup.sh backup schedule on|off [--hour HH]" ;;
      esac
      ;;
    *) die "usage: ./setup.sh backup path|now|list|delete|restore|schedule" ;;
  esac
}

cmd_boot() {
  local sub="${1:-}"
  shift || true
  mkdir -p "${ROOT}/.run"
  case "$sub" in
    enable)
      local list="${1:-}"
      [[ -n "$list" ]] || die "usage: ./setup.sh boot enable vanilla,wotlk"
      catalog_select "$list" || die "Unknown server in: ${list}"
      printf '%s\n' "$(IFS=','; echo "${SELECTED[*]}")" > "${ROOT}/.run/boot.conf"
      log "Boot will start: ${SELECTED[*]}"
      "${ROOT}/scripts/host-setup.sh"
      ;;
    disable)
      : > "${ROOT}/.run/boot.conf"
      log "Boot start disabled"
      "${ROOT}/scripts/host-setup.sh"
      ;;
    *) die "usage: ./setup.sh boot enable SHORTS|disable" ;;
  esac
}

cmd_erase() {
  local scope="${1:-}"
  shift || true
  local short="" confirm=""
  if [[ "$scope" == "volume" ]]; then
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --confirm) confirm="${2:?}"; shift 2 ;;
        *) die "Unknown argument: $1" ;;
      esac
    done
    "${OPS[@]}" erase volume --confirm "$confirm"
    return
  fi
  short="${1:-}"
  shift || true
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --confirm) confirm="${2:?}"; shift 2 ;;
      *) die "Unknown argument: $1" ;;
    esac
  done
  [[ -n "$short" ]] || die "usage: ./setup.sh erase SCOPE SHORT --confirm SHORT"
  "${OPS[@]}" erase "$scope" "$short" --confirm "$confirm"
}

one_realm() {
  local only=""
  if [[ $# -gt 0 && "$1" != --* ]]; then
    only="$1"
  fi
  printf '%s' "$only"
}

# --- dispatch ---
if [[ $# -eq 0 ]]; then
  if [[ -t 0 && -t 1 ]]; then
    command -v python3 >/dev/null || die "python3 is required to open the menu. Run ./setup.sh host"
    exec python3 "${ROOT}/scripts/setup_menu.py"
  fi
  usage >&2
  exit 2
fi

CMD=""
case "$1" in
  help|-h|--help) usage; exit 0 ;;
  doctor|host|setup|up|down|stop|restart|status|logs|list|core|update|access|password|website|clients|backup|boot|erase|menu)
    CMD="$1"
    shift
    ;;
  *) CMD="setup" ;;
esac

case "$CMD" in
  menu)
    [[ -t 0 && -t 1 ]] || { usage >&2; exit 2; }
    exec python3 "${ROOT}/scripts/setup_menu.py"
    ;;
  doctor) "${OPS[@]}" doctor ;;
  host)
    "${ROOT}/scripts/install-packages.sh"
    "${ROOT}/scripts/host-setup.sh"
    ;;
  setup)
    parse_setup_args "$@"
    cmd_setup
    ;;
  list) "${ROOT}/scripts/launch-servers.sh" list ;;
  status)
    ONLY="${1:-all}"
    cmd_status
    ;;
  up|down|stop|restart)
    "${ROOT}/scripts/launch-servers.sh" "$CMD" "$(one_realm "$@")"
    ;;
  logs)
    [[ -n "${1:-}" ]] || die "logs needs a server name"
    "${ROOT}/scripts/launch-servers.sh" logs "$1"
    ;;
  core) cmd_core "$@" ;;
  update) cmd_update "$@" ;;
  access) cmd_access "$@" ;;
  password) cmd_password "$@" ;;
  website) cmd_website "$@" ;;
  clients) "${OPS[@]}" clients ;;
  backup) cmd_backup "$@" ;;
  boot) cmd_boot "$@" ;;
  erase) cmd_erase "$@" ;;
  *) die "Unknown command: $CMD" ;;
esac
