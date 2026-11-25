"""Warlords of Draenor Battle.net account management, 2014–2015."""

from __future__ import annotations

import html

ERA_TITLE = "Password and Security"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _identity(login_kind: str) -> tuple[str, str, str]:
    if login_kind == "email":
        return "Email", "email", "email"
    return "Account Name", "text", "username"


def _nav(mode: str) -> str:
    items = (
        ("/account/", "Overview", mode == "summary"),
        ("/account/", "Settings", False),
        ("/account/password", ERA_TITLE, mode == "password"),
    )
    links = []
    for href, text, current in items:
        cls = "acct-nav-link acct-nav-current" if current else "acct-nav-link"
        links.append(f'<a class="{cls}" href="{href}">{text}</a>')
    return (
        '<nav class="acct-nav" aria-label="Account">'
        '<p class="acct-nav-label">Account Management</p>'
        + "".join(links)
        + "</nav>"
    )


def _characters(characters: list) -> str:
    items = []
    for row in characters or []:
        if not isinstance(row, dict):
            continue
        items.append(
            "<li class=\"acct-char\">"
            f"{_e(row.get('name'))} — level {_e(row.get('level'))} {_e(row.get('class_name'))}"
            "</li>"
        )
    if not items:
        return '<p class="acct-empty">No characters on this realm yet.</p>'
    return '<ul class="acct-chars">' + "".join(items) + "</ul>"


def _login(login_kind: str) -> str:
    label, input_type, auto = _identity(login_kind)
    return f"""<h3 class="acct-sub">Log In</h3>
<form class="acct-form" method="post" action="/account/login">
  <label class="acct-label">{label} <input name="identity" type="{input_type}" autocomplete="{auto}" required></label>
  <label class="acct-label">Password <input type="password" name="password" autocomplete="current-password" required></label>
  <button type="submit">Log In</button>
</form>
<p class="acct-help">There is no emailed password reset. Sign in and change the password on this page.</p>
<p class="acct-help"><a href="/account/create">Create Account</a></p>"""


def _create(login_kind: str) -> str:
    label, input_type, auto = _identity(login_kind)
    return f"""<h3 class="acct-sub">Create Account</h3>
<form class="acct-form" method="post" action="/account/create">
  <label class="acct-label">{label} <input name="identity" type="{input_type}" autocomplete="{auto}" required></label>
  <label class="acct-label">Password <input type="password" name="password" autocomplete="new-password" required></label>
  <label class="acct-label">Confirm password <input type="password" name="confirm" autocomplete="new-password" required></label>
  <button type="submit">Create Account</button>
</form>
<p class="acct-help"><a href="/account/login">Log In</a></p>"""


def _password() -> str:
    return """<h3 class="acct-sub">Change Password</h3>
<form class="acct-form" method="post" action="/account/password">
  <label class="acct-label">Current password <input type="password" name="current" autocomplete="current-password" required></label>
  <label class="acct-label">New password <input type="password" name="password" autocomplete="new-password" required></label>
  <label class="acct-label">Confirm new password <input type="password" name="confirm" autocomplete="new-password" required></label>
  <button type="submit">Change Password</button>
</form>
<p class="acct-help"><a href="/account/">Back to Account</a></p>"""


def _summary(user: str, email: str, characters: list) -> str:
    bits = ['<h3 class="acct-sub">Overview</h3>']
    if user:
        bits.append(
            f'<p class="acct-signed-in">Signed in as <strong class="acct-user">{_e(user)}</strong>.</p>'
        )
    if email:
        bits.append(
            '<p class="acct-address">Email '
            f'<strong class="acct-email">{_e(email)}</strong></p>'
        )
    bits.append('<h3 class="acct-sub">Characters</h3>')
    bits.append(_characters(characters))
    bits.append(
        '<p class="acct-actions"><a href="/account/password">Change Password</a>'
        '<a href="/account/services">Character Services</a>'
        '<a href="/account/logout">Log Out</a></p>'
    )
    return "".join(bits)


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
    # Email is the Battle.net login. Never ask for a separate game name.
    _ = separate_game_name
    era = getattr(exp, "name", "") if exp is not None else ""
    kicker = f'<p class="acct-kicker">{_e(era)}</p>' if era else ""
    if mode == "summary":
        heading, body = "Account", _summary(user, email, characters)
    elif mode == "create":
        heading, body = "Create Account", _create(login_kind)
    elif mode == "password":
        heading, body = ERA_TITLE, _password()
    else:
        heading, body = "Log In", _login(login_kind)
    alerts = []
    if error:
        alerts.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        alerts.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return (
        '<section class="acct acct-wod">'
        + _nav(mode)
        + '<div class="acct-panel">'
        + kicker
        + f'<h2 class="acct-title">{heading}</h2>'
        + "".join(alerts)
        + body
        + "</div></section>"
    )
