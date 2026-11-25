# catalog.sh — Expansion metadata for setup / launch / compose / runtime.
# Fields (pipe-separated):
#   1  short          servers/<short> folder and compose profile
#   2  core           docker/<core> name
#   3  kind           alpha | cmangos | azerothcore | trinity | skyfire
#   4  image          build-servers.sh image tag (without :latest)
#   5  client         clients/<client> folder
#   6  proto          legacy (realmd/authserver:3724) | bnet (bnetserver:1119)
#   7  auth_bin       auth binary filename (empty for alpha)
#   8  world_bin      world binary filename (empty for alpha)
#   9  auth_port      container auth/login port
#  10  world_port     container world port
#  11  rest_port      container LoginREST port (0 if unused)
#  12  loopback       dedicated 127.0.0.x so default ports never collide
#  13  expansion      account.expansion value
#  14  hotfix         hotfix db suffix: none | hotfix | hotfixes
#  15  realm_name     realmlist display name
#  16  db_repo        repos.sh key, or GitHub owner/repo for tdb-github
#  17  db_branch      git ref, or TDB release tag/prefix (empty = newest release)
#  18  db_kind        bundled | cmangos | tdb-github | wod | skyfire | none
#
# shellcheck shell=bash

_CATALOG_SH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_CATALOG_ROOT="$(cd "${_CATALOG_SH_DIR}/../.." && pwd)"

catalog_lines() {
  cat <<'EOF'
alpha|alpha-core|alpha|wow-alpha-core|World-of-Warcraft-0.5|legacy|||3724|8100|0|127.0.0.2|0|none|Alpha 0.5|||bundled
vanilla|cmangos-classic|cmangos|wow-cmangos-classic|World-of-Warcraft-1.12.1|legacy|realmd|mangosd|3724|8085|0|127.0.0.3|0|none|Vanilla|cmangos-classic-db|master|cmangos
tbc|cmangos-tbc|cmangos|wow-cmangos-tbc|World-of-Warcraft-2.4.3|legacy|realmd|mangosd|3724|8085|0|127.0.0.4|1|none|The Burning Crusade|cmangos-tbc-db|master|cmangos
wotlk|azerothcore-wotlk|azerothcore|wow-azerothcore-wotlk|World-of-Warcraft-3.3.5a|legacy|authserver|worldserver|3724|8085|0|127.0.0.5|2|none|Wrath of the Lich King|||bundled
cata|The-Cataclysm-Preservation-Project|trinity|wow-the-cataclysm-preservation-project|World-of-Warcraft-4.3.4|legacy|authserver|worldserver|3724|8085|0|127.0.0.6|3|hotfixes|Cataclysm|The-Cataclysm-Preservation-Project/TrinityCore||tdb-github
mop|SkyFire_548|skyfire|wow-skyfire-548|World-of-Warcraft-5.4.8|legacy|authserver|worldserver|3724|8085|0|127.0.0.7|4|none|Mists of Pandaria|||skyfire
wod|WodCore-Reforged|trinity|wow-wodcore-reforged|World-of-Warcraft-6.2.3|legacy|authserver|worldserver|1119|8085|0|127.0.0.8|5|hotfix|Warlords of Draenor|||wod
legion|TrinityCore-Legion|trinity|wow-trinitycore-legion|World-of-Warcraft-7.3.5|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.9|6|hotfixes|Legion|TrinityCore/TrinityCore|TDB735|tdb-github
bfa|TrinityCore-BFA|trinity|wow-trinitycore-bfa|World-of-Warcraft-8.3.7|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.10|7|hotfixes|Battle for Azeroth|TrinityCore/TrinityCore|TDB837.20101|tdb-github
shadowlands|TrinityCore-Shadowlands|trinity|wow-trinitycore-shadowlands|World-of-Warcraft-9.2.7|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.11|8|hotfixes|Shadowlands|TrinityCore/TrinityCore|TDB927.22111|tdb-github
dragonflight|TrinityCore-Dragonflight|trinity|wow-trinitycore-dragonflight|World-of-Warcraft-10.2.7|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.12|9|hotfixes|Dragonflight|TrinityCore/TrinityCore|TDB1027.24051|tdb-github
warwithin|TrinityCore-WarWithin|trinity|wow-trinitycore-warwithin|World-of-Warcraft-11.2.7|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.13|10|hotfixes|The War Within|TrinityCore/TrinityCore|TDB1127.26011|tdb-github
midnight|TrinityCore|trinity|wow-trinitycore|World-of-Warcraft-12.x.x|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.14|11|hotfixes|Midnight|TrinityCore/TrinityCore|TDB1210|tdb-github
cata-classic|TrinityCore-Cata-Classic|trinity|wow-trinitycore-cata-classic|World-of-Warcraft-4.4.2|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.15|3|hotfixes|Cataclysm Classic|TrinityCore/TrinityCore|cata_classic|bundled
classic-era|TrinityCore-Classic|trinity|wow-trinitycore-classic|World-of-Warcraft-Classic|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.16|0|hotfixes|Classic Era|||bundled
wotlk-classic|TrinityCore-WotLK-Classic|trinity|wow-trinitycore-wotlk-classic|World-of-Warcraft-3.4.3|bnet|bnetserver|worldserver|1119|8085|8081|127.0.0.17|2|hotfixes|Wrath Classic|TrinityCore/TrinityCore|TDB343.24081|tdb-github
EOF
}

