#!/usr/bin/env bash
# launch-servers.sh — Run one, many, or all extracted expansions in Docker.
# Each realm gets its own databases, configs, GM account, and published ports.
#
# Usage (from repo root):
#   ./setup.sh vanilla
#   ./scripts/launch-servers.sh up
#   ./scripts/launch-servers.sh up vanilla
#   ./scripts/launch-servers.sh down [servers]
#   ./scripts/launch-servers.sh stop [servers]
#   ./scripts/launch-servers.sh restart vanilla
#   ./scripts/launch-servers.sh status
#   ./scripts/launch-servers.sh logs vanilla
#   ./scripts/launch-servers.sh list
#
# Default BIND_MODE=haproxy: wow-haproxy publishes stock client ports
# (3724 / 1119, world 8085, REST 8081) on vanilla.local, tbc.local, and the
# other per-realm names. BIND_MODE=ports keeps the unique host ports.
#
# Prerequisites (or just run ./setup.sh which does all of this):
#   ./scripts/build-servers.sh --only <cores>
#   ./scripts/extract-data.sh [servers]
#   docker + docker compose
#
# Default login (created on the first start, then left alone):
#   admin / admin
#   WoD and Legion+: admin@<expansion>.local / admin
# Change it with ./setup.sh password <short>.
# CMaNGOS also ships ADMINISTRATOR / ADMINISTRATOR (and PLAYER, …).
# Alpha creates an account on first login (auto_create_accounts).
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Snapshot layout keys before .env is sourced. setup.sh exports .env before
# it starts this script, so those values match .env and are not an override.
# A value that differs from .env was exported by the operator and is kept.
_PRE_WOW_VOLUME_UUID=${WOW_VOLUME_UUID-}
_PRE_WOW_VOLUME_UUID_SET=${WOW_VOLUME_UUID+x}
_PRE_WOW_VOLUME_MOUNT=${WOW_VOLUME_MOUNT-}
_PRE_WOW_VOLUME_MOUNT_SET=${WOW_VOLUME_MOUNT+x}
_PRE_WOW_TREE=${WOW_TREE-}
_PRE_WOW_TREE_SET=${WOW_TREE+x}
_PRE_WOW_MEDIA_USER=${WOW_MEDIA_USER-}
_PRE_WOW_MEDIA_USER_SET=${WOW_MEDIA_USER+x}

# shellcheck disable=SC1091
source "${ROOT}/docker/runtime/catalog.sh"

RUN_DIR="${ROOT}/.run"
COMPOSE_FILE="${RUN_DIR}/compose.yml"
ENV_FILE="${ROOT}/.env"

BIND_MODE="${BIND_MODE:-haproxy}"
CLI_BIND_MODE="${CLI_BIND_MODE:-}"
POINT_CLIENTS="${POINT_CLIENTS:-0}"
NO_BUILD=0
ONLY=""
CMD=""

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
  echo "Expansion map:"
  printf '  %-14s %-12s %-16s %-18s %s\n' "SHORT" "KIND" "LOOPBACK" "CLIENT" "REALM"
  local short
  while IFS= read -r short; do
    catalog_load "$short"
    printf '  %-14s %-12s %-16s %-18s %s\n' \
      "$CATALOG_SHORT" "$CATALOG_KIND" "$CATALOG_LOOPBACK" \
      "$CATALOG_CLIENT" "$CATALOG_REALM_NAME"
  done < <(catalog_shorts)
  exit 0
}

