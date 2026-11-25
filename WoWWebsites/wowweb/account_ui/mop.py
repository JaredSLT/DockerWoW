"""Mists of Pandaria account sheet: early Battle.net overview.

This realm signs in with the game account name. Email login and a
separate game_name field are not used, even if those flags are set.
"""

from __future__ import annotations

import html

ERA_TITLE = "Battle.net"

_IDENTITY = "Account Name"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _view(mode: str, user: str) -> str:
    if mode == "summary" and user:
        return "summary"
    if mode in {"create", "password"}:
        return mode
    return "login"


def _alerts(error: str, notice: str) -> str:
    bits = []
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    if not bits:
        return ""
    return f'<div class="acct-alerts">{"".join(bits)}</div>'


def _nav(view: str) -> str:
    if view not in {"summary", "password"}:
        return ""
    overview = " acct-nav-here" if view == "summary" else ""
    security = " acct-nav-here" if view == "password" else ""
    return (
        '<nav class="acct-nav">'
        f'<a class="acct-nav-link{overview}" href="/account/">Summary</a>'
        f'<a class="acct-nav-link{security}" href="/account/password">Password and Security</a>'
        "</nav>"
    )


def _head(view: str) -> str:
    return (
        '<header class="acct-head">'
        f'<p class="acct-brand">{ERA_TITLE}</p>'
        f"{_nav(view)}"
        "</header>"
    )


def _realm_line(exp) -> str:
    name = getattr(exp, "name", None)
    text = f"World of Warcraft · {name}" if name else "World of Warcraft"
    return f'<p class="acct-realm">{_e(text)}</p>'


def _characters(characters: list) -> str:
    rows = []
    for row in characters or []:
        if not isinstance(row, dict):
            continue
        name = _e(row.get("name"))
        level = _e(row.get("level"))
        klass = _e(row.get("class_name"))
        rows.append(
            '<li class="acct-char">'
            f'<span class="acct-char-name">{name}</span>'
            f'<span class="acct-char-meta">Level {level} {klass}</span>'
            "</li>"
        )
    if not rows:
        return '<p class="acct-empty">No characters on this realm yet.</p>'
    return f'<ul class="acct-chars">{"".join(rows)}</ul>'


def _login() -> str:
    return f"""<div class="acct-card">
  <h2 class="acct-title">Log In</h2>
  <form class="acct-form" method="post" action="/account/login">
    <label class="acct-label">{_IDENTITY}
      <input class="acct-input" name="identity" type="text" required maxlength="16" autocomplete="username">
    </label>
    <label class="acct-label">Password
      <input class="acct-input" type="password" name="password" required autocomplete="current-password">
    </label>
    <button class="acct-button" type="submit">Log In</button>
  </form>
  <p class="acct-fine">There is no emailed password reset. Sign in and change the password here.</p>
  <p class="acct-switch"><a class="acct-textlink" href="/account/create">Create a Free Account</a></p>
</div>"""


def _create() -> str:
    return f"""<div class="acct-card">
  <h2 class="acct-title">Create Account</h2>
  <form class="acct-form" method="post" action="/account/create">
    <label class="acct-label">{_IDENTITY}
      <input class="acct-input" name="identity" type="text" required maxlength="16" autocomplete="username">
    </label>
    <label class="acct-label">Password
      <input class="acct-input" type="password" name="password" required autocomplete="new-password">
    </label>
    <label class="acct-label">Confirm password
      <input class="acct-input" type="password" name="confirm" required autocomplete="new-password">
    </label>
    <button class="acct-button" type="submit">Create Account</button>
  </form>
  <p class="acct-switch"><a class="acct-textlink" href="/account/login">Log In</a></p>
</div>"""


def _password(user: str) -> str:
    who = ""
    if user:
        who = f'<p class="acct-signed">Signed in as <strong class="acct-user">{_e(user)}</strong>.</p>'
    return f"""<div class="acct-card">
  <h2 class="acct-title">Change Password</h2>
  {who}
  <form class="acct-form" method="post" action="/account/password">
    <label class="acct-label">Current password
      <input class="acct-input" type="password" name="current" required autocomplete="current-password">
    </label>
    <label class="acct-label">New password
      <input class="acct-input" type="password" name="password" required autocomplete="new-password">
    </label>
    <label class="acct-label">Confirm new password
      <input class="acct-input" type="password" name="confirm" required autocomplete="new-password">
    </label>
    <button class="acct-button" type="submit">Change Password</button>
  </form>
  <p class="acct-switch"><a class="acct-textlink" href="/account/">Back to Account</a></p>
</div>"""


def _summary(exp, user: str, characters: list) -> str:
    return f"""<h2 class="acct-title">Account Overview</h2>
<div class="acct-plate">
  <div class="acct-mark" aria-hidden="true"></div>
  <div class="acct-id">
    <p class="acct-kicker">{_IDENTITY}</p>
    <p class="acct-name">{_e(user)}</p>
    {_realm_line(exp)}
  </div>
</div>
<div class="acct-grid">
  <section class="acct-panel">
    <h3 class="acct-panel-title">Account Details</h3>
    <p class="acct-kicker">{_IDENTITY}</p>
    <p class="acct-name">{_e(user)}</p>
    {_realm_line(exp)}
  </section>
  <section class="acct-panel">
    <h3 class="acct-panel-title">Your Game Accounts</h3>
    <p class="acct-gamebar">World of Warcraft</p>
    <p class="acct-copy">World of Warcraft: Mists of Pandaria</p>
    <p class="acct-copy">{_e(user)}</p>
    <h3 class="acct-panel-title">Characters</h3>
    {_characters(characters)}
    <p class="acct-actions"><a class="acct-textlink" href="/account/services">Character Services</a></p>
  </section>
  <section class="acct-panel">
    <h3 class="acct-panel-title">Password and Security</h3>
    <p class="acct-copy">There is no emailed password reset. Sign in and change the password here.</p>
    <p class="acct-actions">
      <a class="acct-button" href="/account/password">Change Password</a>
      <a class="acct-button acct-key" href="/shop">Add a Game Key</a>
      <a class="acct-textlink" href="/account/logout">Log Out</a>
    </p>
  </section>
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
    view = _view(mode, user)
    if view == "summary":
        body = _summary(exp, user, characters)
    elif view == "create":
        body = _create()
    elif view == "password":
        body = _password(user)
    else:
        body = _login()
    # email, login_kind, and separate_game_name stay unused: account name only.
    del email, login_kind, separate_game_name
    return (
        f'<section class="acct-mop acct-{view}">'
        f"{_head(view)}"
        '<div class="acct-body">'
        f"{_alerts(error, notice)}{body}"
        "</div></section>"
    )
