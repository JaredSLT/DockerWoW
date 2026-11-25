"""Section page bodies. Fragments only; the shell adds the document."""

from __future__ import annotations

from .. import assets
from ..catalog import Expansion
from ..content.sections import (
    article_for,
    articles_for,
    classic_copy,
    esports_blocks,
    shop_shelf,
    story_for,
    tournament_esports,
)
from .layout import e


def _paragraphs(lines: tuple[str, ...]) -> str:
    return "".join(f"<p>{e(line)}</p>" for line in lines)


def _blocks(blocks) -> str:
    parts = []
    for block in blocks:
        parts.append(
            '<article class="post">'
            f"<h2>{e(block.heading)}</h2>"
            f"{_paragraphs(block.paragraphs)}"
            "</article>"
        )
    return "".join(parts)


def _story_hero(exp: Expansion) -> str:
    shots = assets.screenshots(exp.id, limit=1)
    if not shots:
        return ""
    src, caption = shots[0]
    # Client extracts only. A remote URL is not a hero.
    if not src.startswith("/static/"):
        return ""
    return f'<figure><img class="hero" src="{e(src)}" alt="{e(caption)}"></figure>'


def support_index(exp: Expansion) -> str:
    items = []
    for article in articles_for(exp):
        items.append(
            "<li>"
            f'<a href="/support/{e(article.slug)}">{e(article.title)}</a>'
            f"<p>{e(article.summary)}</p>"
            "</li>"
        )
    return (
        '<section class="support-index">'
        "<h2>Support</h2>"
        f"<p>Articles for {e(exp.name)}, patch {e(exp.last_patch)}.</p>"
        f"<ul>{''.join(items)}</ul>"
        "</section>"
    )


def support_article(exp: Expansion, slug: str) -> str | None:
    article = article_for(exp, slug)
    if article is None:
        return None
    extra = ""
    if article.slug == "talents":
        extra = '<p><a href="/wow/info/classes/">Talent Calculators</a></p>'
    elif article.slug == "honor":
        extra = '<p><a href="/wow/pvp/rankings">PvP Rankings</a></p>'
    elif article.slug == "arena" and exp.has_armory:
        extra = '<p><a href="/armory/arena">Arena Ladders</a></p>'
    return (
        '<article class="support-article">'
        f"<h2>{e(article.title)}</h2>"
        f"{_paragraphs(article.paragraphs)}"
        f"{extra}"
        '<p><a href="/support">All support articles</a></p>'
        "</article>"
    )


def shop_page(exp: Expansion) -> str:
    shelf = shop_shelf(exp)
    items = "".join(
        "<article class=\"shop-item\">"
        f"<h3>{e(item.title)}</h3>"
        f"<p>{e(item.body)}</p>"
        "</article>"
        for item in shelf.items
    )
    label = "Subscribe" if exp.id in ("bfa", "shadowlands") else "Buy Now"
    return (
        f'<section class="shop-shelf shop-{e(exp.id)}">'
        "<h2>Shop</h2>"
        f"<p>{e(shelf.intro)}</p>"
        f'<div class="shop-items">{items}</div>'
        '<p class="shop-note">This shelf is a display. Nothing here is charged.</p>'
        f'<p class="shop-label"><span class="cta">{label}</span></p>'
        "</section>"
    )


def story_page(exp: Expansion) -> str:
    return f'<section class="story">{_story_hero(exp)}{_blocks(story_for(exp))}</section>'


def esports_page(exp: Expansion) -> str:
    body = _blocks(esports_blocks(exp))
    if tournament_esports(exp):
        extra = (
            '<table class="grid">'
            "<tr><th>Circuit</th><th>Season</th><th>Format</th></tr>"
            f"<tr><td>Arena World Championship</td><td>{e(exp.year)}</td><td>3v3</td></tr>"
            f"<tr><td>Mythic Dungeon International</td><td>{e(exp.year)}</td><td>Mythic dungeons</td></tr>"
            "</table>"
        )
    else:
        links = ['<a href="/wow/pvp/rankings">PvP Rankings</a>']
        if exp.has_armory:
            links.append('<a href="/armory/arena">Arena Ladders</a>')
        extra = "<p>" + " · ".join(links) + "</p>"
    return f'<section class="esports">{body}{extra}</section>'


def classic_page(exp: Expansion) -> str:
    block = classic_copy(exp)
    kind = "classic-promo" if block.heading == "WoW Classic" else "classic-note"
    return f'<section class="{kind}">{_blocks((block,))}</section>'
