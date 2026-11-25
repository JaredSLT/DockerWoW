"""HTML rendering for all four visual generations."""

from .armory import armory_home, character_sheet, guild_page, item_page
from .forums import forum_board, forum_index, forum_thread
from .guide import (
    account_form,
    article_page,
    class_page,
    guide_hub,
    home_page,
    map_page,
    race_page,
    realm_page,
    talent_page,
)
from .layout import e, error_page, layout, simple_list
from .professions import profession_index, profession_page
from .sections import (
    classic_page,
    esports_page,
    shop_page,
    story_page,
    support_article,
    support_index,
)
from .zones import zone_map

__all__ = [
    "e",
    "layout",
    "home_page",
    "article_page",
    "guide_hub",
    "race_page",
    "class_page",
    "talent_page",
    "map_page",
    "realm_page",
    "account_form",
    "armory_home",
    "character_sheet",
    "item_page",
    "guild_page",
    "forum_index",
    "forum_board",
    "forum_thread",
    "simple_list",
    "error_page",
    "support_index",
    "support_article",
    "shop_page",
    "story_page",
    "esports_page",
    "classic_page",
    "profession_index",
    "profession_page",
    "zone_map",
]
