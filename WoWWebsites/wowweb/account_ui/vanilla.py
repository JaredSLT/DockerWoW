"""April 2006 community shell, December 2006 account summary inside it."""

from __future__ import annotations

import html

ERA_TITLE = "Account Management"
_BOX = "/new-hp/images/image-retailbox.gif"

_NAV = (
    ("summary", "/account/", "Account Summary"),
    ("password", "/account/password", "Change Password"),
    ("create", "/account/create", "Create Account"),
)


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _flash(error: str, notice: str) -> str:
    parts = []
    if error:
        parts.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        parts.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(parts)


def _wrap(panel: str) -> str:
    return (
        '<section class="acct-vanilla">'
        f'<h2 class="acct-heading">{ERA_TITLE}</h2>'
        f'<div class="acct-panel">{panel}</div>'
        "</section>"
    )


def _login() -> str:
    return """<h3 class="acct-sub">Log In</h3>
<p class="acct-help">Enter the account name and password you use to play.</p>
<form class="acct-form" method="post" action="/account/login">
  <label class="acct-field">Account Name <input name="identity" type="text" required maxlength="16"></label>
  <label class="acct-field">Password <input type="password" name="password" required></label>
  <button type="submit">Log In</button>
</form>
<p class="acct-help">There is no emailed password reset. Sign in and change the password here.</p>
<p class="acct-actions"><a href="/account/create">Create Account</a></p>
"""


def _create() -> str:
    return """<h3 class="acct-sub">Create Account</h3>
<p class="acct-help">Choose an account name of 3 to 16 letters, numbers, or underscores, and a password.</p>
<form class="acct-form" method="post" action="/account/create">
  <label class="acct-field">Account Name <input name="identity" type="text" required maxlength="16"></label>
  <label class="acct-field">Password <input type="password" name="password" required></label>
  <label class="acct-field">Confirm Password <input type="password" name="confirm" required></label>
  <button type="submit">Create Account</button>
</form>
<p class="acct-actions"><a href="/account/login">Log In</a></p>
"""


def _password() -> str:
    return """<h3 class="acct-sub">Change Password</h3>
<p class="acct-help">Enter your current password, then choose a new one for this account.</p>
<form class="acct-form" method="post" action="/account/password">
  <label class="acct-field">Current Password <input type="password" name="current" required></label>
  <label class="acct-field">New Password <input type="password" name="password" required></label>
  <label class="acct-field">Confirm New Password <input type="password" name="confirm" required></label>
  <button type="submit">Change Password</button>
</form>
<p class="acct-actions"><a href="/account/">Account Summary</a></p>
"""


def _manage() -> str:
    items = []
    for key, href, label in _NAV:
        mark = ' class="acct-here"' if key == "summary" else ""
        items.append(f'<li><a href="{href}"{mark}>{label}</a></li>')
    items.append('<li><a href="/account/services">Character Services</a></li>')
    return (
        '<aside class="acct-manage">'
        '<p class="acct-manage-title">Manage Your Account:</p>'
        f'<ul class="acct-manage-links">{"".join(items)}</ul>'
        '<p class="acct-manage-out"><a class="acct-logout" href="/account/logout">Logout</a></p>'
        "</aside>"
    )


def _summary(exp, user: str, email: str, characters: list) -> str:
    realm = getattr(exp, "realm_name", None)
    lead = (
        f"Characters on the {_e(realm)} realm."
        if realm
        else "Characters on this realm."
    )
    rows = []
    for char in characters or []:
        if not isinstance(char, dict):
            continue
        rows.append(
            "<tr>"
            f"<td>{_e(char.get('name'))}</td>"
            f"<td>{_e(char.get('level'))}</td>"
            f"<td>{_e(char.get('class_name'))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append(
            '<tr><td class="acct-empty" colspan="3">No characters on this realm yet.</td></tr>'
        )
    mail = _e(email) if email else "Not on file"
    return f"""{_manage()}
<p class="acct-welcome"><span class="acct-drop">W</span>elcome, <strong class="acct-name">{_e(user)}</strong>. Should you have any questions regarding your account, please contact World of Warcraft Support by email at <a href="mailto:billing@blizzard.com">billing@blizzard.com</a>. You may also call (800) 59-BLIZZARD from 9AM to 6PM Pacific Time, Monday through Friday, except holidays.</p>
<h3 class="acct-band">Upgrade Your Trial Account</h3>
<div class="acct-card">
  <img class="acct-box" src="{_BOX}" alt="World of Warcraft">
  <p class="acct-help">If this account is still a trial, upgrade it to keep playing. A retail box can also be unlocked with the authentication key in the game client.</p>
  <p class="acct-label">Upgrade Online Now</p>
  <p class="acct-actions"><a class="acct-btn" href="/shop">Upgrade Online Now</a></p>
  <p class="acct-label">Retail Authentication Key</p>
  <p class="acct-keys"><span class="acct-key"></span><span class="acct-key"></span><span class="acct-key"></span><span class="acct-key"></span></p>
  <p class="acct-fine">Blizzard Entertainment reserves the right to disable this feature based upon server space considerations.</p>
</div>
<div class="acct-split">
  <section class="acct-info">
    <h3 class="acct-band">Account Information</h3>
    <p class="acct-who">Account name <strong class="acct-name">{_e(user)}</strong></p>
    <p class="acct-help">Account Status Active</p>
    <p class="acct-lead">{lead}</p>
    <table class="acct-chars">
      <thead><tr><th>Name</th><th>Level</th><th>Class</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <p class="acct-actions"><a class="acct-btn" href="/account/password">Change Password</a></p>
  </section>
  <section class="acct-info">
    <h3 class="acct-band">Contact Information</h3>
    <p class="acct-mail">Email Address <span class="acct-email">{mail}</span></p>
    <p class="acct-help">Address and phone are not stored on this page.</p>
    <p class="acct-actions"><a href="/account/password">Change Password</a></p>
  </section>
</div>
<p class="acct-fine">Cancel Trial Account — trial accounts do not require cancellation. <a href="/support/">Learn more</a></p>
<p class="acct-actions"><a href="/account/create">Create Account</a></p>
"""


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
    # Account name is the login. A separate game name is never collected.
    del login_kind, separate_game_name
    flash = _flash(error, notice)
    if mode == "summary" and user:
        panel = _summary(exp, user, email, characters)
    elif mode == "create":
        panel = _create()
    elif mode == "password":
        panel = _password()
    else:
        panel = _login()
    return _wrap(flash + panel)
