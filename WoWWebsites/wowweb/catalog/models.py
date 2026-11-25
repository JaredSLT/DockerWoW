"""Expansion record."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Expansion:
    id: str
    name: str
    last_patch: str
    last_patch_date: str
    generation: str  # gen1, gen2, gen3, gen4
    lab_short: str
    kind: str  # alpha, cmangos, azerothcore, trinity, skyfire
    proto: str  # legacy | bnet
    client: str
    auth_port: int
    world_port: int
    rest_port: int
    loopback: str
    expansion_level: int
    hotfix_db: str  # none | hotfix | hotfixes
    realm_name: str
    has_armory: bool
    has_auction: bool
    has_achievements: bool
    aliases: tuple[str, ...] = field(default_factory=tuple)
    hero: str = "hero-vanilla.jpg"
    snapshot: str = ""
    year: int = 2006

    def visual(self) -> str:
        """Public-site chrome at this era's last patch.

        ``generation`` stays the data set (forums and talents). The live
        sites did not switch chrome on those same lines.
        """
        if self.id == "alpha":
            return "alpha"
        if self.id == "wod":
            return "gen2"
        if self.id in ("legion", "bfa", "shadowlands"):
            return "wowcom"
        return self.generation



