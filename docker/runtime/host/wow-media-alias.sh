#!/bin/bash
# Bind the stable WoW mount onto the udisks paths containers used to store.
# A desktop automounter names the directory after the filesystem label, and
# appends 1, 2, … when that directory already exists. Docker then keeps the
# empty directory it created while the disk was absent.
set -euo pipefail

env_file=/etc/wow/volume.env
[[ -f "$env_file" ]] || exit 0
# shellcheck disable=SC1090
source "$env_file"

mount="${WOW_VOLUME_MOUNT:-/mnt/wow-nvme}"
user_name="${WOW_MEDIA_USER:-}"
[[ -n "$user_name" ]] || exit 0
mountpoint -q "$mount" || exit 0

label=""
if [[ -n "${WOW_VOLUME_UUID:-}" ]]; then
  label="$(blkid -o value -s LABEL -t "UUID=${WOW_VOLUME_UUID}" 2>/dev/null || true)"
fi
if [[ -z "$label" ]]; then
  label="$(findmnt -n -o LABEL "$mount" 2>/dev/null || true)"
fi
# No label means this is not a udisks removable disk. Nothing to alias.
[[ -n "$label" ]] || exit 0

base="/run/media/${user_name}"
mkdir -p "$base"

alias_one() {
  local dest="$1"
  if mountpoint -q "$dest"; then
    return 0
  fi
  if [[ -d "$dest" ]]; then
    if find "$dest" -type f -print -quit | grep -q .; then
      echo "wow-media-alias: leaving ${dest} in place (it contains files)" >&2
      return 0
    fi
    rm -rf "$dest"
  fi
  mkdir -p "$dest"
  mount --bind "$mount" "$dest"
}

alias_one "${base}/${label}"
# udisks uses <label>1 when <label> already exists as a directory.
alias_one "${base}/${label}1"
