#!/usr/bin/env bash
# Pin a removable WoW disk to a stable mount, or record an internal checkout
# without a second mount of that disk. Installs loopback aliases, /etc/hosts
# names, and the HAProxy config. Safe to re-run. Privileged steps re-exec
# through sudo (passwordless when that works, prompting otherwise).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST_DIR="${ROOT}/docker/runtime/host"
ENV_FILE="${ROOT}/.env"

# shellcheck disable=SC1091
source "${ROOT}/docker/runtime/catalog.sh"
# shellcheck disable=SC1091
source "${ROOT}/docker/runtime/haproxy.sh"

log()  { printf '==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

load_env() {
  if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
}

# findmnt TARGET is the filesystem that holds the repo, not a parent path
# we invent. /run/media and /media are the removable automount roots.
host_target_is_removable() {
  local target="$1"
  [[ "$target" == /run/media || "$target" == /run/media/* || "$target" == /media || "$target" == /media/* ]]
}

# MOUNT plus the repo's path relative to the filesystem that holds it.
# Never appends a fixed directory name.
host_tree_on_mount() {
  local repo="$1" target="$2" mount="$3" rel
  mount="${mount%/}"
  if [[ "$target" != "/" ]]; then
    target="${target%/}"
  fi
  if [[ "$repo" == "$target" ]]; then
    printf '%s' "$mount"
    return 0
  fi
  if [[ "$target" == "/" ]]; then
    printf '%s/%s' "$mount" "${repo#/}"
    return 0
  fi
  if [[ "$repo" != "$target"/* ]]; then
    printf '%s' "$repo"
    return 0
  fi
  rel="${repo#"$target"/}"
  printf '%s/%s' "$mount" "$rel"
}

# Classify a checkout. Sets HOST_LAYOUT, HOST_UUID, HOST_MOUNT, HOST_TREE,
# HOST_FSTYPE, and HOST_FSTAB. HOST_FSTAB is empty on an internal disk.
# The mount preference is only used for a removable disk. An internal disk
# always binds the repo root and does not write an fstab line.
# Arguments: REPO TARGET FSTYPE [UUID] [REMOVABLE_MOUNT]
host_classify_layout() {
  local repo="$1" target="$2" fstype="$3" uuid="${4:-}" mount_pref="${5-}"
  HOST_FSTYPE="$fstype"
  if host_target_is_removable "$target"; then
    HOST_LAYOUT="removable"
    HOST_UUID="$uuid"
    if [[ -n "$mount_pref" ]]; then
      HOST_MOUNT="$mount_pref"
    else
      HOST_MOUNT="/mnt/wow-nvme"
    fi
    HOST_TREE="$(host_tree_on_mount "$repo" "$target" "$HOST_MOUNT")"
    HOST_FSTAB="UUID=${HOST_UUID} ${HOST_MOUNT} ${fstype} nosuid,nodev,nofail,x-systemd.device-timeout=15s,x-systemd.before=docker.service 0 2"
  else
    HOST_LAYOUT="internal"
    # Empty unless the operator pinned a UUID. No fstab and no disk bind.
    HOST_UUID="$uuid"
    HOST_MOUNT="$repo"
    HOST_TREE="$repo"
    HOST_FSTAB=""
  fi
}

resolve_media_user() {
  if [[ -n "${WOW_MEDIA_USER:-}" ]]; then
    MEDIA_USER="$WOW_MEDIA_USER"
  elif [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
    MEDIA_USER="$SUDO_USER"
  else
    MEDIA_USER="$(stat -c '%U' "$ROOT" 2>/dev/null || true)"
    if [[ -z "$MEDIA_USER" || "$MEDIA_USER" == "root" ]]; then
      MEDIA_USER="$(id -un)"
    fi
  fi
}

uuid_mounted_at() {
  local uuid="$1" target
  target="$(findmnt -n -o TARGET -S "UUID=${uuid}" | head -n 1 || true)"
  printf '%s' "$target"
}

mount_uuid_matches() {
  local path="$1" uuid="$2" got
  mountpoint -q "$path" || return 1
  got="$(findmnt -n -o UUID "$path")"
  [[ "$got" == "$uuid" ]]
}

ensure_mount() {
  local uuid src
  uuid="$HOST_UUID"
  [[ -n "$uuid" ]] || die "Could not find the filesystem UUID for ${ROOT}"
  mkdir -p "$HOST_MOUNT"
  if mountpoint -q "$HOST_MOUNT"; then
    mount_uuid_matches "$HOST_MOUNT" "$uuid" \
      || die "${HOST_MOUNT} is already mounted with a different filesystem"
  else
    src="$(uuid_mounted_at "$uuid")"
    if [[ -n "$src" && "$src" != "$HOST_MOUNT" ]]; then
      log "Bind-mounting ${src} onto ${HOST_MOUNT}"
      mount --bind "$src" "$HOST_MOUNT"
    elif [[ -z "$src" ]]; then
      log "Mounting UUID ${uuid} onto ${HOST_MOUNT}"
      mount "UUID=${uuid}" "$HOST_MOUNT"
    fi
  fi
  mount --make-rshared "$HOST_MOUNT"
  mount_uuid_matches "$HOST_MOUNT" "$uuid" || die "${HOST_MOUNT} does not hold UUID ${uuid}"
}

write_fstab() {
  [[ -n "${HOST_FSTAB:-}" ]] || return 0
  python3 - /etc/fstab "$HOST_FSTAB" <<'PY'
import pathlib, sys
path, line = sys.argv[1], sys.argv[2]
block = f"# BEGIN wow-volume\n{line}\n# END wow-volume\n"
file = pathlib.Path(path)
text = file.read_text(encoding="utf-8", errors="replace")
start = text.find("# BEGIN wow-volume\n")
end = text.find("# END wow-volume\n")
if start != -1 and end != -1 and end > start:
    end += len("# END wow-volume\n")
    text = text[:start] + block + text[end:]
else:
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + block
file.write_text(text, encoding="utf-8")
PY
  log "fstab mounts UUID ${HOST_UUID} at ${HOST_MOUNT} (${HOST_FSTYPE}) before docker"
}

install_unit() {
  local name="$1"
  install -m 0644 "${HOST_DIR}/${name}" "/etc/systemd/system/${name}"
}

# The unit files in the repo use the default mount path. Rewrite them for
# whatever mount this removable disk actually uses.
write_mount_units() {
  local mount_unit
  mount_unit="$(systemd-escape --path --suffix=mount "$HOST_MOUNT")"
  cat > /etc/systemd/system/wow-volume-share.service <<EOF
[Unit]
Description=Share the WoW volume mount into Docker containers
After=${mount_unit}
Before=docker.service
ConditionPathIsMountPoint=${HOST_MOUNT}

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/wow-volume-share.sh

[Install]
WantedBy=docker.service
EOF
  cat > /etc/systemd/system/wow-media-alias.service <<EOF
[Unit]
Description=Bind the WoW disk onto its udisks media paths
After=${mount_unit} wow-volume-share.service
Requires=${mount_unit}

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/wow-media-alias.sh

[Install]
WantedBy=multi-user.target
EOF
  chmod 0644 /etc/systemd/system/wow-volume-share.service /etc/systemd/system/wow-media-alias.service
}

install_haproxy_cfg() {
  local cfg="$1" dest="/etc/wow/haproxy.cfg"
  if [[ -d "$dest" ]]; then
    if [[ -n "$(ls -A "$dest")" ]]; then
      die "${dest} is a directory and is not empty"
    fi
    rmdir "$dest"
  fi
  install -m 0644 "$cfg" "$dest"
}

install_scripts() {
  install -d -m 0755 /etc/wow /usr/local/sbin
  install -m 0755 "${HOST_DIR}/wow-loopback.sh" /usr/local/sbin/wow-loopback.sh
  install -m 0755 "${HOST_DIR}/wow-volume-share.sh" /usr/local/sbin/wow-volume-share.sh
  install -m 0755 "${HOST_DIR}/wow-media-alias.sh" /usr/local/sbin/wow-media-alias.sh
  install -m 0755 "${HOST_DIR}/wow-git-update.sh" /usr/local/sbin/wow-git-update.sh
  install -m 0755 "${HOST_DIR}/wow-backup.sh" /usr/local/sbin/wow-backup.sh
  install -m 0755 "${HOST_DIR}/wow-realms.sh" /usr/local/sbin/wow-realms.sh
}

write_volume_env() {
  cat > /etc/wow/volume.env <<EOF
WOW_VOLUME_UUID=${HOST_UUID}
WOW_VOLUME_MOUNT=${HOST_MOUNT}
WOW_TREE=${HOST_TREE}
WOW_MEDIA_USER=${MEDIA_USER}
EOF
  chmod 0644 /etc/wow/volume.env
}

write_loopback_ips() {
  local ips short
  ips="$(mktemp)"
  while IFS= read -r short; do
    catalog_load "$short"
    printf '%s\n' "$CATALOG_LOOPBACK"
  done < <(catalog_shorts) >"$ips"
  install -m 0644 "$ips" /etc/wow/loopback.ips
  rm -f "$ips"
}

write_haproxy() {
  local cfg
  cfg="$(mktemp)"
  haproxy_render "$cfg"
  install_haproxy_cfg "$cfg"
  mkdir -p "${ROOT}/.run"
  install -m 0644 "$cfg" "${ROOT}/.run/haproxy.cfg"
  rm -f "$cfg"
}

install_systemd_units() {
  install_unit wow-loopback.service
  install_unit wow-git-update.service
  install_unit wow-git-update.timer
  install_unit wow-backup.service
  install_unit wow-realms.service
  write_backup_timer
  if [[ "$HOST_LAYOUT" == "removable" ]]; then
    write_mount_units
  fi
}

write_hosts() {
  local tmp short
  tmp="$(mktemp)"
  {
    echo "# BEGIN wow-realms"
    while IFS= read -r short; do
      catalog_load "$short"
      # Public DNS names stay out of this file. Only the loopback names belong here.
      printf '%s %s.local\n' "$CATALOG_LOOPBACK" "$short"
    done < <(catalog_shorts)
    echo "# END wow-realms"
  } >"$tmp"
  python3 - /etc/hosts "$tmp" <<'PY'
import pathlib, sys
hosts = pathlib.Path(sys.argv[1])
block = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8")
if not block.endswith("\n"):
    block += "\n"
text = hosts.read_text(encoding="utf-8", errors="replace")
start = text.find("# BEGIN wow-realms\n")
end = text.find("# END wow-realms\n")
if start != -1 and end != -1 and end > start:
    end += len("# END wow-realms\n")
    text = text[:start] + block + text[end:]
else:
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + block
hosts.write_text(text, encoding="utf-8")
PY
  rm -f "$tmp"
  log "Hostnames vanilla.local, tbc.local, … resolve to per-realm loopback addresses"
}

write_backup_timer() {
  local hour="${BACKUP_HOUR:-04}"
  [[ "$hour" =~ ^[0-9]{2}$ ]] || hour="04"
  cat > /etc/systemd/system/wow-backup.timer <<EOF
[Unit]
Description=Dump WoW realm databases every day

[Timer]
OnCalendar=*-*-* ${hour}:00:00
Persistent=true
AccuracySec=15min

[Install]
WantedBy=timers.target
EOF
  chmod 0644 /etc/systemd/system/wow-backup.timer
}

enable_units() {
  local boot_list=""
  systemctl daemon-reload
  if [[ "$HOST_LAYOUT" == "removable" ]]; then
    systemctl enable wow-loopback.service wow-volume-share.service wow-media-alias.service >/dev/null
  else
    systemctl disable --now wow-volume-share.service >/dev/null 2>&1 || true
    systemctl disable --now wow-media-alias.service >/dev/null 2>&1 || true
    systemctl enable wow-loopback.service >/dev/null
  fi
  # Updates are manual. A timer that rebuilds a live realm stays installed and disabled.
  systemctl disable --now wow-git-update.timer >/dev/null 2>&1 || true
  if [[ "${BACKUP_SCHEDULE:-off}" == "on" ]]; then
    systemctl enable --now wow-backup.timer >/dev/null
  else
    systemctl disable --now wow-backup.timer >/dev/null 2>&1 || true
  fi
  if [[ -f "${ROOT}/.run/boot.conf" ]]; then
    boot_list="$(tr -d '[:space:]' < "${ROOT}/.run/boot.conf")"
  fi
  if [[ -n "$boot_list" ]]; then
    systemctl enable wow-realms.service >/dev/null
  else
    systemctl disable wow-realms.service >/dev/null 2>&1 || true
  fi
  systemctl start wow-loopback.service
  /usr/local/sbin/wow-loopback.sh
  if [[ "$HOST_LAYOUT" == "removable" ]]; then
    systemctl start wow-volume-share.service || warn "volume share service did not start"
    /usr/local/sbin/wow-media-alias.sh
  fi
}

apply_without_systemd() {
  /usr/local/sbin/wow-loopback.sh
  if [[ "$HOST_LAYOUT" == "removable" ]]; then
    /usr/local/sbin/wow-volume-share.sh || warn "volume share did not start"
    /usr/local/sbin/wow-media-alias.sh || warn "media alias did not start"
  fi
  log "Boot persistence needs systemd. Loopback addresses, /etc/hosts, and HAProxy config were written."
}

classify_this_tree() {
  local target fstype uuid=""
  target="$(findmnt -n -o TARGET -T "$ROOT")"
  [[ -n "$target" ]] || die "Could not find the mount that holds ${ROOT}"
  fstype="$(findmnt -n -o FSTYPE -T "$ROOT")"
  [[ -n "$fstype" ]] || die "Could not find the filesystem type for ${ROOT}"
  if host_target_is_removable "$target"; then
    uuid="${WOW_VOLUME_UUID:-}"
    if [[ -z "$uuid" ]]; then
      uuid="$(findmnt -n -o UUID -T "$ROOT")"
    fi
    host_classify_layout "$ROOT" "$target" "$fstype" "$uuid" "${WOW_VOLUME_MOUNT:-}"
  else
    # Do not discover a UUID for an internal disk. Record one only when pinned.
    host_classify_layout "$ROOT" "$target" "$fstype" "${WOW_VOLUME_UUID:-}"
  fi
}

main() {
  if [[ "$(id -u)" -ne 0 ]]; then
    if sudo -n true 2>/dev/null; then
      exec sudo -n -- "$0" "$@"
    fi
    exec sudo -- "$0" "$@"
  fi

  load_env
  resolve_media_user
  classify_this_tree

  if [[ "$HOST_LAYOUT" == "removable" ]]; then
    ensure_mount
    write_fstab
  fi

  [[ -f "${HOST_TREE}/setup.sh" ]] || die "No setup.sh under ${HOST_TREE}"
  log "WoW tree is ${HOST_TREE} (${HOST_LAYOUT})"

  install_scripts
  write_volume_env
  write_loopback_ips
  write_haproxy
  write_hosts

  if command -v systemctl >/dev/null 2>&1; then
    install_systemd_units
    enable_units
  else
    apply_without_systemd
  fi

  if [[ "$HOST_LAYOUT" == "removable" ]]; then
    log "Removable volume is mounted at ${HOST_MOUNT}"
  else
    log "Internal disk. No fstab entry and no extra bind mount."
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