catalog_shorts() {
  catalog_lines | awk -F'|' '{print $1}'
}

catalog_line() {
  local short="$1"
  catalog_lines | awk -F'|' -v s="$short" '$1==s {print; found=1} END{exit !found}'
}

# Populate CATALOG_* globals from a short name.
catalog_load() {
  local line
  line="$(catalog_line "$1")" || return 1
  IFS='|' read -r \
    CATALOG_SHORT \
    CATALOG_CORE \
    CATALOG_KIND \
    CATALOG_IMAGE \
    CATALOG_CLIENT \
    CATALOG_PROTO \
    CATALOG_AUTH_BIN \
    CATALOG_WORLD_BIN \
    CATALOG_AUTH_PORT \
    CATALOG_WORLD_PORT \
    CATALOG_REST_PORT \
    CATALOG_LOOPBACK \
    CATALOG_EXPANSION \
    CATALOG_HOTFIX \
    CATALOG_REALM_NAME \
    CATALOG_DB_REPO \
    CATALOG_DB_BRANCH \
    CATALOG_DB_KIND \
    <<<"$line"
  CATALOG_DB_REPO="${CATALOG_DB_REPO:-}"
  CATALOG_DB_BRANCH="${CATALOG_DB_BRANCH:-}"
  CATALOG_DB_KIND="${CATALOG_DB_KIND:-none}"
  CATALOG_MODULES=""
  _catalog_apply_selection "$CATALOG_SHORT" || return 1
}

# Selection overlay. Python runs only when this short has a saved row.
# Assignments are single-quoted CATALOG_* names; anything else fails the load.
_catalog_apply_selection() {
  local short="$1" sel overlay line
  if [[ -n "${WOW_SELECTION_FILE+x}" ]]; then
    sel="$WOW_SELECTION_FILE"
  else
    sel="${_CATALOG_ROOT}/.run/selection.conf"
  fi
  [[ -f "$sel" ]] || return 0
  grep -Eq "^${short}\\|" "$sel" || return 0
  overlay="$(WOW_SELECTION_FILE="$sel" python3 "${_CATALOG_ROOT}/scripts/select-project.py" --bash-overlay "$short")" || return 1
  [[ -n "$overlay" ]] || return 0
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^CATALOG_[A-Z0-9_]+=\'[^\']*\'$ ]] || return 1
  done <<<"$overlay"
  # shellcheck disable=SC2086
  eval "$overlay"
}

