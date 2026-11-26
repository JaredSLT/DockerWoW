#!/usr/bin/env bash
# Public upstreams for cores and CMaNGOS world databases.
# key|url|ref|kind   kind is branch or tag.
#
# TrinityCore master is Midnight. BFA, Shadowlands, Dragonflight, and War
# Within keep the last-known full TDB tag here as the fallback pin. Legion's
# pin is tag 7.3.5/26972. Wrath Classic's pin is branch 3.4.3. release_pair.py
# advances a frozen core only when the same database tag exists on this repo.
# Dragonflight's pin is TDB1027.24051, not client build 55664.
# Legion is TrinityCore tag 7.3.5/26972 (the 2018 tree patch_trinitycore_legion
# builds). The Legion Preservation Project branch 7.3.5 is a different codebase.
#
# shellcheck shell=bash

repo_lines() {
  cat <<'EOF'
alpha-core|https://github.com/The-Alpha-Project/alpha-core.git|master|branch
cmangos-classic|https://github.com/cmangos/mangos-classic.git|master|branch
cmangos-tbc|https://github.com/cmangos/mangos-tbc.git|master|branch
azerothcore-wotlk|https://github.com/azerothcore/azerothcore-wotlk.git|master|branch
The-Cataclysm-Preservation-Project|https://github.com/The-Cataclysm-Preservation-Project/TrinityCore.git|master|branch
SkyFire_548|https://github.com/ProjectSkyfire/SkyFire_548.git|main|branch
WodCore-Reforged|https://github.com/den13501/WodCore-Reforged.git|reforged|branch
TrinityCore-Legion|https://github.com/TrinityCore/TrinityCore.git|7.3.5/26972|tag
TrinityCore-BFA|https://github.com/TrinityCore/TrinityCore.git|TDB837.20101|tag
TrinityCore-Shadowlands|https://github.com/TrinityCore/TrinityCore.git|TDB927.22111|tag
TrinityCore-Dragonflight|https://github.com/TrinityCore/TrinityCore.git|TDB1027.24051|tag
TrinityCore-WarWithin|https://github.com/TrinityCore/TrinityCore.git|TDB1127.26011|tag
TrinityCore|https://github.com/TrinityCore/TrinityCore.git|master|branch
cmangos-classic-db|https://github.com/cmangos/classic-db.git|master|branch
cmangos-tbc-db|https://github.com/cmangos/tbc-db.git|master|branch
vmangos|https://github.com/vmangos/core.git|development|branch
vmangos-playerbots|https://github.com/ileboii/core.git|vmangos-ike3-playerbots|branch
cmangos-wotlk|https://github.com/cmangos/mangos-wotlk.git|master|branch
cmangos-wotlk-db|https://github.com/cmangos/wotlk-db.git|master|branch
TrinityCore-335|https://github.com/TrinityCore/TrinityCore.git|3.3.5|branch
mangosthree|https://github.com/mangosthree/server.git|master|branch
mangosthree-database|https://github.com/mangosthree/database.git|master|branch
TrinityCore-Cata-Classic|https://github.com/TrinityCore/TrinityCore.git|cata_classic|branch
TrinityCore-Legion-Preservation|https://github.com/The-Legion-Preservation-Project/TrinityCore.git|7.3.5|branch
cmangos-playerbots|https://github.com/cmangos/playerbots.git|master|branch
TrinityCore-Classic|https://github.com/TrinityCoreClassic/core.git|vanilla_classic|branch
TrinityCore-WotLK-Classic|https://github.com/TrinityCoreLegacy/TrinityCore.git|3.4.3|branch
RustyCore|https://github.com/alseif0x/rustycore.git|3.4.3|branch
EOF
}

# Sets REPO_URL, REPO_REF, REPO_KIND. Returns 1 when the key is unknown.
repo_lookup() {
  local key="$1" line
  REPO_URL=""
  REPO_REF=""
  REPO_KIND=""
  line="$(repo_lines | awk -F'|' -v k="$key" '$1==k {print; found=1} END{exit !found}')" || return 1
  IFS='|' read -r _ REPO_URL REPO_REF REPO_KIND <<<"$line"
  [[ -n "$REPO_URL" && -n "$REPO_REF" && -n "$REPO_KIND" ]]
}

# Print the commit SHA for url+ref. Annotated tags use the peeled commit.
# A GitHub token is passed with GIT_CONFIG_* so it is not on the git argv
# and is never written into the repo. 403 and 429 are retried three times.
repo_sha() {
  local url="$1" ref="$2" kind="$3"
  local pattern sha name peeled="" plain=""
  local token attempt errfile rc=1
  if [[ "$kind" == "tag" ]]; then
    pattern="refs/tags/${ref}"
  else
    pattern="refs/heads/${ref}"
  fi
  token="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
  errfile="$(mktemp)"
  for attempt in 1 2 3 4; do
    if [[ -n "$token" ]]; then
      if GIT_TERMINAL_PROMPT=0 \
        GIT_CONFIG_COUNT=1 \
        GIT_CONFIG_KEY_0=http.extraheader \
        GIT_CONFIG_VALUE_0="Authorization: Bearer ${token}" \
        git ls-remote "$url" "$pattern" >"${errfile}.out" 2>"$errfile"
      then
        rc=0
      else
        rc=$?
      fi
    else
      if GIT_TERMINAL_PROMPT=0 git ls-remote "$url" "$pattern" >"${errfile}.out" 2>"$errfile"
      then
        rc=0
      else
        rc=$?
      fi
    fi
    if [[ "$rc" -eq 0 ]]; then
      break
    fi
    if [[ "$attempt" -lt 4 ]] && grep -Eq '403|429' "$errfile"; then
      sleep 1
      continue
    fi
    rm -f "$errfile" "${errfile}.out"
    return 1
  done
  peeled=""
  plain=""
  while IFS=$'\t' read -r sha name; do
    [[ -n "$sha" ]] || continue
    if [[ "$name" == *'^{}' ]]; then
      peeled="$sha"
    else
      plain="$sha"
    fi
  done <"${errfile}.out"
  rm -f "$errfile" "${errfile}.out"
  sha="${peeled:-$plain}"
  [[ -n "$sha" ]] || return 1
  printf '%s' "$sha"
}

repo_sha_for() {
  repo_lookup "$1" || return 1
  repo_sha "$REPO_URL" "$REPO_REF" "$REPO_KIND"
}

# Remember the revision that was compiled and installed. .built is the
# last successful build. .core stays in step so a later poll does not
# rebuild the same revision again.
record_built_rev() {
  local short="$1" value="$2"
  local state_dir="${WOW_STATE_DIR:-${ROOT}/.run/git-revs}"
  [[ -n "$short" && -n "$value" ]] || return 1
  mkdir -p "$state_dir"
  printf '%s\n' "$value" >"${state_dir}/${short}.built.tmp"
  mv "${state_dir}/${short}.built.tmp" "${state_dir}/${short}.built"
  printf '%s\n' "$value" >"${state_dir}/${short}.core.tmp"
  mv "${state_dir}/${short}.core.tmp" "${state_dir}/${short}.core"
}
