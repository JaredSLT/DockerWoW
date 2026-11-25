"""Shadowlands (9.2.7) account pages. Inner HTML only."""

from __future__ import annotations

import html

ERA_TITLE = "Security"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _alerts(error: str, notice: str) -> str:
    parts: list[str] = []
    if error:
        parts.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        parts.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(parts)


def _rail(mode: str) -> str:
    def link(href: str, label: str, current: bool) -> str:
        klass = "acct-rail-link acct-rail-current" if current else "acct-rail-link"
        current_attr = ' aria-current="page"' if current else ""
        return f'<a class="{klass}" href="{href}"{current_attr}>{label}</a>'

    summary = mode == "summary"
    security = mode == "password"
    return (
        '<nav class="acct-rail" aria-label="Account">'
        + link("/account/", "Overview", summary)
        + link("/account/", "Account Details", False)
        + link("/account/#games", "Games & Subscriptions", summary)
        + link("/support/", "Parental Controls", False)
        + link("/account/password", "Security", security)
        + link("/support/", "Privacy & Communication", False)
        + link("/support/", "Connections", False)
        + link("/support/", "Payment Methods", False)
        + link("/support/", "Transaction History", False)
        + link("/wow/", "Download Games", False)
        + "</nav>"
    )


def _identity_field(login_kind: str) -> str:
    if login_kind == "email":
        label, input_type, auto, placeholder = "Email", "email", "email", "Email or Phone"
    else:
        label, input_type, auto, placeholder = "Account name", "text", "username", "Account name"
    return (
        f'<label class="acct-field"><span class="acct-label">{label}</span> '
        f'<input class="acct-input" name="identity" type="{input_type}" '
        f'required autocomplete="{auto}" placeholder="{placeholder}"></label>'
    )


def _game_field(separate_game_name: bool) -> str:
    if not separate_game_name:
        return ""
    return (
        '<label class="acct-field"><span class="acct-label">World of Warcraft account name</span> '
        '<input class="acct-input" name="game_name" required maxlength="16" '
        'autocomplete="username" placeholder="World of Warcraft account name"></label>'
    )


def _mark() -> str:
    return '<p class="bn-mark" aria-hidden="true"><span>Blizzard</span> Entertainment</p>'


def _social() -> str:
    return (
        '<div class="bn-or"><span>Or log in with</span></div>'
        '<div class="bn-social" aria-hidden="true">'
        '<span class="bn-fb">f</span><span class="bn-g">G</span><span class="bn-apple">A</span>'
        "</div>"
    )


def _login(login_kind: str) -> str:
    return (
        '<div class="bn-card">'
        f"{_mark()}"
        '<h3 class="acct-panel-title">Sign in</h3>'
        '<form class="acct-form" method="post" action="/account/login">'
        f"{_identity_field(login_kind)}"
        '<label class="acct-field"><span class="acct-label">Password</span> '
        '<input class="acct-input" type="password" name="password" required '
        'autocomplete="current-password" placeholder="Password"></label>'
        '<button class="acct-submit" type="submit">Log In</button>'
        "</form>"
        f"{_social()}"
        '<p class="acct-switch"><a class="acct-link" href="/account/create">Create a Free Battle.net Account</a></p>'
        '<p class="acct-note">There is no emailed password reset. '
        "Sign in and change the password here.</p>"
        '<p class="acct-switch"><a class="acct-link" href="/support/password">Can\'t log in?</a></p>'
        "</div>"
    )


def _create(login_kind: str, separate_game_name: bool) -> str:
    return (
        '<div class="bn-card">'
        f"{_mark()}"
        '<h3 class="acct-panel-title">Create account</h3>'
        '<form class="acct-form" method="post" action="/account/create">'
        f"{_identity_field(login_kind)}"
        f"{_game_field(separate_game_name)}"
        '<label class="acct-field"><span class="acct-label">Password</span> '
        '<input class="acct-input" type="password" name="password" required '
        'autocomplete="new-password" placeholder="Password"></label>'
        '<label class="acct-field"><span class="acct-label">Confirm password</span> '
        '<input class="acct-input" type="password" name="confirm" required '
        'autocomplete="new-password" placeholder="Confirm password"></label>'
        '<button class="acct-submit" type="submit">Create Account</button>'
        "</form>"
        '<p class="acct-switch"><a class="acct-link" href="/account/login">Log In</a></p>'
        "</div>"
    )