# Default "all" skips a realm whose default project refuses launch until the
# client build matches. Naming the short still selects it.
_catalog_implicit_launch_blocked() {
  local short="$1" projects
  projects="${_CATALOG_ROOT}/docker/runtime/projects.conf"
  [[ -f "$projects" ]] || return 1
  awk -F'|' -v s="$short" '$2==s && $21=="1" && $20=="refuse" { found=1 } END { exit !found }' "$projects" \
    || return 1
  if python3 "${_CATALOG_ROOT}/scripts/select-project.py" --launch-check "$short" >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

# Resolve a user token (short name or docker core name) to a catalog short.
catalog_resolve() {
  local token="$1" short tlow
  token="${token// /}"
  [[ -z "$token" ]] && return 1
  if catalog_line "$token" >/dev/null; then
    printf '%s' "$token"
    return 0
  fi
  tlow="$(printf '%s' "$token" | tr '[:upper:]' '[:lower:]')"
  while IFS= read -r short; do
    catalog_load "$short"
    if [[ "$tlow" == "$short" || "$tlow" == "$(printf '%s' "$CATALOG_CORE" | tr '[:upper:]' '[:lower:]')" ]]; then
      printf '%s' "$short"
      return 0
    fi
  done < <(catalog_shorts)
  return 1
}

# Fill SELECTED=() from a comma-separated spec ("all" or empty = every expansion).
# Prints the bad token to stderr and returns 1 on unknown names.
catalog_select() {
  local spec="${1:-}" item resolved
  SELECTED=()
  if [[ -z "$spec" || "$spec" == "all" ]]; then
    while IFS= read -r item; do
      if _catalog_implicit_launch_blocked "$item"; then
        printf 'Skipping %s until its client build matches the core. Name it explicitly to build or launch it.\n' "$item" >&2
        continue
      fi
      SELECTED+=("$item")
    done < <(catalog_shorts)
    return 0
  fi
  local IFS=','
  read -ra items <<<"$spec"
  unset IFS
  for item in "${items[@]}"; do
    item="${item// /}"
    [[ -z "$item" ]] && continue
    if ! resolved="$(catalog_resolve "$item")"; then
      printf 'Unknown server: %s\n' "$item" >&2
      return 1
    fi
    SELECTED+=("$resolved")
  done
  [[ ${#SELECTED[@]} -gt 0 ]]
}

# Unique host ports used when BIND_MODE=ports (loopback aliases unavailable).
# Auth 13xxx, world 18xxx, rest 18xxx+50 so they never overlap.
catalog_fallback_ports() {
  local short="$1"
  case "$short" in
    alpha)        FB_AUTH=13700; FB_WORLD=18100; FB_REST=0; FB_WEB=19080 ;;
    vanilla)      FB_AUTH=13724; FB_WORLD=18085; FB_REST=0; FB_WEB=19081 ;;
    tbc)          FB_AUTH=13725; FB_WORLD=18086; FB_REST=0; FB_WEB=19082 ;;
    wotlk)        FB_AUTH=13726; FB_WORLD=18087; FB_REST=0; FB_WEB=19083 ;;
    cata)         FB_AUTH=13727; FB_WORLD=18088; FB_REST=0; FB_WEB=19084 ;;
    mop)          FB_AUTH=13728; FB_WORLD=18089; FB_REST=0; FB_WEB=19085 ;;
    wod)          FB_AUTH=11119; FB_WORLD=18090; FB_REST=0; FB_WEB=19086 ;;
    legion)       FB_AUTH=11120; FB_WORLD=18091; FB_REST=18881; FB_WEB=19087 ;;
    bfa)          FB_AUTH=11121; FB_WORLD=18092; FB_REST=18882; FB_WEB=19088 ;;
    shadowlands)  FB_AUTH=11122; FB_WORLD=18093; FB_REST=18883; FB_WEB=19089 ;;
    dragonflight) FB_AUTH=11123; FB_WORLD=18094; FB_REST=18884; FB_WEB=19090 ;;
    warwithin)    FB_AUTH=11124; FB_WORLD=18095; FB_REST=18885; FB_WEB=19091 ;;
    midnight)     FB_AUTH=11125; FB_WORLD=18096; FB_REST=18886; FB_WEB=19092 ;;
    cata-classic) FB_AUTH=11126; FB_WORLD=18097; FB_REST=18887; FB_WEB=19093 ;;
    classic-era)  FB_AUTH=11127; FB_WORLD=18098; FB_REST=18888; FB_WEB=19094 ;;
    wotlk-classic) FB_AUTH=11128; FB_WORLD=18099; FB_REST=18889; FB_WEB=19095 ;;
    *)            return 1 ;;
  esac
}

