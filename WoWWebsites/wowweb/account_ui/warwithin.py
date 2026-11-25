"""The War Within Battle.net account: Sign-in & Security, overview, and the login gate."""

from __future__ import annotations

import html

ERA_TITLE = "Sign-in & Security"


def _e(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _alerts(error: str, notice: str) -> str:
    bits = []
    if error:
        bits.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        bits.append(f'<p class="acct-notice">{_e(notice)}</p>')
    return "".join(bits)


def _identity(login_kind: str) -> tuple[str, str, str]:
    if login_kind == "email":
        return "Email or Phone", "email", "Email or Phone"
    return "Account Name", "text", "Account Name"


def _gate_nav() -> str:
    # ERA_TITLE stays unescaped so the link text keeps a literal ampersand.
    return f"""<nav class="acct-menu acct-gate-nav" aria-label="Account">
  <a class="acct-navlink" href="/account/">Overview</a>
  <a class="acct-navlink" href="/account/password">{ERA_TITLE}</a>
</nav>"""


def _side(active: str) -> str:
    def item(href: str, label: str, key: str) -> str:
        cls = "acct-navlink is-current" if active == key else "acct-navlink"
        return f'<a class="{cls}" href="{href}">{label}</a>'

    overview = item("/account/", "Overview", "overview")
    security = item("/account/password", ERA_TITLE, "security")
    return f"""<nav class="acct-menu" aria-label="Account">
  {overview}
  <a class="acct-navlink" href="/account/">Account Details</a>
  <a class="acct-navlink" href="/account/services">Games &amp; Subscriptions</a>
  <a class="acct-navlink" href="/support/">Parental Controls</a>
  {security}
  <a class="acct-navlink" href="/support/">Privacy &amp; Communication</a>
  <a class="acct-navlink" href="/account/">Connections</a>
  <a class="acct-navlink" href="/account/">Payment Methods</a>
  <a class="acct-navlink" href="/account/">Transaction History</a>
  <a class="acct-navlink" href="/wow/">Download Battle.net</a>
</nav>"""


def _top(show_logout: bool) -> str:
    logout = '<a href="/account/logout">Log Out</a>' if show_logout else ""
    return f"""<header class="bnet-top">
  <a class="bnet-brand" href="/account/"><i aria-hidden="true"></i>Battle.net</a>
  <nav class="bnet-topnav" aria-label="Battle.net">
    <a href="/wow/">Download Battle.net</a>
    <a href="/support/">Support</a>
    <a href="/account/">Account</a>
    {logout}
  </nav>
</header>"""


def _social() -> str:
    buttons = (
        ("soc-google", "Google", "G"),
        ("soc-facebook", "Facebook", "f"),
        ("soc-apple", "Apple", ""),
        ("soc-xbox", "Xbox", "X"),
        ("soc-ps", "PlayStation", "P"),
        ("soc-nintendo", "Nintendo", "N"),
        ("soc-bnet", "Battle.net", "B"),
    )
    first, second = buttons[:3], buttons[3:]

    def row(items) -> str:
        bits = []
        for cls, name, mark in items:
            bits.append(
                f'<button class="{cls}" type="button" aria-label="{name}" title="{name}">{mark}</button>'
            )
        return f'<div>{"".join(bits)}</div>'

    return f'<div class="bnet-social" aria-label="Other sign-in marks">{row(first)}{row(second)}</div>'


def _login(login_kind: str) -> str:
    label, input_type, placeholder = _identity(login_kind)
    return f"""<div class="bnet-gate">
  <p class="bnet-logo"><i aria-hidden="true"></i>BATTLE.NET</p>
  <h1>Log in</h1>
  <p class="bnet-new">New to Battle.net? <a href="/account/create">Sign up</a></p>
  <form class="acct-form" method="post" action="/account/login">
    <label class="acct-label">{label}
      <input class="acct-input" name="identity" type="{input_type}" placeholder="{placeholder}" required autocomplete="username">
    </label>
    <p class="bnet-forgot"><a href="/support/password">Forgot email?</a></p>
    <label class="acct-label">Password
      <input class="acct-input" type="password" name="password" required autocomplete="current-password">
    </label>
    <button class="acct-button bnet-continue" type="submit">Continue</button>
  </form>
  <p class="bnet-legal">By continuing, you acknowledge our <a href="/support/">Privacy Policy</a>.</p>
  <div class="bnet-or" role="separator"><span>OR</span></div>
  {_social()}
  <p class="acct-note">There is no emailed password reset. Sign in and change the password here.</p>
  {_gate_nav()}
</div>"""


def _create(login_kind: str, separate_game_name: bool) -> str:
    label, input_type, placeholder = _identity(login_kind)
    game = ""
    if separate_game_name:
        game = """<label class="acct-label">World of Warcraft account name
      <input class="acct-input" name="game_name" required maxlength="16" autocomplete="username">
    </label>
    """
    return f"""<div class="bnet-gate">
  <p class="bnet-logo"><i aria-hidden="true"></i>BATTLE.NET</p>
  <h1>Sign up</h1>
  <p class="bnet-new">The email is the Battle.net login. The World of Warcraft account name is what you type in the game.</p>
  <form class="acct-form" method="post" action="/account/create">
    <label class="acct-label">{label}
      <input class="acct-input" name="identity" type="{input_type}" placeholder="{placeholder}" required autocomplete="email">
    </label>
    {game}<label class="acct-label">Password
      <input class="acct-input" type="password" name="password" required autocomplete="new-password">
    </label>
    <label class="acct-label">Confirm password
      <input class="acct-input" type="password" name="confirm" required autocomplete="new-password">
    </label>
    <button class="acct-button bnet-continue" type="submit">Create Account</button>
  </form>
  <p class="acct-switch"><a href="/account/login">Log in</a></p>
  {_gate_nav()}
</div>"""


def _password() -> str:
    return """<h1 class="acct-title">""" + ERA_TITLE + """</h1>
<h2 class="acct-sub">Change Password</h2>
<p class="acct-note">Change the password you still know. This page does not email a reset.</p>
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
<p class="acct-switch"><a href="/account/">Back to Account</a></p>"""


def _characters(characters: list) -> str:
    if not characters:
        return '<p class="acct-empty">No characters on this realm yet.</p>'
    items = []
    for c in characters:
        name = _e(c.get("name"))
        level = _e(c.get("level"))
        klass = _e(c.get("class_name"))
        items.append(
            f'<li class="acct-char"><span class="acct-charname">{name}</span>'
            f'<span class="acct-charmeta">{level}</span>'
            f'<span class="acct-charmeta">{klass}</span></li>'
        )
    return f'<ul class="acct-chars">{"".join(items)}</ul>'


def _summary(user: str, email: str, characters: list) -> str:
    return f"""<h1 class="acct-title">Account Overview</h1>
<div class="bnet-cards">
  <section class="bnet-card">
    <h2>Redeem a code</h2>
    <input class="acct-input" placeholder="XXXX-XXXX-XXXX-XXXX" readonly aria-label="Redeem a code">
    <button class="acct-button" type="button">Redeem Code</button>
  </section>
  <section class="bnet-card">
    <h2>Battle.net Balance</h2>
    <p class="bnet-balance">$0.00</p>
    <p><a href="/account/">Payment Methods</a></p>
  </section>
  <section class="bnet-card">
    <h2>Your Information</h2>
    <ul class="acct-rows">
      <li class="acct-row"><span class="acct-rowlabel">Email</span><span class="acct-rowvalue">{_e(email)}</span></li>
      <li class="acct-row"><span class="acct-rowlabel">World of Warcraft account name</span><span class="acct-rowvalue">{_e(user)}</span></li>
    </ul>
  </section>
  <section class="bnet-card">
    <h2>Security Checkup</h2>
    <p><a href="/account/password">{ERA_TITLE}</a></p>
    <p class="acct-note">There is no emailed password reset. Change the password here.</p>
  </section>
</div>
<section class="bnet-card bnet-wide">
  <h2>Subscriptions &amp; Game Time</h2>
  <table class="bnet-sub">
    <thead><tr><th>Game</th><th>Status</th><th>Last Played</th><th>Next Billing Date</th></tr></thead>
    <tbody>
      <tr>
        <td>World of Warcraft (WoW1)</td>
        <td>Active</td>
        <td>—</td>
        <td>—</td>
      </tr>
    </tbody>
  </table>
  <h3 class="acct-section">Characters</h3>
  {_characters(characters)}
</section>
<section class="bnet-card bnet-wide">
  <h2>Recent Purchases</h2>
  <p class="acct-empty">No purchases listed on this page.</p>
</section>
<p class="acct-actions"><a href="/account/password">Change Password</a> · <a href="/account/logout">Log Out</a></p>"""


def _overview_shell(active: str, body: str, show_logout: bool) -> str:
    return f"""<section class="acct acct-warwithin" data-chrome="bnet-overview">
  {_top(show_logout)}
  <div class="bnet-shell">
    <aside class="acct-nav">{_side(active)}</aside>
    <div class="acct-main">{body}</div>
  </div>
</section>"""


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
    _ = exp
    alerts = _alerts(error, notice)
    if mode == "summary":
        return _overview_shell("overview", alerts + _summary(user, email, characters), True)
    if mode == "create":
        return (
            '<section class="acct acct-warwithin" data-chrome="bnet-gate">'
            + alerts
            + _create(login_kind, separate_game_name)
            + "</section>"
        )
    if mode == "password":
        return _overview_shell("security", alerts + _password(), bool(user))
    return (
        '<section class="acct acct-warwithin" data-chrome="bnet-gate">'
        + alerts
        + _login(login_kind)
        + "</section>"
    )
