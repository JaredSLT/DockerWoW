#!/usr/bin/env bash
# Pin the removable WoW disk to a stable mount and install the host pieces
# the stack needs before Docker starts: loopback aliases, /etc/hosts names,
# and the HAProxy config on the root filesystem.
#
# Safe to re-run. Privileged steps re-exec through sudo.
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

if [[ "$(id -u)" -ne 0 ]]; then
  exec sudo -n -- "$0" "$@"
fi

load_env

# Owner of the tree, or the user who invoked sudo. Never a fixed account name.
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
MOUNT="${WOW_VOLUME_MOUNT:-/mnt/wow-nvme}"

discover_uuid() {
  if [[ -n "${WOW_VOLUME_UUID:-}" ]]; then
    printf '%s' "$WOW_VOLUME_UUID"
    return 0
  fi
  findmnt -n -o UUID -T "$ROOT"
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
  uuid="$(discover_uuid)"
  [[ -n "$uuid" ]] || die "Could not find the filesystem UUID for ${ROOT}"
  WOW_VOLUME_UUID="$uuid"
  mkdir -p "$MOUNT"
  if mountpoint -q "$MOUNT"; then
    mount_uuid_matches "$MOUNT" "$uuid" \
      || die "${MOUNT} is already mounted with a different filesystem"
  else
    src="$(uuid_mounted_at "$uuid")"
    if [[ -n "$src" && "$src" != "$MOUNT" ]]; then
      log "Bind-mounting ${src} onto ${MOUNT}"
      mount --bind "$src" "$MOUNT"
    elif [[ -z "$src" ]]; then
      log "Mounting UUID ${uuid} onto ${MOUNT}"
      mount "UUID=${uuid}" "$MOUNT"
    fi
  fi
  mount --make-rshared "$MOUNT"
  mount_uuid_matches "$MOUNT" "$uuid" || die "${MOUNT} does not hold UUID ${uuid}"
}

tree_on_mount() {
  local fs_target rel
  fs_target="$(findmnt -n -o TARGET -T "$ROOT")"
  rel="${ROOT#"$fs_target"}"
  if mount_uuid_matches "$ROOT" "$WOW_VOLUME_UUID"; then
    printf '%s' "$ROOT"
    return 0
  fi
  printf '%s' "${MOUNT}${rel}"
}

write_fstab() {
  local line
  line="UUID=${WOW_VOLUME_UUID} ${MOUNT} ext4 nosuid,nodev,nofail,x-systemd.device-timeout=15s,x-systemd.before=docker.service 0 2"
  python3 - /etc/fstab "$line" <<'PY'
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
  log "fstab mounts UUID ${WOW_VOLUME_UUID} at ${MOUNT} before docker"
}

install_unit() {
  local name="$1"
  install -m 0644 "${HOST_DIR}/${name}" "/etc/systemd/system/${name}"
}

# The unit files in the repo use the default mount path. Rewrite them for
# whatever WOW_VOLUME_MOUNT this host actually uses.
write_mount_units() {
  local mount_unit
  mount_unit="$(systemd-escape --path --suffix=mount "$MOUNT")"
  cat > /etc/systemd/system/wow-volume-share.service <<EOF
[Unit]
Description=Share the WoW volume mount into Docker containers
After=${mount_unit}
Before=docker.service
ConditionPathIsMountPoint=${MOUNT}

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

install_host_files() {
  local ips short
  install -d -m 0755 /etc/wow /usr/local/sbin
  install -m 0755 "${HOST_DIR}/wow-loopback.sh" /usr/local/sbin/wow-loopback.sh
  install -m 0755 "${HOST_DIR}/wow-volume-share.sh" /usr/local/sbin/wow-volume-share.sh
  install -m 0755 "${HOST_DIR}/wow-media-alias.sh" /usr/local/sbin/wow-media-alias.sh
  install -m 0755 "${HOST_DIR}/wow-git-update.sh" /usr/local/sbin/wow-git-update.sh
  install -m 0755 "${HOST_DIR}/wow-backup.sh" /usr/local/sbin/wow-backup.sh
  install -m 0755 "${HOST_DIR}/wow-realms.sh" /usr/local/sbin/wow-realms.sh
  install_unit wow-loopback.service
  install_unit wow-git-update.service
  install_unit wow-git-update.timer
  install_unit wow-backup.service
  install_unit wow-realms.service
  write_backup_timer
  write_mount_units

  cat > /etc/wow/volume.env <<EOF
WOW_VOLUME_UUID=${WOW_VOLUME_UUID}
WOW_VOLUME_MOUNT=${MOUNT}
WOW_TREE=${WOW_TREE}
WOW_MEDIA_USER=${MEDIA_USER}
EOF
  chmod 0644 /etc/wow/volume.env

  ips="$(mktemp)"
  while IFS= read -r short; do
    catalog_load "$short"
    printf '%s\n' "$CATALOG_LOOPBACK"
  done < <(catalog_shorts) >"$ips"
  install -m 0644 "$ips" /etc/wow/loopback.ips
  rm -f "$ips"

  local cfg
  cfg="$(mktemp)"
  haproxy_render "$cfg"
  if [[ -d /etc/wow/haproxy.cfg ]]; then
    die "/etc/wow/haproxy.cfg is a directory (Docker created it). Remove it and re-run."
  fi
  install -m 0644 "$cfg" /etc/wow/haproxy.cfg
  mkdir -p "${ROOT}/.run"
  install -m 0644 "$cfg" "${ROOT}/.run/haproxy.cfg"
  rm -f "$cfg"
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
  rows="$(cat "$tmp")"
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
  systemctl daemon-reload
  systemctl enable wow-loopback.service wow-volume-share.service wow-media-alias.service >/dev/null
  # Updates are manual. A timer that rebuilds a live realm stays installed and disabled.
  systemctl disable --now wow-git-update.timer >/dev/null 2>&1 || true
  if [[ "${BACKUP_SCHEDULE:-off}" == "on" ]]; then
    systemctl enable --now wow-backup.timer >/dev/null
  else
    systemctl disable --now wow-backup.timer >/dev/null 2>&1 || true
  fi
  boot_list=""
  if [[ -f "${ROOT}/.run/boot.conf" ]]; then
    boot_list="$(tr -d '[:space:]' < "${ROOT}/.run/boot.conf")"
  fi
  if [[ -n "$boot_list" ]]; then
    systemctl enable wow-realms.service >/dev/null
  else
    systemctl disable wow-realms.service >/dev/null 2>&1 || true
  fi
  systemctl start wow-loopback.service
  systemctl start wow-volume-share.service || warn "volume share service did not start"
  /usr/local/sbin/wow-loopback.sh
  /usr/local/sbin/wow-media-alias.sh
}

ensure_mount
WOW_TREE="$(tree_on_mount)"
[[ -f "${WOW_TREE}/setup.sh" ]] || die "No setup.sh under ${WOW_TREE} after mounting ${MOUNT}"
log "WoW tree is ${WOW_TREE}"
write_fstab
install_host_files
write_hosts
enable_units
log "Removable volume is mounted at ${MOUNT}"
