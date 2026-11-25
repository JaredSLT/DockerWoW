"""Forum page bodies."""

from __future__ import annotations

from datetime import datetime

from ..catalog import Expansion
from .layout import e

_PAGE_SIZE = 20


def forum_index(exp: Expansion, boards: list[tuple[str, str]]) -> str:
    groups = [
        ("Game Discussion", {
            "general", "suggestions", "pvp", "quests", "dungeons", "delves", "garrisons",
            "housing", "professions", "rp", "trading", "scenarios", "classhalls",
            "islands", "covenants",
        }),
        ("Classes", {
            "druid", "hunter", "mage", "paladin", "priest", "rogue", "shaman", "warlock",
            "warrior", "deathknight", "monk", "demonhunter", "evoker", "classes",
        }),
        ("Community", {"guilds", "realm", "ui"}),
        ("Support", {"bugs", "support"}),
    ]
    leftover = [b for b in boards]
    sections = []
    used = set()
    for heading, slugs in groups:
        rows = []
        for slug, title in leftover:
            if slug in slugs:
                used.add(slug)
                rows.append(
                    "<tr class='forum-row'>"
                    f"<td class='forum-name'><a href='/forums/{e(slug)}'>{e(title)}</a></td>"
                    f"<td class='forum-desc'>Discuss {e(title).lower()} on {e(exp.realm_name)}.</td>"
                    "</tr>"
                )
        if rows:
            sections.append(
                f"<h3 class='forum-cat'>{e(heading)}</h3>"
                "<table class='grid forum-table'>"
                "<thead><tr><th>Forum</th><th>Description</th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table>"
            )
    extra = "".join(
        "<tr class='forum-row'>"
        f"<td class='forum-name'><a href='/forums/{e(s)}'>{e(t)}</a></td>"
        "<td class='forum-desc'></td></tr>"
        for s, t in leftover
        if s not in used
    )
    if extra:
        sections.append(
            "<h3 class='forum-cat'>Other</h3>"
            "<table class='grid forum-table'>"
            "<thead><tr><th>Forum</th><th>Description</th></tr></thead>"
            f"<tbody>{extra}</tbody></table>"
        )
    return (
        "<div class='forums forum-index'>"
        "<h2>World of Warcraft Forums</h2>"
        "<p class='forum-lead'>Blizzard provides these forums for players to chat, exchange ideas, and submit feedback. "
        "Posting requires a realm account. Anyone may read.</p>"
        + "".join(sections)
        + "</div>"
    )


def _coerce_page(page: int, pages: int) -> int:
    try:
        number = int(page)
    except (TypeError, ValueError):
        return 1
    if number < 1:
        return 1
    if number > pages:
        return pages
    return number


def _pager(page: int, pages: int) -> str:
    if pages < 2:
        return ""
    links = []
    for number in range(1, pages + 1):
        mark = " current" if number == page else ""
        links.append(f"<a class='page{mark}' href='?page={number}'>{number}</a>")
    return "<nav class='forum-pager' aria-label='Pages'>" + "".join(links) + "</nav>"


def forum_board(
    title: str,
    slug: str,
    threads: list[dict],
    user: str | None,
    page: int = 1,
) -> str:
    pages = max(1, (len(threads) + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page_n = _coerce_page(page, pages)
    start = (page_n - 1) * _PAGE_SIZE
    rows = []
    for t in threads[start : start + _PAGE_SIZE]:
        last = datetime.utcfromtimestamp(t.get("last") or t["created"]).strftime("%Y-%m-%d %H:%M")
        rows.append(
            "<tr class='thread-row'>"
            f"<td class='thread-title'><a class='topic' href='/forums/{e(slug)}/{t['id']}'>{e(t['title'])}</a></td>"
            f"<td class='thread-author'>{e(t['author'])}</td>"
            f"<td class='thread-replies'>{e(t['replies'])}</td>"
            f"<td class='thread-views'>{e(t.get('views') or 0)}</td>"
            f"<td class='thread-last'><span class='date'>{e(last)}</span></td>"
            "</tr>"
        )
    table = "".join(rows) or "<tr class='forum-empty'><td colspan='5'>No threads yet.</td></tr>"
    if user:
        form = f"""
<h3>New Thread</h3>
<form class="acct" method="post" action="/forums/{e(slug)}/new">
  <label>Title <input name="title" required maxlength="120"></label>
  <label>Body <textarea name="body" required rows="6"></textarea></label>
  <button type="submit">Post</button>
</form>"""
    else:
        form = '<p><a href="/account/login">Log in</a> with a realm account to post.</p>'
    return f"""
<div class='forums forum-board'>
<h2>{e(title)}</h2>
<table class='grid forum-threads'>
<thead><tr><th>Subject</th><th>Author</th><th>Replies</th><th>Views</th><th>Last Post</th></tr></thead>
<tbody>
{table}
</tbody>
</table>
{_pager(page_n, pages)}
{form}
</div>
"""


def forum_thread(board: str, thread: dict, user: str | None) -> str:
    posts = []
    for p in thread.get("posts") or []:
        when = datetime.utcfromtimestamp(p["created"]).strftime("%Y-%m-%d %H:%M")
        kind = "post blizzard-post" if p.get("author") == "Blizzard" else "post"
        posts.append(
            f"<article class='{kind}'><header>{e(p['author'])} · {e(when)}</header>"
            f"<pre>{e(p['body'])}</pre></article>"
        )
    form = ""
    if user:
        form = f"""
<form class="acct" method="post" action="/forums/{e(board)}/{thread['id']}/reply">
  <label>Reply <textarea name="body" required rows="5"></textarea></label>
  <button type="submit">Reply</button>
</form>"""
    return (
        f"<div class='forums forum-thread'><h2>{e(thread['title'])}</h2>"
        f"{''.join(posts)}{form}</div>"
    )
