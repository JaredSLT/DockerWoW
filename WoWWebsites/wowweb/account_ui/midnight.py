"""Midnight account management: Battle.net login, creation, and games list."""

from __future__ import annotations

import html

ERA_TITLE = "Account Security"

_LOGO = """<svg class="bnet-mark" viewBox="0 0 40 40" width="34" height="34" aria-hidden="true">
  <path fill="#148eff" d="M20 3c6.6 0 12 3.6 14.2 8.2-3.6.6-6.6.2-9.2-1.6.8 5.2.4 9.4-2.4 13.2-3.6-1.6-6-5.4-6.2-9.6.2-2.2 2.6-4.6 5.6-5.6-4.6 1-8.4 4.6-8.4 10.2C13.6 26.2 19 32 26 32c2.8 0 5.4-.8 7.4-2.4-1.8 4.6-6.4 7.8-11.8 7.8C13.2 37.4 6 30.2 6 21.4 6 11.6 12.4 3 20 3z"/>
</svg>"""


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
  <a class="bnet-logo" href="/account/">{_LOGO} Battle.net</a>
  <nav class="bnet-tools">
    <a href="/support/">Download Battle.net</a>
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
        ("parental", "/support/", "Parental Controls"),
        ("security", "/account/password", "Security"),
        ("privacy", "/support/", "Privacy & Communication"),
        ("connections", "/support/", "Connections"),
        ("payment", "/support/", "Payment Methods"),
        ("history", "/support/", "Transaction History"),
    )
    links = []
    for key, href, label in items:
        cls = "acct-nav-link"
        current = ""
        if active == key:
            cls += " acct-nav-on"
            current = ' aria-current="page"'
        links.append(f'<a class="{cls}" href="{href}"{current}>{label}</a>')
    links.append('<a class="acct-nav-link" href="/support/">Download Battle.net</a>')
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


def _social() -> str:
    buttons = (
        ("Google", "#fff", "#222", "G"),
        ("Facebook", "#1877f2", "#fff", "f"),
        ("Apple", "#111", "#fff", "A"),
        ("Discord", "#5865f2", "#fff", "D"),
        ("Xbox", "#107c10", "#fff", "X"),
        ("PlayStation", "#003791", "#fff", "P"),
        ("Nintendo", "#e60012", "#fff", "N"),
        ("Battle.net", "#fff", "#148eff", "B"),
    )
    bits = []
    for name, bg, fg, mark in buttons:
        glyph = mark or ""
        bits.append(
            f'<button type="button" aria-label="{_e(name)}" style="background:{bg};color:{fg}">'
            f"{glyph}</button>"
        )
    return "".join(bits)


def _login() -> str:
    return f"""<div class="bnet-gate" data-era-bare="1">
  <a class="bnet-logo" href="/wow/">{_LOGO} Battle.net</a>
  <h1>Log in or sign up</h1>
  <form class="acct-form" method="post" action="/account/login">
    <label class="acct-field"><span class="mn-sr">Email or Phone</span>
      <input class="acct-input" name="identity" type="text" required autocomplete="username" placeholder="Email or Phone">
    </label>
    <p class="acct-links"><a href="/account/login">Forgot email?</a></p>
    <button class="acct-btn" type="submit">Continue</button>
  </form>
  <p class="acct-fine">By continuing, you acknowledge our <a href="/support/">Privacy Policy</a>.</p>
  <p class="bnet-or"><span>OR</span></p>
  <div class="bnet-social">{_social()}</div>
  <p class="acct-hint mn-sr">There is no emailed password reset. Sign in and change the password here.</p>
  <p class="acct-links"><a href="/account/create">Create Account</a></p>
</div>"""


def _login_password(identity: str) -> str:
    return f"""<div class="bnet-gate" data-era-bare="1">
  <a class="bnet-logo" href="/wow/">{_LOGO} Battle.net</a>
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
    game_radio = ""
    if separate_game_name:
        game_radio = '<input class="bnet-step-radio" type="radio" name="mn_step" id="mn-step-tag">'
        game = """<section class="bnet-pane pane-tag">
  <p class="bnet-kicker">Battle.net Account Creation</p>
  <h1>Create Your BattleTag</h1>
  <p>This name is the World of Warcraft game account. It is not an email address.</p>
  <label class="acct-field">BattleTag
    <input class="acct-input" name="game_name" required maxlength="16" autocomplete="username">
  </label>
  <button class="acct-btn" type="submit">Continue</button>
  <p class="acct-links"><label for="mn-step-pass">Go back</label></p>
