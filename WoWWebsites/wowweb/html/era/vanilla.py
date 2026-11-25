"""April 2006 community site and the account-creation receipt."""

from __future__ import annotations

from .common import dev_note, document, esc, styles

_IMG = "/static/img/vanilla2006"
_SHOT = "/static/img/ssotd-elwynn.jpg"
_BOX = "/new-hp/images/image-retailbox.gif"

# Open sections match the 12 April 2006 community home.
_NEWS = (
    ("/wow/", "Current News"),
    ("/wow/news", "Archived News"),
)
_ACCOUNT = (
    ("/account/login", "Log In"),
    ("/account/create", "Create Account"),
    ("/account/", "Manage Account"),
    ("/loginsupport/password.html", "Retrieve Password"),
    ("/wow/realmstatus", "Realm Status"),
)
_GUIDE = (
    ("/wow/info/", "Game Guide"),
    ("/wow/info/introduction", "Introduction"),
    ("/wow/info/basics", "Getting Started"),
    ("/wow/info/races", "Character"),
    ("/info/reputations", "Reputations"),
    ("/info/items", "Items"),
    ("/info/theworld", "The World"),
    ("/info/transportation", "Transportation"),
    ("/info/playerinteraction", "Player Interaction"),
    ("/wow/pvp/rankings", "Player vs Player"),
    ("/support/", "FAQ"),
    ("/story", "Story"),
    ("/burningcrusade", "Burning Crusade"),
)
_WORKSHOP = (
    ("/wow/info/patches", "Under Development"),
    ("/patchnotes", "Previous Patches"),
    ("/wow/pvp/rankings", "Arena"),
    ("/info/encyclopedia", "Encyclopedia"),
    ("/wow/info/classes/", "Talent Calculators"),
    ("/info/events/calendar", "Events Calendar"),
    ("/info/items/armorsets", "Armor Sets"),
    ("/wow/info/basics/map", "World Map"),
    ("/pvp/battlegrounds", "Battlegroups"),
)
_MEDIA = (
    ("/wow/media/screenshots", "Screenshots"),
    ("/wow/media/wallpapers", "Wallpapers"),
    ("/downloads/movies.html", "Movies"),
)
_FORUMS = (
    ("/forums/general", "General"),
    ("/forums/", "Class Forums"),
    ("/forums/realm", "Realm Forums"),
    ("/forums/guilds", "Guild Recruitment"),
    ("/forums/guildrelations", "Guild Relations"),
    ("/forums/support", "Support"),
)
_COMMUNITY = (
    ("/community/", "Overview"),
    ("/contests/", "Contests"),
    ("/community/comics.html", "Comics"),
)
_SUPPORT = (
    ("/support/", "Customer Support"),
)


def _sub(rows) -> str:
    return "".join(f'<a href="{esc(href)}">{esc(label)}</a>' for href, label in rows)


def _section(key: str, label: str, rows, open_: bool) -> str:
    opened = " open" if open_ else ""
    return (
        f'<details class="v-sec v-sec-{key}"{opened}>'
        f"<summary><span>{esc(label)}</span></summary>"
        f'<div class="v-sub">{_sub(rows)}</div>'
        "</details>"
    )


def _menu() -> str:
    return f"""<nav class="v-menu">
{_section("news", "News", _NEWS, False)}
{_section("account", "Account", _ACCOUNT, False)}
{_section("guide", "Game Guide", _GUIDE, True)}
{_section("workshop", "Workshop", _WORKSHOP, True)}
{_section("media", "Media", _MEDIA, False)}
{_section("forums", "Forums", _FORUMS, True)}
{_section("community", "Community", _COMMUNITY, False)}
{_section("support", "Support", _SUPPORT, False)}
</nav>"""


