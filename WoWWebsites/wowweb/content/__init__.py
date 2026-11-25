"""Era page copy."""

from .news import FEATURES, NEWS, PATCH_NOTES, features_for, intro_blurb, news_for
from .races import (
    CLASS_INFO,
    PROFESSIONS,
    RACE_INFO,
    RACES_BY_ERA,
    class_facts,
    classes_for,
    professions_for,
    race_facts,
    races_for,
)

__all__ = [
    "RACES_BY_ERA",
    "RACE_INFO",
    "CLASS_INFO",
    "PROFESSIONS",
    "NEWS",
    "FEATURES",
    "PATCH_NOTES",
    "races_for",
    "race_facts",
    "classes_for",
    "class_facts",
    "professions_for",
    "news_for",
    "features_for",
    "intro_blurb",
]
