#!/bin/bash
# Start the realms listed in .run/boot.conf. An empty file starts nothing.
set -euo pipefail

TREE="/mnt/wow-nvme/WoW"
if [[ -f /etc/wow/volume.env ]]; then
  # shellcheck disable=SC1091
  set -a
  source /etc/wow/volume.env
  set +a
  TREE="${WOW_TREE:-$TREE}"
fi

script="${TREE}/setup.sh"
conf="${TREE}/.run/boot.conf"
[[ -x "$script" && -f "$conf" ]] || exit 0
list="$(tr -d '[:space:]' <"$conf")"
[[ -n "$list" ]] || exit 0

owner="$(stat -c '%U' "$script")"
if [[ "$(id -u)" -eq 0 && "$owner" != "root" ]]; then
  exec runuser -u "$owner" -- "$script" up "$list"
fi
exec "$script" up "$list"