def _rail(ssotd: str) -> str:
    shot = ssotd or _SHOT
    return f"""<aside class="v-rail">
  <div class="v-rail-art">
    <img src="{_IMG}/rail.jpg" alt="">
    <a class="hit hit-faq" href="/support/">FAQ Site</a>
    <a class="hit hit-realms" href="/wow/realmstatus">Realms Status</a>
    <a class="hit hit-create" href="/account/create">Account Creation</a>
    <a class="hit hit-manage" href="/account/">Account Management</a>
    <a class="hit hit-pass" href="/loginsupport/password.html">Retrieve Password</a>
    <a class="hit hit-info" href="/info/items/armorsets">High Level Armor Sets</a>
    <a class="hit hit-indev" href="/wow/info/patches">Shadow of the Necropolis</a>
    <a class="hit hit-pvp" href="/wow/pvp/rankings">PvP Rankings</a>
  </div>
  <div id="ssotd-container" class="ssotd-container">
    <a href="/wow/media/screenshots"><img src="{esc(shot)}" alt="Screenshot of the Day"></a>
  </div>
</aside>"""


def _top(user: str | None) -> str:
    who = ""
    if user:
        who = (
            f'<p class="v-who">Signed in as {esc(user)}'
            f' · <a href="/account/logout">Log Out</a></p>'
        )
    return f"""<header class="v-top">
  <img class="v-header" src="{_IMG}/header.jpg" alt="">
  <img class="v-logo" src="{_IMG}/logo.jpg" alt="">
  <a class="hit-logo" href="/wow/">World of Warcraft Community Site</a>
  <a class="hit-acct" href="/account/">Account Management</a>
  <a class="hit-realm" href="/wow/realmstatus">Realm Status</a>
  {who}
</header>"""


def _frame(body: str, ssotd: str) -> str:
    # Account management fills the parchment. The home keeps the right rail.
    rail = "" if 'class="acct-vanilla"' in body else _rail(ssotd)
    wide = " v-wide" if not rail else ""
    return f"""<div class="v-iron">
  <div class="v-iron-t"><div><div></div></div></div>
  <div class="v-iron-m"><div class="v-iron-r">
    <div class="v-parch">
      <div class="v-center{wide}">{body}</div>
      {rail}
    </div>
  </div></div>
  <div class="v-iron-b"><div><div></div></div></div>
</div>"""


def shell(exp, title, body, user, crumb, dev, online="", login_error="", extra_js="") -> str:
    _ = crumb, online, login_error
    inner = f"""<div class="v-site">
<div class="v-trees v-trees-l"></div>
<div class="v-trees v-trees-r"></div>
{_top(user)}
<img class="v-elf" src="{_IMG}/elf.png" alt="">
<div class="v-body">
{_menu()}
{_frame(body, _SHOT)}
</div>
</div>"""
    css = styles("vanilla") + ["/static/css/forums.css"]
    return document(
        f"{title} — World of Warcraft",
        css,
        "era-vanilla",
        inner,
        dev_note_text=dev_note(exp, dev),
        extra_js=extra_js,
    )


def home_body(exp, news, realm, user) -> str:
    # The 12 April 2006 home is this snapshot, not the later news list.
    _ = exp, news, realm, user
    return """<div class="v-home">
<div class="v-arena">
  <img src="/static/img/vanilla2006/arena.jpg" alt="Welcome to the Arena">
</div>
<section class="v-news">
  <h3>General News</h3>
  <div class="v-cols"><span>News Title</span><span>Date</span></div>
  <details class="v-story" open>
    <summary>
      <span class="v-title">New WoW.com Sneak Peek!</span>
      <span class="v-by">Blaze</span>
      <span class="v-date">4-12-06</span>
    </summary>
    <div class="v-copy">
      <p>There is nothing wrong with your web browser. Do not attempt to adjust the monitor. We control the horizontal. We control the vertical. You are about to experience the awe and mystery which reaches from the inner mind to... the new World of Warcraft website! That's right, our crack team of web technology goblins and gnomish design specialists has been toiling in the dark recesses of the web team's dungeon for quite some time, redesigning the official community site. And now, you can get a first look at the new and improved functionality and the redesign of the site's main page. Here are some of the cool new features you may want to try out:</p>
      <ul>
        <li>Improved left side menu</li>
        <li>Enhanced main page layout</li>
        <li>Cycling flash banner</li>
        <li>Streamlined news section</li>
        <li>PvP Top Ten</li>
      </ul>
      <p>We are excited to present you with the new look of World of Warcraft on the Web, and we hope you like the new design! Please let us know if you experience any problems when viewing the new main page. Send your error reports including information about your operating system, browser, your browser's version, and a screenshot (if possible) to <a href="mailto:wowguide@blizzard.com">wowguide@blizzard.com</a>.</p>
    </div>
  </details>
  <details class="v-story">
    <summary>
      <span class="v-title">Select Realm Transfers</span>
      <span class="v-by">Eyonix</span>
      <span class="v-date">4-12-06</span>
    </summary>
  </details>
</section>
</div>"""


