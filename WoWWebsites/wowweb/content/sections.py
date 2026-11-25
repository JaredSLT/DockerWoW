"""Support, shop, story, esports, and Classic copy."""

from __future__ import annotations

from dataclasses import dataclass

from ..catalog import Expansion

# Arena starts at TBC (expansion_level 1). Dungeon Finder starts at Wrath (2).
# Slugs stay stable so site search can use the same ids.
SUPPORT_MIN_LEVEL = {
    "stuck": 0,
    "password": 0,
    "addons": 0,
    "talents": 0,
    "honor": 0,
    "arena": 1,
    "dungeon-finder": 2,
}

SUPPORT_SLUGS = (
    "stuck",
    "password",
    "addons",
    "talents",
    "honor",
    "arena",
    "dungeon-finder",
)

# BfA and Shadowlands labeled the shelf Subscribe. Every other era said Buy Now.
_SUBSCRIBE = frozenset({"bfa", "shadowlands"})

# WoW Classic as its own promo starts with Battle for Azeroth.
CLASSIC_PROMO_IDS = frozenset({"bfa", "shadowlands", "dragonflight", "warwithin", "midnight"})


@dataclass(frozen=True)
class Article:
    slug: str
    title: str
    summary: str
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class ShelfItem:
    title: str
    body: str


@dataclass(frozen=True)
class ShopShelf:
    intro: str
    items: tuple[ShelfItem, ...]
    button: str


@dataclass(frozen=True)
class Block:
    heading: str
    paragraphs: tuple[str, ...]


def _article(slug: str, title: str, summary: str, paragraphs: tuple[str, ...]) -> Article:
    return Article(slug, title, summary, paragraphs)


def _stuck(exp: Expansion) -> Article:
    return _article(
        "stuck",
        "Character Stuck",
        "When a character cannot move.",
        (
            f"If your character is wedged in the world on {exp.realm_name}, jump, hearth, or release a spirit if the button is still there.",
            "Open Help in the client and choose Character Stuck when this patch lists it. Logging out and back in returns many stuck characters to the place they last rested.",
        ),
    )


def _password(exp: Expansion) -> Article:
    if exp.proto == "bnet":
        follow = (
            "Sign in with the email on the account. Change a password you still know from the account page. "
            "If you cannot sign in, create a new account."
        )
    else:
        follow = (
            "Sign in with the same account name you use in the game client. Change a password you still know from the account page. "
            "If you cannot sign in, create a new account."
        )
    return _article(
        "password",
        "Password and Account Recovery",
        "Signing in when mail cannot reset a password.",
        ("There is no emailed reset on this realm.", follow),
    )


def _addons(exp: Expansion) -> Article:
    return _article(
        "addons",
        "Addons",
        "Interface addons and this client.",
        (
            f"Addons extend the default interface of {exp.name}. Place them in the Interface/AddOns folder of the game client, then enable them at the character screen.",
            f"An addon has to match patch {exp.last_patch}. The realm does not install addons for you.",
        ),
    )


def _talents(exp: Expansion) -> Article:
    return _article(
        "talents",
        "Talents",
        "Spending and planning talent points.",
        (
            "Talents are spent from the character panel once you begin earning points. The trees on the game guide match this era.",
            "Plan a build in the talent calculators before you spend. A trainer in a major city can reset points when this patch still offers that.",
        ),
    )


def _honor(exp: Expansion) -> Article:
    return _article(
        "honor",
        "Honor and Battlegrounds",
        "Ranks, battlegrounds, and honorable kills.",
        (
            f"Honor is the measure of player combat on {exp.realm_name}. Honorable kills and battleground objectives raise your standing.",
            "The PvP rankings list rank and kills for characters on this realm.",
        ),
    )


def _arena(exp: Expansion) -> Article:
    return _article(
        "arena",
        "Arena",
        "Rated teams and the season.",
        (
            "Arenas are rated team combat, separate from honor rank. Register a team and queue the brackets this era offers.",
            "Team rating climbs on wins against other teams. The season, not a single match, is the standing that lasts.",
        ),
    )


