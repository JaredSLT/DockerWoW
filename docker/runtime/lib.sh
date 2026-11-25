# lib.sh — shared helpers for init-db / entrypoint (container and host).
# shellcheck shell=bash

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# Block until the removable disk is mounted and this realm's files are visible.
# Do not mkdir the realm path first. Docker used to create the missing bind
# source on the root filesystem; those empty directories then occupied the
# udisks label path and the real disk mounted somewhere else.
wait_for_realm_volume() {
  local root="${1:-${WOW_ROOT:-/opt/wow}}"
  local mount="${WOW_VOLUME_MOUNT:-/mnt/wow-nvme}"
  local tree="${WOW_TREE:-${mount}/WoW}"
  local i=0
  while true; do
    if [[ -f "${tree}/setup.sh" ]] \
      && { [[ -d "${root}/bin" ]] || [[ -f "${root}/main.py" ]] || [[ -f "${root}/run-server.sh" ]]; }; then
      [[ "$i" -eq 0 ]] || log "Removable volume is ready (${root})"
      return 0
    fi
    if (( i % 6 == 0 )); then
      log "Waiting for removable volume at ${mount} (realm ${root})"
    fi
    sleep 5
    i=$((i + 1))
  done
}

# MariaDB 11 images ship `mariadb` without a `mysql` symlink.
if command -v mysql >/dev/null 2>&1; then
  MYSQL_BIN="$(command -v mysql)"
elif command -v mariadb >/dev/null 2>&1; then
  MYSQL_BIN="$(command -v mariadb)"
else
  MYSQL_BIN="mysql"
fi

# So child tools (InstallFullDB, worldserver AutoSetup) can still call `mysql`.
if ! command -v mysql >/dev/null 2>&1 && [[ -x "$MYSQL_BIN" ]]; then
  mkdir -p /tmp/wow-bin
  ln -sfn "$MYSQL_BIN" /tmp/wow-bin/mysql
  export PATH="/tmp/wow-bin:${PATH}"
fi

mysql_cmd() {
  local extra=()
  [[ -n "${MYSQL_PASSWORD:-}" ]] && extra+=(-p"${MYSQL_PASSWORD}")
  "$MYSQL_BIN" \
    --protocol=TCP \
    -h "${MYSQL_HOST:-db}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "${MYSQL_USER:-wow}" \
    --connect-timeout=10 \
    --max-allowed-packet=1G \
    "${extra[@]}" \
    "$@"
}

mysql_root() {
  local extra=()
  [[ -n "${MYSQL_ROOT_PASSWORD:-}" ]] && extra+=(-p"${MYSQL_ROOT_PASSWORD}")
  "$MYSQL_BIN" \
    --protocol=TCP \
    -h "${MYSQL_HOST:-db}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "${MYSQL_ROOT_USER:-root}" \
    --connect-timeout=10 \
    --max-allowed-packet=1G \
    "${extra[@]}" \
    "$@"
}

wait_for_mysql() {
  local tries="${1:-90}" i
  log "Waiting for MySQL at ${MYSQL_HOST:-db}:${MYSQL_PORT:-3306}"
  for ((i = 1; i <= tries; i++)); do
    if mysql_root -e "SELECT 1" &>/dev/null || mysql_cmd -e "SELECT 1" &>/dev/null; then
      log "MySQL is up"
      return 0
    fi
    sleep 2
  done
  die "MySQL did not become ready"
}

import_sql_file() {
  local db="$1" file="$2"
  local force=()
  [[ "${MYSQL_IMPORT_FORCE:-0}" == "1" ]] && force+=(-f)
  [[ -f "$file" ]] || { warn "SQL file missing: $file"; return 1; }
  log "Import $(basename "$file") -> ${db}  ($(du -h "$file" | cut -f1))"
  # WodCore dumps: utf8mb4mb4, and utf8mb4 + utf8_bin (MariaDB 11 maps utf8→utf8mb3).
  local fix_sql=(sed
    -e 's/utf8mb4mb4/utf8mb4/g'
    -e 's/CHARSET=utf8mb4 COLLATE[= ]utf8_bin/CHARSET=utf8mb4 COLLATE=utf8mb4_bin/g'
    -e 's/CHARSET=utf8mb4 COLLATE[= ]utf8mb3_bin/CHARSET=utf8mb4 COLLATE=utf8mb4_bin/g')
  case "$file" in
    *.gz) gzip -dc "$file" | "${fix_sql[@]}" | mysql_cmd "${force[@]}" --database="$db" ;;
    *)    "${fix_sql[@]}" "$file" | mysql_cmd "${force[@]}" --database="$db" ;;
  esac
}

import_sql_dir() {
  local db="$1" dir="$2" f
  [[ -d "$dir" ]] || return 0
  local files=()
  while IFS= read -r f; do
    files+=("$f")
  done < <(find "$dir" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) | sort)
  [[ ${#files[@]} -eq 0 ]] && return 0
  log "Import ${#files[@]} files from ${dir} -> ${db}"
  for f in "${files[@]}"; do
    import_sql_file "$db" "$f" || warn "Failed: $f"
  done
}

# First matching dump in dest (sql/dumps, sql/, sql/base).
find_sql_dumps() {
  local root="$1" kind="$2"  # kind: world | hotfix
  local dir pat
  local pats=()
  case "$kind" in
    world)
      pats=('TDB*world*.sql' 'TDB*world*.sql.gz' 'TDB_world*.sql' 'TDB_full_world*.sql'
            '*world_database*.sql' 'world_database.sql' '*Full_DB*.sql')
      ;;
    hotfix)
      pats=('TDB*hotfix*.sql' 'TDB*hotfix*.sql.gz' '*hotfix*database*.sql' 'hotfix-database*.sql')
      ;;
    *) return 1 ;;
  esac
  for dir in "${root}/sql/dumps" "${root}/sql" "${root}/sql/base" "${root}"; do
    [[ -d "$dir" ]] || continue
    for pat in "${pats[@]}"; do
      # shellcheck disable=SC2086
      find "$dir" -maxdepth 2 -type f \( -iname "$pat" \) ! -path '*/updates/*' ! -path '*/old/*' ! -path '*/dev/*' \
        | sort | head -1
    done
  done | awk 'NF && !seen[$0]++' | head -1
}

db_has_table() {
  local db="$1" table="$2"
  local n
  n="$(mysql_cmd -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${db}' AND table_name='${table}'" 2>/dev/null || echo 0)"
  [[ "${n// /}" -gt 0 ]]
}