def full(path: str, ctx: dict) -> str | None:
    if path != "/account/completed":
        return None
    exp = ctx["exp"]
    return receipt_document(exp, ctx.get("user"), bool(ctx.get("dev")))


def take(path: str, ctx: dict):
    # Logged-out services would redirect. The community page itself answers.
    if path != "/account/services" or ctx.get("user"):
        return None
    return (
        "Character Services",
        "<h2>Character Services</h2>"
        "<p>Sign in to change a character name or transfer a character. "
        "These services are free.</p>"
        '<p><a href="/account/login">Log In</a> · <a href="/account/create">Create Account</a></p>',
    )


def receipt_document(exp, user, dev: bool) -> str:
    # Values that were covered in the photographs stay blank. The subscription
    # line is the unredacted plan on the December 2004 receipt.
    shown = esc(user) if user else ""
    name_cell = f'<span class="r-value">{shown}</span>' if shown else '<span class="r-blank"></span>'
    inner = f"""<header class="r-head">
  <img src="{_IMG}/logo.jpg" alt="World of Warcraft">
  <p class="r-sub">Account Creation</p>
</header>
<main class="r-sheet">
  <h1>Account Creation Complete!</h1>
  <p class="r-print">Please print this page and save it for your records.</p>
  <img class="r-box" src="{_BOX}" alt="Welcome to World of Warcraft">
  <p>Congratulations! You have successfully completed the World of Warcraft account creation process! You can now use the account you've just created to login and play. If you have questions or concerns about the account creation procedure or your billing information, please contact our billing and account services by email (<a href="mailto:billing@blizzard.com">billing@blizzard.com</a>) or via phone (1-800-59-BLIZZARD). Users in Singapore should please use 1-800-225-5969 (1-800-CALL-WOW).</p>
  <p>If you are new to the game, we recommend you take advantage of the in-game help system, which will help you learn how to complete various actions such as starting quests, initiating combat, searching bodies, and training your character. For further beginner information, check our <a href="/wow/info/basics">Getting Started page</a>.</p>
  <div class="r-panels">
    <section class="r-block">
      <h2>Account Details</h2>
      <table class="r-table">
        <tr><th>Account Name</th><td>{name_cell}</td></tr>
        <tr><th>Password</th><td><span class="r-blank"></span></td></tr>
        <tr><th>Password Question</th><td><span class="r-blank"></span></td></tr>
        <tr><th>Password Answer</th><td><span class="r-blank"></span></td></tr>
      </table>
    </section>
    <section class="r-block">
      <h2>Contact Info</h2>
      <div class="r-blank r-blank-block"></div>
    </section>
  </div>
  <section class="r-block r-pay">
    <h2>Payment Method</h2>
    <table class="r-table">
      <tr><th>Subscription</th><td>1 Month Recurring - $14.99</td></tr>
    </table>
  </section>
  <p class="r-foot">signup.worldofwarcraft.com/completed.html</p>
</main>"""
    return document(
        "Account Creation Complete — World of Warcraft",
        styles("vanilla"),
        "era-vanilla era-vanilla-receipt",
        inner,
        dev_note_text=dev_note(exp, dev),
    )
