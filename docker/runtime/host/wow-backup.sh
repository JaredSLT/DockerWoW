#!/bin/bash
# Dump every realm database. The hour lives in the timer, not here.
set -euo pipefail

TREE=""
if [[ -f /etc/wow/volume.env ]]; then
  # shellcheck disable=SC1091
  set -a
  source /etc/wow/volume.env
  set +a
  TREE="${WOW_TREE:-}"
fi
[[ -n "$TREE" ]] || exit 0

script="${TREE}/setup.sh"
[[ -x "$script" ]] || exit 0

owner="$(stat -c '%U' "$script")"
if [[ "$(id -u)" -eq 0 && "$owner" != "root" ]]; then
  exec runuser -u "$owner" -- "$script" backup now
fi
exec "$script" backup now
