#!/usr/bin/env bash
# Start one expansion: generate configs, run auth + world, create a login.
set -euo pipefail

RUNTIME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${RUNTIME}/lib.sh"

SHORT="${WOW_SHORT:?}"
KIND="${WOW_KIND:?}"
PROTO="${WOW_PROTO:-legacy}"
ROOT="${WOW_ROOT:-/opt/wow}"
AUTH_BIN="${WOW_AUTH_BIN:-}"
WORLD_BIN="${WOW_WORLD_BIN:-}"

wait_for_realm_volume "$ROOT"

export LD_LIBRARY_PATH="${ROOT}/lib:${LD_LIBRARY_PATH:-}"
if [[ -d "${ROOT}/lib/ossl-modules" ]]; then
  export OPENSSL_MODULES="${ROOT}/lib/ossl-modules"
fi
if [[ -f "${ROOT}/lib/mysql_version_shim.so" ]]; then
  export LD_PRELOAD="${ROOT}/lib/mysql_version_shim.so${LD_PRELOAD:+:$LD_PRELOAD}"
fi
cd "$ROOT"
mkdir -p "${ROOT}/logs" "${ROOT}/etc"

# bnetserver.conf.dist looks for ./bnetserver.*.pem; the build installs them in bin/.
if [[ -f "${ROOT}/bin/bnetserver.cert.pem" && ! -e "${ROOT}/bnetserver.cert.pem" ]]; then
  ln -sfn bin/bnetserver.cert.pem "${ROOT}/bnetserver.cert.pem"
fi
if [[ -f "${ROOT}/bin/bnetserver.key.pem" && ! -e "${ROOT}/bnetserver.key.pem" ]]; then
  ln -sfn bin/bnetserver.key.pem "${ROOT}/bnetserver.key.pem"
fi

# shellcheck disable=SC1091
source "${RUNTIME}/catalog.sh"
_extract_wait=0
while ! extract_data_complete "$ROOT" "$KIND"; do
  if (( _extract_wait % 6 == 0 )); then
    log "Waiting for complete client data for ${SHORT} (${EXTRACT_GAP:-missing}). Run: ./extract-data.sh ${SHORT}"
  fi
  sleep 10
  _extract_wait=$((_extract_wait + 1))
done
unset _extract_wait

# AzerothCore AutoSetup looks for ${SourceDirectory}/data/sql/...
# build-core.sh installs SQL at servers/<short>/sql/. A relative link keeps
# working when the tree is mounted somewhere other than this host's path.
if [[ "$KIND" == "azerothcore" ]]; then
  mkdir -p "${ROOT}/data"
  if [[ ! -e "${ROOT}/data/sql" || -L "${ROOT}/data/sql" ]]; then
    ln -sfn ../sql "${ROOT}/data/sql"
  fi
fi

log "Generating configs for ${SHORT} (${KIND})"
python3 "${RUNTIME}/gen-config.py"

# First-time Trinity/AC AutoSetup needs mysql in PATH.
export PATH="/usr/bin:${PATH}"

AUTH_PID=""
WORLD_PID=""
ALPHA_PID=""
WEB_PID=""

cleanup() {
  local code=$?
  trap - EXIT INT TERM
  for pid in $WORLD_PID $AUTH_PID $ALPHA_PID $WEB_PID; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done
  wait || true
  exit "$code"
}
trap cleanup EXIT INT TERM

run_bin() {
  local bin="$1"
  shift
  if [[ -x "${ROOT}/bin/${bin}" ]]; then
    echo "${ROOT}/bin/${bin}"
    return 0
  fi
  if [[ -x "${ROOT}/${bin}" ]]; then
    echo "${ROOT}/${bin}"
    return 0
  fi
  die "Binary not found: ${bin}"
}