# Fail if two expansions would publish the same host port (BIND_MODE=ports).
catalog_assert_unique_host_ports() {
  local short key seen="" extras
  local saved="${BIND_MODE:-ports}"
  BIND_MODE=ports
  while IFS= read -r short; do
    catalog_fallback_ports "$short" || continue
    for key in "$FB_AUTH" "$FB_WORLD" "$FB_REST" "$FB_WEB"; do
      [[ "$key" == "0" || -z "$key" ]] && continue
      if [[ " $seen " == *" $key "* ]]; then
        BIND_MODE="$saved"
        printf 'ERROR: host port %s is assigned to more than one expansion\n' "$key" >&2
        return 1
      fi
      seen+=" $key"
    done
    if [[ "$short" == "alpha" ]]; then
      for extras in 9081 9090 9100; do
        if [[ " $seen " == *" $extras "* ]]; then
          BIND_MODE="$saved"
          printf 'ERROR: host port %s collides with alpha extra ports\n' "$extras" >&2
          return 1
        fi
        seen+=" $extras"
      done
    fi
  done < <(catalog_shorts)
  BIND_MODE="$saved"
  return 0
}

# ACCESS=loopback is the default (vanilla.local on 127.0.0.x).
# ACCESS=ports is one public address and the unique fallback ports.
# ACCESS=public reads .run/access.conf (short|hostname|ip) and publishes
# stock ports on that address. A realm with no row stays on its loopback.
access_mode() {
  local mode="${ACCESS:-}"
  if [[ -n "$mode" ]]; then
    printf '%s' "$mode"
    return 0
  fi
  case "${BIND_MODE:-haproxy}" in
    ports) printf 'ports' ;;
    *) printf 'loopback' ;;
  esac
}

access_file() {
  if [[ -n "${WOW_ACCESS_FILE:-}" ]]; then
    printf '%s' "$WOW_ACCESS_FILE"
  else
    printf '%s' "${_CATALOG_ROOT}/.run/access.conf"
  fi
}

# Print "hostname ip" for a public realm, or nothing.
access_public() {
  local short="$1" line
  [[ "$(access_mode)" == "public" ]] || return 1
  [[ -f "$(access_file)" ]] || return 1
  line="$(awk -F'|' -v s="$short" '$1==s { print $2, $3; exit }' "$(access_file)")"
  [[ -n "$line" ]] || return 1
  printf '%s' "$line"
}

# Public hostname. Falls back to short.local so this machine keeps working.
catalog_hostname() {
  local short="${1:-${CATALOG_SHORT:-}}" line
  if line="$(access_public "$short")"; then
    printf '%s' "${line%% *}"
    return 0
  fi
  printf '%s.local' "$short"
}

# Address HAProxy publishes. Loopback unless this realm has a public row.
catalog_publish_ip() {
  local short="${1:-${CATALOG_SHORT:-}}" line
  if line="$(access_public "$short")"; then
    printf '%s' "${line##* }"
    return 0
  fi
  if [[ "$short" != "${CATALOG_SHORT:-}" ]]; then
    catalog_load "$short" >/dev/null || return 1
  fi
  printf '%s' "$CATALOG_LOOPBACK"
}

# Container port HAProxy listens on. The host publish is the stock client
# port on that realm's 127.0.0.x address; these stay unique inside HAProxy.
catalog_proxy_port() {
  local role="$1" ip="$2" octet
  octet="${ip##*.}"
  case "$role" in
    auth)  printf '%s' $((20000 + octet)) ;;
    world) printf '%s' $((21000 + octet)) ;;
    rest)  printf '%s' $((22000 + octet)) ;;
    *) return 1 ;;
  esac
}

