#!/bin/bash
# Make the stable WoW mount shared so containers bind-mounted rslave see a
# later mount or remount of the removable disk.
set -euo pipefail

env_file=/etc/wow/volume.env
[[ -f "$env_file" ]] || exit 0
# shellcheck disable=SC1090
source "$env_file"

mount="${WOW_VOLUME_MOUNT:-/mnt/wow-nvme}"
if mountpoint -q "$mount"; then
  mount --make-rshared "$mount"
fi
exit 0
