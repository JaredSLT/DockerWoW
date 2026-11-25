"""Death Knight and later-class trees."""

from .models import Tree, _t

DK = (
    Tree(
        "Blood",
        (
            _t("Butchery", 2, 0, 0),
            _t("Subversion", 3, 1, 0),
            _t("Blade Barrier", 5, 2, 0),
            _t("Bladed Armor", 5, 0, 1),
            _t("Scent of Blood", 3, 1, 1),
            _t("Two-Handed Weapon Specialization", 2, 2, 1),
            _t("Rune Tap", 1, 0, 2),
            _t("Dark Conviction", 5, 1, 2),
            _t("Death Rune Mastery", 3, 2, 2),
            _t("Improved Rune Tap", 3, 0, 3),
            _t("Spell Deflection", 3, 2, 3),
            _t("Vendetta", 3, 3, 3),
            _t("Bloody Vengeance", 3, 1, 4),
            _t("Abomination's Might", 2, 2, 4),
            _t("Bloodworms", 3, 0, 5),
            _t("Hysteria", 1, 1, 5),
            _t("Improved Blood Presence", 2, 2, 5),
            _t("Dancing Rune Weapon", 1, 1, 6),
        ),
    ),
    Tree(
        "Frost",
        (
            _t("Improved Icy Touch", 3, 0, 0),
            _t("Runic Power Mastery", 2, 1, 0),
            _t("Toughness", 5, 2, 0),
            _t("Icy Reach", 2, 1, 1),
            _t("Black Ice", 5, 2, 1),
            _t("Nerves of Cold Steel", 3, 3, 1),
            _t("Icy Talons", 5, 0, 2),
            _t("Lichborne", 1, 1, 2),
            _t("Annihilation", 3, 2, 2),
            _t("Killing Machine", 5, 1, 3),
            _t("Chill of the Grave", 2, 2, 3),
            _t("Endless Winter", 2, 3, 3),
            _t("Frigid Dreadplate", 3, 1, 4),
            _t("Glacier Rot", 3, 2, 4),
            _t("Deathchill", 1, 1, 5),
            _t("Improved Icy Talons", 1, 2, 5),
            _t("Merciless Combat", 2, 0, 5),
            _t("Howling Blast", 1, 1, 6),
        ),
    ),
    Tree(
        "Unholy",
        (
            _t("Vicious Strikes", 2, 0, 0),
            _t("Virulence", 3, 1, 0),
            _t("Anticipation", 5, 2, 0),
            _t("Epidemic", 2, 0, 1),
            _t("Morbidity", 3, 1, 1),
            _t("Ravenous Dead", 3, 2, 1),
            _t("On a Pale Horse", 2, 1, 2),
            _t("Blood-Caked Blade", 3, 2, 2),
            _t("Night of the Dead", 2, 3, 2),
            _t("Unholy Blight", 1, 0, 3),
            _t("Impurity", 5, 1, 3),
            _t("Dirge", 2, 2, 3),
            _t("Desecration", 2, 0, 4),
            _t("Master of Ghouls", 1, 2, 4),
            _t("Desolation", 5, 0, 5),
            _t("Ghoul Frenzy", 1, 1, 5),
            _t("Crypt Fever", 3, 2, 5),
            _t("Scourge Strike", 1, 1, 6),
        ),
    ),
)

MONK = (
    Tree("Brewmaster", (_t("Elusive Brew", 1, 1, 0), _t("Guard", 1, 1, 2), _t("Keg Smash", 1, 1, 4))),
    Tree("Mistweaver", (_t("Soothing Mist", 1, 1, 0), _t("Renewing Mist", 1, 1, 2), _t("Thunder Focus Tea", 1, 1, 4))),
    Tree("Windwalker", (_t("Combo Breaker", 1, 1, 0), _t("Fists of Fury", 1, 1, 2), _t("Energizing Brew", 1, 1, 4))),
)

DH = (
    Tree("Havoc", (_t("Fel Mastery", 1, 1, 0), _t("Demon Blades", 1, 1, 2), _t("Metamorphosis", 1, 1, 4))),
    Tree("Vengeance", (_t("Felblade", 1, 1, 0), _t("Soul Cleave", 1, 1, 2), _t("Demonic Infusion", 1, 1, 4))),
)

EVOKER = (
    Tree("Devastation", (_t("Pyre", 1, 1, 0), _t("Dragonrage", 1, 1, 2))),
    Tree("Preservation", (_t("Echo", 1, 1, 0), _t("Rewind", 1, 1, 2))),
    Tree("Augmentation", (_t("Ebon Might", 1, 1, 0), _t("Breath of Eons", 1, 1, 2))),
)

