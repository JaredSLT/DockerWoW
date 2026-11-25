"""Wrath of the Lich King account page (3.3.5a, 2009–2010).

Account-name login. The community shell picks Battle.net chrome for this
inner HTML, and the parchment signup sheet for account creation.
"""

from __future__ import annotations

import html

ERA_TITLE = "Manage Your Account"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _messages(error: str, notice: str) -> str:
    bits = []
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(bits)


def _login(era: str) -> str:
    return f"""<div class="acct-panel">
  <p class="acct-kicker">Battle.net Account</p>
  <h3 class="acct-heading">Account Login</h3>
  <div class="acct-login-grid">
    <form class="acct-form" method="post" action="/account/login">
      <label class="acct-field">Account Name
        <input name="identity" type="text" required autocomplete="username">
      </label>
      <label class="acct-field">Password
        <input type="password" name="password" required autocomplete="current-password">
      </label>
      <button type="submit">Log In</button>
    </form>
    <div class="acct-side">
      <h3>Need an account?</h3>
      <p>Sign in with the account name you use in the {_e(era)} client.</p>
      <a class="acct-cta" href="/account/create">Create an Account</a>
    </div>
  </div>
  <p class="acct-note">There is no emailed password reset. Sign in and change the password here.</p>
  <p class="acct-links"><a href="/account/create">Create Account</a></p>
</div>"""


def _create() -> str:
    return """<div class="acct-panel">
  <h3 class="acct-heading">Create Account</h3>
  <p class="acct-lead">Choose the account name you will type at the login screen.</p>
  <form class="acct-form" method="post" action="/account/create">
    <label class="acct-field">Account Name
      <input name="identity" type="text" required autocomplete="username">
    </label>
    <label class="acct-field">Password
      <input type="password" name="password" required autocomplete="new-password">
    </label>
    <label class="acct-field">Confirm password
      <input type="password" name="confirm" required autocomplete="new-password">
    </label>
    <button type="submit">Create Account</button>
  </form>
  <div class="acct-terms">
    <h3>Terms of Use</h3>
    <p>This account name is what you type at the World of Warcraft login screen. There is no separate game name on this form.</p>
  </div>
  <p class="acct-links"><a href="/account/login">Log In</a></p>
</div>"""


def _password() -> str:
    return """<div class="acct-panel acct-password">
  <h3 class="acct-heading">Change Password</h3>
  <p class="acct-lead">Enter the current password, then choose a new one. There is no emailed reset.</p>
  <form class="acct-form" method="post" action="/account/password">
    <label class="acct-field">Current password
      <input type="password" name="current" required autocomplete="current-password">
    </label>
    <label class="acct-field">New password
      <input type="password" name="password" required autocomplete="new-password">
    </label>
    <label class="acct-field">Confirm new password
      <input type="password" name="confirm" required autocomplete="new-password">
    </label>
    <button type="submit">Change Password</button>
  </form>
  <p class="acct-links"><a href="/account/">Back to Account</a></p>
</div>"""


def _summary(user: str, characters: list) -> str:
    rows = []
    for character in characters or []:
        if not isinstance(character, dict):
            continue
        rows.append(
            "<tr>"
            f"<td>{_e(character.get('name'))}</td>"
            f"<td>{_e(character.get('level'))}</td>"
            f"<td>{_e(character.get('class_name'))}</td>"
            "</tr>"
        )
    body = "".join(rows) or (
        '<tr><td class="acct-empty" colspan="3">No characters on this realm yet.</td></tr>'
    )
    return f"""<div class="acct-summary">
  <p class="acct-kicker">Account Management</p>
  <h3 class="acct-heading">Account Home</h3>
  <h4>My Profile</h4>
  <p class="acct-name">Account name <strong>{_e(user)}</strong></p>
  <h4>Manage My Games</h4>
  <table class="acct-chars">
    <thead><tr><th>Name</th><th>Level</th><th>Class</th></tr></thead>
    <tbody>{body}</tbody>
  </table>
</div>
<p class="acct-links"><a href="/account/password">Change Password</a> · <a href="/account/logout">Log Out</a></p>"""


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
    # 3.3.5a signs in with the game account name. Email and a separate
    # Battle.net game name are not fields on this page.
    del email, login_kind, separate_game_name
    era = getattr(exp, "name", "") or "Wrath of the Lich King"
    mode_class = mode if mode in {"login", "create", "password", "summary"} else "login"
    if mode == "summary":
        panel = _summary(user, characters)
    elif mode == "create":
        panel = _create()
    elif mode == "password":
        panel = _password()
    else:
        panel = _login(era)
    return (
        '<section class="acct acct-wotlk">'
        f'<div class="acct-mode acct-mode-{mode_class}">'
        f'<h2 class="acct-title">{ERA_TITLE}</h2>'
        f"{_messages(error, notice)}"
        f"{panel}"
        "</div></section>"
    )