</section>"""
    submit = "" if separate_game_name else '<button class="acct-btn" type="submit">Continue</button>'
    return f"""<div class="bnet-create" data-era-bare="1">
  <h2 class="acct-title">{ERA_TITLE}</h2>
  <form class="acct-form" method="post" action="/account/create">
    <input class="bnet-step-radio" type="radio" name="mn_step" id="mn-step-name" checked>
    <input class="bnet-step-radio" type="radio" name="mn_step" id="mn-step-id">
    <input class="bnet-step-radio" type="radio" name="mn_step" id="mn-step-terms">
    <input class="bnet-step-radio" type="radio" name="mn_step" id="mn-step-pass">
    {game_radio}
    <section class="bnet-pane pane-name">
      <a class="bnet-logo" href="/wow/">{_LOGO} Battle.net</a>
      <p class="bnet-kicker">Battle.net Account Creation</p>
      <h1>What's Your Name?</h1>
      <p>Your real name may be used later to verify your identity when contacting Battle.net. By default, your name will not be publicly visible. <a href="/support/">Learn More</a></p>
      <label class="acct-field"><span class="mn-sr">First Name</span><input class="acct-input" name="first_name" autocomplete="given-name" placeholder="First Name"></label>
      <label class="acct-field"><span class="mn-sr">Last Name</span><input class="acct-input" name="last_name" autocomplete="family-name" placeholder="Last Name"></label>
      <label class="acct-btn" for="mn-step-id">Continue</label>
      <p class="acct-links"><a href="/account/login">Go back</a></p>
      <p class="bnet-dots" aria-hidden="true"><i class="on"></i><i></i><i></i><i></i><i></i></p>
    </section>
    <section class="bnet-pane pane-id">
      <a class="bnet-logo" href="/wow/">{_LOGO} Battle.net</a>
      <h1>Identify Your Account</h1>
      <label class="acct-field">Email
        <input class="acct-input" name="identity" type="email" required autocomplete="username">
      </label>
      <label class="acct-btn" for="mn-step-terms">Continue</label>
      <p class="acct-links"><label for="mn-step-name">Go back</label></p>
    </section>
    <section class="bnet-pane pane-terms">
      <a class="bnet-logo" href="/wow/">{_LOGO} Battle.net</a>
      <h1>Review Terms</h1>
      <label class="acct-check"><input type="checkbox" name="terms" required> I agree to the terms of use.</label>
      <label class="acct-btn" for="mn-step-pass">Continue</label>
      <p class="acct-links"><label for="mn-step-id">Go back</label></p>
    </section>
    <section class="bnet-pane pane-pass">
      <a class="bnet-logo" href="/wow/">{_LOGO} Battle.net</a>
      <h1>Set Your Password</h1>
      <label class="acct-field">Password <input class="acct-input" type="password" name="password" required autocomplete="new-password"></label>
      <label class="acct-field">Confirm password <input class="acct-input" type="password" name="confirm" required autocomplete="new-password"></label>
      {submit}
      <p class="acct-links">{'<label for="mn-step-tag">Continue</label>' if separate_game_name else ''}<label for="mn-step-terms">Go back</label></p>
    </section>
    {game}
  </form>
</div>"""


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
    <h2 class="acct-license-title">Games</h2>
    <article class="bnet-row">
      <span class="bnet-wowmark" aria-hidden="true">W</span>
      <div>
        <p class="acct-game">World of Warcraft® (<strong class="acct-game-name">{_e(user)}</strong>)</p>
        <p>Americas &amp; Oceania</p>
      </div>
      <div class="bnet-cell"><b class="acct-status">Active</b><small>Status</small></div>
      <div class="bnet-cell"><a href="/account/services">Manage</a></div>
    </article>
    <p class="acct-k">Email</p>
    <p class="acct-email">{_e(email)}</p>
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
