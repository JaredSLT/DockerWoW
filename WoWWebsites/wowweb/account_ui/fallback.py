"""Generic account management used until an expansion module is present."""

from __future__ import annotations

import html

ERA_TITLE = "Account Management"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


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
    bits = [f'<section class="acct acct-fallback"><h2>{ERA_TITLE}</h2>']
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    if mode == "summary" and user:
        ident = email if login_kind == "email" and email else user
        bits.append(f"<p>Signed in as <strong>{_e(ident)}</strong>.</p>")
        if characters:
            items = "".join(
                f"<li>{_e(c.get('name'))} — level {_e(c.get('level'))} {_e(c.get('class_name'))}</li>"
                for c in characters
            )
            bits.append(f"<ul class=\"acct-chars\">{items}</ul>")
        else:
            bits.append("<p>No characters on this realm yet.</p>")
        bits.append(
            '<p><a href="/account/password">Change Password</a> · '
            '<a href="/account/logout">Log Out</a></p>'
        )
    elif mode == "create":
        label = "Email" if login_kind == "email" else "Account Name"
        input_type = "email" if login_kind == "email" else "text"
        game = ""
        if separate_game_name:
            game = (
                '<label>World of Warcraft account name '
                '<input name="game_name" required maxlength="16" autocomplete="username"></label>'
            )
        bits.append(
            f"""<form class="acct-form" method="post" action="/account/create">
  <label>{label} <input name="identity" type="{input_type}" required></label>
  {game}
  <label>Password <input type="password" name="password" required></label>
  <label>Confirm password <input type="password" name="confirm" required></label>
  <button type="submit">Create Account</button>
</form>
<p><a href="/account/login">Log In</a></p>"""
        )
    elif mode == "password":
        bits.append(
            """<form class="acct-form" method="post" action="/account/password">
  <label>Current password <input type="password" name="current" required></label>
  <label>New password <input type="password" name="password" required></label>
  <label>Confirm new password <input type="password" name="confirm" required></label>
  <button type="submit">Change Password</button>
</form>
<p><a href="/account/">Back to Account</a></p>"""
        )
    else:
        label = "Email" if login_kind == "email" else "Account Name"
        input_type = "email" if login_kind == "email" else "text"
        bits.append(
            f"""<form class="acct-form" method="post" action="/account/login">
  <label>{label} <input name="identity" type="{input_type}" required></label>
  <label>Password <input type="password" name="password" required></label>
  <button type="submit">Log In</button>
</form>
<p>There is no emailed password reset. Sign in and change the password here.</p>
<p><a href="/account/create">Create Account</a></p>"""
        )
    bits.append("</section>")
    return "".join(bits)
