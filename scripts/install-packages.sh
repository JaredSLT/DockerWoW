#!/usr/bin/env bash
# Install the packages a new clone needs. Safe to re-run.
# Debian, Ubuntu, Fedora, and Arch. Other distributions are told what to install.
set -euo pipefail

log()  { printf '==> %s\n' "$*"; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

if [[ "$(id -u)" -ne 0 ]]; then
  if sudo -n true 2>/dev/null; then
    exec sudo -n -- "$0" "$@"
  fi
  exec sudo -- "$0" "$@"
fi

[[ -f /etc/os-release ]] || die "No /etc/os-release. Install docker, the compose plugin, rsync, git, python3, curl, and mariadb-client."
# shellcheck disable=SC1091
source /etc/os-release

family=""
case "${ID:-}" in
  debian|ubuntu|linuxmint|pop) family=apt ;;
  fedora|rhel|centos|rocky|almalinux) family=dnf ;;
  arch|manjaro|endeavouros) family=pacman ;;
  *)
    case "${ID_LIKE:-}" in
      *debian*) family=apt ;;
      *fedora*|*rhel*) family=dnf ;;
      *arch*) family=pacman ;;
    esac
    ;;
esac

[[ -n "$family" ]] || die "Unsupported distro ${ID:-unknown}. Install docker, the compose plugin, rsync, git, python3, curl, and mariadb-client, then re-run ./setup.sh host."

case "$family" in
  apt)
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y docker.io rsync git python3 curl mariadb-client
    if ! apt-get install -y docker-compose-v2; then
      apt-get install -y docker-compose || die "Could not install docker compose"
    fi
    ;;
  dnf)
    dnf install -y docker docker-compose rsync git python3 curl mariadb
    ;;
  pacman)
    pacman -Sy --noconfirm --needed docker docker-compose rsync git python curl mariadb-clients
    ;;
esac

if command -v systemctl >/dev/null; then
  systemctl enable --now docker >/dev/null || systemctl enable --now docker.service >/dev/null || true
fi

if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != "root" ]]; then
  if getent group docker >/dev/null; then
    usermod -aG docker "$SUDO_USER" || true
    log "Added ${SUDO_USER} to the docker group. Open a new login if docker info fails."
  fi
fi

log "Packages are installed."
