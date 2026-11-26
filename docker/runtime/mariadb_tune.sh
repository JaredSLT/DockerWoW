#!/usr/bin/env bash
# One formula for the wow-db buffer pool and flush method.
# Sourced by launch-servers.sh. setup_ops.py doctor runs: mariadb_tune.sh --print
# shellcheck shell=bash
set -euo pipefail

# MemTotal is KiB. The pool is 25% of that, clamped to 256M..4G.
mariadb_pool_kb() {
  local mem_kb="$1"
  local pool=$((mem_kb / 4))
  local min_kb=$((256 * 1024))
  local max_kb=$((4 * 1024 * 1024))
  if ((pool < min_kb)); then
    pool=$min_kb
  fi
  if ((pool > max_kb)); then
    pool=$max_kb
  fi
  printf '%s' "$pool"
}

mariadb_buffer_pool() {
  local pool_kb gib mib
  pool_kb="$(mariadb_pool_kb "$1")"
  gib=$((1024 * 1024))
  mib=1024
  if ((pool_kb % gib == 0)); then
    printf '%sG' $((pool_kb / gib))
  elif ((pool_kb % mib == 0)); then
    printf '%sM' $((pool_kb / mib))
  else
    printf '%sK' "$pool_kb"
  fi
}

# True when the clamped pool is larger than half of MemTotal.
# 25% never is; the 256M floor is, on a host with under 512M.
mariadb_pool_exceeds_half() {
  local mem_kb="$1" pool_kb half
  pool_kb="$(mariadb_pool_kb "$mem_kb")"
  half=$((mem_kb / 2))
  ((pool_kb > half))
}

# O_DIRECT fails on zfs, fuse, 9p, virtiofs, and overlay Docker data roots.
mariadb_flush_method() {
  local fstype="${1:-}"
  fstype="${fstype,,}"
  case "$fstype" in
    zfs|fuse|9p|virtiofs|overlay|fuse.*)
      printf 'fsync'
      ;;
    *)
      printf 'O_DIRECT'
      ;;
  esac
}

mariadb_memtotal_kb() {
  awk '/^MemTotal:/ { print $2; found = 1 } END { if (!found) exit 1 }' /proc/meminfo
}

mariadb_docker_fstype() {
  local root="" fstype=""
  if command -v docker >/dev/null 2>&1; then
    if command -v timeout >/dev/null 2>&1; then
      root="$(timeout 15 docker info -f '{{.DockerRootDir}}' 2>/dev/null || true)"
    else
      root="$(docker info -f '{{.DockerRootDir}}' 2>/dev/null || true)"
    fi
  fi
  if [[ -z "$root" ]]; then
    root="/var/lib/docker"
  fi
  if command -v findmnt >/dev/null 2>&1 && [[ -e "$root" ]]; then
    fstype="$(findmnt -n -o FSTYPE -T "$root" 2>/dev/null || true)"
  fi
  printf '%s' "$fstype"
}

# Rewrite innodb_buffer_pool_size and innodb_flush_method in the template.
mariadb_write_cnf() {
  local template="$1" dest="$2" mem_kb="$3" fstype="$4"
  local pool method
  pool="$(mariadb_buffer_pool "$mem_kb")"
  method="$(mariadb_flush_method "$fstype")"
  [[ -f "$template" ]] || return 1
  mkdir -p "$(dirname "$dest")"
  sed \
    -e "s/^[[:space:]]*innodb_buffer_pool_size[[:space:]]*=.*/innodb_buffer_pool_size = ${pool}/" \
    -e "s/^[[:space:]]*innodb_flush_method[[:space:]]*=.*/innodb_flush_method = ${method}/" \
    "$template" >"${dest}.tmp"
  mv "${dest}.tmp" "$dest"
}

mariadb_print() {
  local mem fstype pool method exceeds=0
  mem="$(mariadb_memtotal_kb)"
  fstype="$(mariadb_docker_fstype)"
  pool="$(mariadb_buffer_pool "$mem")"
  method="$(mariadb_flush_method "$fstype")"
  if mariadb_pool_exceeds_half "$mem"; then
    exceeds=1
  fi
  printf 'pool=%s\nflush=%s\nexceeds=%s\nmemtotal_kb=%s\nfstype=%s\n' \
    "$pool" "$method" "$exceeds" "$mem" "$fstype"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  case "${1:-}" in
    --print)
      mariadb_print
      ;;
    --write)
      [[ $# -eq 3 ]] || { printf 'usage: mariadb_tune.sh --write TEMPLATE DEST\n' >&2; exit 2; }
      mem="$(mariadb_memtotal_kb)"
      fstype="$(mariadb_docker_fstype)"
      mariadb_write_cnf "$2" "$3" "$mem" "$fstype"
      if mariadb_pool_exceeds_half "$mem"; then
        printf 'ERROR: MariaDB buffer pool is larger than half of MemTotal\n' >&2
        exit 1
      fi
      ;;
    *)
      printf 'usage: mariadb_tune.sh --print|--write TEMPLATE DEST\n' >&2
      exit 2
      ;;
  esac
fi
