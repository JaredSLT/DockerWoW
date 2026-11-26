"""Dragonflight 10.2.7 Blizzard account page."""

from __future__ import annotations

import html

ERA_TITLE = "Blizzard Account"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _messages(error: str, notice: str) -> str:
    bits = []
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(bits)


def _nav(mode: str) -> str:
    current = "security" if mode == "password" else "overview" if mode in ("summary", "login") else ""
    items = (
        ("overview", "/account/", "Account Overview"),
        ("details", "/account/", "Account Details"),
        ("games", "/account/", "Games & Subscriptions"),
        ("parental", "/account/", "Parental Controls"),
        ("security", "/account/password", "Security"),
        ("privacy", "/account/", "Privacy & Communication"),
        ("connections", "/account/", "Connections"),
        ("payment", "/account/", "Payment Methods"),
        ("history", "/account/", "Transaction History"),
    )

    def link(key: str, href: str, label: str) -> str:
        cls = f"acct-nav-link acct-nav-{key}"
        aria = ""
        if key == current:
            cls += " acct-nav-current"
            aria = ' aria-current="page"'
        return f'<a class="{cls}" href="{href}"{aria}>{label}</a>'

    # Login still has to expose Overview and Security. The crop is the card.
    if mode in ("login", "create"):
        return (
            f'<nav class="acct-nav acct-sr" aria-label="{ERA_TITLE}">'
            f'<p class="acct-brand">{ERA_TITLE}</p>'
            f'{link("overview", "/account/", "Overview")}'
            f'{link("security", "/account/password", "Security")}'
            "</nav>"
        )
    links = "".join(link(key, href, label) for key, href, label in items)
    return (
        f'<nav class="acct-nav" aria-label="{ERA_TITLE}">'
        f'<p class="acct-brand acct-sr">{ERA_TITLE}</p>'
        f"{links}"
        "</nav>"
    )


def _top(mode: str) -> str:
    if mode in ("login", "create"):
        return ""
    return (
        '<header class="acct-top">'
        '<a class="acct-blizzard" href="/wow/"><img src="/static/img/dragonflight/blizz-logo.png" alt=""><span class="acct-sr">Blizzard</span></a>'
        '<nav class="acct-toplinks" aria-label="Blizzard">'
        '<a class="acct-toplink" href="/wow/">Games</a>'
        '<a class="acct-toplink" href="/shop">Shop</a>'
        '<a class="acct-toplink" href="/wow/news">News</a>'
        '<a class="acct-toplink" href="/esports">Esports</a>'
        "</nav>"
        '<a class="acct-support" href="/support/">Support</a>'
        "</header>"
    )


def _identity(login_kind: str) -> tuple[str, str]:
    if login_kind == "email":
        return "Email or Phone", "email"
    return "Account Name", "text"


def _socials() -> str:
    # Icons are cropped from the login photograph. The red arrow is not included.
    rows = (
        (
            ("acct-social-google", "Google", "social-google.png"),
            ("acct-social-facebook", "Facebook", "social-facebook.png"),
            ("acct-social-apple", "Apple", "social-apple.png"),
        ),
        (
            ("acct-social-xbox", "Xbox", "social-xbox.png"),
            ("acct-social-playstation", "PlayStation", "social-playstation.png"),
            ("acct-social-nintendo", "Nintendo", "social-nintendo.png"),
            ("acct-social-battlenet", "Battle.net", "social-battlenet.png"),
        ),
    )
    built = []
    for row in rows:
        buttons = "".join(
            f'<button class="acct-social {name}" type="button" aria-label="{label}"'
            f' style="background-image:url(\'/static/img/dragonflight/{image}\')"></button>'
            for name, label, image in row
        )
        built.append(f'<div class="acct-social-row">{buttons}</div>')
    return f'<div class="acct-socials">{"".join(built)}</div>'


def _login(login_kind: str) -> str:
    label, input_type = _identity(login_kind)
    return f"""<p class="acct-logo"><img class="acct-logo-img" src="/static/img/dragonflight/bnet-logo.png" alt=""><span class="acct-sr">BATTLE.NET</span></p>
<h3 class="acct-sub">Log In</h3>
{_socials()}
<p class="acct-or"><span>Or log in with</span></p>
<form class="acct-form" method="post" action="/account/login">
  <label class="acct-field"><span class="acct-sr">{label}</span> <input name="identity" type="{input_type}" required placeholder="{label}" autocomplete="username"></label>
  <label class="acct-field"><span class="acct-sr">Password</span> <input type="password" name="password" required placeholder="Password" autocomplete="current-password"></label>
  <button class="acct-submit" type="submit">Log In</button>
</form>
<p class="acct-lead acct-sr">There is no emailed password reset. Sign in and change the password here.</p>
<p class="acct-note"><a href="/account/create">Create Account</a></p>"""


