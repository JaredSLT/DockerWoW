"""Shared markup helpers for era shells.

Era modules must not import wowweb.html.layout or wowweb.html.guide.
"""

from __future__ import annotations

import html
from typing import Any


def esc(text: Any) -> str:
    return html.escape("" if text is None else str(text), quote=True)


def dev_note(exp: Any, dev: bool) -> str:
    if not dev:
        return ""
    return (
        f"Last patch {esc(exp.last_patch)} · {esc(exp.last_patch_date)} · "
        f"Local realm {esc(exp.realm_name)} · Visual source {esc(exp.snapshot)} · "
        "Not affiliated with Blizzard Entertainment."
    )


def document(
    title: str,
    css: list[str],
    body_class: str,
    inner: str,
    *,
    dev_note_text: str = "",
    extra_js: str = "",
) -> str:
    links = "\n".join(f'<link rel="stylesheet" href="{esc(href)}">' for href in css)
    foot = f'<p class="dev-foot">{dev_note_text}</p>' if dev_note_text else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
{links}
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body class="{esc(body_class)}">
{inner}
{foot}
<script src="/static/js/site.js"></script>
{extra_js}
</body>
</html>
"""


def styles(exp_id: str) -> list[str]:
    return [
        f"/static/css/era-{exp_id}.css",
        "/static/css/icons.css",
        "/static/css/account.css",
        f"/static/css/account-{exp_id}.css",
    ]


def signed_in(user: str | None) -> str:
    if user:
        return (
            f'<span class="who">Signed in as <strong>{esc(user)}</strong> · '
            f'<a href="/account/">Account</a> · <a href="/account/logout">Log Out</a></span>'
        )
    return '<span class="who"><a href="/account/login">Log In</a></span>'
