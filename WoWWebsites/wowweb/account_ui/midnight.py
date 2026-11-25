"""Midnight account management: Battle.net login, creation, and games list."""

from __future__ import annotations

import html

ERA_TITLE = "Account Security"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _alerts(error: str, notice: str) -> str:
    bits = []
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(bits)


def _chars(characters: list) -> str:
    rows = []
    for char in characters or []:
        if not isinstance(char, dict):
            continue
        rows.append(
            "<li class=\"acct-char\">"
            f'<span class="acct-char-name">{_e(char.get("name"))}</span>'
            f'<span class="acct-char-level">level {_e(char.get("level"))}</span>'
            f'<span class="acct-char-class">{_e(char.get("class_name"))}</span>'
            "</li>"
        )
    if not rows:
        return '<p class="acct-empty">No characters on this realm yet.</p>'
    return f'<ul class="acct-chars">{"".join(rows)}</ul>'


def _top(user: str, email: str) -> str:
    who = _e(user) if user else "Account"
    mail = f'<span class="bnet-mail">{_e(email)}</span>' if email else ""
    return f"""<header class="bnet-top">
  <a class="bnet-logo" href="/account/">Battle.net</a>
  <nav class="bnet-tools">
    <a href="/support/">Support</a>
    <span class="bnet-user">{mail} {who}</span>
    <a href="/account/logout">Log Out</a>
  </nav>
</header>"""


def _nav(active: str) -> str:
    items = (
        ("overview", "/account/", "Account Overview"),
        ("details", "/account/", "Account Details"),
        ("games", "/account/", "Games & Subscriptions"),
        ("security", "/account/password", "Security"),
        ("privacy", "/support/", "Privacy & Communication"),
        ("payment", "/support/", "Payment Methods"),
    )
    links = []
    for key, href, label in items:
        cls = "acct-nav-link"
        current = ""
        if active == key:
            cls += " acct-nav-on"
            current = ' aria-current="page"'
        links.append(f'<a class="{cls}" href="{href}"{current}>{label}</a>')
    return '<nav class="acct-nav" aria-label="Account">' + "".join(links) + "</nav>"


def _shell(active: str, main: str, user: str = "", email: str = "") -> str:
    return (
        '<section class="acct-midnight" data-era-bare="1">'
        f"{_top(user, email)}"
        '<div class="acct-frame">'
        f"{_nav(active)}"
        f'<div class="acct-main"><h2 class="acct-title">{ERA_TITLE}</h2>{main}</div>'
        "</div></section>"
    )


def _login() -> str:
    buttons = ("Google", "Facebook", "Apple", "Discord", "Xbox", "PlayStation", "Nintendo", "Battle.net")
    social = "".join(f'<button type="button">{_e(name)}</button>' for name in buttons)
    return f"""<div class="bnet-gate" data-era-bare="1">
  <a class="bnet-logo" href="/wow/">Battle.net</a>
  <h1>Log in or sign up</h1>
  <form class="acct-form" method="post" action="/account/login">
    <label class="acct-field">Email or Phone
      <input class="acct-input" name="identity" type="text" required autocomplete="username">
    </label>
    <p class="acct-links"><a href="/account/login">Forgot email?</a></p>
    <button class="acct-btn" type="submit">Continue</button>
  </form>
  <p class="acct-fine">By continuing, you acknowledge our <a href="/support/">Privacy Policy</a>.</p>
  <p class="bnet-or"><span>OR</span></p>
  <div class="bnet-social" aria-hidden="true">{social}</div>
  <p class="acct-hint">There is no emailed password reset. Sign in and change the password here.</p>
  <p class="acct-links"><a href="/account/create">Create Account</a></p>
</div>"""


def _login_password(identity: str) -> str:
    return f"""<div class="bnet-gate" data-era-bare="1">
  <a class="bnet-logo" href="/wow/">Battle.net</a>
  <h1>Log in or sign up</h1>
  <form class="acct-form" method="post" action="/account/login">
    <input type="hidden" name="identity" value="{_e(identity)}">
    <p class="acct-email">{_e(identity)}</p>
    <label class="acct-field">Password
      <input class="acct-input" type="password" name="password" required autocomplete="current-password">
    </label>
    <button class="acct-btn" type="submit">Log In</button>
  </form>
  <p class="acct-links"><a href="/account/login">Use a different email</a></p>
</div>"""


