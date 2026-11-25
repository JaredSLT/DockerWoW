#!/bin/bash
# Add the per-realm loopback addresses listed in /etc/wow/loopback.ips.
# Installed to /usr/local/sbin so it runs before the removable disk is mounted.
set -euo pipefail

list=/etc/wow/loopback.ips
[[ -f "$list" ]] || exit 0

while read -r ip; do
  [[ -z "$ip" || "$ip" == \#* ]] && continue
  if ip -4 addr show dev lo | grep -q "inet ${ip}/"; then
    continue
  fi
  ip addr add "${ip}/32" dev lo
done <"$list"