def _create(login_kind: str, separate_game_name: bool) -> str:
    label, input_type = _identity(login_kind)
    game = ""
    if separate_game_name:
        game = (
            '<label class="acct-field">World of Warcraft license name '
            '<input name="game_name" required maxlength="16" autocomplete="off"></label>'
        )
    return f"""<p class="acct-logo"><img class="acct-logo-img" src="/static/img/dragonflight/bnet-logo.png" alt=""><span class="acct-sr">BATTLE.NET</span></p>
<h3 class="acct-sub">Create Account</h3>
<p class="acct-lead">Email is the Blizzard login. The license name is the World of Warcraft account, up to 16 characters. There is no emailed password reset.</p>
<form class="acct-form" method="post" action="/account/create">
  <label class="acct-field">{label} <input name="identity" type="{input_type}" required autocomplete="username"></label>
  {game}
  <label class="acct-field">Password <input type="password" name="password" required autocomplete="new-password"></label>
  <label class="acct-field">Confirm password <input type="password" name="confirm" required autocomplete="new-password"></label>
  <button class="acct-submit" type="submit">Create Account</button>
</form>
<p class="acct-note"><a href="/account/login">Log In</a></p>"""


def _password() -> str:
    return """<h3 class="acct-sub">Security</h3>
<h4 class="acct-subhead">Change Password</h4>
<p class="acct-lead">There is no emailed password reset. Sign in and change the password here.</p>
<form class="acct-form" method="post" action="/account/password">
  <label class="acct-field">Current password <input type="password" name="current" required autocomplete="current-password"></label>
  <label class="acct-field">New password <input type="password" name="password" required autocomplete="new-password"></label>
  <label class="acct-field">Confirm new password <input type="password" name="confirm" required autocomplete="new-password"></label>
  <button class="acct-submit" type="submit">Change Password</button>
</form>
<p class="acct-note"><a href="/account/">Back to Account</a></p>"""


def _summary(exp, user: str, email: str, characters: list) -> str:
    rows = []
    for char in characters or []:
        if not isinstance(char, dict):
            continue
        rows.append(
            '<li class="acct-char">'
            f'<span class="acct-char-name">{_e(char.get("name"))}</span>'
            f'<span class="acct-char-meta">Level {_e(char.get("level"))} {_e(char.get("class_name"))}</span>'
            "</li>"
        )
    if rows:
        char_block = f'<ul class="acct-chars">{"".join(rows)}</ul>'
    else:
        char_block = '<p class="acct-meta">No characters on this realm yet.</p>'
    realm = _e(getattr(exp, "realm_name", "") or "")
    # The August 2023 crop stops at Battle.net Balance. License and characters
    # stay under that line for the account page; they are not a game tile.
    return f"""<h3 class="acct-sub">Account Overview</h3>
<section class="acct-alert">
  <h3 class="acct-alert-title">The email address {_e(email)} is unverified.</h3>
  <p class="acct-alert-copy">Verifying your email address adds additional security and lets you recover your account if you ever can't access it.</p>
  <p class="acct-meta"><a class="acct-resend" href="/account/">Resend Verification Email</a></p>
</section>
<section class="acct-redeem">
  <h3 class="acct-block-title">Redeem a Code</h3>
  <div class="acct-redeem-row">
    <input class="acct-code" type="text" placeholder="XXXX-XXXX-XXXX-XXXX" aria-label="Redeem a code" disabled>
    <button class="acct-redeem-btn" type="button" disabled>Redeem Code</button>
  </div>
</section>
<section class="acct-balance">
  <h3 class="acct-block-title">Battle.net Balance</h3>
  <p class="acct-meta"><a href="/account/">Payment Methods</a></p>
</section>
<section class="acct-license">
  <h3 class="acct-block-title">World of Warcraft license</h3>
  <p class="acct-value">{_e(user)}</p>
  <p class="acct-meta">Game account name on {realm}.</p>
  <h3 class="acct-block-title">Characters</h3>
  {char_block}
</section>
<p class="acct-actions"><a href="/account/password">Change Password</a> · <a href="/account/logout">Log Out</a></p>"""


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
    if mode == "summary":
        main = _summary(exp, user, email, characters)
        mode_cls = "acct-mode-summary"
    elif mode == "create":
        main = _create(login_kind, separate_game_name)
        mode_cls = "acct-mode-create"
    elif mode == "password":
        main = _password()
        mode_cls = "acct-mode-password"
    else:
        main = _login(login_kind)
        mode_cls = "acct-mode-login"
    kicker = f"{_e(getattr(exp, 'name', '') or 'Dragonflight')} · {_e(getattr(exp, 'last_patch', '') or '10.2.7')}"
    return (
        f'<section class="acct-df {mode_cls}">'
        f"{_top(mode)}"
        '<div class="acct-frame">'
        f"{_nav(mode)}"
        '<div class="acct-main">'
        f'<p class="acct-kicker acct-sr">{kicker}</p>'
        f'<h2 class="acct-title acct-sr">{ERA_TITLE}</h2>'
        f"{_messages(error, notice)}"
        f"{main}"
        "</div></div></section>"
    )
