"""Profession index and one page per profession."""

from __future__ import annotations

from html import escape

from ..catalog import Expansion
from ..content import professions_for


def _slug(name: str) -> str:
    return name.lower().replace(" ", "")


def _text(value: str) -> str:
    return escape(value, quote=False)


def profession_index(exp: Expansion) -> str:
    items = []
    for name, _desc in professions_for(exp):
        slug = escape(_slug(name), quote=True)
        items.append(f'<li><a href="/wow/info/professions/{slug}">{_text(name)}</a></li>')
    return "<h2>Professions</h2><ul>" + "".join(items) + "</ul>"


def profession_page(exp: Expansion, slug: str) -> str | None:
    want = _slug(slug)
    for name, desc in professions_for(exp):
        if _slug(name) == want:
            return f"<h2>{_text(name)}</h2><p>{_text(desc)}</p>"
    return None
