"""Legion 7.3.5 Battle.net account settings.

The wowcom community shell wraps this fragment. Login is the email on the
Battle.net account; the World of Warcraft account name is separate.
"""

from __future__ import annotations

import html

ERA_TITLE = "Account Settings"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _alerts(error: str, notice: str) -> str:
    parts = []
    if error:
        parts.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        parts.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(parts)


def _identity_field(login_kind: str) -> str:
    if login_kind == "email":
        label, input_type = "Email", "email"
    else:
        label, input_type = "Account Name", "text"
    return (
        f'<label class="acct-field">{label} '
        f'<input name="identity" type="{input_type}" required autocomplete="username"></label>'
    )


def _game_field(separate_game_name: bool) -> str:
    if not separate_game_name:
        return ""
    return (
        '<label class="acct-field">World of Warcraft account name '
        '<input name="game_name" required maxlength="16" autocomplete="username"></label>'
    )


def _nav(current: str) -> str:
    def item(mode: str, href: str, label: str) -> str:
        current_attr = ' class="acct-nav-current"' if mode == current else ""
        return f'<a{current_attr} href="{href}">{label}</a>'

    return (
        '<nav class="acct-nav" aria-label="Account Settings">'
        + item("summary", "/account/", "Overview")
        + item("password", "/account/password", "Password &amp; Security")
        + "</nav>"
    )


def _sheet(current: str, inner: str) -> str:
    return f'<div class="acct-layout">{_nav(current)}<div class="acct-main">{inner}</div></div>'


def _characters(characters: list) -> str:
    rows = []
    for entry in characters or []:
        if not isinstance(entry, dict):
            rows.append(f'<li class="acct-char"><span class="acct-char-name">{_e(entry)}</span></li>')
            continue
        rows.append(
            '<li class="acct-char">'
            f'<span class="acct-char-name">{_e(entry.get("name"))}</span>'
            f'<span class="acct-char-level">{_e(entry.get("level"))}</span>'
            f'<span class="acct-char-class">{_e(entry.get("class_name"))}</span>'
            "</li>"
        )
    if not rows:
        return '<p class="acct-empty">No characters on this account yet.</p>'
    body = "".join(rows)
    return (
        '<div class="acct-roster">'
        '<h3 class="acct-sub">Characters</h3>'
        '<div class="acct-char acct-char-head"><span>Name</span><span>Level</span><span>Class</span></div>'
        f'<ul class="acct-chars">{body}</ul>'
        "</div>"
    )


def _summary(user: str, email: str, characters: list) -> str:
    shown_email = _e(email) if email else "—"
    inner = (
        '<section class="acct-panel">'
        '<h3>Overview</h3>'
        f'<p class="acct-lead">Signed in as <strong class="acct-user">{_e(user)}</strong>.</p>'
        '<dl class="acct-facts">'
        '<div class="acct-fact"><dt>Email</dt>'
        f"<dd>{shown_email}</dd></div>"
        '<div class="acct-fact"><dt>World of Warcraft account name</dt>'
        f"<dd>{_e(user)}</dd></div>"
        "</dl>"
        f"{_characters(characters)}"
        '<div class="acct-games">'
        '<h3 class="acct-sub">Your Game Accounts</h3>'
        '<p class="acct-game"><span>World of Warcraft: Legion</span> '
        '<span class="acct-active">Active</span></p>'
        "</div>"
        '<p class="acct-actions">'
        '<a href="/account/password">Password &amp; Security</a>'
        '<a href="/account/logout">Log Out</a>'
        "</p>"
        "</section>"
    )
    return _sheet("summary", inner)


def _login(login_kind: str) -> str:
    return (
        '<div class="acct-card">'
        "<h3>Sign In</h3>"
        f'<form class="acct-form" method="post" action="/account/login">'
        f"{_identity_field(login_kind)}"
        '<label class="acct-field">Password '
        '<input type="password" name="password" required autocomplete="current-password"></label>'
        '<button type="submit">Log in to Blizzard</button>'
        "</form>"
        '<p class="acct-hint">There is no emailed password reset. Sign in and change the password here.</p>'
        '<p class="acct-actions"><a href="/account/create">Create a Free Blizzard Account</a></p>'
        '<p class="acct-actions"><a href="/support/password">Can\'t log in?</a></p>'
        "</div>"
    )


def _create(login_kind: str, separate_game_name: bool) -> str:
    return (
        '<div class="acct-card">'
        "<h3>Create Account</h3>"
        '<form class="acct-form" method="post" action="/account/create">'
        f"{_identity_field(login_kind)}"
        f"{_game_field(separate_game_name)}"
        '<label class="acct-field">Password '
        '<input type="password" name="password" required autocomplete="new-password"></label>'
        '<label class="acct-field">Confirm password '
        '<input type="password" name="confirm" required autocomplete="new-password"></label>'
        '<button type="submit">Create Account</button>'
        "</form>"
        '<p class="acct-actions"><a href="/account/login">Log In</a></p>'
        "</div>"
    )


def _password() -> str:
    inner = (
        '<section class="acct-panel">'
        "<h3>Password &amp; Security</h3>"
        '<p class="acct-hint">Change the password for this Battle.net login.</p>'
        '<form class="acct-form" method="post" action="/account/password">'
        '<label class="acct-field">Current password '
        '<input type="password" name="current" required autocomplete="current-password"></label>'
        '<label class="acct-field">New password '
        '<input type="password" name="password" required autocomplete="new-password"></label>'
        '<label class="acct-field">Confirm new password '
        '<input type="password" name="confirm" required autocomplete="new-password"></label>'
        '<button type="submit">Change Password</button>'
        "</form>"
        '<p class="acct-actions"><a href="/account/">Back to Account</a></p>'
        "</section>"
    )
    return _sheet("password", inner)


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
    del exp
    if mode == "create":
        shown, body = "create", _create(login_kind, separate_game_name)
    elif mode == "password":
        shown, body = "password", _password()
    elif mode == "summary" and user:
        shown, body = "summary", _summary(user, email, characters)
    else:
        shown, body = "login", _login(login_kind)
    return (
        f'<section class="acct acct-legion acct-mode-{shown}">'
        '<header class="acct-mast">'
        '<p class="acct-brand">Battle.net</p>'
        f"<h2 class=\"acct-title\">{ERA_TITLE}</h2>"
        "</header>"
        f"{_alerts(error, notice)}"
        f"{body}"
        "</section>"
    )
