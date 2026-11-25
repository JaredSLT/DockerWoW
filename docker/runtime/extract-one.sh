#!/usr/bin/env bash
# extract-one.sh — run inside the core image (or on the host) for one expansion.
# Required env: WOW_SHORT WOW_KIND CLIENT DEST
# Optional: STEPS (maps,vmaps,mmaps[,harvest]) JOBS FORCE CLEAN CORE_NAME
#
# Every extracted tree (dbc/maps/vmaps/mmaps/cameras/gt, or alpha etc/maps)
# is written into DEST — the servers/<short> folder mounted at /opt/wow —
# so worldserver/mangosd DataDir="." finds it on launch.
set -euo pipefail

SHORT="${WOW_SHORT:?}"
KIND="${WOW_KIND:?}"
CLIENT="${CLIENT:?}"
DEST="${DEST:?}"
CORE_NAME="${CORE_NAME:-}"
STEPS="${STEPS:-maps,vmaps,mmaps}"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 4)}"
FORCE="${FORCE:-0}"
CLEAN="${CLEAN:-0}"
KEEP_BUILDINGS="${KEEP_BUILDINGS:-0}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${HERE}/catalog.sh"

log()  { printf '==> [%s] %s\n' "$SHORT" "$*"; }
warn() { printf 'WARNING: [%s] %s\n' "$SHORT" "$*" >&2; }
die()  { printf 'ERROR: [%s] %s\n' "$SHORT" "$*" >&2; exit 1; }

want() {
  [[ ",${STEPS}," == *",$1,"* ]]
}

# vmap4extractor / mapextractor look for Data/enUS. Some clients only ship enGB.
ensure_extractor_locale() {
  local data="${CLIENT}/Data"
  [[ -d "$data" ]] || return 0
  [[ -d "${data}/enUS" || -L "${data}/enUS" ]] && return 0
  local loc
  for loc in enGB enCN deDE frFR esES esMX ruRU koKR zhCN zhTW ptBR; do
    if [[ -d "${data}/${loc}" ]]; then
      ln -sfn "$loc" "${data}/enUS"
      log "Linked Data/enUS -> Data/${loc} so extractors find locale MPQs"
      return 0
    fi
  done
}

count_files() {
  local dir="$1" pat="$2"
  [[ -d "$dir" ]] || { echo 0; return; }
  find -H "$dir" -type f -name "$pat" 2>/dev/null | wc -l
}

dir_file_count() {
  local dir="$1"
  [[ -d "$dir" ]] || { echo 0; return; }
  find -H "$dir" -type f 2>/dev/null | wc -l
}

skip_if_present() {
  local label="$1" dir="$2" pat="$3"
  [[ "$FORCE" -eq 1 ]] && return 1
  local n
  n="$(count_files "$dir" "$pat")"
  if [[ "$n" -gt 0 ]]; then
    log "Skip ${label} (${n} ${pat} already in ${dir#"$DEST"/})"
    return 0
  fi
  return 1
}

wipe_step_tree() {
  local step="$1" d
  local dirs=()
  case "$KIND/$step" in
    alpha/maps) dirs=(etc/maps etc/mdx etc/wmo_liquids etc/wmo_geometry) ;;
    alpha/navs|alpha/vmaps|alpha/mmaps) dirs=(etc/navs) ;;
    */maps) dirs=(maps dbc cameras Cameras gt) ;;
    */vmaps) dirs=(vmaps Buildings) ;;
    */mmaps) dirs=(mmaps) ;;
  esac
  for d in "${dirs[@]}"; do
    [[ -e "${DEST}/${d}" || -L "${DEST}/${d}" ]] || continue
    rm -rf "${DEST:?}/${d}"
    log "  removed ${d}/"
  done
  # Tools such as MoveMapGen refuse to start if their output dir is missing.
  case "$KIND/$step" in
    alpha/maps) mkdir -p "${DEST}/etc/maps" ;;
    alpha/navs|alpha/vmaps|alpha/mmaps) mkdir -p "${DEST}/etc/navs" ;;
    */maps) mkdir -p "${DEST}/maps" "${DEST}/dbc" ;;
    */vmaps) mkdir -p "${DEST}/vmaps" ;;
    */mmaps) mkdir -p "${DEST}/mmaps" ;;
  esac
}

