#!/usr/bin/env bash
# Allow the current realm ports through an already-active firewall.
# Does not install a firewall and does not turn one on.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/docker/runtime/catalog.sh"

if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.env"
  set +a
fi

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

if [[ "$(id -u)" -ne 0 ]]; then
  if sudo -n true 2>/dev/null; then
    exec sudo -n -- "$0" "$@"
  fi
  exec sudo -- "$0" "$@"
fi

ports=()
while IFS= read -r short; do
  catalog_load "$short" || continue
  catalog_host_ports "$short" || continue
  ports+=("$HOST_AUTH" "$HOST_WORLD" "$HOST_WEB")
  [[ "${HOST_REST}" != "0" ]] && ports+=("$HOST_REST")
done < <(catalog_shorts)

if command -v ufw >/dev/null && ufw status | grep -q 'Status: active'; then
  for port in "${ports[@]}"; do
    [[ "$port" == "0" ]] && continue
    ufw allow "${port}/tcp"
  done
  log "ufw allows the realm ports."
  exit 0
fi

if command -v firewall-cmd >/dev/null && firewall-cmd --state >/dev/null 2>&1; then
  for port in "${ports[@]}"; do
    [[ "$port" == "0" ]] && continue
    firewall-cmd --add-port="${port}/tcp" --permanent
  done
  firewall-cmd --reload
  log "firewalld allows the realm ports."
  exit 0
fi

log "No active ufw or firewalld. Nothing was changed."
