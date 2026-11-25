"""Battle for Azeroth (8.3.7) Battle.net account overview."""

from __future__ import annotations

import html

ERA_TITLE = "Account Overview"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _messages(error: str, notice: str) -> str:
    bits = []
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(bits)


def _identity(login_kind: str) -> str:
    if login_kind == "email":
        label, kind = "Email", "email"
    else:
        label, kind = "Account Name", "text"
    return (
        f'<label class="acct-label">{label}'
        f'<input class="acct-input" name="identity" type="{kind}" required autocomplete="username">'
        "</label>"
    )


def _cards(overview: str, security: str) -> str:
    return (
        '<div class="acct-layout">'
        f'<article class="acct-card acct-overview">{overview}</article>'
        f'<aside class="acct-card acct-security">{security}</aside>'
        "</div>"
    )


def _characters(characters: list) -> str:
    if not characters:
        return '<p class="acct-empty">No characters on this realm yet.</p>'
    items = []
    for c in characters:
        items.append(
            '<li class="acct-char">'
            f'<span class="acct-char-name">{_e(c.get("name"))}</span> '
            f'<span class="acct-char-meta">level {_e(c.get("level"))} {_e(c.get("class_name"))}</span>'
            "</li>"
        )
    return f'<ul class="acct-chars">{"".join(items)}</ul>'


def _login(login_kind: str) -> str:
    overview = (
        '<h3 class="acct-card-title">Sign In</h3>'
        '<p class="acct-copy">Sign in with the email on your Battle.net account.</p>'
        '<form class="acct-form" method="post" action="/account/login">'
        f"{_identity(login_kind)}"
        '<label class="acct-label">Password'
        '<input class="acct-input" type="password" name="password" required autocomplete="current-password">'
        "</label>"
        '<button class="acct-button" type="submit">Log In</button>'
        "</form>"
        '<p class="acct-links"><a href="/account/create">Create Account</a></p>'
    )
    security = (
        '<h3 class="acct-card-title">Security</h3>'
        "<p class=\"acct-copy\">There is no emailed password reset. "
        "Sign in and change the password here.</p>"
    )
    return _cards(overview, security)


def _create(login_kind: str, separate_game_name: bool) -> str:
    game = ""
    if separate_game_name:
        game = (
            '<label class="acct-label">World of Warcraft account name'
            '<input class="acct-input" name="game_name" required maxlength="16" autocomplete="username">'
            "</label>"
            '<p class="acct-hint">Up to 16 characters. This is the name you enter in the game.</p>'
        )
    overview = (
        '<h3 class="acct-card-title">Create Account</h3>'
        '<p class="acct-copy">The email is your Battle.net login. '
        "The World of Warcraft account name is separate.</p>"
        '<form class="acct-form" method="post" action="/account/create">'
        f"{_identity(login_kind)}"
        f"{game}"
        '<label class="acct-label">Password'
        '<input class="acct-input" type="password" name="password" required autocomplete="new-password">'
        "</label>"
        '<label class="acct-label">Confirm password'
        '<input class="acct-input" type="password" name="confirm" required autocomplete="new-password">'
        "</label>"
        '<button class="acct-button" type="submit">Create Account</button>'
        "</form>"
        '<p class="acct-links"><a href="/account/login">Log In</a></p>'
    )
    security = (
        '<h3 class="acct-card-title">Security</h3>'
        "<p class=\"acct-copy\">There is no emailed password reset. "
        "After you sign in, change the password on this page.</p>"
    )
    return _cards(overview, security)


def _password(user: str) -> str:
    who = f" Signed in as <strong>{_e(user)}</strong>." if user else ""
    overview = (
        '<h3 class="acct-card-title">Change Password</h3>'
        f"<p class=\"acct-copy\">Enter the current Battle.net password, then choose a new one.{who}</p>"
        '<form class="acct-form" method="post" action="/account/password">'
        '<label class="acct-label">Current Battle.net password'
        '<input class="acct-input" type="password" name="current" required autocomplete="current-password">'
        "</label>"
        '<label class="acct-label">New password'
        '<input class="acct-input" type="password" name="password" required autocomplete="new-password">'
        "</label>"
        '<label class="acct-label">Confirm new password'
        '<input class="acct-input" type="password" name="confirm" required autocomplete="new-password">'
        "</label>"
        '<button class="acct-button" type="submit">Change Password</button>'
        "</form>"
        '<p class="acct-links"><a href="/account/">Back to Account</a></p>'
    )
    security = (
        '<h3 class="acct-card-title">Security</h3>'
        "<p class=\"acct-copy\">There is no emailed password reset. "
        "The current Battle.net password is required to set a new one.</p>"
    )
    return _cards(overview, security)


def _summary(user: str, email: str, characters: list) -> str:
    overview = (
        '<h3 class="acct-card-title">Overview</h3>'
        '<dl class="acct-facts">'
        '<div class="acct-fact"><dt>Email</dt>'
        f"<dd>{_e(email)}</dd></div>"
        '<div class="acct-fact"><dt>Game account name</dt>'
        f"<dd>{_e(user)}</dd></div>"
        "</dl>"
        '<h4 class="acct-subhead">Characters</h4>'
        f"{_characters(characters)}"
    )
    security = (
        '<h3 class="acct-card-title">Security</h3>'
        '<p class="acct-copy">Change the Battle.net password, or sign out of this page.</p>'
        '<p class="acct-links"><a href="/account/password">Change Password</a></p>'
        '<p class="acct-links"><a href="/account/logout">Log Out</a></p>'
    )
    return _cards(overview, security)


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
    if mode == "summary" and user:
        body = _summary(user, email, characters)
    elif mode == "create":
        body = _create(login_kind, separate_game_name)
    elif mode == "password":
        body = _password(user)
    else:
        body = _login(login_kind)
    return (
        '<section class="acct acct-bfa">'
        '<header class="acct-bar">'
        '<p class="acct-brand">Battle.net</p>'
        f'<h2 class="acct-title">{ERA_TITLE}</h2>'
        f'<p class="acct-meta">{_e(exp.name)} · {_e(exp.last_patch)}</p>'
        "</header>"
        '<div class="acct-body">'
        f"{_messages(error, notice)}"
        f"{body}"
        "</div>"
        "</section>"
    )