# Skip a complete step. Incomplete leftover data is deleted and the step re-runs.
skip_complete_step() {
  local step="$1"
  if [[ "$FORCE" -eq 1 ]]; then
    log "Force ${step}: deleting previous extract output"
    wipe_step_tree "$step"
    return 1
  fi
  if extract_step_complete "$DEST" "$KIND" "$step"; then
    log "Skip ${step} (complete)"
    return 0
  fi
  if [[ -n "${EXTRACT_GAP:-}" ]]; then
    log "Incomplete ${step} (${EXTRACT_GAP}) — deleting it and extracting again"
    wipe_step_tree "$step"
  fi
  return 1
}

find_tool() {
  local name="$1" p
  local candidates=("${DEST}/bin/${name}" "${DEST}/bin/tools/${name}")
  if [[ -n "$CORE_NAME" ]]; then
    candidates+=(
      "/servers/${CORE_NAME}/bin/${name}"
      "/servers/${CORE_NAME}/bin/tools/${name}"
    )
  fi
  for p in "${candidates[@]}"; do
    [[ -x "$p" ]] && { printf '%s' "$p"; return 0; }
  done
  return 1
}

need_tool() {
  local name="$1" path
  path="$(find_tool "$name")" || die "Missing extractor: ${name}"
  printf '%s' "$path"
}

run() {
  log "+ $*"
  "$@"
}

# True if dir looks like extractor output (not a stock client folder).
is_extract_tree() {
  local dir="$1" name="$2"
  [[ -d "$dir" ]] || return 1
  case "$name" in
    maps)     [[ "$(count_files "$dir" '*.map')" -gt 0 ]] ;;
    dbc)      [[ "$(count_files "$dir" '*.dbc')" -gt 0 || "$(count_files "$dir" '*.db2')" -gt 0 ]] ;;
    cameras|Cameras) [[ "$(dir_file_count "$dir")" -gt 0 ]] ;;
    gt)       [[ "$(dir_file_count "$dir")" -gt 0 ]] ;;
    vmaps)    [[ "$(dir_file_count "$dir")" -gt 0 ]] ;;
    mmaps)    [[ "$(count_files "$dir" '*.mmtile')" -gt 0 || "$(count_files "$dir" '*.mmap')" -gt 0 ]] ;;
    Buildings) [[ "$(dir_file_count "$dir")" -gt 0 ]] ;;
    *)        return 1 ;;
  esac
}

same_path() {
  local a b
  a="$(readlink -f "$1" 2>/dev/null || printf '%s' "$1")"
  b="$(readlink -f "$2" 2>/dev/null || printf '%s' "$2")"
  [[ "$a" == "$b" ]]
}

# Move src → dest. If dest already has extract files, leave src alone.
place_extract_dir() {
  local src="$1" dest="$2" label="$3"
  [[ -d "$src" ]] || return 0
  if same_path "$src" "$dest"; then
    return 0
  fi
  if [[ -d "$dest" ]] && [[ "$(dir_file_count "$dest")" -gt 0 ]]; then
    return 0
  fi
  log "Placing ${label} into server folder (${src} -> ${dest})"
  mkdir -p "$(dirname "$dest")"
  if [[ -d "$dest" ]]; then
    rmdir "$dest" 2>/dev/null || rm -rf "$dest"
  fi
  if mv "$src" "$dest" 2>/dev/null; then
    return 0
  fi
  mkdir -p "$dest"
  cp -a "${src}/." "$dest/"
  rm -rf "$src"
}

# Pull extractor output out of the client / tool dirs and into DEST.
# Tools that ignore -o write next to the client or CWD; the server reads DEST.
harvest_stray_output() {
  [[ "$KIND" == "alpha" ]] && return 0
  local root name src
  local roots=("$CLIENT" "${DEST}/bin" "${DEST}/bin/tools")
  case "$(basename "$CLIENT")" in
    _retail_|_classic_|_beta_|_xptr_|"World of Warcraft")
      roots+=("$(dirname "$CLIENT")")
      ;;
  esac
  # Also check CWD if extractors were invoked from somewhere else.
  roots+=("$(pwd)")

  local seen="" r
  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    r="$(readlink -f "$root" 2>/dev/null || printf '%s' "$root")"
    [[ "$seen" == *"|$r|"* ]] && continue
    seen+="|$r|"
    same_path "$root" "$DEST" && continue
    for name in maps dbc cameras Cameras gt vmaps mmaps Buildings; do
      src="${root}/${name}"
      is_extract_tree "$src" "$name" || continue
      place_extract_dir "$src" "${DEST}/${name}" "$name/"
    done
  done
}