def _dungeon_finder(exp: Expansion) -> Article:
    if exp.expansion_level >= 6:
        paragraphs = (
            "The Group Finder is this era's Dungeon Finder. Queue a random dungeon by role, or list a group of your own.",
            "Mythic dungeons above that random queue still ask for a full party. The finder does not turn a keystone for you.",
        )
    elif exp.expansion_level >= 3:
        paragraphs = (
            "The Dungeon Finder queues a random dungeon. Choose tank, healer, or damage, and wait for the group to fill.",
            "The Raid Finder sits beside it for the raid wings this patch offers. A party that is already full can still walk in.",
        )
    else:
        paragraphs = (
            "The Dungeon Finder queues a Northrend dungeon. Choose tank, healer, or damage.",
            "A group that is already full can meet at the stone and walk in. The finder is for the group you do not have yet.",
        )
    return _article(
        "dungeon-finder",
        "Dungeon Finder",
        "Queue a dungeon by role.",
        paragraphs,
    )


_BUILDERS = {
    "stuck": _stuck,
    "password": _password,
    "addons": _addons,
    "talents": _talents,
    "honor": _honor,
    "arena": _arena,
    "dungeon-finder": _dungeon_finder,
}


def article_for(exp: Expansion, slug: str) -> Article | None:
    key = (slug or "").strip().lower()
    minimum = SUPPORT_MIN_LEVEL.get(key)
    if minimum is None or exp.expansion_level < minimum:
        return None
    return _BUILDERS[key](exp)


def articles_for(exp: Expansion) -> list[Article]:
    found = []
    for slug in SUPPORT_SLUGS:
        article = article_for(exp, slug)
        if article is not None:
            found.append(article)
    return found


_BOX_BODY = {
    "alpha": "The alpha of World of Warcraft. A smaller Azeroth, with the map still being cut.",
    "vanilla": "The original game box. Two continents, eight races, and nine classes, at patch 1.12.1.",
    "tbc": "The expansion box. Outland beyond the Dark Portal, blood elves, draenei, and arenas.",
    "wotlk": "The expansion box. Northrend, death knights, and the road to the Frozen Throne.",
    "cata": "The expansion box. A world reshaped by the Cataclysm, with worgen and goblins among the factions.",
    "mop": "The expansion box. Pandaria, pandaren, and monks.",
    "wod": "The expansion box. Draenor of the past, garrisons, and the Iron Horde.",
    "legion": "The expansion box. The Broken Isles, Argus, and demon hunters.",
    "bfa": "The expansion box. Kul Tiras, Zandalar, and the faction war.",
    "shadowlands": "The expansion box. The Shadowlands beyond the veil, covenants, and the realms of the dead.",
    "dragonflight": "The expansion box. The Dragon Isles, dragonriding, and the dracthyr.",
    "warwithin": "The expansion box. Khaz Algar beneath Azeroth, delves, and the earthen.",
    "midnight": "The expansion box. Quel'Thalas standing against the Void.",
}


def shop_shelf(exp: Expansion) -> ShopShelf:
    title = "World of Warcraft" if exp.id in ("alpha", "vanilla") else exp.name
    body = _BOX_BODY.get(exp.id, f"The box for {exp.name}.")
    game_time = (
        f"Game time for the {exp.realm_name} realm. "
        f"Play {exp.name} at patch {exp.last_patch} once the account exists."
    )
    button = "Subscribe" if exp.id in _SUBSCRIBE else "Buy Now"
    return ShopShelf(
        intro=f"The shop shelf for {exp.name}.",
        items=(
            ShelfItem(title, body),
            ShelfItem("Game Time", game_time),
        ),
        button=button,
    )


def _b(heading: str, *paragraphs: str) -> Block:
    return Block(heading, paragraphs)


