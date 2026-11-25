"""Cataclysm 4.3.4 Services account panel.

Login is the game account name. There is no separate game-account field
and no emailed password reset.
"""

from __future__ import annotations

import html

ERA_TITLE = "Account Services"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _menu(active: str) -> str:
    entries = (
        ("summary", "/account/", "Account Summary"),
        ("password", "/account/password", "Change Password"),
        ("characters", "/account/#acct-characters", "Character Services"),
    )
    rows = []
    for key, href, label in entries:
        cls = "acct-link acct-active" if key == active else "acct-link"
        rows.append(f'<li class="acct-item"><a class="{cls}" href="{href}">{label}</a></li>')
    return (
        '<nav class="acct-nav" aria-label="Account Services">'
        f'<ul class="acct-menu">{"".join(rows)}</ul></nav>'
    )


def _characters(characters) -> str:
    rows = []
    for entry in characters or []:
        if isinstance(entry, dict):
            name = entry.get("name")
            level = entry.get("level")
            class_name = entry.get("class_name")
        else:
            name, level, class_name = entry, "", ""
        rows.append(
            '<li class="acct-char">'
            f'<span class="acct-name">{_e(name)}</span> '
            f'<span class="acct-level">level {_e(level)}</span> '
            f'<span class="acct-class">{_e(class_name)}</span>'
            "</li>"
        )
    if not rows:
        return '<p class="acct-empty">No characters on this realm yet.</p>'
    return f'<ul class="acct-chars">{"".join(rows)}</ul>'


def _panel(mode: str, user: str, characters) -> str:
    if mode == "summary":
        chars = _characters(characters)
        return f"""<div class="acct-panel" id="acct-summary">
  <p class="acct-kicker">Account Home</p>
  <h3 class="acct-heading">My Profile</h3>
  <p class="acct-signed">Signed in as <strong class="acct-user">{_e(user)}</strong>.</p>
  <p class="acct-actions"><a href="/account/password">Change Password</a>
    <a href="/account/logout">Log Out</a></p>
</div>
<div class="acct-panel" id="acct-characters">
  <h3 class="acct-heading">Character Services</h3>
  {chars}
</div>
<div class="acct-panel" id="acct-games">
  <h3 class="acct-heading">Manage My Games</h3>
  <p class="acct-note">World of Warcraft: Cataclysm</p>
  <p class="acct-actions"><a href="/wow/">Manage Game</a></p>
</div>"""
    if mode == "create":
        return """<div class="acct-panel">
  <h3 class="acct-heading">Create Account</h3>
  <form class="acct-form" method="post" action="/account/create">
    <label>Account Name <input name="identity" type="text" required autocomplete="username"></label>
    <label>Password <input type="password" name="password" required autocomplete="new-password"></label>
    <label>Confirm password <input type="password" name="confirm" required autocomplete="new-password"></label>
    <button type="submit">Create Account</button>
  </form>
  <p class="acct-switch"><a href="/account/login">Log In</a></p>
</div>"""
    if mode == "password":
        return """<div class="acct-panel">
  <h3 class="acct-heading">Change Password</h3>
  <form class="acct-form" method="post" action="/account/password">
    <label>Current password <input type="password" name="current" required autocomplete="current-password"></label>
    <label>New password <input type="password" name="password" required autocomplete="new-password"></label>
    <label>Confirm new password <input type="password" name="confirm" required autocomplete="new-password"></label>
    <button type="submit">Change Password</button>
  </form>
  <p class="acct-switch"><a href="/account/">Account Summary</a></p>
</div>"""
    return """<div class="acct-panel">
  <h3 class="acct-heading">Log In</h3>
  <form class="acct-form" method="post" action="/account/login">
    <label>Account Name <input name="identity" type="text" required autocomplete="username"></label>
    <label>Password <input type="password" name="password" required autocomplete="current-password"></label>
    <button type="submit">Log In</button>
  </form>
  <p class="acct-note">There is no emailed password reset. Sign in and change the password here.</p>
  <p class="acct-switch"><a href="/account/create">Create Account</a></p>
</div>"""


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
    # 4.3.4 keeps the game account name. Email login and a second name are ignored.
    del exp, email, login_kind, separate_game_name
    active = "password" if mode == "password" else ("summary" if mode == "summary" else "")
    bits = [
        '<section class="acct acct-cata">',
        '<p class="acct-brand">Battle.net</p>',
        f'<h2 class="acct-title">{ERA_TITLE}</h2>',
    ]
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    bits.append('<div class="acct-layout">')
    bits.append(_menu(active))
    bits.append(f'<div class="acct-main">{_panel(mode, user, characters)}</div>')
    bits.append("</div></section>")
    return "".join(bits)