# Drop an empty placeholder dir so a case-alias symlink can take its place.
remove_empty_dir() {
  local dir="$1"
  [[ -d "$dir" && ! -L "$dir" && "$(dir_file_count "$dir")" -eq 0 ]] || return 1
  rmdir "$dir" 2>/dev/null
}

# CMaNGOS looks for Cameras/; Trinity/AC/SkyFire look for cameras/.
# Trinity-family cores also prefer dbc/<locale>/ over a flat dbc/*.dbc.
normalize_data_layout() {
  [[ "$KIND" == "alpha" ]] && return 0
  remove_empty_dir "${DEST}/cameras" || true
  remove_empty_dir "${DEST}/Cameras" || true
  if [[ -d "${DEST}/Cameras" && ! -e "${DEST}/cameras" ]]; then
    ln -s Cameras "${DEST}/cameras"
    log "Linked cameras -> Cameras (Trinity-style DataDir)"
  elif [[ -d "${DEST}/cameras" && ! -e "${DEST}/Cameras" ]]; then
    ln -s cameras "${DEST}/Cameras"
    log "Linked Cameras -> cameras (CMaNGOS-style DataDir)"
  fi

  if [[ "$KIND" == "azerothcore" || "$KIND" == "skyfire" ]] && [[ -d "${DEST}/dbc" ]]; then
    local locale locname f
    for locale in "${DEST}/dbc"/enUS "${DEST}/dbc"/enGB; do
      [[ -d "$locale" ]] || continue
      locname="$(basename "$locale")"
      (
        cd "${DEST}/dbc"
        find "$locname" -maxdepth 1 -type f \( -name '*.dbc' -o -name '*.db2' \) | while read -r f; do
          ln -sfn "$f" "$(basename "$f")"
        done
      )
      mkdir -p "${DEST}/gt"
      (
        cd "${DEST}/gt"
        find "../dbc/${locname}" -maxdepth 1 -type f -name 'gt*.dbc' | while read -r f; do
          ln -sfn "$f" "$(basename "$f")"
        done
      )
      log "Linked DBC/gt files from dbc/${locname} for AzerothCore DataDir"
    done
  elif [[ "$KIND" != "cmangos" && -d "${DEST}/dbc" ]]; then
    local top_dbc locale_dirs locale locname f
    top_dbc="$(find "${DEST}/dbc" -maxdepth 1 -type f \( -name '*.dbc' -o -name '*.db2' \) | wc -l)"
    locale_dirs="$(find "${DEST}/dbc" -mindepth 1 -maxdepth 1 -type d | wc -l)"
    if [[ "$top_dbc" -gt 0 && "$locale_dirs" -eq 0 ]]; then
      mkdir -p "${DEST}/dbc/enUS"
      find "${DEST}/dbc" -maxdepth 1 -type f \( -name '*.dbc' -o -name '*.db2' \) -exec mv -t "${DEST}/dbc/enUS" {} +
      log "Moved ${top_dbc} DBC files into dbc/enUS/ (server locale path)"
    fi
    # Firestorm/WoD LoadDBCStores looks in DataDir/dbc/*.dbc (not dbc/<locale>/).
    # Extractors write dbc/frFR when the client has no enUS MPQ.
    # Do not flatten for modern Trinity: mmaps_generator treats dbc/*.db2 as
    # locale dirs and then opens dbc/SomeFile.db2/LiquidType.db2.
    if [[ "$SHORT" == "wod" ]]; then
      if [[ ! -e "${DEST}/dbc/enUS" ]]; then
        for locale in "${DEST}/dbc"/enGB "${DEST}/dbc"/frFR "${DEST}/dbc"/deDE "${DEST}/dbc"/esES; do
          if [[ -d "$locale" ]]; then
            ln -sfn "$(basename "$locale")" "${DEST}/dbc/enUS"
            log "Linked dbc/enUS -> dbc/$(basename "$locale")"
            break
          fi
        done
      fi
      if [[ -d "${DEST}/dbc/enUS" || -L "${DEST}/dbc/enUS" ]]; then
        (
          cd "${DEST}/dbc"
          find -L enUS -maxdepth 1 -type f \( -name '*.dbc' -o -name '*.db2' \) | while read -r f; do
            [[ -e "$(basename "$f")" ]] && continue
            ln -sfn "$f" "$(basename "$f")"
          done
        )
      fi
    fi
  fi
}