def _create(separate_game_name: bool) -> str:
    game = ""
    if separate_game_name:
        game = """<fieldset class="bnet-step">
  <legend>Create Your BattleTag</legend>
  <p>This name is the World of Warcraft game account. It is not an email address.</p>
  <label class="acct-field">BattleTag
    <input class="acct-input" name="game_name" required maxlength="16" autocomplete="username">
  </label>
</fieldset>"""
    main = f"""<div class="bnet-create">
  <a class="bnet-logo" href="/wow/">Battle.net</a>
  <p class="bnet-kicker">Battle.net Account Creation</p>
  <form class="acct-form" method="post" action="/account/create">
    <fieldset class="bnet-step">
      <legend>What's Your Name?</legend>
      <p>Your real name may be used later to verify your identity when contacting Battle.net. By default, your name will not be publicly visible.</p>
      <label class="acct-field">First Name <input class="acct-input" name="first_name" autocomplete="given-name"></label>
      <label class="acct-field">Last Name <input class="acct-input" name="last_name" autocomplete="family-name"></label>
    </fieldset>
    <fieldset class="bnet-step">
      <legend>Identify Your Account</legend>
      <label class="acct-field">Email
        <input class="acct-input" name="identity" type="email" required autocomplete="username">
      </label>
    </fieldset>
    <fieldset class="bnet-step">
      <legend>Review Terms</legend>
      <label class="acct-check"><input type="checkbox" name="terms" required> I agree to the terms of use.</label>
    </fieldset>
    <fieldset class="bnet-step">
      <legend>Set Your Password</legend>
      <label class="acct-field">Password <input class="acct-input" type="password" name="password" required autocomplete="new-password"></label>
      <label class="acct-field">Confirm password <input class="acct-input" type="password" name="confirm" required autocomplete="new-password"></label>
    </fieldset>
    {game}
    <button class="acct-btn" type="submit">Create Account</button>
  </form>
  <p class="acct-links"><a href="/account/login">Go back</a></p>
</div>"""
    return _shell("overview", main)


def _password() -> str:
    main = """<h1>Security</h1>
<p class="acct-hint">Change the password for this account. Sign in and update it here.</p>
<form class="acct-form" method="post" action="/account/password">
  <label class="acct-field">Current password <input class="acct-input" type="password" name="current" required autocomplete="current-password"></label>
  <label class="acct-field">New password <input class="acct-input" type="password" name="password" required autocomplete="new-password"></label>
  <label class="acct-field">Confirm new password <input class="acct-input" type="password" name="confirm" required autocomplete="new-password"></label>
  <button class="acct-btn" type="submit">Change Password</button>
</form>
<p class="acct-links"><a href="/account/">Back to Account</a></p>"""
    return _shell("security", main)


def _summary(user: str, email: str, characters: list) -> str:
    main = f"""<div class="bnet-games">
  <h1>Games &amp; Subscriptions</h1>
  <section class="acct-license">
    <h3 class="acct-license-title">Games</h3>
    <p class="acct-game">World of Warcraft</p>
    <p class="acct-k">Email</p>
    <p class="acct-email">{_e(email)}</p>
    <p class="acct-game">Game account <strong class="acct-game-name">{_e(user)}</strong></p>
    <p class="acct-status">Active</p>
    {_chars(characters)}
  </section>
  <p class="acct-actions"><a href="/account/password">Change Password</a> · <a href="/account/logout">Log Out</a></p>
</div>"""
    return _shell("games", main, user, email)


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
    _ = exp, login_kind
    alerts = _alerts(error, notice)
    if mode == "summary" and user:
        return alerts + _summary(user, email, characters)
    if mode == "create":
        return alerts + _create(separate_game_name)
    if mode == "password":
        return alerts + _password()
    if mode == "login-password":
        return alerts + _login_password(email)
    return alerts + _login()
