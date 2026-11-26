"""Legion 7.3.5 Battle.net account settings.

Login is the email on the Battle.net account. The World of Warcraft account
name is a separate field. The creation form follows the 2017 field order in
English. The summary shows Legion active and Warlords expired, and it does
not invent a redacted account name.
"""

from __future__ import annotations

import html

ERA_TITLE = "Account Settings"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _alerts(error: str, notice: str) -> str:
    parts = []
    if error:
        parts.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        parts.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(parts)


def _identity_field(login_kind: str) -> str:
    if login_kind == "email":
        label, input_type, placeholder = "E-mail", "email", "E-mail"
    else:
        label, input_type, placeholder = "Account Name", "text", "Account Name"
    return (
        f'<label class="acct-field">{label} '
        f'<input name="identity" type="{input_type}" placeholder="{placeholder}" '
        f'required autocomplete="username"></label>'
    )


def _game_field(separate_game_name: bool) -> str:
    if not separate_game_name:
        return ""
    return (
        '<label class="acct-field">World of Warcraft account name '
        '<input name="game_name" required maxlength="16" autocomplete="username"></label>'
    )


def _nav(current: str) -> str:
    def item(mode: str, href: str, label: str) -> str:
        current_attr = ' class="acct-nav-current"' if mode == current else ""
        return f'<a{current_attr} href="{href}">{label}</a>'

    return (
        '<nav class="acct-nav" aria-label="Account Settings">'
        + item("summary", "/account/", "Overview")
        + item("games", "/shop", "Games &amp; Codes")
        + item("history", "/account/", "Transaction History")
        + item("password", "/account/password", "Password &amp; Security")
        + "</nav>"
    )


def _sheet(current: str, inner: str) -> str:
    return f'<div class="acct-layout">{_nav(current)}<div class="acct-main">{inner}</div></div>'


def _characters(characters: list) -> str:
    rows = []
    for entry in characters or []:
        if not isinstance(entry, dict):
            rows.append(f'<li class="acct-char"><span class="acct-char-name">{_e(entry)}</span></li>')
            continue
        rows.append(
            '<li class="acct-char">'
            f'<span class="acct-char-name">{_e(entry.get("name"))}</span>'
            f'<span class="acct-char-level">{_e(entry.get("level"))}</span>'
            f'<span class="acct-char-class">{_e(entry.get("class_name"))}</span>'
            "</li>"
        )
    if not rows:
        return '<p class="acct-empty">No characters on this account yet.</p>'
    body = "".join(rows)
    return (
        '<div class="acct-roster">'
        '<h3 class="acct-sub">Characters</h3>'
        '<div class="acct-char acct-char-head"><span>Name</span><span>Level</span><span>Class</span></div>'
        f'<ul class="acct-chars">{body}</ul>'
        "</div>"
    )


def _summary(user: str, email: str, characters: list) -> str:
    shown_email = _e(email) if email else "—"
    inner = (
        '<section class="acct-panel">'
        '<header class="manage-head">'
        '<p class="manage-word">Management</p>'
        '<form class="manage-search" action="/wow/search" method="get">'
        '<input type="search" name="q" placeholder="Search Battle.net" aria-label="Search Battle.net">'
        "</form>"
        '<p class="manage-balance">Balance: <strong>GBP 0.00</strong></p>'
        "</header>"
        '<p class="auth-banner">Protect your Blizzard Account with the free '
        '<a href="/account/password">Blizzard Mobile Authenticator</a>. '
        "The free Blizzard Mobile Authenticator adds an extra layer of security to your account.</p>"
        '<h3 class="acct-sub">Your Game Accounts</h3>'
        '<div class="game-accounts">'
        '<p class="game-family">World of Warcraft</p>'
        '<p class="acct-game"><span>World of Warcraft: Legion</span> '
        f'<span class="acct-who">{_e(user)}</span> '
        '<span class="acct-region">Europe (EU)</span> '
        '<span class="acct-active">Active</span></p>'
        '<p class="acct-game"><span>World of Warcraft: Warlords of Draenor</span> '
        '<span class="acct-expired">Time Expired</span></p>'
        "</div>"
        '<p class="acct-side">'
        '<a class="key-btn" href="/shop">Add a Game Key</a>'
        '<a href="/shop">Buy Digital Games</a>'
        '<a href="/support/">Merge a World of Warcraft Account</a>'
        "</p>"
        '<h3>Overview</h3>'
        f'<p class="acct-lead">Signed in as <strong class="acct-user">{_e(user)}</strong>.</p>'
        '<dl class="acct-facts">'
        '<div class="acct-fact"><dt>Email</dt>'
        f"<dd>{shown_email}</dd></div>"
        '<div class="acct-fact"><dt>World of Warcraft account name</dt>'
        f"<dd>{_e(user)}</dd></div>"
        "</dl>"
        f"{_characters(characters)}"
        '<p class="acct-actions">'
        '<a href="/account/password">Password &amp; Security</a>'
        '<a href="/account/logout">Log Out</a>'
        "</p>"
        "</section>"
    )
    return _sheet("summary", inner)