start_alpha() {
  local py="${ROOT}/.venv/bin/python"
  [[ -x "$py" ]] || py="python3"
  export CONSOLE_MODE=False
  export FORWARD_ADDRESS_OVERRIDE="${WOW_PUBLIC_HOST:-127.0.0.2}"
  log "Starting alpha-core (${py} main.py)"
  "$py" "${ROOT}/main.py" >>"${ROOT}/logs/server.log" 2>&1 &
  ALPHA_PID=$!
}

start_auth() {
  [[ -n "$AUTH_BIN" ]] || return 0
  local exe conf
  exe="$(run_bin "$AUTH_BIN")"
  conf="${ROOT}/etc/${AUTH_BIN}.conf"
  log "Starting ${AUTH_BIN}"
  "$exe" -c "$conf" >>"${ROOT}/logs/${AUTH_BIN}.log" 2>&1 &
  AUTH_PID=$!
}

start_world() {
  [[ -n "$WORLD_BIN" ]] || return 0
  local exe conf
  exe="$(run_bin "$WORLD_BIN")"
  conf="${ROOT}/etc/${WORLD_BIN}.conf"
  log "Starting ${WORLD_BIN} (first boot applies SQL updates — can take a long time)"
  "$exe" -c "$conf" >>"${ROOT}/logs/${WORLD_BIN}.log" 2>&1 &
  WORLD_PID=$!
}

wait_port() {
  local port="$1" tries="${2:-30}" i
  for ((i = 1; i <= tries; i++)); do
    if python3 -c "import socket;s=socket.socket();s.settimeout(1);s.connect(('127.0.0.1',${port}));s.close()" 2>/dev/null; then
      return 0
    fi
    sleep 2
  done
  return 1
}

post_setup() {
  log "Configuring realmlist + account"
  python3 "${RUNTIME}/post-setup.py" || warn "post-setup returned $?"
}

start_website() {
  if [[ ! -f /opt/wowweb/serve.py ]]; then
    warn "No community site in this image"
    return 0
  fi
  mkdir -p /var/lib/wowweb "${ROOT}/logs"
  log "Starting community site on :${WOW_WEB_PORT:-8090}"
  python3 /opt/wowweb/serve.py "${SHORT}" \
    --host 0.0.0.0 \
    --port "${WOW_WEB_PORT:-8090}" \
    --data /var/lib/wowweb \
    >>"${ROOT}/logs/wowweb.log" 2>&1 &
  WEB_PID=$!
}

start_website

if [[ "$KIND" == "alpha" ]]; then
  start_alpha
  sleep 3
  post_setup
  log "${SHORT} is up (pid ${ALPHA_PID})"
  wait "$ALPHA_PID"
  exit $?
fi

# World first so AutoSetup can create the auth schema before authserver/bnet starts.
start_world
if [[ -n "$WORLD_PID" ]]; then
  # Give the process a moment to die on immediate config errors.
  sleep 5
  if ! kill -0 "$WORLD_PID" 2>/dev/null; then
    if wait_port "${WOW_WORLD_PORT:-8085}" 3; then
      log "${WORLD_BIN} parent exited but world port is open (daemonized) — continuing"
    else
      warn "${WORLD_BIN} exited immediately — last 80 log lines:"
      tail -n 80 "${ROOT}/logs/${WORLD_BIN}.log" || true
      exit 1
    fi
  fi
fi

# Auth schema appears after AutoSetup; then we can start auth and seed the login.
export WOW_DB_WAIT="${WOW_DB_WAIT:-1800}"
python3 - <<'PY'
import os, time, subprocess, sys

def ready():
    short = os.environ["WOW_SHORT"]
    import shutil
    client = shutil.which("mysql") or shutil.which("mariadb") or "mysql"
    cmd = [
        client, "--protocol=TCP",
        "-h", os.environ.get("MYSQL_HOST", "db"),
        "-P", os.environ.get("MYSQL_PORT", "3306"),
        "-u", os.environ.get("MYSQL_USER", "wow"),
        "--batch", "--skip-column-names",
        "-e", f"SHOW TABLES FROM `{short}_auth` LIKE 'realmlist'",
    ]
    pw = os.environ.get("MYSQL_PASSWORD")
    if pw:
        cmd.insert(6, f"-p{pw}")
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode == 0 and "realmlist" in p.stdout

