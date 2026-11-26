"""Cataclysm-era Battle.net account panels.

Login is the game account name in an email-shaped dialog. There is no
separate game-account field and no emailed password reset.
"""

from __future__ import annotations

import html

ERA_TITLE = "Account Services"

_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_COUNTRIES = (
    "United States", "United Kingdom", "Canada", "Australia",
    "Brazil", "Mexico", "Argentina", "Chile", "Germany", "France",
    "Spain", "Russia", "Switzerland", "Other",
)


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _menu(active: str) -> str:
    entries = (
        ("summary", "/account/", "Account Summary"),
        ("password", "/account/password", "Change Password"),
        ("characters", "/account/services", "Character Services"),
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


def _options(values, placeholder: str) -> str:
    bits = [f'<option value="">{_e(placeholder)}</option>']
    for value in values:
        bits.append(f'<option>{_e(value)}</option>')
    return "".join(bits)


def _birth() -> str:
    months = _options(_MONTHS, "Month")
    days = _options([str(n) for n in range(1, 32)], "Day")
    years = _options([str(n) for n in range(2011, 1900, -1)], "Year")
    return (
        '<fieldset class="acct-birth">'
        "<legend>Date of Birth</legend>"
        f'<label>Month <select name="birth_month">{months}</select></label>'
        f'<label>Day <select name="birth_day">{days}</select></label>'
        f'<label>Year <select name="birth_year">{years}</select></label>'
        "</fieldset>"
    )


def _country() -> str:
    options = "".join(
        f'<option{" selected" if name == "United States" else ""}>{_e(name)}</option>'
        for name in _COUNTRIES
    )
    return (
        '<label class="acct-country">Country of Residence '
        f'<select name="country">{options}</select></label>'
    )


def _panel(mode: str, user: str, characters) -> str:
    if mode == "summary":
        chars = _characters(characters)
        return f"""<div class="acct-panel" id="acct-summary">
  <p class="acct-kicker">Account Management</p>
  <h3 class="acct-heading">Account Home</h3>
  <h3 class="acct-heading">My Profile</h3>
  <p class="acct-signed">Signed in as <strong class="acct-user">{_e(user)}</strong>.</p>
  <p class="acct-actions"><a href="/account/password">Change Password</a>
    <a href="/support/">Change Contact Info</a>
    <a href="/support/">Communication Preferences</a>
    <a href="/account/password">Change Security Options</a>
    <a href="/account/logout">Log Out</a></p>
</div>
<div class="acct-panel" id="acct-characters">
  <h3 class="acct-heading">Character Services</h3>
  {chars}
</div>
<div class="acct-panel" id="acct-games">
  <h3 class="acct-heading">Manage My Games</h3>
  <p class="acct-actions"><a href="/shop">Add or Upgrade a Game</a>
    <a href="/support/">Item Code Redemption</a>
    <a href="/support/">Parental Controls</a></p>
  <article class="acct-game">
    <h4>World of Warcraft: Cataclysm</h4>
    <p class="acct-actions"><a href="/wow/">Manage Game</a></p>
  </article>
</div>"""
    if mode == "create":
        return f"""<div class="acct-panel">
  <h3 class="acct-heading">Account Creation</h3>
  <p class="acct-privacy">We value and respect your privacy.
    <a href="/support/">Privacy Policy</a>.</p>
  <form class="acct-form" method="post" action="/account/create">
    {_country()}
    {_birth()}
    <div class="acct-namepair">
      <label>First Name <input name="first_name" type="text" autocomplete="given-name"></label>
      <label>Last Name <input name="last_name" type="text" autocomplete="family-name"></label>
    </div>
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
    return """<div class="acct-panel acct-dialog">
  <p class="bnet-wordmark"><span class="bnet-atom" aria-hidden="true"></span> Battle.net</p>
  <h3 class="acct-heading">Log In</h3>
  <form class="acct-form" method="post" action="/account/login">
    <label>Email Address <input name="identity" type="text" required autocomplete="username"></label>
    <label>Password <input type="password" name="password" required autocomplete="current-password"></label>
    <p class="acct-row">
      <button type="submit">Log In</button>
      <label class="acct-keep"><input type="checkbox" name="stay" checked> Keep me logged in</label>
    </p>
  </form>
  <p class="acct-note">There is no emailed password reset. Sign in and change the password here.</p>
  <p class="acct-help"><a href="/account/login">Can't log in?</a></p>
  <p class="acct-help"><a href="/support/">Learn how to protect your account!</a></p>
  <p class="acct-switch">Don't have an account yet? <a href="/account/create">Register now!</a></p>
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
    # The 2012 dialog says email. The field is still the game account name.
    del exp, email, login_kind, separate_game_name
    active = "password" if mode == "password" else ("summary" if mode == "summary" else "")
    bits = [
        f'<section class="acct acct-cata acct-mode-{_e(mode)}">',
        f'<h2 class="acct-title">{ERA_TITLE}</h2>',
    ]
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    bits.append('<div class="acct-layout">')
    if mode == "password":
        bits.append(_menu("password"))
    bits.append(f'<div class="acct-main">{_panel(mode, user, characters)}</div>')
    if mode == "login":
        bits.append(_menu(""))
    bits.append("</div></section>")
    return "".join(bits)