_STORIES = {
    "alpha": (
        _b(
            "Azeroth in Alpha",
            "The alpha walks a smaller Azeroth. Humans and orcs are already at war, classes are still moving, and stretches of the Eastern Kingdoms and Kalimdor are not on the map yet.",
        ),
    ),
    "vanilla": (
        _b(
            "Azeroth",
            "Four years after the Third War, the Alliance and the Horde share two continents. Stormwind and Orgrimmar are the capitals, and the road runs out to Blackrock Mountain, Zul'Gurub, Ahn'Qiraj, and Naxxramas.",
            "This age ends at a quiet Dark Portal. Outland is not on the map.",
        ),
    ),
    "tbc": (
        _b(
            "Outland",
            "The Dark Portal burns again. Beyond it is Outland: Hellfire Peninsula, Zangarmarsh, Nagrand, Shadowmoon, and the Black Temple where Illidan holds what remains of his army.",
            "Blood elves join the Horde and draenei join the Alliance. The war climbs Tempest Keep, Serpentshrine Cavern, and the Sunwell.",
        ),
    ),
    "wotlk": (
        _b(
            "Northrend",
            "The Lich King wakes on the Frozen Throne. Ships land in Northrend, in the Borean Tundra and the Howling Fjord, and the road runs through Dragonblight to Icecrown.",
            "Death knights walk out of Acherus. Ulduar, the Argent Tournament, and Icecrown Citadel are the last marches of this war.",
        ),
    ),
    "cata": (
        _b(
            "The Cataclysm",
            "Deathwing returns, and the Cataclysm is the break that follows. Stormwind floods, the Barrens split, and the elemental planes bleed into the old continents.",
            "Worgen and goblins take faction banners. The Dragon Aspects gather for a last stand at the Hour of Twilight.",
        ),
    ),
    "mop": (
        _b(
            "Pandaria",
            "A mist lifts, and Pandaria is no longer hidden. Pandaren of the Wandering Isle choose a side, and monks train beside a war the continent did not ask for.",
            "The sha feed on that anger. The campaign runs from the Jade Forest to the Throne of Thunder and ends at the gates of Orgrimmar.",
        ),
    ),
    "wod": (
        _b(
            "Draenor",
            "A new Dark Portal opens onto Draenor as it was, before the world was torn apart. The Iron Horde marches out of that past, and both factions raise garrisons in Frostfire Ridge and Shadowmoon Valley.",
            "Tanaan Jungle hides the last road. Hellfire Citadel is the fortress at the end of the Iron Horde.",
        ),
    ),
    "legion": (
        _b(
            "The Legion Returns",
            "The Burning Legion returns in force. Class orders take up artifact weapons, demon hunters break their cages, and the war is fought on two maps.",
        ),
        _b(
            "The Broken Isles",
            "The Broken Isles rise around the Tomb of Sargeras: Azsuna, Val'sharah, Highmountain, Stormheim, and Suramar under its shield. Order halls arm the campaign, and the Tomb is the first ending.",
        ),
        _b(
            "Argus",
            "When the Tomb falls, the Army of the Light leads the war to Argus. Krokuun, Mac'Aree, and the Antoran Wastes end at the Burning Throne. The last of this age leaves a wound in Silithus.",
        ),
    ),
    "bfa": (
        _b(
            "A World at War",
            "The Alliance and the Horde open the war on two homelands at once. Everything that follows starts there.",
        ),
        _b(
            "Kul Tiras",
            "Kul Tiras is the Alliance front. Boralus, Tiragarde Sound, Drustvar, and Stormsong Valley are a sea kingdom slow to trust its own lost daughter, and the tidesages keep the old rites.",
        ),
        _b(
            "Zandalar",
            "Zandalar is the Horde front. Zuldazar, Nazmir, and Vol'dun belong to an old empire under a young king. The war between these continents is the heart of the age, long before Ny'alotha stirs.",
        ),
    ),
    "shadowlands": (
        _b(
            "The Shadowlands",
            "The Shadowlands are where the dead are supposed to go. Souls are pulled off that path into the Maw, and Oribos sends the living on into the realms beyond the veil.",
            "Bastion, Maldraxxus, Ardenweald, and Revendreth each keep a covenant. The chain runs through Korthia to Zereth Mortis, where the Jailer's work on death finally has a door.",
        ),
    ),
    "dragonflight": (
        _b(
            "The Dragon Isles",
            "The Dragon Isles are the dragonflights' first home, awake again. The Waking Shores, the Ohn'ahran Plains, the Azure Span, and Thaldraszus each belong to a flight.",
            "Dragonriding crosses that map. The dracthyr return with the isles, and the last season opens the Emerald Dream.",
        ),
    ),
    "warwithin": (
        _b(
            "Khaz Algar",
            "Khaz Algar is the earthen kingdom under Azeroth. The Isle of Dorn sits in open light. The Ringing Deeps, Hallowfall, and Azj-Kahet stack in the dark beneath it.",
            "Nerubians hold the lowest city. Delves drop into smaller holes in the same stone, and the harbinger's warning starts here.",
        ),
    ),
    "midnight": (
        _b(
            "Quel'Thalas",
            "Quel'Thalas is the field. Silvermoon, Eversong, and the Sunwell stand in the open, and the elves' homeland is the war, not a side chapter.",
        ),
        _b(
            "The Void",
            "The Void is the invader. Dim skies and a devouring dark reach for the Sunwell, and Quel'Thalas holds the line because its people do.",
        ),
    ),
}


