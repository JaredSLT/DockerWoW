#!/usr/bin/env bash
# Create per-expansion databases and import whatever base SQL we have.
# Trinity/AzerothCore leave world/auth/characters empty so AutoSetup can run.
set -euo pipefail

RUNTIME="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${RUNTIME}/lib.sh"

SHORT="${WOW_SHORT:?WOW_SHORT is required}"
KIND="${WOW_KIND:?WOW_KIND is required}"
ROOT="${WOW_ROOT:-/opt/wow}"
HOTFIX="${WOW_HOTFIX:-none}"
DB_KIND="${WOW_DB_KIND:-}"

wait_for_realm_volume "$ROOT"

AUTH_DB="${SHORT}_auth"
WORLD_DB="${SHORT}_world"
CHARS_DB="${SHORT}_characters"
LOGS_DB="${SHORT}_logs"
REALM_DB="${SHORT}_realm"
DBC_DB="${SHORT}_dbc"

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

mark_imported() {
  mysql_cmd <<SQL
CREATE TABLE IF NOT EXISTS \`${AUTH_DB}\`.wow_launch_meta (
  k VARCHAR(64) PRIMARY KEY,
  v VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO \`${AUTH_DB}\`.wow_launch_meta (k, v) VALUES ('imported', '1')
  ON DUPLICATE KEY UPDATE v='1';
SQL
  rm -f "${ROOT}/.reimport"
}

# Playerbots SQL is copied beside the core as sql/playerbots/{world,characters}.
# Only that expansion's folder is in world/. Never replay sql/updates/mangos here.
apply_playerbots_sql() {
  local marker="${ROOT}/.core-id" modules=""
  [[ "$KIND" == "cmangos" ]] || return 0
  [[ -f "$marker" ]] || return 0
  modules="$(sed -n 's/^modules=//p' "$marker" | head -1)"
  [[ ",${modules}," == *",playerbots,"* ]] || return 0
  local base="${ROOT}/sql/playerbots"
  if [[ ! -d "$base" ]]; then
    log "playerbots is selected but ${base} is missing"
    return 0
  fi
  local applied
  applied="$(mysql_cmd -N -e "SELECT v FROM \`${AUTH_DB}\`.wow_launch_meta WHERE k='playerbots_sql'" 2>/dev/null || true)"
  if [[ "$applied" == "1" && ! -f "${ROOT}/.reimport" ]]; then
    return 0
  fi
  log "Applying playerbots SQL for ${SHORT} (not sql/updates/mangos)"
  import_sql_dir "$WORLD_DB" "${base}/world"
  import_sql_dir "$CHARS_DB" "${base}/characters"
  mysql_cmd <<SQL
CREATE TABLE IF NOT EXISTS \`${AUTH_DB}\`.wow_launch_meta (
  k VARCHAR(64) PRIMARY KEY,
  v VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
INSERT INTO \`${AUTH_DB}\`.wow_launch_meta (k, v) VALUES ('playerbots_sql', '1')
  ON DUPLICATE KEY UPDATE v='1';
SQL
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
  if [[ -n "$dump" ]]; then
    import_sql_file "$WORLD_DB" "$dump"
    return 0
  fi
  return 1
}

import_hotfix_dump() {
  [[ "$HOTFIX" != "none" && -n "$HOTFIX" ]] || return 0
  local dump hf_db="${SHORT}_${HOTFIX}"
  dump="$(find_sql_dumps "$ROOT" hotfix || true)"
  if [[ -n "$dump" ]]; then
    import_sql_file "$hf_db" "$dump"
    return 0
  fi
  return 0
}

# CMaNGOS update ids compare as major*100+minor: z2815_01 -> 281501, s2492_01 -> 249201.
# InstallFullDB.sh applies only core files newer than db_version.required_*.
# Replaying older files with --force runs their DROP TABLE statements anyway
# (the leading db_version ALTER does not match, but -f continues). z2771 and
# s2424 recreate creature_spawn_data_template and insert Entry 0 at CurHealth 1.
# mangosd treats any CurHealth > 0 as the creature's current HP, so every spawn
# that uses template 0 comes up at 1 HP.
cmangos_rev_number() {
  local name="$1"
  if [[ "$name" =~ [zs]([0-9]+)_([0-9]+) ]]; then
    printf '%d\n' "$((10#${BASH_REMATCH[1]}${BASH_REMATCH[2]}))"
    return 0
  fi
  return 1
}

cmangos_live_world_rev() {
  local col rev best=0
  while IFS= read -r col; do
    col="${col//[[:space:]]/}"
    [[ -n "$col" ]] || continue
    rev="$(cmangos_rev_number "${col#required_}")" || continue
    if (( rev > best )); then
      best=$rev
    fi
  done < <(mysql_cmd -N -e "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${WORLD_DB}' AND TABLE_NAME='db_version' AND COLUMN_NAME LIKE 'required\\_%'" 2>/dev/null || true)
  (( best > 0 )) || return 1
  printf '%d\n' "$best"
}

cmangos_align_world_version() {
  local live dir f base rev applied=0
  live="$(cmangos_live_world_rev)" || {
    log "No db_version required_* column — not applying core sql/updates/mangos"
    return 0
  }
  dir="${ROOT}/sql/updates/mangos"
  [[ -d "$dir" ]] || return 0
  log "Applying core world updates newer than revision ${live}"
  while IFS= read -r f; do
    base="$(basename "$f")"
    rev="$(cmangos_rev_number "$base")" || continue
    if (( rev > live )); then
      # No --force. A file whose leading ALTER does not match the live
      # required_* column must not continue into DROP TABLE.
      import_sql_file "$WORLD_DB" "$f" || die "Core world update failed: ${base}"
      applied=$((applied + 1))
    fi
  done < <(find "$dir" -maxdepth 1 -type f -name '*.sql' | sort)
  log "Applied ${applied} core world update(s)"
}

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
  import_sql_dir "$WORLD_DB" "${sql}/base/dbc/original_data"
  import_sql_dir "$WORLD_DB" "${sql}/base/dbc/cmangos_fixes"
  # ScriptDev2 (script data incl. spell.sql).
  import_sql_dir "$WORLD_DB" "${sql}/scriptdev2"
  # ACID content.
  local acid
  acid="$(find "${ROOT}/db/ACID" -maxdepth 1 -type f -iname 'acid_*.sql' | head -1 || true)"
  [[ -n "$acid" ]] && import_sql_file "$WORLD_DB" "$acid"
  # CMaNGOS custom SQL.
  local custom="${ROOT}/db/utilities/cmangos_custom.sql"
  [[ -f "$custom" ]] && import_sql_file "$WORLD_DB" "$custom"
}

# Recreate an empty character schema without touching auth or world.
ensure_character_schema() {
  case "$KIND" in
    cmangos)
      if ! db_has_table "$CHARS_DB" "characters"; then
        log "Character schema missing — importing base characters SQL for ${SHORT}"
        import_sql_file "$CHARS_DB" "${ROOT}/sql/base/characters.sql"
        import_sql_dir "$CHARS_DB" "${ROOT}/sql/updates/characters"
      fi
      ;;
    alpha)
      if ! db_has_table "$REALM_DB" "characters"; then
        log "Alpha character schema missing — importing realm SQL"
        import_sql_file "$REALM_DB" "${ROOT}/etc/databases/realm/realm.sql"
        import_sql_dir "$REALM_DB" "${ROOT}/etc/databases/realm/updates"
      fi
      ;;
    skyfire)
      if ! db_has_table "$CHARS_DB" "characters"; then
        log "Character schema missing — importing SkyFire characters base SQL"
        [[ -f "${ROOT}/sql/base/characters_database.sql" ]] && import_sql_file "$CHARS_DB" "${ROOT}/sql/base/characters_database.sql"
        import_sql_dir "$CHARS_DB" "${ROOT}/sql/updates/characters"
      fi
      ;;
    trinity)
      if [[ -f "${ROOT}/sql/base/characters_database.sql" ]] && ! db_has_table "$CHARS_DB" "characters"; then
        log "Importing Trinity characters base SQL"
        import_sql_file "$CHARS_DB" "${ROOT}/sql/base/characters_database.sql"
        import_sql_dir "$CHARS_DB" "${ROOT}/sql/updates/characters"
      fi
      ;;
    azerothcore)
      if [[ -d "${ROOT}/sql/base/db_characters" ]] && ! db_has_table "$CHARS_DB" "characters"; then
        log "Importing AzerothCore base characters SQL"
        import_sql_dir "$CHARS_DB" "${ROOT}/sql/base/db_characters"
      fi
      ;;
  esac
}

import_cmangos() {
  local sql="${ROOT}/sql"
  local dbrepo="${ROOT}/db"
  [[ -d "$sql" ]] || die "No sql/ under ${ROOT}"

  # The version marker can already be the latest core file while spawn data
  # is still the wiped seed. Rebuild from Full_DB, then align applies only
  # core updates newer than that dump.
  if cmangos_spawn_tables_wiped && [[ -d "${dbrepo}/Full_DB" ]]; then
    cmangos_reset_world_for_reimport
  fi

  if ! auth_schema_present; then
    import_sql_file "$AUTH_DB" "${sql}/base/realmd.sql"
    import_sql_file "$CHARS_DB" "${sql}/base/characters.sql"
    [[ -f "${sql}/base/logs.sql" ]] && import_sql_file "$LOGS_DB" "${sql}/base/logs.sql"
    import_sql_dir "$AUTH_DB" "${sql}/updates/realmd"
    import_sql_dir "$CHARS_DB" "${sql}/updates/characters"
    import_sql_dir "$LOGS_DB" "${sql}/updates/logs"
  elif ! db_has_table "$CHARS_DB" "characters"; then
    log "Character schema missing — importing base characters SQL for ${SHORT}"
    import_sql_file "$CHARS_DB" "${sql}/base/characters.sql"
    import_sql_dir "$CHARS_DB" "${sql}/updates/characters"
  else
    log "Auth/characters schema already present for ${SHORT}"
  fi

  if world_has_content; then
    log "World content already present for ${SHORT}"
    cmangos_align_world_version
    cmangos_guard_empty_addon_query
    # A world imported before the DBC step has creatures but zero spells;
    # mangosd then segfaults. Backfill the DBC content data if missing.
    if [[ "$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${WORLD_DB}\`.spell_template" 2>/dev/null || echo 0)" == "0" ]]; then
      log "spell_template empty — backfilling DBC content data for ${SHORT}"
      cmangos_apply_content_data
    fi
    apply_playerbots_sql
    return 0
  fi

  if [[ -d "${dbrepo}/Full_DB" ]]; then
    log "Importing CMaNGOS Full_DB + Updates from servers/${SHORT}/db"
    local f
    while IFS= read -r f; do
      import_sql_file "$WORLD_DB" "$f"
    done < <(find "${dbrepo}/Full_DB" -maxdepth 1 -type f \( -name '*.sql' -o -name '*.sql.gz' \) | sort)
    import_sql_dir "$WORLD_DB" "${dbrepo}/Updates"
    import_sql_dir "$WORLD_DB" "${dbrepo}/Updates/Instances"
    # Core schema backfill (skip if the content dump is already at/above core).
    cmangos_align_world_version
    # DBC (spells/items) + scriptdev2 + ACID + custom — canonical InstallFullDB.
    cmangos_apply_content_data
    cmangos_guard_empty_addon_query
    apply_playerbots_sql
    return 0
  fi

  import_sql_file "$WORLD_DB" "${sql}/base/mangos.sql"
  [[ -f "${sql}/scriptdev2/scriptdev2.sql" ]] && import_sql_file "$WORLD_DB" "${sql}/scriptdev2/scriptdev2.sql"
  import_sql_dir "$WORLD_DB" "${sql}/updates/mangos"
  cmangos_apply_content_data
  cmangos_guard_empty_addon_query
  apply_playerbots_sql
}

import_alpha() {
  local db="${ROOT}/etc/databases"
  [[ -d "$db" ]] || die "No etc/databases under ${ROOT}"
  import_sql_file "$AUTH_DB" "${db}/auth/auth.sql"
  import_sql_file "$REALM_DB" "${db}/realm/realm.sql"
  import_sql_file "$WORLD_DB" "${db}/world/world.sql"
  # DBC tables are created by the client extract (main.py -e), not a shipped dump.
  if [[ -f "${db}/dbc/dbc.sql" ]]; then
    import_sql_file "$DBC_DB" "${db}/dbc/dbc.sql"
  else
    log "No bundled dbc.sql — alpha extract will populate ${DBC_DB}"
  fi
  import_sql_dir "$AUTH_DB" "${db}/auth/updates"
  import_sql_dir "$REALM_DB" "${db}/realm/updates"
  import_sql_dir "$WORLD_DB" "${db}/world/updates"
  import_sql_dir "$DBC_DB" "${db}/dbc/updates"
}

# AzerothCore AutoSetup applies db_world / db_characters, then db_auth updates
# without importing sql/base/db_auth first if the schema looks "started".
import_trinity_base() {
  local sql="${ROOT}/sql"
  if [[ -f "${sql}/base/auth_database.sql" ]] && ! db_has_table "$AUTH_DB" "updates_include"; then
    log "Importing Trinity auth base SQL"
    import_sql_file "$AUTH_DB" "${sql}/base/auth_database.sql"
    import_sql_dir "$AUTH_DB" "${sql}/updates/auth"
  fi
  if [[ -f "${sql}/base/characters_database.sql" ]] && ! db_has_table "$CHARS_DB" "characters"; then
    log "Importing Trinity characters base SQL"
    import_sql_file "$CHARS_DB" "${sql}/base/characters_database.sql"
    import_sql_dir "$CHARS_DB" "${sql}/updates/characters"
  fi
}

import_azerothcore_base() {
  local sql="${ROOT}/sql"
  local dir
  if [[ -d "${sql}/base/db_auth" ]]; then
    log "Importing AzerothCore base auth SQL"
    import_sql_dir "$AUTH_DB" "${sql}/base/db_auth"
  fi
  if [[ -d "${sql}/base/db_characters" ]] && ! db_has_table "$CHARS_DB" "characters"; then
    log "Importing AzerothCore base characters SQL"
    import_sql_dir "$CHARS_DB" "${sql}/base/db_characters"
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
  [[ -f "${sql}/base/auth_database.sql" ]] && import_sql_file "$AUTH_DB" "${sql}/base/auth_database.sql"
  [[ -f "${sql}/base/characters_database.sql" ]] && import_sql_file "$CHARS_DB" "${sql}/base/characters_database.sql"
  [[ -f "${sql}/base/stored_procs.sql" ]] && import_sql_file "$WORLD_DB" "${sql}/base/stored_procs.sql" || true
  import_sql_dir "$AUTH_DB" "${sql}/updates/auth"
  import_sql_dir "$CHARS_DB" "${sql}/updates/characters"
  if world_has_content; then
    log "World content already present for ${SHORT}"
    return 0
  fi
  if import_world_dump; then
    import_sql_dir "$WORLD_DB" "${sql}/updates/world"
    return 0
  fi
  local world_dump
  world_dump="$(find "$sql" -maxdepth 2 -type f \( -iname '*world*.sql' -o -iname 'SFDB*.sql' \) ! -path '*/old/*' ! -path '*/updates/*' ! -path '*/dev/*' | head -1 || true)"
  if [[ -n "$world_dump" ]]; then
    import_sql_file "$WORLD_DB" "$world_dump"
    import_sql_dir "$WORLD_DB" "${sql}/updates/world"
  else
    warn "No SkyFire world dump found — ${SHORT} will start without creature/quest data"
    import_sql_dir "$WORLD_DB" "${sql}/updates/world"
  fi
}

if [[ "$KIND" == "alpha" ]] && ! db_has_table "$DBC_DB" "Map"; then
  log "alpha_dbc.Map missing — importing bundled DBC"
  if [[ -f "${ROOT}/etc/databases/dbc/dbc.sql" ]]; then
    import_sql_file "$DBC_DB" "${ROOT}/etc/databases/dbc/dbc.sql"
    import_sql_dir "$DBC_DB" "${ROOT}/etc/databases/dbc/updates"
  else
    die "No etc/databases/dbc/dbc.sql"
  fi
fi

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

reimport_requested=0
if [[ -f "${ROOT}/.reimport" ]]; then
  reimport_requested=1
  log "Reimport marker present for ${SHORT}. Schema already on disk will be loaded again."
fi

if [[ "$reimport_requested" -eq 0 ]] && already_imported && world_has_content; then
  if [[ "$KIND" == "cmangos" ]] && cmangos_spawn_tables_wiped && [[ -d "${ROOT}/db/Full_DB" ]]; then
    log "CMaNGOS world for ${SHORT} is missing spawn data — reimporting Full_DB"
    import_cmangos
    mark_imported || true
    log "Database init complete for ${SHORT}"
    exit 0
  fi
  log "Databases for ${SHORT} already imported — skip dump import"
  # A character wipe drops only that database. World content is still present,
  # so this branch is the one that runs on the next start.
  ensure_character_schema
  if [[ "$KIND" == "azerothcore" ]] && ! db_has_table "$AUTH_DB" "rbac_permissions"; then
    log "AzerothCore auth base missing — importing sql/base/db_auth"
    import_azerothcore_base
  fi
  if [[ "$KIND" == "trinity" ]] && ! db_has_table "$AUTH_DB" "updates_include"; then
    log "Trinity auth base missing — importing sql/base/auth_database.sql"
    # Partial auth schemas (e.g. motd already present) must not abort the import.
    MYSQL_IMPORT_FORCE=1 import_trinity_base
  fi
  if [[ "$KIND" == "cmangos" ]]; then
    cmangos_align_world_version
    cmangos_guard_empty_addon_query
    apply_playerbots_sql
    if [[ "$(mysql_cmd -N -e "SELECT COUNT(*) FROM \`${WORLD_DB}\`.spell_template" 2>/dev/null || echo 0)" == "0" ]]; then
      log "spell_template empty — backfilling DBC content data for ${SHORT}"
      cmangos_apply_content_data
    fi
  fi
  log "Database init complete for ${SHORT}"
  exit 0
fi

case "$KIND" in
  cmangos)     import_cmangos ;;
  alpha)
    if auth_schema_present; then
      log "Auth schema already present for ${SHORT} — skip dump import"
      if ! db_has_table "$REALM_DB" "characters"; then
        log "Alpha character schema missing — importing realm SQL"
        import_sql_file "$REALM_DB" "${ROOT}/etc/databases/realm/realm.sql"
        import_sql_dir "$REALM_DB" "${ROOT}/etc/databases/realm/updates"
      fi
    else
      import_alpha
    fi
    if ! db_has_table "$DBC_DB" "Map"; then
      log "alpha_dbc.Map missing — importing bundled DBC"
      if [[ -f "${ROOT}/etc/databases/dbc/dbc.sql" ]]; then
        import_sql_file "$DBC_DB" "${ROOT}/etc/databases/dbc/dbc.sql"
        import_sql_dir "$DBC_DB" "${ROOT}/etc/databases/dbc/updates"
      else
        die "No etc/databases/dbc/dbc.sql (rsync must not exclude database/dbc or etc/databases/dbc)"
      fi
    fi
    ;;
  skyfire)
    if auth_schema_present; then
      log "Auth schema already present for ${SHORT}"
      if ! db_has_table "$CHARS_DB" "characters"; then
        log "Character schema missing — importing SkyFire characters base SQL"
        [[ -f "${ROOT}/sql/base/characters_database.sql" ]] && import_sql_file "$CHARS_DB" "${ROOT}/sql/base/characters_database.sql"
        import_sql_dir "$CHARS_DB" "${ROOT}/sql/updates/characters"
      fi
      import_world_dump || true
    else
      import_skyfire
    fi
    ;;
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

mark_imported || true
log "Database init complete for ${SHORT}"
