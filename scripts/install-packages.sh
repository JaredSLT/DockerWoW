#!/usr/bin/env bash
# Install the packages a new clone needs. Safe to re-run.
# Debian, Ubuntu, Fedora, and Arch. Other distributions are told what to install
# unless docker, compose, git, python3, rsync, and curl are already on PATH.
set -euo pipefail

log()  { printf '==> %s\n' "$*"; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

have_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    return 0
  fi
  command -v docker-compose >/dev/null 2>&1
}

tools_ready() {
  command -v docker >/dev/null 2>&1 || return 1
  command -v git >/dev/null 2>&1 || return 1
  command -v python3 >/dev/null 2>&1 || return 1
  command -v rsync >/dev/null 2>&1 || return 1
  command -v curl >/dev/null 2>&1 || return 1
  have_compose
}

if tools_ready; then
  log "docker, compose, git, python3, rsync, and curl are already installed."
  exit 0
fi

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
    pkgs=(rsync git python3 curl mariadb-client)
    # A working Docker Engine must not be replaced by the distro docker.io package.
    if ! command -v docker >/dev/null 2>&1; then
      pkgs+=(docker.io)
    fi
    apt-get install -y "${pkgs[@]}"
    if ! have_compose; then
      if ! apt-get install -y docker-compose-v2; then
        apt-get install -y docker-compose || die "Could not install docker compose"
      fi
    fi
    ;;
  dnf)
    pkgs=(rsync git python3 curl mariadb)
    command -v docker >/dev/null 2>&1 || pkgs+=(docker)
    have_compose || pkgs+=(docker-compose)
    dnf install -y "${pkgs[@]}"
    ;;
  pacman)
    pkgs=(rsync git python curl mariadb-clients)
    command -v docker >/dev/null 2>&1 || pkgs+=(docker)
    have_compose || pkgs+=(docker-compose)
    pacman -Sy --noconfirm --needed "${pkgs[@]}"
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
