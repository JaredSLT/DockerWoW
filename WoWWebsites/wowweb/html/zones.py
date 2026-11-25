"""World map for one expansion. Fragments only; the shell adds the document."""

from __future__ import annotations

from html import escape

from ..catalog import Expansion
from ..content.zones import zones_for


def _text(value: str) -> str:
    return escape(value, quote=False)


def zone_map(exp: Expansion) -> str:
    blocks = []
    for row in zones_for(exp):
        items = "".join(f"<li>{_text(name)}</li>" for name in row["zones"])
        blocks.append(
            '<li class="map">'
            f"<h2>{_text(row['continent'])}</h2>"
            f'<ul class="zone-list">{items}</ul>'
            "</li>"
        )
    return f'<ul class="map-list">{"".join(blocks)}</ul>'