dotenv_value() {
  local key="$1" file="$2" line k v
  [[ -f "$file" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="${line#"${line%%[![:space:]]*}"}"
    [[ "$line" == *=* ]] || continue
    k="${line%%=*}"
    k="${k%"${k##*[![:space:]]}"}"
    [[ "$k" == "$key" ]] || continue
    v="${line#*=}"
    v="${v#"${v%%[![:space:]]*}"}"
    v="${v%"${v##*[![:space:]]}"}"
    v="${v%\"}"
    v="${v#\"}"
    v="${v%\'}"
    v="${v#\'}"
    printf '%s' "$v"
    return 0
  done <"$file"
}

# /etc/wow/volume.env is the host layout. It replaces the same keys from .env.
# An operator export that differs from .env still wins. WOW_TREE, when still
# empty, is this checkout (the directory that contains setup.sh).
load_volume_env() {
  local key val line file_uuid="" file_mount="" file_tree="" file_user=""
  local saw_uuid=0 saw_mount=0 saw_tree=0 saw_user=0
  local volume_env="${WOW_VOLUME_ENV:-/etc/wow/volume.env}"
  if [[ -f "$volume_env" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="${line#"${line%%[![:space:]]*}"}"
      [[ "$line" == *=* ]] || continue
      key="${line%%=*}"
      key="${key%"${key##*[![:space:]]}"}"
      val="${line#*=}"
      case "$key" in
        WOW_VOLUME_UUID) file_uuid="$val"; saw_uuid=1 ;;
        WOW_VOLUME_MOUNT) file_mount="$val"; saw_mount=1 ;;
        WOW_TREE) file_tree="$val"; saw_tree=1 ;;
        WOW_MEDIA_USER) file_user="$val"; saw_user=1 ;;
      esac
    done <"$volume_env"
  fi
  apply_layout_key WOW_VOLUME_UUID "$file_uuid" "$saw_uuid"
  apply_layout_key WOW_VOLUME_MOUNT "$file_mount" "$saw_mount"
  apply_layout_key WOW_TREE "$file_tree" "$saw_tree"
  apply_layout_key WOW_MEDIA_USER "$file_user" "$saw_user"
  if [[ -z "${WOW_TREE:-}" ]]; then
    export WOW_TREE="$ROOT"
  fi
  if [[ -z "${WOW_VOLUME_MOUNT:-}" ]]; then
    export WOW_VOLUME_MOUNT="$WOW_TREE"
  fi
}

apply_layout_key() {
  local key="$1" file_val="$2" from_file="$3"
  local pre_set_var="_PRE_${key}_SET" pre_val_var="_PRE_${key}" dotenv
  dotenv="$(dotenv_value "$key" "$ENV_FILE")"
  if [[ -n "${!pre_set_var:-}" ]]; then
    local pre="${!pre_val_var-}"
    if [[ "$pre" != "$dotenv" ]]; then
      export "${key}=${pre}"
      return 0
    fi
  fi
  if [[ "$from_file" == "1" ]]; then
    export "${key}=${file_val}"
  fi
}

load_env() {
  if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
  if [[ -n "${CLI_BIND_MODE:-}" ]]; then
    BIND_MODE="$CLI_BIND_MODE"
  fi
  load_volume_env
}

# Mount the removable disk at a stable path and refresh hosts / HAProxy.
ensure_host() {
  "${ROOT}/scripts/host-setup.sh"
  load_volume_env
}

layout_run_dir() {
  printf '%s/.run' "${WOW_TREE:-$ROOT}"
}

copy_layout_file() {
  local src="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [[ "$src" -ef "$dest" ]]; then
    return 0
  fi
  cp -a "$src" "$dest"
}

render_haproxy() {
  # shellcheck disable=SC1091
  source "${ROOT}/docker/runtime/haproxy.sh"
  local dir="${ROOT}/.run"
  mkdir -p "$dir"
  haproxy_render "${dir}/haproxy.cfg"
  copy_layout_file "${dir}/haproxy.cfg" "$(layout_run_dir)/haproxy.cfg"
}

write_mariadb_cnf() {
  # shellcheck disable=SC1091
  source "${ROOT}/docker/runtime/mariadb_tune.sh"
  local mem fstype dir="${ROOT}/.run"
  mem="$(mariadb_memtotal_kb)"
  fstype="$(mariadb_docker_fstype)"
  mkdir -p "$dir"
  mariadb_write_cnf "${ROOT}/docker/runtime/mysql.cnf" "${dir}/mariadb.cnf" "$mem" "$fstype"
  copy_layout_file "${dir}/mariadb.cnf" "$(layout_run_dir)/mariadb.cnf"
}

assert_mariadb_pool() {
  # shellcheck disable=SC1091
  source "${ROOT}/docker/runtime/mariadb_tune.sh"
  local mem pool
  mem="$(mariadb_memtotal_kb)"
  pool="$(mariadb_buffer_pool "$mem")"
  if mariadb_pool_exceeds_half "$mem"; then
    die "MariaDB buffer pool ${pool} is larger than half of MemTotal. Refusing to start wow-db."
  fi
}

prepare_stack_files() {
  load_volume_env
  render_haproxy
  write_mariadb_cnf
}

# wow-<short>-init is read-only, so only the host removes .reimport, and only
# after that init exits 0. A stale exited container from an earlier start does
# not count: FinishedAt has to fall in this run.
init_succeeded_since() {
  local name="$1" start="$2"
  command -v docker >/dev/null 2>&1 || return 1
  docker inspect "$name" >/dev/null 2>&1 || return 1
  python3 - "$name" "$start" <<'PY'
import subprocess, sys
from datetime import datetime, timezone
name, start = sys.argv[1], int(sys.argv[2])
raw = subprocess.check_output(
    ["docker", "inspect", "-f", "{{.State.Status}} {{.State.ExitCode}} {{.State.FinishedAt}}", name],
    text=True,
).strip()
status, code, finished = raw.split(" ", 2)
if status != "exited" or code != "0":
    sys.exit(1)
if not finished or finished.startswith("0001"):
    sys.exit(1)
if finished.endswith("Z"):
    finished = finished[:-1] + "+00:00"
if "." in finished:
    head, tail = finished.split(".", 1)
    frac, rest = "", ""
    for i, ch in enumerate(tail):
        if ch.isdigit():
            frac += ch
        else:
            rest = tail[i:]
            break
    finished = head + "." + (frac[:6] or "0") + (rest or "+00:00")
dt = datetime.fromisoformat(finished)
if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)
epoch = int(dt.timestamp())
sys.exit(0 if epoch + 5 >= start else 1)
PY
}

clear_reimport_marker() {
  local short="$1"
  rm -f "${ROOT}/servers/${short}/.reimport"
}

compose() {
  if docker compose version &>/dev/null; then
    docker compose --project-directory "$RUN_DIR" -f "$COMPOSE_FILE" "$@"
  elif command -v docker-compose >/dev/null; then
    docker-compose --project-directory "$RUN_DIR" -f "$COMPOSE_FILE" "$@"
  else
    die "docker compose is required"
  fi
}

parse_selection() {
  catalog_select "${1:-}" || die "Unknown server in: ${1:-} (try --list)"
}

available_for_launch() {
  local short="$1"
  catalog_load "$short" || return 1
  install_present "${ROOT}/servers/${short}" || return 1
  # The core tag (wow-cmangos-classic) is only needed to build the runtime
  # image. An existing wow-run-<short> image is enough to start the realm.
  docker image inspect "${CATALOG_IMAGE}:latest" &>/dev/null && return 0
  docker image inspect "wow-run-${short}:latest" &>/dev/null || return 1
  return 0
}

# Stop before compose when the selected core is not what this slot was built as.
# ./setup.sh up cannot skip the selector. A batch of "all" skips a refused realm
# instead of taking the other realms down with it.
assert_selection_ready() {
  local short="$1" allow_skip="${2:-0}"
  if python3 "${ROOT}/scripts/select-project.py" --launch-check "$short"; then
    return 0
  fi
  if [[ "$allow_skip" -eq 1 ]]; then
    return 1
  fi
  exit 1
}

filter_launchable() {
  local short
  LAUNCH=()
  SKIPPED=()
  for short in "${SELECTED[@]}"; do
    if available_for_launch "$short"; then
      LAUNCH+=("$short")
    else
      SKIPPED+=("$short")
    fi
  done
}

ensure_loopback() {
  local ip="$1"
  if ip -4 addr show lo 2>/dev/null | grep -q "inet ${ip}/"; then
    return 0
  fi
  if ip addr add "${ip}/32" dev lo 2>/dev/null; then
    log "Added loopback alias ${ip}"
    return 0
  fi
  if command -v sudo >/dev/null && sudo -n ip addr add "${ip}/32" dev lo 2>/dev/null; then
    log "Added loopback alias ${ip} (sudo)"
    return 0
  fi
  return 1
}

prepare_bind_mode() {
  local short ip failed=0
  [[ "$BIND_MODE" == "ports" ]] && return 0
  if [[ "$BIND_MODE" == "haproxy" ]]; then
    while IFS= read -r short; do
      catalog_load "$short"
      ensure_loopback "$CATALOG_LOOPBACK" || failed=1
    done < <(catalog_shorts)
    [[ "$failed" -eq 0 ]] || die "Cannot add loopback aliases (HAProxy binds one 127.0.0.x per realm)"
    return 0
  fi
  for short in "${LAUNCH[@]}"; do
    catalog_load "$short"
    ip="$CATALOG_LOOPBACK"
    if ! ensure_loopback "$ip"; then
      warn "Cannot add ${ip} on lo"
      failed=1
    fi
  done
  if [[ "$failed" -eq 1 ]]; then
    warn "Falling back to unique host ports (classic clients still expect :3724)"
    BIND_MODE=ports
  fi
}

stage_wowweb_site() {
  local short="$1" src="$2" site="$3"
  [[ -d "$src" ]] || return 1
  mkdir -p "${site}/static/img/client"
  cp -a "${src}/serve.py" "${site}/serve.py" || return 1
  cp -a "${src}/wowweb" "${site}/wowweb" || return 1
  find "$site" -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf
  find "$site" -type f -name '*.pyc' -delete || true
  mkdir -p "${site}/static/img"
  cp -a "${src}/static/css" "${src}/static/js" "${site}/static/" || return 1
  find "${src}/static/img" -maxdepth 1 -type f -exec cp -a {} "${site}/static/img/" \; || return 1
  if [[ -d "${src}/static/img/client/${short}" ]]; then
    cp -a "${src}/static/img/client/${short}" "${site}/static/img/client/${short}" || return 1
  fi
}

stage_runtime_context() {
  local short="$1" dest="$2"
  local src="${ROOT}/WoWWebsites" rt="${ROOT}/docker/runtime"
  mkdir -p "${dest}/wowweb-site" || return 1
  # A file keeps the directory in the Docker build context when the site is absent.
  touch "${dest}/wowweb-site/.keep" || return 1
  # Called from `if`, where set -e does not stop the function, so fail explicitly.
  cp -a \
    "${rt}/entrypoint.sh" "${rt}/healthcheck.sh" "${rt}/init-db.sh" \
    "${rt}/lib.sh" "${rt}/catalog.sh" "${rt}/gen-config.py" "${rt}/post-setup.py" \
    "${dest}/" || return 1
  if [[ -d "$src" ]] && stage_wowweb_site "$short" "$src" "${dest}/wowweb-site"; then
    return 0
  fi
  mkdir -p "${dest}/wowweb-site"
  touch "${dest}/wowweb-site/.keep"
  if [[ -d "$src" ]]; then
    warn "Could not copy WoWWebsites. The runtime image will contain an empty site."
  else
    warn "WoWWebsites is missing. The runtime image will contain an empty site."
  fi
}

ensure_runtime_image() {
  local short="$1"
  catalog_load "$short"
  local tag="wow-run-${short}:latest" base="${CATALOG_IMAGE}:latest"
  if [[ "$NO_BUILD" -eq 1 ]]; then
    docker image inspect "$tag" &>/dev/null \
      || die "Runtime image ${tag} missing (omit --no-build, or run ./setup.sh ${short})"
    return 0
  fi
  if ! docker image inspect "$base" &>/dev/null; then
    docker image inspect "$tag" &>/dev/null \
      || die "Runtime image ${tag} missing and base ${base} is not tagged"
    # Replacing a tag that is also the build source drops the source mid-build.
    docker tag "$tag" "${tag}-base"
    base="${tag}-base"
    warn "Base image ${CATALOG_IMAGE}:latest is missing; rebuilding ${tag} from itself"
  fi
  local stage rc=0
  stage="$(mktemp -d /tmp/wow-run-build.XXXXXX)"
  log "Building runtime overlay ${tag}  (FROM ${base})"
  if ! stage_runtime_context "$short" "$stage"; then
    rm -rf "$stage"
    return 1
  fi
  docker build \
    -f "${ROOT}/docker/runtime/Dockerfile" \
    --build-arg "BASE_IMAGE=${base}" \
    -t "$tag" \
    "$stage" || rc=$?
  rm -rf "$stage"
  return "$rc"
}

# Always emit every expansion as a compose profile so `up vanilla` cannot
# rewrite the file and --remove-orphans a running tbc/wotlk container.
write_compose() {
  load_volume_env
  # shellcheck disable=SC1091
  source "${ROOT}/docker/runtime/compose.sh"
  catalog_assert_unique_host_ports || die "catalog host ports overlap — cannot run expansions together"
  local all=() short
  while IFS= read -r short; do
    all+=("$short")
  done < <(catalog_shorts)
  compose_emit "$COMPOSE_FILE" "${all[@]}"
  log "Wrote ${COMPOSE_FILE} (${#all[@]} expansions as profiles)"
}

# True if TCP addr:port is already bound. 127.0.0.1:8081 does not block
# 127.0.0.14:8081, so the address has to be the one this realm publishes.
host_port_busy() {
  local addr="$1" port="$2"
  python3 - "$addr" "$port" <<'PY'
import socket, sys
addr, port = sys.argv[1], int(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((addr, port))
except OSError:
    sys.exit(0)
finally:
    s.close()
sys.exit(1)
PY
}

# Containers publishing this exact address:port, or 0.0.0.0 / :: which
# would block it. A match on :18081 must not count as port 8081.
publishers_of() {
  local addr="$1" port="$2"
  python3 - "$addr" "$port" <<'PY'
import re, subprocess, sys
addr, port = sys.argv[1], sys.argv[2]
out = subprocess.check_output(
    ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"], text=True)
pat = re.compile(
    rf'(?:^|[\s,])(?:0\.0\.0\.0|{re.escape(addr)}|\[::\]):{port}->')
for line in out.splitlines():
    name, _, ports = line.partition("\t")
    if name and pat.search(ports):
        print(name)
PY
}

# Refuse to start a realm whose published ports belong to some other process.
# wow-haproxy already holds the stock auth/world/REST ports on each realm's
# loopback address; that is the frontend, not a conflict.
assert_launch_ports_free() {
  local short port owner name allowed
  for short in "${LAUNCH[@]}"; do
    catalog_load "$short"
    catalog_host_ports "$short"
    local ports=("$HOST_AUTH" "$HOST_WORLD")
    [[ "$HOST_REST" != "0" && -n "$HOST_REST" ]] && ports+=("$HOST_REST")
    if [[ "$short" == "alpha" ]]; then
      ports+=(9081 9090 9100)
    fi
    for port in "${ports[@]}"; do
      [[ -z "$port" || "$port" == "0" ]] && continue
      host_port_busy "$HOST_BIND" "$port" || continue
      owner="$(publishers_of "$HOST_BIND" "$port")"
      if [[ -z "$owner" ]]; then
        die "Host port ${HOST_BIND}:${port} is already in use (needed by ${short})"
      fi
      allowed=1
      while IFS= read -r name; do
        [[ -z "$name" ]] && continue
        if [[ "$name" != "wow-${short}" && "$name" != "wow-haproxy" ]]; then
          allowed=0
          break
        fi
      done <<<"$owner"
      [[ "$allowed" -eq 1 ]] && continue
      die "Host port ${HOST_BIND}:${port} is already published by ${owner//$'\n'/, } (needed by ${short})"
    done
  done
}

profile_args() {
  local short
  for short in "${LAUNCH[@]}"; do
    printf -- '--profile\n%s\n' "$short"
  done
}

point_one_client() {
  local short="$1" host="$2" client dir f
  catalog_load "$short"
  dir="${ROOT}/clients/${CATALOG_CLIENT}"
  [[ -d "$dir" ]] || { warn "No client at clients/${CATALOG_CLIENT}"; return 0; }

  local found=0
  while IFS= read -r f; do
    found=1
    printf 'set realmlist %s\nset realmname "%s"\n' "$host" "$CATALOG_REALM_NAME" >"$f"
    log "Wrote ${f#"$ROOT"/}"
  done < <(find "$dir" -iname 'realmlist.wtf' -type f 2>/dev/null)
  if [[ "$found" -eq 0 && "$CATALOG_PROTO" == "legacy" ]]; then
    printf 'set realmlist %s\nset realmname "%s"\n' "$host" "$CATALOG_REALM_NAME" \
      >"${dir}/realmlist.wtf"
    log "Wrote clients/${CATALOG_CLIENT}/realmlist.wtf"
  fi

  while IFS= read -r f; do
    python3 - "$f" "$host" "$CATALOG_PROTO" <<'PY'
import pathlib, re, sys
path = pathlib.Path(sys.argv[1])
host = sys.argv[2]
proto = sys.argv[3]
text = path.read_text(encoding="utf-8", errors="replace")
if proto == "bnet":
    if re.search(r'(?i)^SET\s+portal\b', text, re.M):
        text = re.sub(r'(?i)^SET\s+portal\s+".*"', f'SET portal "{host}"', text, count=1, flags=re.M)
    else:
        text = f'SET portal "{host}"\n' + text
else:
    if re.search(r'(?i)^SET\s+realmlist\b', text, re.M):
        text = re.sub(r'(?i)^SET\s+realmlist\s+".*"', f'SET realmlist "{host}"', text, count=1, flags=re.M)
    else:
        text = f'SET realmlist "{host}"\n' + text
path.write_text(text, encoding="utf-8")
print(f"==> updated {path}")
PY
  done < <(find "$dir" -iname 'Config.wtf' -type f 2>/dev/null)
}

public_host_for() {
  local short="$1"
  catalog_load "$short"
  if [[ "${BIND_MODE}" == "haproxy" ]]; then
    catalog_hostname "$short"
  elif [[ "${BIND_MODE}" == "loopback" ]]; then
    printf '%s' "$CATALOG_LOOPBACK"
  else
    printf '%s' "${REALM_ADDRESS:-${PUBLIC_HOST:-127.0.0.1}}"
  fi
}

point_clients() {
  local short
  for short in "${LAUNCH[@]}"; do
    point_one_client "$short" "$(public_host_for "$short")"
  done
}

login_name_for() {
  local short="$1" name="${ACCOUNT_NAME:-admin}"
  catalog_load "$short"
  name="${name%%@*}"
  if [[ "$CATALOG_PROTO" == "bnet" || "$short" == "wod" ]]; then
    printf '%s@%s.local' "${name,,}" "$short"
  else
    printf '%s' "$name"
  fi
}

print_login_card() {
  local short host auth_p world_p rest_p login
  echo
  echo "========================================"
  log "Ready (or starting)."
  echo
  printf '  %-14s %-16s %-22s %-22s %s\n' "SERVER" "HOST" "AUTH" "WORLD" "CLIENT"
  for short in "${LAUNCH[@]}"; do
    catalog_load "$short"
    catalog_host_ports "$short"
    host="$(public_host_for "$short")"
    auth_p="${HOST_AUTH}"
    world_p="${HOST_WORLD}"
    rest_p="${HOST_REST}"
    login="$(login_name_for "$short")"
    if [[ -f "${ROOT}/servers/${short}/.gm-created" ]]; then
      printf '  %-14s login %s (password already set)\n' "$short" "$login"
    else
      printf '  %-14s login %s / %s\n' "$short" "$login" "${ACCOUNT_PASSWORD:-admin}"
    fi
    if [[ "$BIND_MODE" == "ports" ]]; then
      printf '  %-14s site http://%s:%s/\n' "" "$host" "${HOST_WEB}"
    else
      printf '  %-14s site http://%s/\n' "" "$host"
    fi
    if [[ "$CATALOG_PROTO" == "bnet" ]]; then
      printf '  %-14s %-16s %-22s %-22s %s\n' \
        "$short" "$host" "${host}:${auth_p} (bnet)" "${host}:${world_p}" "$CATALOG_CLIENT"
      if [[ "$rest_p" != "0" ]]; then
        printf '  %-14s %-16s REST %s  portal=%s\n' "" "" "${host}:${rest_p}" "$host"
      fi
    else
      printf '  %-14s %-16s %-22s %-22s %s\n' \
        "$short" "$host" "${host}:${auth_p}" "${host}:${world_p}" "$CATALOG_CLIENT"
    fi
  done
  echo
  if [[ "$BIND_MODE" == "haproxy" ]]; then
    echo "  Point the client at the HOST name. Stock ports: auth 3724 or 1119, world 8085, REST 8081."
    echo "  Classic:  set realmlist vanilla.local"
    echo "  Modern:   SET portal \"legion.local\""
  elif [[ "$BIND_MODE" == "loopback" ]]; then
    echo "  realmlist.wtf / Config.wtf SET realmlist (or SET portal) to the HOST above."
  else
    echo "  Unique ports are in use. Stock classic clients still connect to :3724 only."
  fi
  echo "  First worldserver start applies SQL updates and can take many minutes."
  echo "  Maps/vmaps/mmaps/dbc belong in servers/<short>/ (DataDir=.)."
  echo "========================================"
}

cmd_list() {
  printf '%-14s %-12s %-36s %-10s %-10s %s\n' \
    "SHORT" "KIND" "IMAGE" "IMAGE?" "SERVERS?" "LOOPBACK"
  local short status host
  while IFS= read -r short; do
    catalog_load "$short"
    status="no"
    docker image inspect "${CATALOG_IMAGE}:latest" &>/dev/null && status="ok"
    host="missing"
    install_present "${ROOT}/servers/${short}" && host="present"
    printf '%-14s %-12s %-36s %-10s %-10s %s\n' \
      "$short" "$CATALOG_KIND" "$CATALOG_IMAGE" "$status" "$host" "$CATALOG_LOOPBACK"
  done < <(catalog_shorts)
}

port_open() {
  local host="$1" port="$2"
  if command -v python3 >/dev/null; then
    python3 - "$host" "$port" <<'PY'
import socket, sys
host, port = sys.argv[1], int(sys.argv[2])
s = socket.socket()
s.settimeout(1.5)
try:
    s.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    s.close()
PY
  else
    timeout 1 bash -c "echo >/dev/tcp/${host}/${port}" &>/dev/null
  fi
}

wait_ready() {
  local timeout="${WOW_READY_WAIT:-2700}"
  local start now elapsed short host auth_p world_p
  local pending=("${LAUNCH[@]}")
  local ready=() failed=()
  start="$(date +%s)"
  log "Waiting up to ${timeout}s for login ports (auth + world). First boot applies SQL and can take a long time."
  while [[ ${#pending[@]} -gt 0 ]]; do
    now="$(date +%s)"
    elapsed=$((now - start))
    if [[ "$elapsed" -ge "$timeout" ]]; then
      failed=("${pending[@]}")
      break
    fi
    local still=()
    for short in "${pending[@]}"; do
      catalog_load "$short"
      catalog_host_ports "$short"
      host="$(public_host_for "$short")"
      auth_p="${HOST_AUTH}"
      world_p="${HOST_WORLD}"
      local login_up=0
      if [[ "$BIND_MODE" == "haproxy" ]]; then
        if docker exec "wow-${short}" python3 -c "
import socket
for port in (${auth_p}, ${world_p}):
    s = socket.socket()
    s.settimeout(2)
    s.connect(('127.0.0.1', port))
    s.close()
" 2>/dev/null; then
          login_up=1
        fi
      elif port_open "$host" "$auth_p" && port_open "$host" "$world_p"; then
        login_up=1
      fi
      if [[ "$login_up" -eq 1 ]]; then
        log "${short} is accepting logins on ${host}:${auth_p} (world ${host}:${world_p})"
        ready+=("$short")
      elif docker inspect -f '{{.State.Running}}' "wow-${short}" 2>/dev/null | grep -qx true; then
        still+=("$short")
      else
        warn "${short} container is not running — see: ./launch-servers.sh logs ${short}"
        failed+=("$short")
      fi
    done
    pending=("${still[@]}")
    [[ ${#pending[@]} -eq 0 ]] && break
    sleep 5
  done
  if [[ ${#failed[@]} -gt 0 ]]; then
    warn "Not login-ready yet: ${failed[*]}"
    warn "Watch SQL/map load with: ./launch-servers.sh logs <short>"
  fi
}

cmd_prepare_db() {
  command -v docker >/dev/null || die "docker is required"
  load_env
  ensure_host
  parse_selection "${ONLY}"
  LAUNCH=("${SELECTED[@]}")
  [[ ${#LAUNCH[@]} -gt 0 ]] || die "prepare-db needs at least one expansion"
  mkdir -p "$RUN_DIR"
  prepare_stack_files
  assert_mariadb_pool
  write_compose
  log "Starting shared MariaDB"
  compose up -d db
  local short ready=()
  for short in "${LAUNCH[@]}"; do
    catalog_load "$short"
    if ! install_present "${ROOT}/servers/${short}"; then
      die "${short}: servers/${short} is missing (compile first)"
    fi
    if ! assert_selection_ready "$short"; then
      die "${short}: selected core does not match the install"
    fi
    ready+=("$short")
  done
  LAUNCH=("${ready[@]}")
  local rc
  for short in "${LAUNCH[@]}"; do
    log "Initialize databases for ${short}"
    rc=0
    compose --profile "$short" run --rm "${short}-init" || rc=$?
    if [[ "$rc" -ne 0 ]]; then
      exit "$rc"
    fi
    clear_reimport_marker "$short"
  done
}

cmd_up() {
  command -v docker >/dev/null || die "docker is required"
  load_env
  ensure_host
  parse_selection "${ONLY}"
  filter_launchable
  [[ ${#LAUNCH[@]} -gt 0 ]] || die "Nothing to launch. Build+extract first: ./setup.sh ${ONLY:-<short>}"
  if [[ ${#SKIPPED[@]} -gt 0 ]]; then
    warn "Skipping (no image or servers/<short>): ${SKIPPED[*]}"
  fi
  local short dest still=() incomplete=()
  for short in "${LAUNCH[@]}"; do
    catalog_load "$short"
    dest="${ROOT}/servers/${short}"
    if extract_data_complete "$dest" "$CATALOG_KIND"; then
      still+=("$short")
    else
      incomplete+=("$short")
      warn "${short}: incomplete client data (${EXTRACT_GAP:-missing maps/vmaps/mmaps})"
    fi
  done
  if [[ ${#incomplete[@]} -gt 0 ]]; then
    warn "Re-extract with: ./extract-data.sh $(IFS=','; echo "${incomplete[*]}")"
    if [[ -n "$ONLY" && "$ONLY" != "all" ]]; then
      die "Refusing to start until extraction is complete: ${incomplete[*]}"
    fi
    warn "Not starting incomplete realms: ${incomplete[*]}"
  fi
  LAUNCH=("${still[@]}")
  [[ ${#LAUNCH[@]} -gt 0 ]] || die "Nothing to launch (need a complete extract). ./extract-data.sh ${ONLY:-}"
  local allow_skip=0 checked=()
  if [[ -z "$ONLY" || "$ONLY" == "all" ]]; then
    allow_skip=1
  fi
  for short in "${LAUNCH[@]}"; do
    if assert_selection_ready "$short" "$allow_skip"; then
      checked+=("$short")
    else
      warn "Not starting ${short} (selection does not match the install or the client build)"
    fi
  done
  LAUNCH=("${checked[@]}")
  [[ ${#LAUNCH[@]} -gt 0 ]] || die "Nothing to launch (selection or client build refused). ./scripts/select-project.py --list"
  prepare_bind_mode
  mkdir -p "$RUN_DIR"
  prepare_stack_files
  assert_mariadb_pool
  for short in "${LAUNCH[@]}"; do
    ensure_runtime_image "$short"
  done
  write_compose
  assert_launch_ports_free
  log "Starting MariaDB + ${#LAUNCH[@]} expansion(s): ${LAUNCH[*]}"
  # Do not --remove-orphans: other expansions in this compose file stay up.
  # shellcheck disable=SC2046
  compose $(profile_args) up -d db
  if [[ "$BIND_MODE" == "haproxy" ]]; then
    log "Starting HAProxy (vanilla.local, tbc.local, … on stock client ports)"
    compose up -d haproxy
  fi
  local started rc=0
  started="$(date +%s)"
  # shellcheck disable=SC2046
  compose $(profile_args) up -d "${LAUNCH[@]}" || rc=$?
  for short in "${LAUNCH[@]}"; do
    if init_succeeded_since "wow-${short}-init" "$started"; then
      clear_reimport_marker "$short"
    fi
  done
  if [[ "$rc" -ne 0 ]]; then
    exit "$rc"
  fi
  if [[ "$POINT_CLIENTS" == "1" ]]; then
    point_clients
  fi
  wait_ready
}

cmd_down() {
  load_env
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    parse_selection "${ONLY:-all}"
    LAUNCH=("${SELECTED[@]}")
    write_compose
  else
    if [[ -n "$ONLY" && "$ONLY" != "all" ]]; then
      parse_selection "$ONLY"
      LAUNCH=("${SELECTED[@]}")
      # shellcheck disable=SC2046
      compose $(profile_args) stop "${LAUNCH[@]}" || true
      # shellcheck disable=SC2046
      compose $(profile_args) rm -f "${LAUNCH[@]}" || true
      return 0
    fi
  fi
  local profiles=() short
  while IFS= read -r short; do
    profiles+=(--profile "$short")
  done < <(catalog_shorts)
  compose "${profiles[@]}" down --remove-orphans
}

cmd_stop() {
  load_env
  [[ -f "$COMPOSE_FILE" ]] || die "No compose file — nothing is running via launch-servers.sh"
  parse_selection "${ONLY:-all}"
  LAUNCH=("${SELECTED[@]}")
  # shellcheck disable=SC2046
  compose $(profile_args) stop "${LAUNCH[@]}"
}

cmd_restart() {
  load_env
  ensure_host
  [[ -f "$COMPOSE_FILE" ]] || die "No compose file — run: ./launch-servers.sh up"
  parse_selection "${ONLY:-all}"
  LAUNCH=("${SELECTED[@]}")
  prepare_bind_mode
  prepare_stack_files
  assert_mariadb_pool
  write_compose
  log "Recreating ${LAUNCH[*]} against the current volume mount"
  # shellcheck disable=SC2046
  compose $(profile_args) up -d db
  if [[ "$BIND_MODE" == "haproxy" ]]; then
    compose up -d --force-recreate --no-deps haproxy
  fi
  # --no-deps keeps a restart from replaying database imports.
  # shellcheck disable=SC2046
  compose $(profile_args) up -d --force-recreate --no-deps "${LAUNCH[@]}"
}

cmd_status() {
  load_env
  if [[ -f "$COMPOSE_FILE" ]]; then
    compose ps -a
  else
    docker ps -a --filter 'name=wow-' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
  fi
}

cmd_logs() {
  load_env
  [[ -f "$COMPOSE_FILE" ]] || die "No compose file — run: ./launch-servers.sh up"
  parse_selection "${ONLY:-}"
  [[ ${#SELECTED[@]} -gt 0 ]] || die "logs needs a server name"
  LAUNCH=("${SELECTED[@]}")
  # shellcheck disable=SC2046
  compose $(profile_args) logs -f --tail=200 "${SELECTED[0]}"
}

# --- args ---
# Sourcing this file (tests) must not parse argv or start a realm.
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  return 0 2>/dev/null || exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    --list) CMD="list"; shift ;;
    --ports) CLI_BIND_MODE=ports; shift ;;
    --loopback) CLI_BIND_MODE=loopback; shift ;;
    --haproxy) CLI_BIND_MODE=haproxy; shift ;;
    --no-point-clients) POINT_CLIENTS=0; shift ;;
    --no-build) NO_BUILD=1; shift ;;
    --only) ONLY="${2:?}"; shift 2 ;;
    up|down|stop|restart|status|logs|list|point-clients|prepare-db)
      CMD="$1"
      shift
      if [[ $# -gt 0 && "$1" != --* ]]; then
        ONLY="$1"
        shift
      fi
      ;;
    *)
      if [[ -z "$CMD" ]]; then
        CMD="up"
        ONLY="$1"
        shift
      else
        die "Unknown argument: $1 (try --help)"
      fi
      ;;
  esac
done

CMD="${CMD:-up}"

case "$CMD" in
  up) cmd_up ;;
  down) cmd_down ;;
  stop) cmd_stop ;;
  restart) cmd_restart ;;
  status) cmd_status ;;
  logs) cmd_logs ;;
  list) cmd_list ;;
  prepare-db) cmd_prepare_db ;;
  point-clients)
    load_env
    parse_selection "${ONLY:-all}"
    filter_launchable
    [[ ${#LAUNCH[@]} -gt 0 ]] || LAUNCH=("${SELECTED[@]}")
    prepare_bind_mode
    point_clients
    ;;
  *) die "Unknown command: $CMD" ;;
esac
