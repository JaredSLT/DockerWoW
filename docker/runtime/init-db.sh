#!/usr/bin/env bash
# Create per-expansion databases and import whatever base SQL we have.
# Trinity/AzerothCore leave sql/updates to the world process (AutoSetup).
# CMaNGOS, Alpha, and SkyFire apply pending files on every init, including
# the already-imported path. The init mount is read-only: do not remove .reimport.
set -euo pipefail

RUNTIME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${RUNTIME}/lib.sh"

SHORT="${WOW_SHORT:?WOW_SHORT is required}"
KIND="${WOW_KIND:?WOW_KIND is required}"
ROOT="${WOW_ROOT:-/opt/wow}"
ROOT="${ROOT%/}"
HOTFIX="${WOW_HOTFIX:-none}"
DB_KIND="${WOW_DB_KIND:-}"

wait_for_realm_volume "$ROOT"

AUTH_DB="${SHORT}_auth"
WORLD_DB="${SHORT}_world"
CHARS_DB="${SHORT}_characters"
LOGS_DB="${SHORT}_logs"
REALM_DB="${SHORT}_realm"
DBC_DB="${SHORT}_dbc"

# Set when this run loaded that schema, so hashed SQL is applied again.
CMANGOS_WORLD_RELOADED=0
CMANGOS_CHARS_RELOADED=0
ALPHA_AUTH_RELOADED=0
ALPHA_REALM_RELOADED=0
ALPHA_WORLD_RELOADED=0
ALPHA_DBC_RELOADED=0
SKYFIRE_AUTH_RELOADED=0
SKYFIRE_CHARS_RELOADED=0
SKYFIRE_WORLD_RELOADED=0

wait_for_mysql

