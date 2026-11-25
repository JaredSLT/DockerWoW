"""HTTP server: era community site + Armory + forums + accounts."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path

from .. import accounts, lab
from ..catalog import Expansion
from .handler import ROOT, STATIC, SiteHandler
from .routes import Routes


class BoundHandler(Routes, SiteHandler):
    """Routes mixed onto the request handler."""


def make_server(
    exp: Expansion,
    host: str,
    port: int,
    lab_root: Path | None,
    data_dir: Path,
) -> ThreadingHTTPServer:
    cfg = lab.load_lab(lab_root)
    secret = accounts.session_secret(data_dir)

    class Bound(BoundHandler):
        pass

    Bound.exp = exp
    Bound.labcfg = cfg
    Bound.data_dir = data_dir
    Bound.secret = secret
    ThreadingHTTPServer.allow_reuse_address = True
    return ThreadingHTTPServer((host, port), Bound)


__all__ = ["ROOT", "STATIC", "make_server"]
