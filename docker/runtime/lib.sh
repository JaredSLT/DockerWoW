# lib.sh — shared helpers for init-db / entrypoint (container and host).
# shellcheck shell=bash

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# True when this realm directory is visible. WOW_TREE, when set, must be the
# repo root (setup.sh lives there). Do not append a fixed directory name.
realm_volume_ready() {
  local root="${1:-${WOW_ROOT:-/opt/wow}}"
  if [[ ! -d "${root}/bin" && ! -f "${root}/main.py" && ! -f "${root}/run-server.sh" ]]; then
    return 1
  fi
  if [[ -n "${WOW_TREE:-}" && ! -f "${WOW_TREE}/setup.sh" ]]; then
    return 1
  fi
  return 0
}

# Block until the removable disk is mounted and this realm's files are visible.
# Do not mkdir the realm path first. Docker used to create the missing bind
# source on the root filesystem; those empty directories then occupied the
# udisks label path and the real disk mounted somewhere else.
wait_for_realm_volume() {
  local root="${1:-${WOW_ROOT:-/opt/wow}}"
  local i=0
  while true; do
    if realm_volume_ready "$root"; then
      [[ "$i" -eq 0 ]] || log "Removable volume is ready (${root})"
      return 0
    fi
    if (( i % 6 == 0 )); then
      if [[ -n "${WOW_TREE:-}" ]]; then
        log "Waiting for realm files at ${root} (tree ${WOW_TREE})"
      else
        log "Waiting for realm files at ${root}"
      fi
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

_WOW_MYSQL_USER_CNF=""
_WOW_MYSQL_ROOT_CNF=""

mysql_cnf_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '%s' "$s"
}

# Mode 0600 client defaults. Password stays in the file, not on argv.
mysql_client_defaults() {
  local which="$1"
  local file user pass
  if [[ "$which" == "root" ]]; then
    if [[ -n "${_WOW_MYSQL_ROOT_CNF}" && -f "${_WOW_MYSQL_ROOT_CNF}" ]]; then
      printf '%s\n' "${_WOW_MYSQL_ROOT_CNF}"
      return 0
    fi
    user="${MYSQL_ROOT_USER:-root}"
    pass="${MYSQL_ROOT_PASSWORD:-}"
  else
    if [[ -n "${_WOW_MYSQL_USER_CNF}" && -f "${_WOW_MYSQL_USER_CNF}" ]]; then
      printf '%s\n' "${_WOW_MYSQL_USER_CNF}"
      return 0
    fi
    user="${MYSQL_USER:-wow}"
    pass="${MYSQL_PASSWORD:-}"
  fi
  local old_umask
  old_umask="$(umask)"
  umask 077
  file="$(mktemp /tmp/wow-mysql.XXXXXX)"
  umask "$old_umask"
  {
    printf '%s\n' '[client]'
    printf 'host="%s"\n' "$(mysql_cnf_escape "${MYSQL_HOST:-db}")"
    printf 'port=%s\n' "${MYSQL_PORT:-3306}"
    printf 'user="%s"\n' "$(mysql_cnf_escape "$user")"
    printf 'password="%s"\n' "$(mysql_cnf_escape "$pass")"
  } >"$file"
  chmod 0600 "$file"
  if [[ "$which" == "root" ]]; then
    _WOW_MYSQL_ROOT_CNF="$file"
  else
    _WOW_MYSQL_USER_CNF="$file"
  fi
  printf '%s\n' "$file"
}

mysql_cmd() {
  local cnf
  cnf="$(mysql_client_defaults user)"
  env -u MYSQL_PWD "$MYSQL_BIN" \
    --defaults-extra-file="$cnf" \
    --protocol=TCP \
    -h "${MYSQL_HOST:-db}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "${MYSQL_USER:-wow}" \
    --connect-timeout=10 \
    --max-allowed-packet=1G \
    "$@"
}