# Host ports actually published by compose.
# haproxy: stock client ports on a dedicated 127.0.0.x, fronted by wow-haproxy.
#   Auth 3724 or 1119, world 8085 (alpha 8100), REST 8081. The hostname above
#   resolves to that address, so a stock client needs no custom port.
# loopback: stock auth on 127.0.0.x; world/REST stay on the unique fallback
#   ports because a process bound to *:8085 also blocks 127.0.0.x:8085.
# ports: every listener on 0.0.0.0 with the unique fallback ports.
catalog_host_ports() {
  catalog_load "$1" || return 1
  catalog_fallback_ports "$1" || return 1
  HOST_NAME="$(catalog_hostname "$CATALOG_SHORT")"
  if [[ "${BIND_MODE:-ports}" == "haproxy" ]]; then
    HOST_BIND="$(catalog_publish_ip "$CATALOG_SHORT")"
    HOST_AUTH="${CATALOG_AUTH_PORT}"
    HOST_WORLD="${CATALOG_WORLD_PORT}"
    HOST_REST="${CATALOG_REST_PORT}"
    HOST_WEB=80
  elif [[ "${BIND_MODE:-ports}" == "loopback" ]]; then
    HOST_BIND="${CATALOG_LOOPBACK}"
    HOST_AUTH="${CATALOG_AUTH_PORT}"
    HOST_WORLD="${FB_WORLD}"
    HOST_REST="${FB_REST}"
    HOST_WEB=80
  else
    HOST_BIND="0.0.0.0"
    HOST_AUTH="${FB_AUTH}"
    HOST_WORLD="${FB_WORLD}"
    HOST_REST="${FB_REST}"
    HOST_WEB="${FB_WEB}"
  fi
}

install_present() {
  local dest="$1"
  [[ -d "${dest}/bin" ]] && return 0
  [[ -f "${dest}/main.py" || -f "${dest}/run-server.sh" ]] && return 0
  return 1
}

# True when extract-data.sh has produced maps the world process can load.
# Prefer extract_data_complete — "some .map files exist" is not enough to boot.
extract_data_present() {
  extract_data_complete "$1" "$2"
}

_extract_count() {
  local dir="$1" pat="$2"
  [[ -d "$dir" ]] || { printf '0'; return; }
  find "$dir" -maxdepth 1 -type f -name "$pat" 2>/dev/null | wc -l
}

# Recursive count (alpha navs live in etc/navs/Nav/<map>/*.nav).
_extract_count_r() {
  local dir="$1" pat="$2"
  [[ -d "$dir" ]] || { printf '0'; return; }
  find "$dir" -type f -name "$pat" 2>/dev/null | wc -l
}

# Unique 3-digit map ids from maps/*.map (0002035.map → 000).
extract_map_ids() {
  local maps="$1"
  [[ -d "$maps" ]] || return 0
  find "$maps" -maxdepth 1 -type f -name '*.map' 2>/dev/null \
    | sed 's|.*/||; s/^\([0-9][0-9][0-9]\).*/\1/' \
    | grep -E '^[0-9]{3}$' | sort -u
}

# Print map ids that have .map tiles but no sidecar (000.vmtree / 000.mmap).
extract_missing_sidecars() {
  local maps="$1" side="$2" ext="$3" id
  while IFS= read -r id; do
    [[ -n "$id" ]] || continue
    [[ -f "${side}/${id}${ext}" ]] || printf '%s\n' "$id"
  done < <(extract_map_ids "$maps")
}

# Continent ids that exist in this maps/ tree. Extractors often skip empty
# test maps (573, 605, …); those must not block launch.
extract_continent_ids() {
  local maps="$1" id
  # 000/001/530/571 plus Pandaria 870. Map files may be 0002035.map or 0000_20_35.map.
  for id in 000 001 530 571 870; do
    find "$maps" -maxdepth 1 -type f \( -name "${id}*.map" -o -name "0${id}_*.map" \) 2>/dev/null | grep -q . \
      && printf '%s\n' "$id"
  done
}