log "Ensuring MySQL user ${MYSQL_USER:-wow} and databases for ${SHORT}"
mysql_root <<SQL
CREATE USER IF NOT EXISTS '${MYSQL_USER:-wow}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD:-wow}';
CREATE USER IF NOT EXISTS '${MYSQL_USER:-wow}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD:-wow}';
CREATE DATABASE IF NOT EXISTS \`${AUTH_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS \`${WORLD_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS \`${CHARS_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON \`${AUTH_DB}\`.* TO '${MYSQL_USER:-wow}'@'%';
GRANT ALL PRIVILEGES ON \`${WORLD_DB}\`.* TO '${MYSQL_USER:-wow}'@'%';
GRANT ALL PRIVILEGES ON \`${CHARS_DB}\`.* TO '${MYSQL_USER:-wow}'@'%';
GRANT ALL PRIVILEGES ON \`${AUTH_DB}\`.* TO '${MYSQL_USER:-wow}'@'localhost';
GRANT ALL PRIVILEGES ON \`${WORLD_DB}\`.* TO '${MYSQL_USER:-wow}'@'localhost';
GRANT ALL PRIVILEGES ON \`${CHARS_DB}\`.* TO '${MYSQL_USER:-wow}'@'localhost';
SQL

if [[ "$KIND" == "cmangos" ]]; then
  mysql_root <<SQL
CREATE DATABASE IF NOT EXISTS \`${LOGS_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON \`${LOGS_DB}\`.* TO '${MYSQL_USER:-wow}'@'%';
GRANT ALL PRIVILEGES ON \`${LOGS_DB}\`.* TO '${MYSQL_USER:-wow}'@'localhost';
SQL
fi

if [[ "$KIND" == "alpha" ]]; then
  mysql_root <<SQL
CREATE DATABASE IF NOT EXISTS \`${REALM_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS \`${DBC_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON \`${REALM_DB}\`.* TO '${MYSQL_USER:-wow}'@'%';
GRANT ALL PRIVILEGES ON \`${DBC_DB}\`.* TO '${MYSQL_USER:-wow}'@'%';
GRANT ALL PRIVILEGES ON \`${REALM_DB}\`.* TO '${MYSQL_USER:-wow}'@'localhost';
GRANT ALL PRIVILEGES ON \`${DBC_DB}\`.* TO '${MYSQL_USER:-wow}'@'localhost';
SQL
fi

if [[ "$HOTFIX" != "none" && -n "$HOTFIX" ]]; then
  HF_DB="${SHORT}_${HOTFIX}"
  mysql_root <<SQL
CREATE DATABASE IF NOT EXISTS \`${HF_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON \`${HF_DB}\`.* TO '${MYSQL_USER:-wow}'@'%';
GRANT ALL PRIVILEGES ON \`${HF_DB}\`.* TO '${MYSQL_USER:-wow}'@'localhost';
SQL
fi

mysql_root -e "FLUSH PRIVILEGES;"

already_imported() {
  mysql_cmd -N -e "SELECT COUNT(*) FROM ${AUTH_DB}.wow_launch_meta WHERE k='imported'" 2>/dev/null | grep -qx 1
}

ensure_launch_tables() {
  mysql_cmd <<SQL || return 1
CREATE TABLE IF NOT EXISTS \`${AUTH_DB}\`.wow_launch_meta (
  k VARCHAR(64) PRIMARY KEY,
  v VARCHAR(512) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
ALTER TABLE \`${AUTH_DB}\`.wow_launch_meta MODIFY v VARCHAR(512) NOT NULL;
CREATE TABLE IF NOT EXISTS \`${AUTH_DB}\`.wow_sql_applied (
  path VARCHAR(512) NOT NULL PRIMARY KEY,
  sha256 VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
SQL
}

# Stamp is written only after base import and the incremental pass both succeed.
# Do not delete .reimport; the mount is read-only and the host removes it.
mark_imported() {
  local stamp="" esc=""
  ensure_launch_tables || return 1
  if [[ -f "${ROOT}/.reimport" ]]; then
    stamp="$(trim_line "$(head -n 1 "${ROOT}/.reimport" || true)")"
  fi
  if [[ -n "$stamp" ]]; then
    esc="$(sql_quote "$stamp")"
    mysql_cmd <<SQL || return 1
START TRANSACTION;
INSERT INTO \`${AUTH_DB}\`.wow_launch_meta (k, v) VALUES ('imported', '1')
  ON DUPLICATE KEY UPDATE v='1';
INSERT INTO \`${AUTH_DB}\`.wow_launch_meta (k, v) VALUES ('reimport_stamp', '${esc}')
  ON DUPLICATE KEY UPDATE v='${esc}';
COMMIT;
SQL
  else
    mysql_cmd <<SQL || return 1
INSERT INTO \`${AUTH_DB}\`.wow_launch_meta (k, v) VALUES ('imported', '1')
  ON DUPLICATE KEY UPDATE v='1';
SQL
  fi
}

sql_sha256() {
  local file="$1" sum
  if command -v sha256sum >/dev/null 2>&1; then
    sum="$(sha256sum -- "$file")"
  elif command -v shasum >/dev/null 2>&1; then
    sum="$(shasum -a 256 -- "$file")"
  else
    die "sha256sum is required to record applied SQL"
  fi
  printf '%s' "${sum%% *}"
}

sql_hash_applied() {
  local hash="$1" n esc
  esc="$(sql_quote "$hash")"
  n="$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${AUTH_DB}\`.wow_sql_applied WHERE sha256='${esc}'" 2>/dev/null || echo 0)"
  n="${n//[[:space:]]/}"
  [[ "${n:-0}" -gt 0 ]]
}

record_sql_applied() {
  local path="$1" hash="$2" p h
  p="$(sql_quote "$path")"
  h="$(sql_quote "$hash")"
  mysql_cmd -e "INSERT INTO \`${AUTH_DB}\`.wow_sql_applied (path, sha256) VALUES ('${p}', '${h}') ON DUPLICATE KEY UPDATE sha256='${h}'"
}

sql_like_prefix() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//%/\\%}"
  s="${s//_/\\_}"
  printf '%s' "$s"
}

forget_applied_prefix() {
  local prefix="$1" esc
  ensure_launch_tables || die "Could not create wow_sql_applied"
  esc="$(sql_quote "$(sql_like_prefix "$prefix")")"
  mysql_cmd -e "DELETE FROM \`${AUTH_DB}\`.wow_sql_applied WHERE path LIKE '${esc}%'" \
    || die "Could not clear applied SQL for ${prefix}"
}

# depth "all" walks subdirectories. Default is one level so db/Updates does not
# also pull in db/Updates/Instances (that directory is applied on its own).
apply_hashed_sql_dir() {
  local db="$1" dir="$2" depth="${3:-1}"
  local f hash rel applied=0 saved
  [[ -d "$dir" ]] || return 0
  saved="${MYSQL_IMPORT_FORCE:-0}"
  MYSQL_IMPORT_FORCE=0
  ensure_launch_tables || die "Could not create wow_sql_applied"
  local files=()
  if [[ "$depth" == "all" ]]; then
    while IFS= read -r f; do
      [[ -n "$f" ]] || continue
      files+=("$f")
    done < <(find "$dir" -type f \( -name '*.sql' -o -name '*.sql.gz' \) | LC_ALL=C sort)
  else
    while IFS= read -r f; do
      [[ -n "$f" ]] || continue
      files+=("$f")
    done < <(find "$dir" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) | LC_ALL=C sort)
  fi
  for f in "${files[@]}"; do
    hash="$(sql_sha256 "$f")"
    rel="${f#"${ROOT}/"}"
    if sql_hash_applied "$hash"; then
      continue
    fi
    import_sql_file "$db" "$f" || die "SQL update failed: ${rel}"
    record_sql_applied "$rel" "$hash" || die "Could not record applied SQL ${rel}"
    applied=$((applied + 1))
  done
  MYSQL_IMPORT_FORCE="$saved"
  if (( applied > 0 )); then
    log "Applied ${applied} hashed SQL file(s) from ${dir#"${ROOT}/"}"
  fi
}

# No --force. A file whose leading ALTER does not match the live required_*
# column must not continue into DROP TABLE.
cmangos_align_db() {
  local db="$1" dir="$2" label="$3"
  local live f applied=0 saved
  [[ -d "$dir" ]] || return 0
  saved="${MYSQL_IMPORT_FORCE:-0}"
  MYSQL_IMPORT_FORCE=0
  if ! live="$(cmangos_live_rev "$db")"; then
    MYSQL_IMPORT_FORCE="$saved"
    log "No required_* version column in ${db} — not applying ${label}"
    return 0
  fi
  log "Applying ${label} updates newer than revision ${live}"
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    import_sql_file "$db" "$f" || die "Core update failed: $(basename "$f")"
    applied=$((applied + 1))
  done < <(cmangos_pending_updates "$db" "$dir")
  MYSQL_IMPORT_FORCE="$saved"
  log "Applied ${applied} ${label} update(s)"
}

# Playerbots SQL is copied beside the core as sql/playerbots/{world,characters}.
# Only that expansion's folder is in world/. Never replay sql/updates/mangos here.
apply_playerbots_sql() {
  local marker="${ROOT}/.core-id" modules="" base
  [[ "$KIND" == "cmangos" ]] || return 0
  [[ -f "$marker" ]] || return 0
  modules="$(sed -n 's/^modules=//p' "$marker" | head -1)"
  [[ ",${modules}," == *",playerbots,"* ]] || return 0
  base="${ROOT}/sql/playerbots"
  if [[ ! -d "$base" ]]; then
    log "playerbots is selected but ${base} is missing"
    return 0
  fi
  if [[ "$CMANGOS_WORLD_RELOADED" == 1 ]]; then
    forget_applied_prefix "sql/playerbots/world/"
  fi
  if [[ "$CMANGOS_CHARS_RELOADED" == 1 ]]; then
    forget_applied_prefix "sql/playerbots/characters/"
  fi
  log "Applying playerbots SQL for ${SHORT} (not sql/updates/mangos)"
  apply_hashed_sql_dir "$WORLD_DB" "${base}/world" all
  apply_hashed_sql_dir "$CHARS_DB" "${base}/characters" all
}

world_has_content() {
  local table n
  for table in creature creature_template creature_template_wdb; do
    if db_has_table "$WORLD_DB" "$table"; then
      n="$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${WORLD_DB}\`.\`${table}\`" 2>/dev/null || echo 0)"
      n="${n// /}"
      [[ "${n:-0}" -gt 50 ]] && return 0
    fi
  done
  return 1
}

auth_schema_present() {
  db_has_table "$AUTH_DB" "account" || db_has_table "$AUTH_DB" "accounts"
}

import_world_dump() {
  local dump
  dump="$(find_sql_dumps "$ROOT" world || true)"
  if [[ -z "$dump" ]]; then
    return 1
  fi
  import_sql_file "$WORLD_DB" "$dump" || die "Import failed: ${dump}"
}

import_hotfix_dump() {
  [[ "$HOTFIX" != "none" && -n "$HOTFIX" ]] || return 0
  local dump hf_db="${SHORT}_${HOTFIX}"
  dump="$(find_sql_dumps "$ROOT" hotfix || true)"
  if [[ -n "$dump" ]]; then
    import_sql_file "$hf_db" "$dump" || die "Import failed: ${dump}"
  fi
}

# CMaNGOS update ids compare as major*100+minor: z2815_01 -> 281501, s2492_01 -> 249201.
# InstallFullDB.sh applies only core files newer than the version table.
# Replaying older files with --force runs their DROP TABLE statements anyway
# (the leading db_version ALTER does not match, but -f continues). z2771 and
# s2424 recreate creature_spawn_data_template and insert Entry 0 at CurHealth 1.
# mangosd treats any CurHealth > 0 as the creature's current HP, so every spawn
# that uses template 0 comes up at 1 HP.

# True when the live spawn tables are the one-row seed left by z2771 / s2424.
# Content dumps ship CurHealth 0 on template 0 and many spawn links.
cmangos_spawn_tables_wiped() {
  local links templates
  db_has_table "$WORLD_DB" "creature_spawn_data" || return 1
  db_has_table "$WORLD_DB" "creature_spawn_data_template" || return 1
  links="$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${WORLD_DB}\`.creature_spawn_data" 2>/dev/null || echo 0)"
  templates="$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${WORLD_DB}\`.creature_spawn_data_template" 2>/dev/null || echo 0)"
  links="${links//[[:space:]]/}"
  templates="${templates//[[:space:]]/}"
  [[ "${links:-0}" -eq 0 && "${templates:-0}" -le 1 ]]
}

cmangos_reset_world_for_reimport() {
  log "Recreating ${WORLD_DB}: creature spawn data was wiped by a core update replay"
  mysql_root <<SQL
DROP DATABASE IF EXISTS \`${WORLD_DB}\`;
CREATE DATABASE \`${WORLD_DB}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON \`${WORLD_DB}\`.* TO '${MYSQL_USER:-wow}'@'%';
GRANT ALL PRIVILEGES ON \`${WORLD_DB}\`.* TO '${MYSQL_USER:-wow}'@'localhost';
FLUSH PRIVILEGES;
SQL
}

# Canonical apply_full_dbc_data + apply_full_scriptdev2_data + apply_acid_data +
# apply_custom_data from CMaNGOS InstallFullDB.sh. The Full_DB dump ships schema
# plus creature/item rows but NOT the spell data; the spells come from the core's
# DBC original_data (Spell.sql). Skipping this leaves spell_template empty and
# mangosd segfaults loading CreatureEventAI (references missing spell ids).
# CMaNGOS Query() returns nullptr when a SELECT matches 0 rows.
# ObjectMgr::LoadGameObjects then Fetch()s gameobject_addon and segfaults.
cmangos_guard_empty_addon_query() {
  local n
  n="$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${WORLD_DB}\`.gameobject_addon" 2>/dev/null || echo 0)"
  n="${n// /}"
  if [[ "${n:-0}" -eq 0 ]]; then
    log "gameobject_addon empty — inserting dummy row so mangosd does not SIGSEGV in LoadGameObjects"
    mysql_cmd -e "INSERT INTO \`${WORLD_DB}\`.gameobject_addon (guid, animprogress, state, StringId) VALUES (0, 100, -1, 0)"
  fi
  # LoadScriptMap dereferences GetScriptMap() after LoadScripts returns early on 0 rows.
  local tbl
  while IFS= read -r tbl; do
    [[ -z "$tbl" ]] && continue
    n="$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${WORLD_DB}\`.\`${tbl}\`" 2>/dev/null || echo 0)"
    n="${n// /}"
    if [[ "${n:-0}" -eq 0 ]]; then
      log "${tbl} empty — inserting dummy row so mangosd does not SIGSEGV in LoadScriptMap"
      mysql_cmd -e "INSERT INTO \`${WORLD_DB}\`.\`${tbl}\` (id, comments) VALUES (0, 'wow-lab empty-table guard')" || true
    fi
  done < <(mysql_cmd -N -e "SELECT table_name FROM information_schema.tables WHERE table_schema='${WORLD_DB}' AND table_name LIKE 'dbscripts_%' ORDER BY 1")
  # Entry 0 spawns crash map load; Oronok's SummonedCreatureDespawn null-derefs on TemporarySpawn::UnSummon.
  mysql_cmd -e "DELETE FROM \`${WORLD_DB}\`.gameobject WHERE id=0" 2>/dev/null || true
  mysql_cmd -e "DELETE FROM \`${WORLD_DB}\`.creature WHERE id=0" 2>/dev/null || true
  mysql_cmd -e "UPDATE \`${WORLD_DB}\`.creature_template SET ScriptName='' WHERE ScriptName='npc_spawned_oronok_tornheart'" 2>/dev/null || true
}

cmangos_apply_content_data() {
  local sql="${ROOT}/sql"
  # DBC original_data (spell/item content) + CMaNGOS DBC fixes.
  import_sql_dir "$WORLD_DB" "${sql}/base/dbc/original_data" || die "DBC original_data import failed"
  import_sql_dir "$WORLD_DB" "${sql}/base/dbc/cmangos_fixes" || die "DBC cmangos_fixes import failed"
  # ScriptDev2 (script data incl. spell.sql).
  import_sql_dir "$WORLD_DB" "${sql}/scriptdev2" || die "ScriptDev2 import failed"
  # ACID content.
  local acid
  acid="$(find "${ROOT}/db/ACID" -maxdepth 1 -type f -iname 'acid_*.sql' | head -1 || true)"
  if [[ -n "$acid" ]]; then
    import_sql_file "$WORLD_DB" "$acid" || die "Import failed: ${acid}"
  fi
  # CMaNGOS custom SQL.
  local custom="${ROOT}/db/utilities/cmangos_custom.sql"
  if [[ -f "$custom" ]]; then
    import_sql_file "$WORLD_DB" "$custom" || die "Import failed: ${custom}"
  fi
}

# Recreate an empty character schema without touching auth or world.
# Core updates are applied later by the incremental pass, not all at once.
ensure_character_schema() {
  case "$KIND" in
    cmangos)
      if ! db_has_table "$CHARS_DB" "characters"; then
        log "Character schema missing — importing base characters SQL for ${SHORT}"
        import_sql_file "$CHARS_DB" "${ROOT}/sql/base/characters.sql" || die "Import failed: characters.sql"
        CMANGOS_CHARS_RELOADED=1
      fi
      ;;
    alpha)
      if ! db_has_table "$REALM_DB" "characters"; then
        log "Alpha character schema missing — importing realm SQL"
        import_sql_file "$REALM_DB" "${ROOT}/etc/databases/realm/realm.sql" || die "Import failed: realm.sql"
        ALPHA_REALM_RELOADED=1
      fi
      ;;
    skyfire)
      if ! db_has_table "$CHARS_DB" "characters"; then
        log "Character schema missing — importing SkyFire characters base SQL"
        if [[ -f "${ROOT}/sql/base/characters_database.sql" ]]; then
          import_sql_file "$CHARS_DB" "${ROOT}/sql/base/characters_database.sql" || die "Import failed: characters_database.sql"
        fi
        SKYFIRE_CHARS_RELOADED=1
      fi
      ;;
    trinity)
      if [[ -f "${ROOT}/sql/base/characters_database.sql" ]] && ! db_has_table "$CHARS_DB" "characters"; then
        log "Importing Trinity characters base SQL"
        import_sql_file "$CHARS_DB" "${ROOT}/sql/base/characters_database.sql" || die "Import failed: characters_database.sql"
      fi
      ;;
    azerothcore)
      if [[ -d "${ROOT}/sql/base/db_characters" ]] && ! db_has_table "$CHARS_DB" "characters"; then
        log "Importing AzerothCore base characters SQL"
        import_sql_dir "$CHARS_DB" "${ROOT}/sql/base/db_characters" || die "AzerothCore characters import failed"
      fi
      ;;
  esac
}

import_cmangos() {
  local sql="${ROOT}/sql"
  local dbrepo="${ROOT}/db"
  local f
  [[ -d "$sql" ]] || die "No sql/ under ${ROOT}"

  # The version marker can already be the latest core file while spawn data
  # is still the wiped seed. Rebuild from Full_DB, then align applies only
  # core updates newer than that dump.
  if cmangos_spawn_tables_wiped && [[ -d "${dbrepo}/Full_DB" ]]; then
    cmangos_reset_world_for_reimport
  fi

  if ! auth_schema_present; then
    import_sql_file "$AUTH_DB" "${sql}/base/realmd.sql" || die "Import failed: realmd.sql"
    import_sql_file "$CHARS_DB" "${sql}/base/characters.sql" || die "Import failed: characters.sql"
    if [[ -f "${sql}/base/logs.sql" ]]; then
      import_sql_file "$LOGS_DB" "${sql}/base/logs.sql" || die "Import failed: logs.sql"
    fi
    CMANGOS_CHARS_RELOADED=1
  elif ! db_has_table "$CHARS_DB" "characters"; then
    log "Character schema missing — importing base characters SQL for ${SHORT}"
    import_sql_file "$CHARS_DB" "${sql}/base/characters.sql" || die "Import failed: characters.sql"
    CMANGOS_CHARS_RELOADED=1
  else
    log "Auth/characters schema already present for ${SHORT}"
  fi

  if world_has_content; then
    log "World content already present for ${SHORT}"
    return 0
  fi

  if [[ -d "${dbrepo}/Full_DB" ]]; then
    log "Importing CMaNGOS Full_DB from servers/${SHORT}/db"
    while IFS= read -r f; do
      [[ -n "$f" ]] || continue
      import_sql_file "$WORLD_DB" "$f" || die "Full_DB import failed: $(basename "$f")"
    done < <(find "${dbrepo}/Full_DB" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) | LC_ALL=C sort)
    CMANGOS_WORLD_RELOADED=1
    return 0
  fi

  import_sql_file "$WORLD_DB" "${sql}/base/mangos.sql" || die "Import failed: mangos.sql"
  if [[ -f "${sql}/scriptdev2/scriptdev2.sql" ]]; then
    import_sql_file "$WORLD_DB" "${sql}/scriptdev2/scriptdev2.sql" || die "Import failed: scriptdev2.sql"
  fi
  CMANGOS_WORLD_RELOADED=1
}

import_alpha() {
  local db="${ROOT}/etc/databases"
  [[ -d "$db" ]] || die "No etc/databases under ${ROOT}"
  if ! auth_schema_present; then
    import_sql_file "$AUTH_DB" "${db}/auth/auth.sql" || die "Import failed: auth.sql"
    import_sql_file "$REALM_DB" "${db}/realm/realm.sql" || die "Import failed: realm.sql"
    import_sql_file "$WORLD_DB" "${db}/world/world.sql" || die "Import failed: world.sql"
    ALPHA_AUTH_RELOADED=1
    ALPHA_REALM_RELOADED=1
    ALPHA_WORLD_RELOADED=1
  else
    log "Auth schema already present for ${SHORT} — skip dump import"
    if ! db_has_table "$REALM_DB" "characters"; then
      log "Alpha character schema missing — importing realm SQL"
      import_sql_file "$REALM_DB" "${db}/realm/realm.sql" || die "Import failed: realm.sql"
      ALPHA_REALM_RELOADED=1
    fi
  fi
}

ensure_alpha_dbc() {
  [[ "$KIND" == "alpha" ]] || return 0
  if db_has_table "$DBC_DB" "Map"; then
    return 0
  fi
  log "alpha_dbc.Map missing — importing bundled DBC"
  if [[ -f "${ROOT}/etc/databases/dbc/dbc.sql" ]]; then
    import_sql_file "$DBC_DB" "${ROOT}/etc/databases/dbc/dbc.sql" || die "Import failed: dbc.sql"
    ALPHA_DBC_RELOADED=1
  else
    die "No etc/databases/dbc/dbc.sql (rsync must not exclude database/dbc or etc/databases/dbc)"
  fi
}

# AzerothCore / Trinity AutoSetup applies sql/updates. Init only loads a
# missing base schema. Do not import sql/updates from here.
import_trinity_base() {
  local sql="${ROOT}/sql"
  if [[ -f "${sql}/base/auth_database.sql" ]] && ! db_has_table "$AUTH_DB" "updates_include"; then
    log "Importing Trinity auth base SQL"
    import_sql_file "$AUTH_DB" "${sql}/base/auth_database.sql" || die "Import failed: auth_database.sql"
  fi
  if [[ -f "${sql}/base/characters_database.sql" ]] && ! db_has_table "$CHARS_DB" "characters"; then
    log "Importing Trinity characters base SQL"
    import_sql_file "$CHARS_DB" "${sql}/base/characters_database.sql" || die "Import failed: characters_database.sql"
  fi
}

import_azerothcore_base() {
  local sql="${ROOT}/sql"
  if [[ -d "${sql}/base/db_auth" ]] && ! db_has_table "$AUTH_DB" "rbac_permissions"; then
    log "Importing AzerothCore base auth SQL"
    import_sql_dir "$AUTH_DB" "${sql}/base/db_auth" || die "AzerothCore auth import failed"
  fi
  if [[ -d "${sql}/base/db_characters" ]] && ! db_has_table "$CHARS_DB" "characters"; then
    log "Importing AzerothCore base characters SQL"
    import_sql_dir "$CHARS_DB" "${sql}/base/db_characters" || die "AzerothCore characters import failed"
  fi
}

import_optional_world_dump() {
  if world_has_content; then
    log "World content already present for ${SHORT}"
    return 0
  fi
  if import_world_dump; then
    import_hotfix_dump
    return 0
  fi
  log "No TDB/world dump for ${SHORT} — worldserver AutoSetup will create schema only"
}

import_skyfire() {
  local sql="${ROOT}/sql"
  if ! auth_schema_present; then
    if [[ -f "${sql}/base/auth_database.sql" ]]; then
      import_sql_file "$AUTH_DB" "${sql}/base/auth_database.sql" || die "Import failed: auth_database.sql"
    fi
    SKYFIRE_AUTH_RELOADED=1
  else
    log "Auth schema already present for ${SHORT}"
  fi
  if ! db_has_table "$CHARS_DB" "characters"; then
    log "Character schema missing — importing SkyFire characters base SQL"
    if [[ -f "${sql}/base/characters_database.sql" ]]; then
      import_sql_file "$CHARS_DB" "${sql}/base/characters_database.sql" || die "Import failed: characters_database.sql"
    fi
    SKYFIRE_CHARS_RELOADED=1
  fi
  if [[ -f "${sql}/base/stored_procs.sql" ]]; then
    import_sql_file "$WORLD_DB" "${sql}/base/stored_procs.sql" || die "Import failed: stored_procs.sql"
  fi
  if world_has_content; then
    log "World content already present for ${SHORT}"
    return 0
  fi
  if import_world_dump; then
    SKYFIRE_WORLD_RELOADED=1
    return 0
  fi
  warn "No SkyFire world dump found — ${SHORT} will start without creature/quest data"
}

cmangos_apply_incremental() {
  cmangos_align_db "$WORLD_DB" "${ROOT}/sql/updates/mangos" "core world"
  cmangos_align_db "$CHARS_DB" "${ROOT}/sql/updates/characters" "core characters"
  cmangos_align_db "$AUTH_DB" "${ROOT}/sql/updates/realmd" "core realmd"
  cmangos_align_db "$LOGS_DB" "${ROOT}/sql/updates/logs" "core logs"
  if [[ "$CMANGOS_WORLD_RELOADED" == 1 ]]; then
    forget_applied_prefix "db/Updates/"
  fi
  apply_hashed_sql_dir "$WORLD_DB" "${ROOT}/db/Updates"
  apply_hashed_sql_dir "$WORLD_DB" "${ROOT}/db/Updates/Instances"
}

alpha_apply_incremental() {
  if [[ "$ALPHA_AUTH_RELOADED" == 1 ]]; then
    forget_applied_prefix "etc/databases/auth/updates/"
  fi
  if [[ "$ALPHA_REALM_RELOADED" == 1 ]]; then
    forget_applied_prefix "etc/databases/realm/updates/"
  fi
  if [[ "$ALPHA_WORLD_RELOADED" == 1 ]]; then
    forget_applied_prefix "etc/databases/world/updates/"
  fi
  if [[ "$ALPHA_DBC_RELOADED" == 1 ]]; then
    forget_applied_prefix "etc/databases/dbc/updates/"
  fi
  apply_hashed_sql_dir "$AUTH_DB" "${ROOT}/etc/databases/auth/updates"
  apply_hashed_sql_dir "$REALM_DB" "${ROOT}/etc/databases/realm/updates"
  apply_hashed_sql_dir "$WORLD_DB" "${ROOT}/etc/databases/world/updates"
  apply_hashed_sql_dir "$DBC_DB" "${ROOT}/etc/databases/dbc/updates"
}

skyfire_apply_one() {
  local db="$1" dir="$2" label="$3"
  if cmangos_live_rev "$db" >/dev/null 2>&1; then
    cmangos_align_db "$db" "$dir" "$label"
  else
    apply_hashed_sql_dir "$db" "$dir"
  fi
}

skyfire_apply_incremental() {
  if [[ "$SKYFIRE_AUTH_RELOADED" == 1 ]]; then
    forget_applied_prefix "sql/updates/auth/"
  fi
  if [[ "$SKYFIRE_CHARS_RELOADED" == 1 ]]; then
    forget_applied_prefix "sql/updates/characters/"
  fi
  if [[ "$SKYFIRE_WORLD_RELOADED" == 1 ]]; then
    forget_applied_prefix "sql/updates/world/"
  fi
  skyfire_apply_one "$AUTH_DB" "${ROOT}/sql/updates/auth" "skyfire auth"
  skyfire_apply_one "$CHARS_DB" "${ROOT}/sql/updates/characters" "skyfire characters"
  skyfire_apply_one "$WORLD_DB" "${ROOT}/sql/updates/world" "skyfire world"
}

cmangos_backfill_spells() {
  local n
  n="$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${WORLD_DB}\`.spell_template" 2>/dev/null || echo 0)"
  n="${n//[[:space:]]/}"
  if [[ "${n:-0}" == "0" ]]; then
    log "spell_template empty — backfilling DBC content data for ${SHORT}"
    cmangos_apply_content_data
  fi
}

if [[ "$DB_KIND" == "vmangos" || "$DB_KIND" == "mangosthree" ]]; then
  if [[ -f "${ROOT}/.reimport" ]]; then
    die "${SHORT}: ${DB_KIND} has no automatic world import. Databases were dumped and dropped. Load that core's base SQL yourself, then remove servers/${SHORT}/.reimport. sql/updates/mangos was not applied."
  fi
  if already_imported && world_has_content; then
    log "${SHORT}: ${DB_KIND} import is not automatic. Existing databases were left in place."
    exit 0
  fi
  die "${SHORT}: ${DB_KIND} database import is not wired. Refusing to apply another core's SQL into this slot."
fi

run_base=0
if [[ -f "${ROOT}/.reimport" ]]; then
  if reimport_selects_importer "${ROOT}/.reimport"; then
    log "Reimport stamp for ${SHORT} does not match the database. Base SQL will be imported."
    run_base=1
  else
    log "Reimport stamp for ${SHORT} already matches. Skipping base SQL."
    run_base=0
  fi
elif ! { already_imported && world_has_content; }; then
  run_base=1
fi

# Spawn-table wipe is repaired even when the reimport stamp already matches.
if [[ "$KIND" == "cmangos" ]] && cmangos_spawn_tables_wiped && [[ -d "${ROOT}/db/Full_DB" ]]; then
  log "CMaNGOS world for ${SHORT} is missing spawn data — reimporting Full_DB"
  run_base=1
fi

if [[ "$run_base" -eq 1 ]]; then
  case "$KIND" in
    cmangos) import_cmangos ;;
    alpha) import_alpha ;;
    skyfire) import_skyfire ;;
    azerothcore)
      import_azerothcore_base
      import_optional_world_dump
      ;;
    trinity)
      import_trinity_base
      import_optional_world_dump
      log "${KIND} will apply remaining auth/characters/world updates on first worldserver start"
      ;;
    *)
      die "Unknown WOW_KIND=${KIND}"
      ;;
  esac
else
  log "Databases for ${SHORT} already imported — skip dump import"
  ensure_character_schema
  if [[ "$KIND" == "azerothcore" ]] && ! db_has_table "$AUTH_DB" "rbac_permissions"; then
    log "AzerothCore auth base missing — importing sql/base/db_auth"
    import_azerothcore_base
  fi
  if [[ "$KIND" == "trinity" ]] && ! db_has_table "$AUTH_DB" "updates_include"; then
    log "Trinity auth base missing — importing sql/base/auth_database.sql"
    import_trinity_base
  fi
fi

ensure_alpha_dbc

case "$KIND" in
  cmangos)
    cmangos_apply_incremental
    cmangos_backfill_spells
    cmangos_guard_empty_addon_query
    apply_playerbots_sql
    ;;
  alpha)
    alpha_apply_incremental
    ;;
  skyfire)
    skyfire_apply_incremental
    ;;
  trinity|azerothcore)
    ;;
  *)
    die "Unknown WOW_KIND=${KIND}"
    ;;
esac

mark_imported || die "Could not record import for ${SHORT}"
log "Database init complete for ${SHORT}"
