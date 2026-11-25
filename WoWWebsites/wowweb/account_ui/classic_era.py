"""Classic Era account pages. Email is the Battle.net login."""

from __future__ import annotations

import html

ERA_TITLE = "Account Management"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _messages(error: str, notice: str) -> str:
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


def _login(login_kind: str) -> str:
    label, input_type = _identity(login_kind)
    return f"""<h3 class="acct-sub">Sign In</h3>
<p class="acct-lead">There is no emailed password reset. Sign in and change the password here.</p>
<form class="acct-form" method="post" action="/account/login">
  <label>{label} <input name="identity" type="{input_type}" required autocomplete="username"></label>
  <label>Password <input type="password" name="password" required autocomplete="current-password"></label>
  <button type="submit">Log In</button>
</form>
<p class="acct-note"><a href="/account/create">Create Account</a></p>"""


def _create(login_kind: str, separate_game_name: bool) -> str:
    label, input_type = _identity(login_kind)
    game = ""
    if separate_game_name:
        game = (
            '<label>World of Warcraft account name '
            '<input name="game_name" required maxlength="16" autocomplete="off"></label>'
        )
    return f"""<h3 class="acct-sub">Create Account</h3>
<p class="acct-lead">Email is the login. The account name is the World of Warcraft name, up to 16 characters.</p>
<form class="acct-form" method="post" action="/account/create">
  <label>{label} <input name="identity" type="{input_type}" required autocomplete="username"></label>
  {game}
  <label>Password <input type="password" name="password" required autocomplete="new-password"></label>
  <label>Confirm password <input type="password" name="confirm" required autocomplete="new-password"></label>
  <button type="submit">Create Account</button>
</form>
<p class="acct-note"><a href="/account/login">Log In</a></p>"""


def _password() -> str:
    return """<h3 class="acct-sub">Change Password</h3>
<p class="acct-lead">There is no emailed password reset. Sign in and change the password here.</p>
<form class="acct-form" method="post" action="/account/password">
  <label>Current password <input type="password" name="current" required autocomplete="current-password"></label>
  <label>New password <input type="password" name="password" required autocomplete="new-password"></label>
  <label>Confirm new password <input type="password" name="confirm" required autocomplete="new-password"></label>
  <button type="submit">Change Password</button>
</form>
<p class="acct-note"><a href="/account/">Back to Account</a></p>"""


def _summary(exp, user: str, email: str, characters: list, login_kind: str) -> str:
    ident = email if login_kind == "email" and email else user
    rows = []
    for char in characters or []:
        if not isinstance(char, dict):
            continue
        rows.append(
            '<li class="acct-char">'
            f'<span class="acct-char-name">{_e(char.get("name"))}</span>'
            f'<span class="acct-char-meta">Level {_e(char.get("level"))} {_e(char.get("class_name"))}</span>'
            "</li>"
        )
    if rows:
        roster = f'<ul class="acct-chars">{"".join(rows)}</ul>'
    else:
        roster = '<p class="acct-meta">No characters on this realm yet.</p>'
    realm = _e(getattr(exp, "realm_name", "") or "")
    email_line = f'<p class="acct-meta">Email {_e(email)}</p>' if email else ""
    return f"""<h3 class="acct-sub">Overview</h3>
<p class="acct-signed">Signed in as <strong>{_e(ident)}</strong>.</p>
<p class="acct-meta">Game account <strong>{_e(user)}</strong> on {realm}.</p>
{email_line}
<h3 class="acct-sub">Characters</h3>
{roster}
<p class="acct-actions"><a href="/account/password">Change Password</a> · <a href="/account/logout">Log Out</a></p>"""


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
    if mode == "summary":
        main = _summary(exp, user, email, characters, login_kind)
    elif mode == "create":
        main = _create(login_kind, separate_game_name)
    elif mode == "password":
        main = _password()
    else:
        main = _login(login_kind)
    return (
        '<section class="acct-ce">'
        f'<h2 class="acct-title">{ERA_TITLE}</h2>'
        f"{_messages(error, notice)}"
        f"{main}"
        "</section>"
    )
