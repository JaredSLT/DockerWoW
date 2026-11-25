"""Character Services page. One form per action, rendered for the signed-in account."""

from __future__ import annotations

import html

from .. import accounts
from ..catalog import Expansion
from ..lab import LabConfig
from . import actions
from .config import load_config, transfer_targets


def _e(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def transfer_fields(src: Expansion, email: str, username: str, targets: list) -> dict:
    """Which extra account fields a forward move has to ask for."""
    has_email = "@" in (email or "")
    game_ok = bool(accounts.USER_RE.match(username or ""))
    return {
        "email": any(accounts.email_login(dest) and not has_email for dest in targets),
        "game": any(dest.proto == "bnet" and not game_ok for dest in targets),
        "account": any((not accounts.email_login(dest)) and not game_ok for dest in targets),
    }


def render_page(
    exp: Expansion,
    *,
    user: str,
    error: str = "",
    notice: str = "",
    characters: list | None = None,
    guilds: list | None = None,
    email: str = "",
    token_balance: int = 0,
) -> str:
    settings = load_config(exp.id)
    targets = transfer_targets(exp)
    roster = characters or []
    led = guilds or []
    fields = transfer_fields(exp, email, user, targets)
    parts = ["<h2>Character Services</h2>"]
    if error:
        parts.append(f'<p class="acct-error">{_e(error)}</p>')
    if notice:
        parts.append(f'<p class="acct-notice">{_e(notice)}</p>')
    parts.append(
        "<p>These services are free. Log out of the game before you use one. "
        "A character has to be offline.</p>"
    )
    if not roster:
        parts.append("<p>Create a character in game first.</p>")
    if settings.get("boost_level") and not settings.get("boost"):
        parts.append(
            f'<p class="acct-muted">Character boosts are turned off. '
            f'Set "boost" to true in wowweb/services/config/{_e(exp.id)}.json to turn them on.</p>'
        )
    if settings.get("token_gold") and not settings.get("wow_token"):
        parts.append(
            f'<p class="acct-muted">The WoW Token is turned off. '
            f'Set "wow_token" to true in wowweb/services/config/{_e(exp.id)}.json to turn it on.</p>'
        )
    if settings.get("name_change"):
        parts.append("<section class='acct-services'><h3>Name change</h3>")
        parts.append("<p>Two to twelve letters. The first letter is capitalized.</p>")
        for row in roster:
            parts.append(_character_heading(row))
            parts.append(
                "<form method='post' action='/account/services/name' class='acct-form'>"
                f"<input type='hidden' name='guid' value='{int(row['guid'])}'>"
                f"<label>New name for {_e(row['name'])}"
                "<input name='name' maxlength='12' required></label>"
                "<button type='submit'>Change name</button></form>"
            )
        parts.append("</section>")
    if settings.get("appearance_change"):
        parts.append(_flag_section(
            "Appearance change",
            "The game will ask you to change this character's appearance, including gender, the next time you log in.",
            roster,
            "/account/services/appearance",
            "Change appearance",
        ))
    if settings.get("race_change"):
        parts.append(_flag_section(
            "Race change",
            "The game will walk this character through a new race on the same faction the next time you log in. "
            "They must be at least level 10, or level 55 for a death knight.",
            roster,
            "/account/services/race",
            "Change race",
        ))
    if settings.get("faction_change"):
        parts.append(_flag_section(
            "Faction change",
            "The game will walk this character through a faction change the next time you log in. "
            "Race, appearance, and name can change with it. "
            "They must be at least level 10, or level 55 for a death knight.",
            roster,
            "/account/services/faction",
            "Change faction",
        ))
    if settings.get("guild_name_change"):
        parts.append("<section class='acct-services'><h3>Guild name change</h3>")
        parts.append("<p>Guild masters can rename a guild. The new name has to be unique on this realm.</p>")
        if not led:
            parts.append("<p>None of your characters is a guild master.</p>")
        for guild in led:
            parts.append(
                "<form method='post' action='/account/services/guild' class='acct-form'>"
                f"<input type='hidden' name='guild_id' value='{int(guild['id'])}'>"
                f"<label>New name for {_e(guild['name'])}"
                "<input name='name' maxlength='24' required></label>"
                "<button type='submit'>Rename guild</button></form>"
            )
        parts.append("</section>")
    if settings.get("expansion_transfer") and targets:
        parts.append("<section class='acct-services'><h3>Expansion transfer</h3>")
        parts.append(
            "<p>Move a character forward to a later expansion and keep playing them there. "
            "The usual step is the next expansion. You can skip ahead. They leave this realm. "
            "Gold and gear that exist in the new world go with them. "
            "They arrive in Stormwind or Orgrimmar.</p>"
        )
        for row in roster:
            options = []
            for index, dest in enumerate(targets):
                label = dest.name + (" (the usual next step)" if index == 0 else "")
                options.append(f"<option value='{_e(dest.id)}'>{_e(label)}</option>")
            extra = ""
            if fields["email"]:
                extra += (
                    "<label>Email for the destination account"
                    "<input name='dest_email' type='email' required></label>"
                )
            if fields["game"]:
                extra += (
                    "<label>World of Warcraft account name on the destination"
                    "<input name='dest_game' required></label>"
                )
            if fields["account"]:
                extra += (
                    "<label>Account name on the destination"
                    "<input name='dest_account' required></label>"
                )
            parts.append(_character_heading(row))
            parts.append(
                "<form method='post' action='/account/services/transfer' class='acct-form'>"
                f"<input type='hidden' name='guid' value='{int(row['guid'])}'>"
                f"<label>Move {_e(row['name'])} to<select name='dest'>{''.join(options)}</select></label>"
                "<label>Password<input name='password' type='password' autocomplete='current-password' required></label>"
                f"<label>Type {_e(row['name'])} to confirm<input name='confirm' required></label>"
                f"{extra}<button type='submit'>Transfer character</button></form>"
            )
        parts.append("</section>")
    if settings.get("boost"):
        level = int(settings.get("boost_level") or 0)
        parts.append("<section class='acct-services'><h3>Character boost</h3>")
        if level <= 0:
            parts.append(
                f"<p>Set boost_level in wowweb/services/config/{_e(exp.id)}.json before using a boost.</p>"
            )
        else:
            parts.append(
                f"<p>Raises a character to level {level}. Spells and talents reset the next time you log in. "
                "Gear is left as it is.</p>"
            )
            for row in roster:
                parts.append(_character_heading(row))
                parts.append(
                    "<form method='post' action='/account/services/boost' class='acct-form'>"
                    f"<input type='hidden' name='guid' value='{int(row['guid'])}'>"
                    f"<button type='submit'>Boost {_e(row['name'])} to {level}</button></form>"
                )
        parts.append("</section>")
    if settings.get("wow_token"):
        gold = int(settings.get("token_gold") or 0)
        parts.append("<section class='acct-services'><h3>WoW Token</h3>")
        parts.append(f"<p>This account holds {int(token_balance)} WoW Token(s).</p>")
        if gold <= 0:
            parts.append(
                f"<p>Set token_gold in wowweb/services/config/{_e(exp.id)}.json before using the WoW Token.</p>"
            )
        else:
            parts.append(
                f"<p>One token is {gold} gold. Buying a token takes that gold from the character. "
                "Selling a token pays the character the same amount.</p>"
            )
            for row in roster:
                parts.append(_character_heading(row))
                parts.append(
                    "<form method='post' action='/account/services/token' class='acct-form'>"
                    f"<input type='hidden' name='guid' value='{int(row['guid'])}'>"
                    "<button type='submit' name='side' value='buy'>Buy a token</button> "
                    "<button type='submit' name='side' value='sell'>Sell a token</button></form>"
                )
        parts.append("</section>")
    return "\n".join(parts)


def _character_heading(row: dict) -> str:
    online = " (online)" if row.get("online") else ""
    return (
        f"<p><strong>{_e(row['name'])}</strong>{online} — "
        f"level {int(row.get('level') or 0)} {_e(row.get('class_name') or '')}</p>"
    )


def _flag_section(title: str, text: str, roster: list, action: str, button: str) -> str:
    parts = [f"<section class='acct-services'><h3>{_e(title)}</h3>", f"<p>{_e(text)}</p>"]
    for row in roster:
        parts.append(_character_heading(row))
        parts.append(
            f"<form method='post' action='{_e(action)}' class='acct-form'>"
            f"<input type='hidden' name='guid' value='{int(row['guid'])}'>"
            f"<button type='submit'>{_e(button)}</button></form>"
        )
    parts.append("</section>")
    return "\n".join(parts)


def services_page(cfg: LabConfig, exp: Expansion, user: str, data_dir, error: str = "", notice: str = "") -> str:
    summary = accounts.account_summary(cfg, exp, user)
    balance = 0
    if load_config(exp.id).get("wow_token"):
        balance = actions.token_balance(data_dir, exp.id, user)
    return render_page(
        exp,
        user=user,
        error=error,
        notice=notice,
        characters=actions.list_characters(cfg, exp, user),
        guilds=actions.list_guilds(cfg, exp, user),
        email=summary.get("email") or "",
        token_balance=balance,
    )