summarize_dest() {
  log "Server data dir: ${DEST}"
  if [[ "$KIND" == "alpha" ]]; then
    log "  etc/maps: $(count_files "${DEST}/etc/maps" '*.map') .map"
    log "  etc/navs: $(count_files "${DEST}/etc/navs" '*.nav') .nav"
    return 0
  fi
  log "  maps:    $(count_files "${DEST}/maps" '*.map') .map"
  log "  dbc:     $(count_files "${DEST}/dbc" '*') files"
  log "  vmaps:   $(dir_file_count "${DEST}/vmaps") files"
  log "  mmaps:   $(dir_file_count "${DEST}/mmaps") files"
  log "  cameras: $(dir_file_count "${DEST}/cameras") files"
  log "  gt:      $(dir_file_count "${DEST}/gt") files"
}

wipe_here() {
  local d
  local dirs=()
  if [[ "$KIND" == "alpha" ]]; then
    want maps && dirs+=(etc/maps etc/mdx etc/wmo_liquids etc/wmo_geometry)
    { want vmaps || want mmaps; } && dirs+=(etc/navs)
  else
    want maps && dirs+=(maps dbc cameras Cameras gt)
    want vmaps && dirs+=(vmaps Buildings)
    want mmaps && dirs+=(mmaps)
  fi
  [[ ${#dirs[@]} -gt 0 ]] || return 0
  log "Removing previous extract data so it can be regenerated"
  for d in "${dirs[@]}"; do
    [[ -n "$d" ]] || continue
    [[ -e "${DEST}/${d}" || -L "${DEST}/${d}" ]] || continue
    rm -rf "${DEST:?}/${d}"
    log "  removed ${d}/"
  done
}

# Do not wipe on harvest-only — that path only relocates leftovers.
if [[ "$CLEAN" -eq 1 && "$STEPS" != "harvest" ]]; then
  wipe_here
fi

mkdir -p "${DEST}/logs"
# Run extractors from DEST so tools that only write to CWD land in the server folder.
cd "$DEST"

[[ -d "${DEST}/lib" ]] && export LD_LIBRARY_PATH="${DEST}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [[ -n "$CORE_NAME" && -d "/servers/${CORE_NAME}/lib" ]]; then
  export LD_LIBRARY_PATH="${DEST}/lib:/servers/${CORE_NAME}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

[[ -d "${CLIENT}/Data" || -d "${CLIENT}/data" ]] || die "Client has no Data/: ${CLIENT}"

LOG="${DEST}/logs/extract-${SHORT}.log"
: >>"$LOG"
exec > >(tee -a "$LOG") 2>&1

log "kind=${KIND} client=${CLIENT} dest=${DEST} steps=${STEPS} jobs=${JOBS}"
log "Writing extract data into the server folder (${DEST})"

harvest_stray_output
normalize_data_layout

if [[ "$STEPS" == "harvest" ]]; then
  summarize_dest
  log "Finished (harvest only)"
  exit 0
fi

# Determine the correct client root for extractors.
# MPQ clients (vanilla → mop): $CLIENT is the wow root, Data/ contains .mpq files.
# CASC clients (wod → retail): $CLIENT is the wow root, but CASC storage lives
# in $CLIENT/Data/ (with subdirs data/, indices/, config/).  mapextractor and
# vmap4extractor need the CASC root ($CLIENT/Data), not the wow root.
# Copied CASC trees often lack .build.info. CascLib needs it beside Data/.
ensure_casc_build_info() {
  local client="$1"
  local info="${client}/.build.info"
  [[ -f "$info" ]] && return 0
  [[ -d "${client}/Data/config" ]] || return 0
  local build_key="" cdn_key="" ver="0.0.0.0" f header
  while IFS= read -r f; do
    header="$(head -1 "$f" 2>/dev/null | tr -d '\r' || true)"
    if [[ "$header" == "# Build Configuration" && -z "$build_key" ]]; then
      build_key="$(basename "$f")"
      ver="$(tr -d '\r' <"$f" | awk -F' = ' '/^build-name /{print $2; exit}')"
      ver="${ver#WOW-}"
      ver="${ver%%_*}"
    elif [[ "$header" == "# CDN Configuration" && -z "$cdn_key" ]]; then
      cdn_key="$(basename "$f")"
    fi
  done < <(find "${client}/Data/config" -type f)
  [[ -n "$build_key" && -n "$cdn_key" ]] || return 0
  # Version field like 8.3.7.35662 if we can parse WOW-35662patch8.3.7
  if [[ "$ver" == *patch* ]]; then
    local buildnum="${ver%%patch*}"
    local patch="${ver#*patch}"
    ver="${patch}.${buildnum}"
  fi
  printf '%s\n%s\n' \
    'Branch!STRING:0|Active!DEC:1|Build Key!HEX:16|CDN Key!HEX:16|Install Key!HEX:16|IM Size!DEC:4|CDN Path!STRING:0|CDN Hosts!STRING:0|Tags!STRING:0|Armadillo!STRING:0|Last Activated!STRING:0|Version!STRING:0' \
    "us|1|${build_key}|${cdn_key}|||tpr/wow||||2020-01-01T00:00:00Z|${ver}" \
    >"$info"
  log "Wrote ${info} (build=${build_key} cdn=${cdn_key} ver=${ver})"
}

casc_client_root() {
  local client="$1"
  # CASC structure: Data/ contains data/ indices/ config/ (no .mpq files)
  if [[ -d "${client}/Data" ]] && \
     [[ -d "${client}/Data/data" || -d "${client}/Data/indices" || -d "${client}/Data/config" ]] && \
     [[ ! -f "${client}/Data/common.MPQ" && ! -f "${client}/Data/expansion.MPQ" ]]; then
    printf '%s' "${client}/Data"
    return 0
  fi
  # MPQ structure: Data/ contains .mpq files directly
  if [[ -d "${client}/Data" ]]; then
    printf '%s' "${client}"
    return 0
  fi
  return 1
}

extract_maps_cmangos() {
  skip_complete_step maps && return 0
  local ad
  ad="$(need_tool ad)"
  (cd "$DEST" && run "$ad" -i "$CLIENT" -o "$DEST")
  harvest_stray_output
}

extract_maps_trinityish() {
  skip_complete_step maps && return 0
  local bin
  if bin="$(find_tool mapextractor)"; then
    :
  elif bin="$(find_tool map_extractor)"; then
    :
  else
    die "No mapextractor / map_extractor"
  fi
  ensure_casc_build_info "$CLIENT"
  # Trinity BfA+ does CascOpenStorage(input/Data). Passing Data/ becomes Data/Data.
  local input_path="$CLIENT"
  local extra=()
  if [[ -f "${CLIENT}/.build.info" ]]; then
    extra+=(-l enUS)
  fi
  (cd "$DEST" && run "$bin" -i "$input_path" -o "$DEST" "${extra[@]}")
  harvest_stray_output
}

extract_vmaps_cmangos() {
  skip_complete_step vmaps && return 0
  local ext asm
  ext="$(need_tool vmap_extractor)"
  asm="$(need_tool vmap_assembler)"
  (cd "$DEST" && run "$ext" -d "${CLIENT}/Data" -o "$DEST")
  mkdir -p "${DEST}/vmaps"
  (cd "$DEST" && run "$asm" "${DEST}/Buildings" "${DEST}/vmaps")
  harvest_stray_output
}

extract_vmaps_modern() {
  skip_complete_step vmaps && return 0
  local ext asm data_arg
  if ext="$(find_tool vmap4extractor)"; then
    :
  elif ext="$(find_tool vmap4_extractor)"; then
    :
  else
    die "No vmap4extractor / vmap4_extractor"
  fi
  if asm="$(find_tool vmap4assembler)"; then
    :
  elif asm="$(find_tool vmap4_assembler)"; then
    :
  else
    die "No vmap4assembler / vmap4_assembler"
  fi
  # Trinity/TCPP: -d is wow root ($input/Data/*.MPQ).
  # AzerothCore and SkyFire: -d is the Data directory ($input/world.MPQ).
  # SkyFire 5.4.8 also has Data/misc.MPQ; ReadLiquidType.dbc opens that first
  # and dies because LiquidType.dbc lives in patched locale MPQs.
  local vmap_dir misc aside=""
  if [[ "$KIND" == "trinity" ]]; then
    vmap_dir="$CLIENT"
  else
    vmap_dir="${CLIENT}/Data"
  fi
  [[ -d "${CLIENT}/Data" ]] || die "vmap4extractor: no ${CLIENT}/Data"
  # WodCore vmap4extractor ignores -d and CascOpenStorage("./Data") from cwd.
  ensure_casc_build_info "$CLIENT"
  if casc_root="$(casc_client_root "$CLIENT")"; then
    ln -sfn "$casc_root" "${DEST}/Data"
    [[ -f "${CLIENT}/.build.info" ]] && ln -sfn "${CLIENT}/.build.info" "${DEST}/.build.info"
    log "Linked CASC Data + .build.info into dest for vmap4extractor"
  fi
  restore_misc() {
    if [[ -n "$aside" && -f "$aside" ]]; then
      mv "$aside" "${CLIENT}/Data/misc.MPQ"
      aside=""
    fi
  }
  if [[ "$KIND" == "skyfire" ]]; then
    misc="${CLIENT}/Data/misc.MPQ"
    if [[ -f "$misc" ]]; then
      aside="${misc}.wow-lab-aside"
      mv "$misc" "$aside"
      log "Moved Data/misc.MPQ aside so SkyFire vmap4extractor uses locale MPQs"
    fi
  fi
  if (cd "$DEST" && run "$ext" -d "$vmap_dir"); then
    restore_misc
  else
    restore_misc
    return 1
  fi
  mkdir -p "${DEST}/vmaps"
  (cd "$DEST" && run "$asm" Buildings vmaps)
  harvest_stray_output
}

extract_mmaps_cmangos() {
  skip_complete_step mmaps && return 0
  mkdir -p "${DEST}/mmaps"
  local gen cfg off
  gen="$(need_tool MoveMapGen)"
  cfg="$(dirname "$gen")/config.json"
  off="$(dirname "$gen")/offmesh.txt"
  local args=(--silent --threads "$JOBS" --workdir "$DEST")
  [[ -f "$cfg" ]] && args+=(--configInputPath "$cfg")
  [[ -f "$off" ]] && args+=(--offMeshInput "$off")
  (cd "$DEST" && run "$gen" "${args[@]}")
  harvest_stray_output
}

extract_mmaps_modern() {
  skip_complete_step mmaps && return 0
  mkdir -p "${DEST}/mmaps"
  local gen
  gen="$(need_tool mmaps_generator)"
  if [[ "$KIND" == "azerothcore" ]]; then
    local cfg="${DEST}/bin/mmaps-config.yaml"
    [[ -f "$cfg" ]] || cfg="$(dirname "$gen")/mmaps-config.yaml"
    (cd "$DEST" && run "$gen" --silent --threads "$JOBS" ${cfg:+--config "$cfg"})
  else
    (cd "$DEST" && run "$gen" --silent --threads "$JOBS")
  fi
  harvest_stray_output
}

extract_alpha() {
  mkdir -p "${DEST}/etc/maps" "${DEST}/etc/navs" "${DEST}/etc/config"
  local py="" cfg="${DEST}/etc/config/config.yml"
  [[ -f "${cfg}.dist" && ! -f "$cfg" ]] && cp "${cfg}.dist" "$cfg"
  [[ -f "$cfg" ]] || die "alpha config.yml missing"
  export WOW_ROOT="${DEST}"
  export WOW_SHORT="${SHORT}"
  export WOW_KIND="${KIND}"
  export MYSQL_HOST="${MYSQL_HOST:-db}"
  export MYSQL_PORT="${MYSQL_PORT:-3306}"
  export MYSQL_USER="${MYSQL_USER:-wow}"
  export MYSQL_PASSWORD="${MYSQL_PASSWORD:-wow}"
  python3 "${HERE}/gen-config.py"

  if [[ -x /servers/alpha-core/.venv/bin/python ]]; then
    py=/servers/alpha-core/.venv/bin/python
  elif [[ -x "${DEST}/.venv/bin/python" ]]; then
    py="${DEST}/.venv/bin/python"
  else
    py="$(command -v python3 || true)"
  fi
  [[ -n "$py" ]] || die "No python for alpha extractors"

  python3 - "$cfg" "$CLIENT" <<'PY'
import pathlib, re, sys
path, client = pathlib.Path(sys.argv[1]), sys.argv[2]
text = path.read_text(encoding="utf-8", errors="replace")
if re.search(r"wow_root_path:", text):
    text = re.sub(r"(wow_root_path:\s*).*", rf"\1'{client}'", text, count=1)
else:
    text += f"\nExtractor:\n    Maps:\n        wow_root_path: '{client}'\n"
path.write_text(text, encoding="utf-8")
print(f"==> set Extractor.Maps.wow_root_path = {client}")
PY

  local do_maps=0 do_navs=0
  want maps && do_maps=1
  { want vmaps || want mmaps; } && do_navs=1

  if [[ "$do_maps" -eq 1 ]] && skip_complete_step maps; then
    do_maps=0
  fi
  if [[ "$do_navs" -eq 1 ]] && skip_complete_step navs; then
    do_navs=0
  fi
  [[ "$do_maps$do_navs" == "00" ]] && return 0

  local answers=""
  [[ "$do_maps" -eq 1 ]] && answers+="y\n" || answers+="n\n"
  # MapExtractor asks to delete existing .map files when the dir is not empty.
  if [[ "$do_maps" -eq 1 ]] && [[ "$(count_files "${DEST}/etc/maps" '*.map')" -gt 0 ]]; then
    answers+="y\n"
  fi
  [[ "$do_navs" -eq 1 ]] && answers+="y\n" || answers+="n\n"
  # NavExtractor: "Number of threads? [1-N]"
  if [[ "$do_navs" -eq 1 ]]; then
    answers+="${JOBS}\n"
  fi
  log "Running alpha main.py -e (maps=${do_maps} navs=${do_navs} jobs=${JOBS})"
  (cd "$DEST" && printf '%b' "$answers" | "$py" "${DEST}/main.py" -e)
}

if [[ "$KIND" == "alpha" ]]; then
  extract_alpha
else
  ensure_extractor_locale
  if want maps; then
    log "Extracting DBC / maps / cameras / gt into ${DEST}"
    if [[ "$KIND" == "cmangos" ]]; then
      extract_maps_cmangos
    else
      extract_maps_trinityish
    fi
    harvest_stray_output
    normalize_data_layout
    log "maps done ($(count_files "${DEST}/maps" '*.map') .map, $(count_files "${DEST}/dbc" '*' ) dbc)"
  fi
  if want vmaps; then
    log "Extracting vmaps into ${DEST}/vmaps"
    if [[ "$KIND" == "cmangos" ]]; then
      extract_vmaps_cmangos
    else
      extract_vmaps_modern
    fi
    harvest_stray_output
    log "vmaps done ($(count_files "${DEST}/vmaps" '*') files)"
  fi
  if want mmaps; then
    log "Generating mmaps into ${DEST}/mmaps (this is the slow step)"
    if [[ "$KIND" == "cmangos" ]]; then
      extract_mmaps_cmangos
    else
      extract_mmaps_modern
    fi
    harvest_stray_output
    log "mmaps done ($(count_files "${DEST}/mmaps" '*') files)"
  fi
fi

harvest_stray_output
normalize_data_layout

if [[ "$KEEP_BUILDINGS" != "1" && -d "${DEST}/Buildings" ]]; then
  # Intermediate vmap extract; assembled output lives in vmaps/.
  if want vmaps && [[ "$(count_files "${DEST}/vmaps" '*')" -gt 0 ]]; then
    rm -rf "${DEST}/Buildings"
    log "Removed intermediate Buildings/"
  fi
fi

summarize_dest

if [[ "$KIND" == "alpha" ]]; then
  if want maps && ! extract_step_complete "$DEST" "$KIND" maps; then
    die "maps still incomplete after extract: ${EXTRACT_GAP:-unknown}"
  fi
  if { want vmaps || want mmaps; } && ! extract_step_complete "$DEST" "$KIND" navs; then
    die "navs still incomplete after extract: ${EXTRACT_GAP:-unknown}"
  fi
else
  if want maps && ! extract_step_complete "$DEST" "$KIND" maps; then
    die "maps still incomplete after extract: ${EXTRACT_GAP:-unknown}"
  fi
  if want vmaps && ! extract_step_complete "$DEST" "$KIND" vmaps; then
    die "vmaps still incomplete after extract: ${EXTRACT_GAP:-unknown}"
  fi
  if want mmaps && ! extract_step_complete "$DEST" "$KIND" mmaps; then
    die "mmaps still incomplete after extract: ${EXTRACT_GAP:-unknown}"
  fi
fi
log "Finished (extract complete for requested steps)"
