#!/usr/bin/env bash
# Realm container HEALTHCHECK: auth listener (login) and world listener (enter world).
set -euo pipefail
python3 - <<'PY'
import os, socket, sys

def listening(port: int) -> bool:
    if port <= 0:
        return True
    sock = socket.socket()
    sock.settimeout(2)
    try:
        sock.connect(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()

auth = int(os.environ.get("WOW_AUTH_PORT") or "0")
world = int(os.environ.get("WOW_WORLD_PORT") or "0")
sys.exit(0 if listening(auth) and listening(world) else 1)
PY
