#!/bin/bash
# Run the public-repo poller as the owner of the WoW tree.
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

script="${TREE}/scripts/update-from-git.sh"
[[ -x "$script" ]] || exit 0

owner="$(stat -c '%U' "$script")"
if [[ "$(id -u)" -eq 0 && "$owner" != "root" ]]; then
  exec runuser -u "$owner" -- "$script"
fi
exec "$script"