# Trinity 3-digit 000.vmtree, SkyFire 4-digit 0000.vmtree, or nested
# vmaps/0000/0000.vmtree (War Within vmap4assembler).
extract_sidecar_exists() {
  local side="$1" id="$2" ext="$3" pad
  [[ -f "${side}/${id}${ext}" ]] && return 0
  [[ -f "${side}/${id}/${id}${ext}" ]] && return 0
  printf -v pad '%04d' "$((10#$id))" 2>/dev/null || pad="$id"
  [[ -f "${side}/${pad}${ext}" ]] && return 0
  [[ -f "${side}/${pad}/${pad}${ext}" ]] && return 0
  return 1
}

extract_missing_continent_sidecars() {
  local maps="$1" side="$2" ext="$3" id
  while IFS= read -r id; do
    [[ -n "$id" ]] || continue
    extract_sidecar_exists "$side" "$id" "$ext" || printf '%s\n' "$id"
  done < <(extract_continent_ids "$maps")
}

_extract_gap_list() {
  local ids="$1" n
  n="$(printf '%s\n' "$ids" | grep -c . || true)"
  EXTRACT_GAP_N="${n:-0}"
  printf '%s' "$(printf '%s\n' "$ids" | grep . | head -12 | tr '\n' ' ')"
  [[ "${n:-0}" -gt 12 ]] && printf '…'
}

# Sets EXTRACT_GAP on failure. Maps + vmaps + mmaps must all match map coverage;
# leftover tiles without headers count as incomplete.
extract_data_complete() {
  local dest="$1" kind="$2"
  EXTRACT_GAP=""
  EXTRACT_GAP_N=0
  local n ids missing

  if [[ "$kind" == "alpha" ]]; then
    n="$(_extract_count "${dest}/etc/maps" '*.map')"
    n="${n// /}"
    if [[ "${n:-0}" -eq 0 ]]; then
      EXTRACT_GAP="no etc/maps/*.map"
      return 1
    fi
    n="$(_extract_count_r "${dest}/etc/navs" '*.nav')"
    n="${n// /}"
    if [[ "${n:-0}" -eq 0 ]]; then
      EXTRACT_GAP="no etc/navs/Nav/**/*.nav"
      return 1
    fi
    local azeroth kalimdor
    azeroth="$(_extract_count_r "${dest}/etc/navs/Nav/Azeroth" '*.nav')"
    kalimdor="$(_extract_count_r "${dest}/etc/navs/Nav/Kalimdor" '*.nav')"
    azeroth="${azeroth// /}"; kalimdor="${kalimdor// /}"
    if [[ "${azeroth:-0}" -lt 100 || "${kalimdor:-0}" -lt 100 ]]; then
      EXTRACT_GAP="navs missing continents (Azeroth=${azeroth:-0} Kalimdor=${kalimdor:-0})"
      return 1
    fi
    return 0
  fi

  n="$(_extract_count "${dest}/maps" '*.map')"
  n="${n// /}"
  if [[ "${n:-0}" -eq 0 ]]; then
    EXTRACT_GAP="no maps/*.map"
    return 1
  fi

  n="$(find "${dest}/dbc" -type f \( -name '*.dbc' -o -name '*.db2' \) 2>/dev/null | wc -l)"
  n="${n// /}"
  if [[ "${n:-0}" -eq 0 ]]; then
    EXTRACT_GAP="no dbc/*.dbc (or .db2)"
    return 1
  fi

  ids="$(extract_map_ids "${dest}/maps")"
  if [[ -z "$ids" ]]; then
    EXTRACT_GAP="no numeric map ids in maps/"
    return 1
  fi

  missing="$(extract_missing_continent_sidecars "${dest}/maps" "${dest}/vmaps" '.vmtree')"
  if [[ -n "$missing" ]]; then
    EXTRACT_GAP="vmaps missing continent .vmtree: $(_extract_gap_list "$missing")"
    return 1
  fi
  n="$(find "${dest}/vmaps" -type f 2>/dev/null | wc -l)"; n="${n// /}"
  if [[ "${n:-0}" -eq 0 ]]; then
    EXTRACT_GAP="no vmaps"
    return 1
  fi

  missing="$(extract_missing_continent_sidecars "${dest}/maps" "${dest}/mmaps" '.mmap')"
  if [[ -n "$missing" ]]; then
    EXTRACT_GAP="mmaps missing continent .mmap headers: $(_extract_gap_list "$missing")"
    return 1
  fi

  n="$(_extract_count "${dest}/mmaps" '*.mmtile')"
  n="${n// /}"
  if [[ "${n:-0}" -eq 0 ]]; then
    EXTRACT_GAP="no mmaps/*.mmtile"
    return 1
  fi
  return 0
}