mysql_root() {
  local cnf
  cnf="$(mysql_client_defaults root)"
  env -u MYSQL_PWD "$MYSQL_BIN" \
    --defaults-extra-file="$cnf" \
    --protocol=TCP \
    -h "${MYSQL_HOST:-db}" \
    -P "${MYSQL_PORT:-3306}" \
    -u "${MYSQL_ROOT_USER:-root}" \
    --connect-timeout=10 \
    --max-allowed-packet=1G \
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
  local force=() status=0
  [[ "${MYSQL_IMPORT_FORCE:-0}" == "1" ]] && force+=(-f)
  [[ -f "$file" ]] || { warn "SQL file missing: $file"; return 1; }
  log "Import $(basename "$file") -> ${db}  ($(du -h "$file" | cut -f1))"
  # WodCore dumps: utf8mb4mb4, and utf8mb4 + utf8_bin (MariaDB 11 maps utf8→utf8mb3).
  local fix_sql=(sed
    -e 's/utf8mb4mb4/utf8mb4/g'
    -e 's/CHARSET=utf8mb4 COLLATE[= ]utf8_bin/CHARSET=utf8mb4 COLLATE=utf8mb4_bin/g'
    -e 's/CHARSET=utf8mb4 COLLATE[= ]utf8mb3_bin/CHARSET=utf8mb4 COLLATE=utf8mb4_bin/g')
  # pipefail so gzip/sed failures are not hidden behind mysql's status.
  # `|| status` keeps best-effort callers from dying inside this function.
  set -o pipefail
  case "$file" in
    *.gz)
      gzip -dc "$file" | "${fix_sql[@]}" | mysql_cmd "${force[@]}" --database="$db" || status=$?
      ;;
    *)
      "${fix_sql[@]}" "$file" | mysql_cmd "${force[@]}" --database="$db" || status=$?
      ;;
  esac
  [[ "$status" -eq 0 ]]
}