def story_for(exp: Expansion) -> tuple[Block, ...]:
    return _STORIES.get(exp.id, (_b(exp.name, (f"The story of {exp.name}.",)),))


def tournament_esports(exp: Expansion) -> bool:
    # Legion and later keep a seasonal cup page. Earlier eras stay on arena and honor.
    return exp.expansion_level >= 6


def esports_blocks(exp: Expansion) -> tuple[Block, ...]:
    if tournament_esports(exp):
        return (
            _b(
                "Tournament Standings",
                (
                    f"Tournament standings for {exp.year}. Regional cups in the Americas, Europe, and beyond "
                    f"feed the Arena World Championship and Mythic Dungeon International for {exp.name}."
                ),
            ),
            _b(
                "Arena World Championship",
                (
                    f"The {exp.year} Arena World Championship is the 3v3 circuit for {exp.name}. "
                    "Regional cups play the season's arenas and feed a global final."
                ),
            ),
            _b(
                "Mythic Dungeon International",
                (
                    f"Mythic Dungeon International {exp.year} times five-player groups through the mythic dungeons of {exp.name}. "
                    "The standings are best times, not a random queue."
                ),
            ),
        )
    if exp.expansion_level < 1:
        text = (
            f"Arena and honor are the standings players ask about. On {exp.realm_name} the live ladder is honor: "
            "ranks from battlegrounds and world combat. Arena teams are not part of this patch, so there is no rated season beside that ladder."
        )
    else:
        text = (
            f"Arena and honor standings are both open on {exp.realm_name}. "
            "Honor still climbs from battlegrounds and world combat. "
            "Arena teams play a rated season, and that rating is its own ladder."
        )
    return (_b("Arena and Honor", text),)


def classic_copy(exp: Expansion) -> Block:
    if exp.id in CLASSIC_PROMO_IDS:
        return _b(
            "WoW Classic",
            (
                "WoW Classic is original Azeroth, the 1.12 era. Eight races and nine classes share the Eastern Kingdoms and Kalimdor.",
                "Honor ranks, battlegrounds, and the raids of that first age are the whole of the world. The Dark Portal is still a gate, not a road to a later continent.",
            ),
        )
    return _b(
        "The Original World",
        (
            f"This is the original world. {exp.name} at patch {exp.last_patch} is the Azeroth you are already in, not a second ruleset beside it.",
        ),
    )