extract_step_complete() {
  local dest="$1" kind="$2" step="$3"
  EXTRACT_GAP=""
  local n missing
  case "$kind/$step" in
    alpha/maps)
      n="$(_extract_count "${dest}/etc/maps" '*.map')"; n="${n// /}"
      [[ "${n:-0}" -gt 0 ]] || { EXTRACT_GAP="no etc/maps"; return 1; }
      ;;
    alpha/navs|alpha/vmaps|alpha/mmaps)
      n="$(_extract_count_r "${dest}/etc/navs" '*.nav')"; n="${n// /}"
      [[ "${n:-0}" -gt 0 ]] || { EXTRACT_GAP="no etc/navs/Nav/**/*.nav"; return 1; }
      local azeroth kalimdor
      azeroth="$(_extract_count_r "${dest}/etc/navs/Nav/Azeroth" '*.nav')"
      kalimdor="$(_extract_count_r "${dest}/etc/navs/Nav/Kalimdor" '*.nav')"
      azeroth="${azeroth// /}"; kalimdor="${kalimdor// /}"
      if [[ "${azeroth:-0}" -lt 100 || "${kalimdor:-0}" -lt 100 ]]; then
        EXTRACT_GAP="navs missing continents (Azeroth=${azeroth:-0} Kalimdor=${kalimdor:-0})"
        return 1
      fi
      ;;
    */maps)
      n="$(_extract_count "${dest}/maps" '*.map')"; n="${n// /}"
      [[ "${n:-0}" -gt 0 ]] || { EXTRACT_GAP="no maps"; return 1; }
      n="$(find "${dest}/dbc" -type f \( -name '*.dbc' -o -name '*.db2' \) 2>/dev/null | wc -l)"
      n="${n// /}"
      [[ "${n:-0}" -gt 0 ]] || { EXTRACT_GAP="no dbc"; return 1; }
      ;;
    */vmaps)
      missing="$(extract_missing_continent_sidecars "${dest}/maps" "${dest}/vmaps" '.vmtree')"
      [[ -z "$missing" ]] || { EXTRACT_GAP="incomplete continent vmaps: $(_extract_gap_list "$missing")"; return 1; }
      n="$(find "${dest}/vmaps" -type f 2>/dev/null | wc -l)"; n="${n// /}"
      [[ "${n:-0}" -gt 0 ]] || { EXTRACT_GAP="no vmaps"; return 1; }
      ;;
    */mmaps)
      missing="$(extract_missing_continent_sidecars "${dest}/maps" "${dest}/mmaps" '.mmap')"
      [[ -z "$missing" ]] || { EXTRACT_GAP="incomplete continent mmaps: $(_extract_gap_list "$missing")"; return 1; }
      n="$(_extract_count "${dest}/mmaps" '*.mmtile')"; n="${n// /}"
      [[ "${n:-0}" -gt 0 ]] || { EXTRACT_GAP="no mmtile"; return 1; }
      ;;
    *) return 1 ;;
  esac
  return 0
}
