#!/usr/bin/env bash
# Thin wrapper so ./scripts/select-project.sh and the Python menu stay the same command.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "${ROOT}/scripts/select-project.py" "$@"
