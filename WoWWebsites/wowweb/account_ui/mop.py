"""Mists of Pandaria account sheet: early Battle.net overview.

This realm signs in with the game account name. Email login and a
separate game_name field are not used, even if those flags are set.
"""

from __future__ import annotations

import html

ERA_TITLE = "Battle.net"
_IMG = "/static/img/mop"
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


def _options(values: list[str], selected: str = "") -> str:
    bits = []
    for value in values:
        mark = " selected" if value == selected else ""
        bits.append(f"<option{mark}>{_e(value)}</option>")
    return "".join(bits)


def _login() -> str:
    return f"""<div class="acct-card">
  <img class="acct-logo" src="{_IMG}/bnet-logo.png" alt="">
  <a class="acct-close" href="/wow/" aria-label="Close">×</a>
  <form class="acct-form" method="post" action="/account/login">
    <label class="acct-label"><span class="acct-clip">{_IDENTITY}</span>
      <input class="acct-input" name="identity" type="text" required maxlength="16" autocomplete="username">
    </label>
    <label class="acct-label"><span class="acct-clip">Password</span>
      <input class="acct-input" type="password" name="password" required autocomplete="current-password">
    </label>
    <button class="acct-button" type="submit">Log In</button>
  </form>
  <p class="acct-fine">There is no emailed password reset. Sign in and change the password here.</p>
  <p class="acct-switch"><a class="acct-textlink" href="/account/create">Create a Free Account</a></p>
</div>"""


def _create() -> str:
    days = _options([str(n) for n in range(1, 32)], "1")
    months = _options(
        ["January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"],
        "January",
    )
    years = _options([str(n) for n in range(2013, 1909, -1)], "1990")
    countries = _options(
        ["United States", "United Kingdom", "Canada", "Australia", "Germany", "France", "Brazil", "Russian Federation"],
        "United States",
    )
    questions = _options(
        ["Select a question", "What was the name of your first school?", "What was your first pet's name?", "In what city were you born?"],
        "Select a question",
    )
    return f"""<div class="acct-card">
  <h2 class="acct-title">Create an Account</h2>
  <p class="acct-privacy">We respect the privacy of our users and take steps to keep it secure. For more on how we store and use your personal information, read our <a class="acct-textlink" href="/support/">privacy policy</a>.</p>
  <form class="acct-form" method="post" action="/account/create">
    <label class="acct-label">Country of Residence
      <select class="acct-input" name="country">{countries}</select>
    </label>
    <div class="acct-birthrow">
      <span class="acct-label">Date of Birth</span>
      <span class="acct-birth">
        <select class="acct-input" name="bday" aria-label="Day">{days}</select>
        <select class="acct-input" name="bmonth" aria-label="Month">{months}</select>
        <select class="acct-input" name="byear" aria-label="Year">{years}</select>
      </span>
      <p class="acct-child">If you are creating an account for your child, <a class="acct-textlink" href="/support/">click here</a>.</p>
    </div>
    <label class="acct-label">Salutation
      <select class="acct-input" name="salutation">{_options(["Mr", "Ms"], "Mr")}</select>
    </label>
    <div class="acct-split">
      <label class="acct-label">First Name
        <input class="acct-input" name="first_name" type="text" maxlength="32" autocomplete="given-name">
      </label>
      <label class="acct-label">Last Name
        <input class="acct-input" name="last_name" type="text" maxlength="32" autocomplete="family-name">
      </label>
    </div>
    <label class="acct-label">{_IDENTITY}
      <input class="acct-input" name="identity" type="text" required maxlength="16" autocomplete="username">
    </label>
    <div class="acct-split">
      <label class="acct-label">Password
        <input class="acct-input" type="password" name="password" required autocomplete="new-password">
      </label>
      <label class="acct-label">Confirm Password
        <input class="acct-input" type="password" name="confirm" required autocomplete="new-password">
      </label>
    </div>
    <div class="acct-split">
      <label class="acct-label">Secret Question
        <select class="acct-input" name="secret_q">{questions}</select>
      </label>
      <label class="acct-label">Answer
        <input class="acct-input" name="secret_a" type="text" maxlength="64" autocomplete="off">
      </label>
    </div>
    <div class="acct-agree">
      <h3 class="acct-agree-title">Chat Agreement</h3>
      <div>
        <p class="acct-copy">Battle.net offers chat between your characters and other players. Those messages are not private. To keep the community safe, Blizzard may store and review chat and other communications.</p>
        <label class="acct-check"><input type="checkbox" name="chat_ok" required> I agree to let Blizzard store and review my in-game chat and other communications.</label>
        <label class="acct-check"><input type="checkbox" name="terms_ok" required> I accept the terms of the user agreement for my country of residence. If I am under 18, I agree that my parent or guardian has also read and accepted the user agreement on my behalf.</label>
        <label class="acct-check"><input type="checkbox" name="fraud_ok" required> I understand and accept the terms of the Agreement on Combating Fraud.</label>
      </div>
    </div>
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


def _summary(exp, user: str, characters: list) -> str:
    _ = exp
    who = _e(user)
    return f"""<h2 class="acct-title">Your Game Accounts</h2>
<div class="acct-sum">
  <aside class="acct-blur" aria-hidden="true"></aside>
  <div class="acct-games">
    <section class="acct-gamegroup">
      <h3 class="acct-gamebar">Diablo III</h3>
      <a class="acct-game" href="/shop"><span class="acct-gem acct-gem-d" aria-hidden="true">D</span><span><strong>Diablo® III</strong><small>(Standard Edition)</small></span></a>
    </section>
    <section class="acct-gamegroup">
      <h3 class="acct-gamebar">World of Warcraft</h3>
      <a class="acct-game" href="/wow/"><span class="acct-gem acct-gem-w" aria-hidden="true">W</span><span><strong>World of Warcraft®: Mists of Pandaria™</strong><small><span class="acct-kicker">{_IDENTITY}</span> {who}</small></span></a>
      <a class="acct-game" href="/account/create"><span class="acct-gem acct-gem-w" aria-hidden="true">W</span><span><strong>World of Warcraft®</strong><small>Play for Free</small></span></a>
      {_characters(characters)}
    </section>
    <section class="acct-gamegroup">
      <h3 class="acct-gamebar">StarCraft II</h3>
      <a class="acct-game" href="/shop"><span class="acct-gem acct-gem-s" aria-hidden="true">S</span><span><strong>StarCraft® II: Wings of Liberty®</strong></span></a>
    </section>
  </div>
  <aside class="acct-rail">
    <a class="acct-button" href="/shop">Add a Game Key</a>
    <a class="acct-textlink" href="/shop">Buy Digital Games</a>
    <a class="acct-textlink" href="/account/">Merge a World of Warcraft Account</a>
    <a class="acct-textlink" href="/wow/media/wallpapers">Download Game Clients</a>
    <a class="acct-textlink" href="/account/password">Beta Profile Settings</a>
    <a class="acct-textlink" href="/account/password">Password and Security</a>
    <a class="acct-textlink" href="/account/services">Character Services</a>
    <a class="acct-textlink" href="/account/logout">Log Out</a>
  </aside>
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
