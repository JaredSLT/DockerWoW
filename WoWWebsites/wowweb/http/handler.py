"""HTTP handler, cookies, static files."""

from __future__ import annotations

import mimetypes
import posixpath
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .. import accounts, html as H, lab
from ..catalog import Expansion

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "static"
ARCHIVE = STATIC / "archive" / "vanilla"
_ARCHIVE_EXT = {
    ".css",
    ".js",
    ".gif",
    ".jpg",
    ".jpeg",
    ".png",
    ".swf",
    ".xml",
    ".xsl",
    ".cur",
    ".ico",
    ".htm",
}


class SiteHandler(BaseHTTPRequestHandler):
    server_version = "WoWWeb/1.0"
    exp: Expansion
    labcfg: lab.LabConfig
    data_dir: Path
    secret: bytes

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def user(self) -> str | None:
        raw = self.headers.get("Cookie", "")
        token = ""
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == "wowweb":
                token = v
        got = accounts.verify_session(self.secret, token)
        if not got:
            return None
        exp_id, name = got
        if exp_id != self.exp.id:
            return None
        return name

    def send_html(self, body: str, status: int = 200, headers: list[tuple[str, str]] | None = None) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for k, v in headers or []:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, loc: str, extra: list[tuple[str, str]] | None = None) -> None:
        self.send_response(303)
        self.send_header("Location", loc)
        for k, v in extra or []:
            self.send_header(k, v)
        self.end_headers()

    def page(
        self,
        title: str,
        inner: str,
        crumb: str = "",
        extra_js: str = "",
        status: int = 200,
        login_error: str = "",
    ) -> None:
        dev = "dev" in parse_qs(urlparse(self.path).query)
        online = ""
        if self.exp.id == "alpha":
            status_row = lab.realm_status(self.labcfg, self.exp)
            online = "up" if status_row.get("up") else "down"
        self.send_html(
            H.layout(
                self.exp,
                title,
                inner,
                self.user(),
                crumb or title,
                extra_js,
                dev=dev,
                online=online,
                login_error=login_error,
            ),
            status,
        )

    def read_post(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b""
        qs = parse_qs(raw.decode("utf-8", errors="replace"), keep_blank_values=True)
        return {k: (v[-1] if v else "") for k, v in qs.items()}

    def do_GET(self) -> None:
        self.dispatch("GET")

    def do_POST(self) -> None:
        self.dispatch("POST")

    def dispatch(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = posixpath.normpath(unquote(parsed.path))
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)

        if path.startswith("/static/"):
            return self.serve_static(path[len("/static/") :])
        archived = self.archive_asset(path)
        if archived is not None:
            return self.serve_file(archived)

        try:
            if method == "POST":
                return self.route_post(path)
            return self.route_get(path, qs)
        except Exception as exc:  # noqa: BLE001
            self.page("Error", H.simple_list("Something went wrong", [str(exc)]), status=500)

    def archive_asset(self, path: str) -> Path | None:
        if self.exp.id != "vanilla":
            return None
        suffix = Path(path).suffix.lower()
        if suffix not in _ARCHIVE_EXT:
            return None
        if suffix == ".htm" and "/new-hp/menus/" not in path:
            return None
        root = ARCHIVE.resolve()
        target = (root / path.lstrip("/")).resolve()
        if not str(target).startswith(str(root)) or not target.is_file():
            return None
        return target

    def serve_static(self, rel: str) -> None:
        target = (STATIC / rel).resolve()
        if not str(target).startswith(str(STATIC.resolve())) or not target.is_file():
            self.send_error(404)
            return
        self.serve_file(target)

    def serve_file(self, target: Path) -> None:
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if target.suffix in {".css", ".js"}:
            self.send_header("Cache-Control", "no-store")
        else:
            self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(data)
