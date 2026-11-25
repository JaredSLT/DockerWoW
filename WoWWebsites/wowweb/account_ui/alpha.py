"""Centered 2004 parchment account card.

One game account name. No separate game-name field and no emailed reset.
"""

from __future__ import annotations

import html

ERA_TITLE = "Account Login"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _alerts(error: str, notice: str) -> str:
    bits = []
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(bits)


def _identity(login_kind: str) -> tuple[str, str]:
    if login_kind == "email":
        return "Email", "email"
    return "Account Name", "text"


def _who(user: str, email: str, login_kind: str) -> str:
    label, _input_type = _identity(login_kind)
    shown = email if login_kind == "email" and email else user
    return (
        '<table class="acct-table">'
        '<tr class="acct-row">'
        f'<th class="acct-label" scope="row">{label}</th>'
        f'<td class="acct-name">{_e(shown)}</td>'
        "</tr></table>"
    )


def _field(label: str, name: str, input_type: str, autocomplete: str, *, maxlength: str = "") -> str:
    extra = f' maxlength="{maxlength}"' if maxlength else ""
    return (
        '<tr class="acct-row">'
        f'<th class="acct-label" scope="row"><label for="acct-{name}">{label}</label></th>'
        '<td class="acct-field">'
        f'<input id="acct-{name}" name="{name}" type="{input_type}" required{extra} '
        f'autocomplete="{autocomplete}">'
        "</td></tr>"
    )


def _login(login_kind: str) -> str:
    label, input_type = _identity(login_kind)
    return (
        f'<form class="acct-form" method="post" action="/account/login">'
        '<div class="acct-well"><table class="acct-table">'
        + _field(label, "identity", input_type, "username", maxlength="16")
        + _field("Password", "password", "password", "current-password")
        + "</table>"
        '<button class="acct-submit" type="submit">Log In</button>'
        "</div></form>"
        '<hr class="acct-rule">'
        '<p class="acct-note">There is no emailed reset. Sign in and change the password here.</p>'
        '<ul class="acct-links"><li><a href="/account/create">Create Account</a></li></ul>'
    )


def _create(login_kind: str) -> str:
    label, input_type = _identity(login_kind)
    return (
        '<form class="acct-form" method="post" action="/account/create">'
        '<div class="acct-well"><table class="acct-table">'
        + _field(label, "identity", input_type, "username", maxlength="16")
        + _field("Password", "password", "password", "new-password")
        + _field("Confirm Password", "confirm", "password", "new-password")
        + "</table>"
        '<button class="acct-submit" type="submit">Create Account</button>'
        "</div></form>"
        '<ul class="acct-links"><li><a href="/account/login">Log In</a></li></ul>'
    )


def _password(user: str, email: str, login_kind: str) -> str:
    who = _who(user, email, login_kind) if user else ""
    return (
        who
        + '<form class="acct-form" method="post" action="/account/password">'
        '<div class="acct-well"><table class="acct-table">'
        + _field("Current Password", "current", "password", "current-password")
        + _field("New Password", "password", "password", "new-password")
        + _field("Confirm Password", "confirm", "password", "new-password")
        + "</table>"
        '<button class="acct-submit" type="submit">Change Password</button>'
        "</div></form>"
        '<ul class="acct-links"><li><a href="/account/">Back to Account</a></li></ul>'
    )


def _characters(characters: list) -> str:
    rows = []
    for entry in characters or []:
        if not isinstance(entry, dict):
            continue
        rows.append(
            '<tr class="acct-row">'
            f'<td>{_e(entry.get("name"))}</td>'
            f'<td>{_e(entry.get("level"))}</td>'
            f'<td>{_e(entry.get("class_name"))}</td>'
            "</tr>"
        )
    if not rows:
        return '<p class="acct-empty">No characters on this realm yet.</p>'
    return (
        '<table class="acct-chars"><thead><tr>'
        '<th class="acct-label" scope="col">Character</th>'
        '<th class="acct-label" scope="col">Level</th>'
        '<th class="acct-label" scope="col">Class</th>'
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _summary(user: str, email: str, login_kind: str, characters: list) -> str:
    return (
        _who(user, email, login_kind)
        + _characters(characters)
        + '<ul class="acct-links">'
        '<li><a href="/account/password">Change Password</a></li>'
        '<li><a href="/account/logout">Log Out</a></li>'
        "</ul>"
    )


def render(
    exp,
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
    del exp, separate_game_name
    if mode == "summary" and user:
        body = _summary(user, email, login_kind, characters)
    elif mode == "create":
        body = _create(login_kind)
    elif mode == "password":
        body = _password(user, email, login_kind)
    else:
        body = _login(login_kind)
    heading = "Create Account" if mode == "create" else ERA_TITLE
    return (
        '<section class="acct-alpha"><div class="acct-card">'
        f'<h2 class="acct-title">{heading}</h2>'
        f"{_alerts(error, notice)}{body}"
        "</div></section>"
    )
