"""Per-expansion account management pages.

Each expansion module owns its markup. Shared login and password changes
live in wowweb.accounts and wowweb.http.routes.
"""

from __future__ import annotations

import importlib

from ..catalog import Expansion


def render_account(
    exp: Expansion,
    *,
    user: str,
    error: str,
    notice: str,
    mode: str,
    email: str,
    characters: list,
    login_kind: str,
    separate_game_name: bool,
) -> str:
    name = exp.id.replace("-", "_")
    try:
        module = importlib.import_module(f"wowweb.account_ui.{name}")
    except ModuleNotFoundError:
        from . import fallback as module
    html = module.render(
        exp,
        user=user,
        error=error,
        notice=notice,
        mode=mode,
        email=email,
        characters=characters,
        login_kind=login_kind,
        separate_game_name=separate_game_name,
    )
    if mode == "summary" and user:
        html += '<p class="acct-services-link"><a href="/account/services">Character Services</a></p>'
    return html
