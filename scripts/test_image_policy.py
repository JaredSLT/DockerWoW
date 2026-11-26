#!/usr/bin/env python3
"""Image policy: Docker build context must not disable TLS verification."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKER = ROOT / "docker"
FORBIDDEN = ("sslVerify false", "http.sslVerify")
SAFE_DIRECTORY_FILES = (
    "docker/cmangos-classic/Dockerfile",
    "docker/TrinityCore/Dockerfile",
)


class ImagePolicyTests(unittest.TestCase):
    def test_docker_tree_does_not_disable_tls_verify(self):
        offenders = []
        for path in sorted(DOCKER.rglob("*")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for needle in FORBIDDEN:
                if needle in text:
                    offenders.append(f"{path.relative_to(ROOT)} contains {needle!r}")
        self.assertEqual(offenders, [])

    def test_safe_directory_still_set(self):
        for rel in SAFE_DIRECTORY_FILES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertIn("safe.directory", text, rel)


if __name__ == "__main__":
    unittest.main()