def _login(login_kind: str) -> str:
    return (
        '<div class="acct-card">'
        '<img class="blizz-logo" src="/static/img/legion/blizz-logo.jpg" alt="Blizzard Entertainment">'
        "<h3>Sign In</h3>"
        f'<form class="acct-form" method="post" action="/account/login">'
        f"{_identity_field(login_kind)}"
        '<label class="acct-field">Password '
        '<input type="password" name="password" placeholder="Password" required autocomplete="current-password"></label>'
        '<button type="submit">Log in to Blizzard</button>'
        "</form>"
        '<p class="acct-or"><span>OR</span></p>'
        '<button class="fb-btn" type="button">Log in with Facebook</button>'
        '<p class="acct-actions"><a href="/account/create">Create a Free Blizzard Account</a></p>'
        '<p class="acct-actions"><a href="/support/password">Can\'t log in?</a></p>'
        '<p class="acct-hint">There is no emailed password reset. Sign in and change the password here.</p>'
        '<p class="acct-legal"><a href="/support/">Battle.net EULA</a> · '
        '<a href="/support/">Privacy</a> · <a href="/support/">Terms</a> · '
        '<a href="/support/">Copyright Infringement</a></p>'
        "</div>"
    )


def _birth() -> str:
    months = (
        "Month",
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    options = "".join(f'<option value="{index}">{label}</option>' for index, label in enumerate(months))
    return (
        '<fieldset class="acct-birth"><legend>Birth date</legend>'
        '<label>Year <input name="birth_year" inputmode="numeric" maxlength="4" placeholder="Year"></label>'
        f'<label>Month <select name="birth_month">{options}</select></label>'
        '<label>Day <input name="birth_day" inputmode="numeric" maxlength="2" placeholder="Day"></label>'
        "</fieldset>"
    )


def _create(login_kind: str, separate_game_name: bool) -> str:
    countries = ("United States", "United Kingdom", "Canada", "Australia", "Germany", "France", "Japan")
    options = "".join(f'<option>{_e(name)}</option>' for name in countries)
    return (
        '<div class="acct-card">'
        '<img class="blizz-logo" src="/static/img/legion/blizz-logo.jpg" alt="Blizzard Entertainment">'
        "<h3>Create Account</h3>"
        '<button class="fb-btn" type="button">Sign up with Facebook</button>'
        '<p class="acct-or"><span>or</span></p>'
        '<p class="acct-lead">Create a Blizzard account and start the adventure.</p>'
        '<form class="acct-form" method="post" action="/account/create">'
        f'<label class="acct-field">Country <select name="country">{options}</select></label>'
        '<div class="acct-names">'
        '<label class="acct-field">First name <input name="first_name" autocomplete="given-name"></label>'
        '<label class="acct-field">Last name <input name="last_name" autocomplete="family-name"></label>'
        "</div>"
        f"{_birth()}"
        f"{_identity_field(login_kind)}"
        f'<label class="acct-field">Confirm email '
        f'<input name="email_confirm" type="{"email" if login_kind == "email" else "text"}" '
        f'autocomplete="email"></label>'
        f"{_game_field(separate_game_name)}"
        '<label class="acct-field">Password '
        '<input type="password" name="password" placeholder="Password" required autocomplete="new-password"></label>'
        '<label class="acct-field">Confirm password '
        '<input type="password" name="confirm" placeholder="Confirm password" required autocomplete="new-password"></label>'
        '<label class="acct-field">Security question <select name="security_question">'
        '<option value="">Choose a question</option>'
        "<option>Name of your first pet</option>"
        "<option>City where you were born</option>"
        "<option>Favorite book</option>"
        "</select></label>"
        '<label class="acct-field">Secret answer <input name="secret_answer" autocomplete="off"></label>'
        '<label class="acct-check"><input type="checkbox" name="news"> '
        "Receive news and special offers</label>"
        '<button type="submit">Create Free Account</button>'
        "</form>"
        '<p class="acct-actions"><a href="/account/login">Already have an account?</a></p>'
        '<p class="acct-fine">By clicking Create Free Account, you agree to the '
        '<a href="/support/">Battle.net End User License Agreement</a> and '
        '<a href="/support/">Privacy Policy</a>.</p>'
        '<footer class="acct-copy"><p>©2017 Blizzard Entertainment, Inc.</p>'
        '<p><a href="/support/">Careers</a> · <a href="/support/">About</a> · '
        '<a href="/support/">Support</a> · <a href="/support/">Press</a> · <a href="/support/">API</a></p>'
        '<p><a href="/support/">Privacy</a> · <a href="/support/">Terms</a></p></footer>'
        "</div>"
    )


def _password() -> str:
    inner = (
        '<section class="acct-panel">'
        "<h3>Password &amp; Security</h3>"
        '<p class="acct-hint">Change the password for this Battle.net login.</p>'
        '<form class="acct-form" method="post" action="/account/password">'
        '<label class="acct-field">Current password '
        '<input type="password" name="current" required autocomplete="current-password"></label>'
        '<label class="acct-field">New password '
        '<input type="password" name="password" required autocomplete="new-password"></label>'
        '<label class="acct-field">Confirm new password '
        '<input type="password" name="confirm" required autocomplete="new-password"></label>'
        '<button type="submit">Change Password</button>'
        "</form>"
        '<p class="acct-actions"><a href="/account/">Back to Account</a></p>'
        "</section>"
    )
    return _sheet("password", inner)


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
    del exp
    if mode == "create":
        shown, body = "create", _create(login_kind, separate_game_name)
    elif mode == "password":
        shown, body = "password", _password()
    elif mode == "summary" and user:
        shown, body = "summary", _summary(user, email, characters)
    else:
        shown, body = "login", _login(login_kind)
    return (
        f'<section class="acct acct-legion acct-mode-{shown}">'
        '<header class="acct-mast">'
        '<p class="acct-brand">Battle.net</p>'
        f"<h2 class=\"acct-title\">{ERA_TITLE}</h2>"
        "</header>"
        f"{_alerts(error, notice)}"
        f"{body}"
        "</section>"
    )
