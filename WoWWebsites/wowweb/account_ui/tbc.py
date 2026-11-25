"""Burning Crusade account page (2.4.3, 2008).

Account-name login. Two columns with a fel-green left rule.
The community chrome wraps this inner HTML.
"""

from __future__ import annotations

import html

ERA_TITLE = "Burning Crusade Account"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _messages(error: str, notice: str) -> str:
    bits = []
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(bits)


def _side(exp) -> str:
    realm = getattr(exp, "realm_name", "") or "The Burning Crusade"
    patch = getattr(exp, "last_patch", "") or "2.4.3"
    return f"""<aside class="acct-side">
  <p class="acct-realm">{_e(realm)}</p>
  <p class="acct-patch">Patch {_e(patch)}</p>
  <p class="acct-note">Use the account name from the game client. Sign in, then change the password here.</p>
</aside>"""


def _login(era: str) -> str:
    return f"""<div class="acct-panel">
  <h3 class="acct-heading">Log In</h3>
  <p class="acct-lead">Sign in with the account name you use for {_e(era)}.</p>
  <form class="acct-form" method="post" action="/account/login">
    <label class="acct-field">Account Name
      <input name="identity" type="text" required autocomplete="username">
    </label>
    <label class="acct-field">Password
      <input type="password" name="password" required autocomplete="current-password">
    </label>
    <button type="submit">Log In</button>
  </form>
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
    items = []
    for character in characters or []:
        if not isinstance(character, dict):
            continue
        items.append(
            "<li>"
            f'<span class="acct-char-name">{_e(character.get("name"))}</span> '
            f'<span class="acct-char-level">level {_e(character.get("level"))}</span> '
            f'<span class="acct-char-class">{_e(character.get("class_name"))}</span>'
            "</li>"
        )
    if not items:
        items.append('<li class="acct-empty">No characters on this realm yet.</li>')
    roster = "".join(items)
    return f"""<div class="acct-panel acct-summary">
  <p class="acct-name">Account name <strong>{_e(user)}</strong></p>
  <h3 class="acct-heading">Character Status</h3>
  <ul class="acct-chars">{roster}</ul>
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
    # 2.4.3 signs in with the game account name. Email and a separate
    # game name are not fields on this page.
    del email, login_kind, separate_game_name
    era = getattr(exp, "name", "") or "The Burning Crusade"
    if mode == "summary":
        panel = _summary(user, characters)
    elif mode == "create":
        panel = _create()
    elif mode == "password":
        panel = _password()
    else:
        panel = _login(era)
    return (
        '<section class="acct acct-tbc">'
        f'<h2 class="acct-title">{ERA_TITLE}</h2>'
        f"{_messages(error, notice)}"
        f'<div class="acct-cols"><div class="acct-main">{panel}</div>{_side(exp)}</div>'
        "</section>"
    )