def _password() -> str:
    return (
        '<div class="acct-block acct-security">'
        '<h3 class="acct-panel-title">Security</h3>'
        '<p class="acct-note">Change the password on this account. '
        "Sign in with it the next time you play.</p>"
        '<form class="acct-form" method="post" action="/account/password">'
        '<label class="acct-field"><span class="acct-label">Current password</span> '
        '<input class="acct-input" type="password" name="current" required '
        'autocomplete="current-password"></label>'
        '<label class="acct-field"><span class="acct-label">New password</span> '
        '<input class="acct-input" type="password" name="password" required '
        'autocomplete="new-password"></label>'
        '<label class="acct-field"><span class="acct-label">Confirm new password</span> '
        '<input class="acct-input" type="password" name="confirm" required '
        'autocomplete="new-password"></label>'
        '<button class="acct-submit" type="submit">Change Password</button>'
        "</form>"
        '<p class="acct-switch"><a class="acct-link" href="/account/">Back to Account</a></p>'
        "</div>"
    )


def _characters(characters: list) -> str:
    items: list[str] = []
    for c in characters or []:
        if not isinstance(c, dict):
            continue
        items.append(
            '<li class="acct-char">'
            f'<span class="acct-char-name">{_e(c.get("name"))}</span>'
            f'<span class="acct-char-level">{_e(c.get("level"))}</span>'
            f'<span class="acct-char-class">{_e(c.get("class_name"))}</span>'
            "</li>"
        )
    if not items:
        return '<p class="acct-empty">No characters on this realm yet.</p>'
    return f'<ul class="acct-chars">{"".join(items)}</ul>'


def _summary(user: str, email: str, characters: list) -> str:
    return (
        '<div class="acct-block" id="games">'
        '<h3 class="acct-panel-title">Games &amp; Subscriptions</h3>'
        '<section class="bn-panel"><h4 class="acct-subhead">Game Accounts</h4>'
        '<div class="bn-game">'
        '<span class="bn-w" aria-hidden="true">W</span>'
        '<div><strong>World of Warcraft</strong>'
        f'<span class="bn-sub">{_e(email)}</span>'
        '<span class="bn-sub">Game account</span></div>'
        f'<div><strong class="acct-fact-value">{_e(user)}</strong>'
        '<span class="bn-sub">Account Status</span><span class="bn-sub">Active</span></div>'
        "</div>"
        '<dl class="acct-facts">'
        '<div class="acct-fact"><dt class="acct-fact-label">Email</dt>'
        f'<dd class="acct-fact-value">{_e(email)}</dd></div>'
        '<div class="acct-fact"><dt class="acct-fact-label">Game account</dt>'
        f'<dd class="acct-fact-value">{_e(user)}</dd></div>'
        "</dl>"
        '<h4 class="acct-subhead">Characters</h4>'
        f"{_characters(characters)}"
        '<p class="acct-actions">'
        '<a class="acct-link" href="/account/password">Change Password</a>'
        '<a class="acct-link" href="/account/logout">Log Out</a>'
        "</p></section></div>"
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
    _ = exp
    if mode == "summary":
        body = _summary(user, email, characters)
        kind = "acct-manage"
    elif mode == "create":
        body = _create(login_kind, separate_game_name)
        kind = "acct-gate"
    elif mode == "password":
        body = _password()
        kind = "acct-manage"
    else:
        body = _login(login_kind)
        kind = "acct-gate"
    rail = _rail(mode) if kind == "acct-manage" else ""
    return (
        f'<section class="acct acct-shadowlands {kind}">'
        '<header class="acct-mast">'
        f'<h2 class="acct-title">{ERA_TITLE}</h2>'
        "</header>"
        '<div class="acct-layout">'
        f"{rail}"
        f'<div class="acct-panel">{_alerts(error, notice)}{body}</div>'
        "</div>"
        "</section>"
    )