_import_sql_dir() {
  local db="$1" dir="$2" mode="$3"
  local f
  [[ -d "$dir" ]] || return 0
  local files=()
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    files+=("$f")
  done < <(find "$dir" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) | LC_ALL=C sort)
  [[ ${#files[@]} -eq 0 ]] && return 0
  log "Import ${#files[@]} files from ${dir} -> ${db}"
  for f in "${files[@]}"; do
    if ! import_sql_file "$db" "$f"; then
      if [[ "$mode" == "best-effort" ]]; then
        warn "Failed: $f"
      else
        return 1
      fi
    fi
  done
}

# Abort on the first failed file. A missing directory is not an error.
import_sql_dir() {
  _import_sql_dir "$1" "$2" abort
}

# Old warn-and-continue behavior. Callers must opt in.
import_sql_dir_best_effort() {
  _import_sql_dir "$1" "$2" best-effort
}

# TDB1127.26021 -> 1127.26021. Any other dotted number is the fallback.
sql_dump_version() {
  local base
  base="$(basename "$1")"
  if [[ "$base" =~ [Tt][Dd][Bb][^0-9]*([0-9]+(\.[0-9]+)+) ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  if [[ "$base" =~ ([0-9]+(\.[0-9]+)+) ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}

# True when dotted version $1 is strictly newer than $2.
version_gt() {
  local IFS=.
  local -a left=() right=()
  local i n l r
  read -r -a left <<< "$1"
  read -r -a right <<< "$2"
  n=${#left[@]}
  if (( ${#right[@]} > n )); then
    n=${#right[@]}
  fi
  for ((i = 0; i < n; i++)); do
    l=$((10#${left[i]:-0}))
    r=$((10#${right[i]:-0}))
    if (( l > r )); then
      return 0
    fi
    if (( l < r )); then
      return 1
    fi
  done
  return 1
}

# Every world or hotfix dump find_sql_dumps would consider.
# Paths under a directory named old, updates, or dev are omitted.
list_sql_dump_candidates() {
  local root="$1" kind="$2"
  local dir pat
  local pats=()
  case "$kind" in
    world)
      pats=('TDB*world*.sql' 'TDB*world*.sql.gz' 'TDB_world*.sql' 'TDB_full_world*.sql'
            '*world_database*.sql' 'world_database.sql' '*Full_DB*.sql'
            'SFDB*.sql' 'SFDB*.sql.gz')
      ;;
    hotfix)
      pats=('TDB*hotfix*.sql' 'TDB*hotfix*.sql.gz' '*hotfix*database*.sql' 'hotfix-database*.sql')
      ;;
    *) return 1 ;;
  esac
  for dir in "${root}/sql/dumps" "${root}/sql" "${root}/sql/base" "${root}"; do
    [[ -d "$dir" ]] || continue
    for pat in "${pats[@]}"; do
      find "$dir" -maxdepth 2 -type f -iname "$pat" \
        ! -path '*/updates/*' ! -path '*/old/*' ! -path '*/dev/*'
    done
  done
}

# Highest TDB-style number wins. Without a numeric version, newest mtime wins.
find_sql_dumps() {
  local root="$1" kind="$2"
  local f ver="" mtime best="" best_ver="" best_mtime=-1
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    mtime="$(stat -c %Y -- "$f" 2>/dev/null || printf '0')"
    if ver="$(sql_dump_version "$f")"; then
      if [[ -z "$best" || -z "$best_ver" ]]; then
        best="$f"
        best_ver="$ver"
        best_mtime="$mtime"
      elif version_gt "$ver" "$best_ver"; then
        best="$f"
        best_ver="$ver"
        best_mtime="$mtime"
      elif ! version_gt "$best_ver" "$ver"; then
        if (( mtime > best_mtime )); then
          best="$f"
          best_ver="$ver"
          best_mtime="$mtime"
        fi
      fi
    elif [[ -z "$best_ver" ]]; then
      if [[ -z "$best" ]] || (( mtime > best_mtime )); then
        best="$f"
        best_mtime="$mtime"
      fi
    fi
  done < <(list_sql_dump_candidates "$root" "$kind" | awk 'NF && !seen[$0]++')
  [[ -n "$best" ]] || return 1
  printf '%s\n' "$best"
}

db_has_table() {
  local db="$1" table="$2"
  local n
  n="$(mysql_cmd -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${db}' AND table_name='${table}'" 2>/dev/null || echo 0)"
  [[ "${n// /}" -gt 0 ]]
}

trim_line() {
  local s="$1"
  s="${s//$'\r'/}"
  s="${s%%$'\n'*}"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

sql_quote() {
  local s="$1"
  s="${s//\'/\'\'}"
  printf '%s' "$s"
}

# z2815_01 -> 281501 and s2492_01 -> 249201. A leading MAJOR_MINOR is accepted too.
cmangos_rev_number() {
  local name="$1"
  if [[ "$name" =~ [zs]([0-9]+)_([0-9]+) ]]; then
    printf '%d\n' "$((10#${BASH_REMATCH[1]}${BASH_REMATCH[2]}))"
    return 0
  fi
  if [[ "$name" =~ (^|[^0-9])([0-9]+)_([0-9]+) ]]; then
    printf '%d\n' "$((10#${BASH_REMATCH[2]}${BASH_REMATCH[3]}))"
    return 0
  fi
  if [[ "$name" =~ (^|[^0-9])([0-9]+)([^0-9]|$) ]]; then
    printf '%d\n' "$((10#${BASH_REMATCH[2]}))"
    return 0
  fi
  return 1
}

# Highest required_* revision on db_version / character_db_version /
# realmd_db_version / logs_db_version, whichever exists in this database.
cmangos_live_rev() {
  local db="$1"
  local col rev best=0 found=0
  while IFS= read -r col; do
    col="${col//[[:space:]]/}"
    [[ -n "$col" ]] || continue
    rev="$(cmangos_rev_number "$col")" || continue
    if (( rev > best )); then
      best=$rev
      found=1
    fi
  done < <(mysql_cmd -N -e "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${db}' AND TABLE_NAME IN ('db_version','character_db_version','realmd_db_version','logs_db_version') AND COLUMN_NAME LIKE 'required\\_%'" 2>/dev/null || true)
  if (( found == 0 )); then
    return 1
  fi
  printf '%d\n' "$best"
}

# Print sql/updates files in dir whose revision is newer than the live required_* value.
cmangos_pending_updates() {
  local db="$1" dir="$2"
  local live f base rev
  [[ -d "$dir" ]] || return 0
  live="$(cmangos_live_rev "$db")" || return 0
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    base="$(basename "$f")"
    rev="$(cmangos_rev_number "$base")" || continue
    if (( rev > live )); then
      printf '%s\n' "$f"
    fi
  done < <(find "$dir" -maxdepth 1 -type f -name '*.sql' | LC_ALL=C sort)
}

# Return 0 when ${ROOT}/.reimport should run the base importer.
# Equal file and wow_launch_meta.reimport_stamp values return 1.
# A missing stamp file returns 1 so the caller can use the imported-row check.
reimport_selects_importer() {
  local stamp_file="$1"
  local auth_db="${2:-${AUTH_DB:-}}"
  local file_stamp db_stamp
  [[ -f "$stamp_file" ]] || return 1
  file_stamp="$(trim_line "$(head -n 1 "$stamp_file" || true)")"
  [[ -n "$file_stamp" ]] || return 0
  db_stamp="$(mysql_cmd -N -e "SELECT v FROM \`${auth_db}\`.wow_launch_meta WHERE k='reimport_stamp'" 2>/dev/null || true)"
  db_stamp="$(trim_line "$db_stamp")"
  if [[ "$file_stamp" == "$db_stamp" ]]; then
    return 1
  fi
  return 0
}