deadline = time.time() + int(os.environ.get("WOW_DB_WAIT", "1800"))
while time.time() < deadline:
    if ready():
        sys.exit(0)
    time.sleep(5)
print("WARNING: auth realmlist table not visible yet; starting auth anyway", file=sys.stderr)
sys.exit(0)
PY

# Write the client-visible address and clear OFFLINE / VERSION_MISMATCH
# before authserver loads realmlist. AzerothCore exits when no realm stays
# loadable. World clears the offline bit again on a later timer.
post_setup

# AzerothCore marks every realm offline at auth startup, then exits if that
# was the only realm. World clears the bit on a later timer. Drop the flag
# and retry until auth is actually listening.
clear_realm_flag() {
  [[ "$KIND" == "azerothcore" ]] || return 0
  local client
  client="$(command -v mariadb || command -v mysql || true)"
  [[ -n "$client" ]] || return 0
  "$client" --protocol=TCP \
    -h "${MYSQL_HOST:-db}" -P "${MYSQL_PORT:-3306}" \
    -u "${MYSQL_USER:-wow}" ${MYSQL_PASSWORD:+-p"$MYSQL_PASSWORD"} \
    -e "UPDATE \`${SHORT}_auth\`.realmlist SET flag=0 WHERE id=1" \
    >/dev/null 2>&1 || true
}

auth_listening() {
  [[ -n "${AUTH_PID:-}" ]] || return 1
  kill -0 "$AUTH_PID" 2>/dev/null || return 1
  wait_port "${WOW_AUTH_PORT:-3724}" 3
}

if [[ -n "${AUTH_BIN}" ]]; then
  _auth_try=1
  while (( _auth_try <= 8 )); do
    clear_realm_flag
    start_auth
    if auth_listening; then
      break
    fi
    warn "${AUTH_BIN} is not listening (try ${_auth_try})"
    if [[ -n "${AUTH_PID:-}" ]]; then
      kill "$AUTH_PID" 2>/dev/null || true
      wait "$AUTH_PID" 2>/dev/null || true
    fi
    AUTH_PID=""
    _auth_try=$((_auth_try + 1))
    sleep 3
  done
  unset _auth_try
  if [[ -z "${AUTH_PID:-}" ]] || ! kill -0 "$AUTH_PID" 2>/dev/null; then
    warn "${AUTH_BIN} exited — last 80 log lines:"
    tail -n 80 "${ROOT}/logs/${AUTH_BIN}.log" || true
  fi
fi

# Auth marks every realm offline at startup. World clears that bit only on
# UpdateUptimeInterval (minutes). Until then the client realm stays offline.
if [[ "$KIND" == "azerothcore" ]]; then
  if wait_port "${WOW_WORLD_PORT:-8085}" 180; then
    clear_realm_flag
    log "World is listening — cleared realm offline flag"
  else
    warn "World port not open yet; realm stays offline until the uptime timer"
  fi
fi

log "${SHORT} processes running (auth=${AUTH_PID:-none} world=${WORLD_PID:-none})"
log "Logs: ${ROOT}/logs/"

# Stay up as long as world (or auth if world is missing) is alive.
if [[ -n "$WORLD_PID" ]]; then
  wait "$WORLD_PID"
  code=$?
  [[ -n "$AUTH_PID" ]] && kill "$AUTH_PID" 2>/dev/null || true
  exit "$code"
fi
if [[ -n "$AUTH_PID" ]]; then
  wait "$AUTH_PID"
  exit $?
fi
die "Nothing to run for ${SHORT}"
