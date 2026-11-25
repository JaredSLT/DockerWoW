"""GET/POST route handlers mixed into SiteHandler."""

from __future__ import annotations

from .. import accounts, armory, assets, content, forums, html as H, lab, search as site_search, talents
from ..account_ui import render_account
from ..content.sections import article_for
from ..html.vanilla_pages import rewrite as rewrite_vanilla
from ..html.vanilla_pages import special as vanilla_special
from ..html import era as era_pack
from ..html.vanilla_site import screenshot_of_the_day
from ..services import actions as service_actions
from ..services.page import services_page


class Routes:
    def _era_ctx(self, path: str, qs: dict, user: str | None, dev: bool) -> dict:
        return {
            "exp": self.exp,
            "user": user,
            "dev": dev,
            "qs": qs,
            "path": path,
            "labcfg": self.labcfg,
            "data_dir": self.data_dir,
        }

    def _era_full(self, path: str, qs: dict, user: str | None, dev: bool) -> bool:
        mod = era_pack.module(self.exp.id)
        if mod is None or not hasattr(mod, "full"):
            return False
        doc = mod.full(path, self._era_ctx(path, qs, user, dev))
        if not doc:
            return False
        self.send_html(doc)
        return True

    def _era_take(self, path: str, qs: dict, user: str | None, dev: bool) -> bool:
        mod = era_pack.module(self.exp.id)
        if mod is None or not hasattr(mod, "take"):
            return False
        taken = mod.take(path, self._era_ctx(path, qs, user, dev))
        if not taken:
            return False
        title, body = taken
        self.page(title, body)
        return True

    def route_get(self, path: str, qs: dict) -> None:
        exp = self.exp
        user = self.user()
        dev = "dev" in qs
        if exp.id == "vanilla":
            rewritten = rewrite_vanilla(path)
            if rewritten != path:
                path = rewritten
            elif path not in ("/", "/wow"):
                frag = vanilla_special(path)
                if frag is not None:
                    title, body = frag
                    return self.page(title, body)
        if self._era_full(path, qs, user, dev):
            return
        if path in ("/", "/wow"):
            realm = lab.realm_status(self.labcfg, exp)
            news = content.news_for(exp)
            chrome = exp.visual()
            if chrome == "gen1":
                crumb = "World of Warcraft Community Site"
            elif chrome == "alpha":
                crumb = "Current News"
            elif chrome == "gen2":
                crumb = "World of Warcraft"
            elif news:
                crumb = news[0][0]
            else:
                crumb = exp.name
            return self.page(crumb, H.home_page(exp, news, realm), crumb=crumb)
        if self._era_take(path, qs, user, dev):
            return
        if path == "/account/retrieve":
            return self.page(
                "Retrieve Password",
                "<h2>Retrieve Password</h2>"
                "<p>There is no emailed password reset. Sign in and change the password on the account page.</p>"
                '<p><a href="/account/login">Log In</a></p>',
            )
        if path == "/wow/news":
            items = "".join(
                f'<li><a href="/wow/news/{i}">{H.e(d)} — {H.e(t)}</a></li>'
                for i, (t, d, _) in enumerate(content.news_for(exp))
            )
            return self.page("Archived News", f"<h2>Archived News</h2><ul>{items}</ul>")
        if path.startswith("/wow/news/"):
            try:
                idx = int(path.rsplit("/", 1)[-1])
                t, d, b = content.news_for(exp)[idx]
            except (ValueError, IndexError):
                return self.page("News", H.error_page("That story is not on this site."), status=404)
            return self.page(t, H.article_page(t, d, b))
        if path in ("/wow/info", "/wow/info/introduction"):
            return self.page(
                "Game Guide",
                H.guide_hub(exp, content.races_for(exp), content.classes_for(exp), content.features_for(exp)),
            )
        if path == "/wow/info/features":
            return self.page("Features", H.simple_list("Features", content.features_for(exp)))
        if path == "/wow/info/races":
            links = []
            for r in content.races_for(exp):
                icon = assets.race_icon(exp.id, r)
                img = f'<img class="item-icon" src="{H.e(icon)}" alt="">' if icon else ""
                links.append(f'<li>{img}<a href="/wow/info/races/{r}">{content.RACE_INFO[r][0]}</a></li>')
            return self.page("Races", "<ul>" + "".join(links) + "</ul>")
        if path.startswith("/wow/info/races/"):
            slug = path.rsplit("/", 1)[-1]
            if slug not in content.RACE_INFO:
                return self.page("Races", H.error_page("Unknown race."), status=404)
            return self.page(content.RACE_INFO[slug][0], H.race_page(slug, exp))
        if path in ("/wow/info/classes", "/wow/info/classes/"):
            bits = []
            for c in content.classes_for(exp):
                name = content.CLASS_INFO[c][0]
                icon = assets.class_icon(exp.id, c)
                img = f'<img class="item-icon" src="{H.e(icon)}" alt="">' if icon else ""
                bits.append(
                    f'<li>{img}<a href="/wow/info/classes/{c}">{name}</a> — '
                    f'<a href="/wow/info/classes/{c}/talents.html">Talents</a></li>'
                )
            return self.page("Classes", "<h2>Classes</h2><ul>" + "".join(bits) + "</ul>")
        if path.endswith("/talents.html") and "/wow/info/classes/" in path:
            slug = path.split("/wow/info/classes/")[1].split("/")[0]
            trees = talents.trees_for(exp, slug)
            if not trees:
                return self.page("Talents", H.error_page("No talent tree for this class in this era."), status=404)
            build = (qs.get("build") or [""])[0]
            ranks = talents.parse_build(trees, build)
            pts = talents.points_available(exp)
            inner = H.talent_page(exp, slug, trees, ranks, pts, talents.encode_build(ranks))
            return self.page(f"{slug.title()} Talents", inner, crumb=f"{slug.title()} Talent Calculator")
        if path.startswith("/wow/info/classes/"):
            slug = path.rsplit("/", 1)[-1]
            if slug not in content.CLASS_INFO:
                return self.page("Classes", H.error_page("Unknown class."), status=404)
            return self.page(content.CLASS_INFO[slug][0], H.class_page(slug, exp))
        if path == "/wow/info/professions":
            return self.page("Professions", H.profession_index(exp))
        if path.startswith("/wow/info/professions/"):
            slug = path.rsplit("/", 1)[-1]
            body = H.profession_page(exp, slug)
            if body is None:
                return self.page("Professions", H.error_page("That profession is not part of this era."), status=404)
            return self.page("Professions", body)
        if path in ("/wow/info/basics", "/wow/info/beginners"):
            return self.page(
                "New Players",
                "<p>Four years have passed since the Third War. Choose a race, a class, and a realm. "
                "Quest, group, and find a profession. The <a href='/wow/info/basics/map'>world map</a> "
                "and <a href='/wow/info/classes/'>talent calculators</a> are the two pages every new adventurer needs.</p>"
                + H.simple_list("Start here", ["Create an account", "Read the race pages", "Pick a class", "Check realm status"]),
            )
        if path == "/wow/info/patches":
            note = content.PATCH_NOTES.get(exp.id, "")
            return self.page("Previous Patches", f"<p>{H.e(note)}</p><p>Last patch: <strong>{H.e(exp.last_patch)}</strong></p>")
        if path == "/wow/info/awards":
            return self.page("Awards", "<p>World of Warcraft collected a wall of industry awards through this era.</p>")
        if path == "/wow/info/basics/map":
            return self.page("World Map", H.zone_map(exp))
        if path == "/wow/realmstatus":
            return self.page(
                "Realm Status",
                H.realm_page(exp, lab.realm_status(self.labcfg, exp), dev="dev" in qs),
            )
        if path == "/wow/pvp/rankings":
            rows = armory.honor_ladder(self.labcfg, exp)
            if rows:
                table = "<table class='grid'><tr><th>Name</th><th>Level</th><th>Class</th><th>Honorable Kills</th><th>Rank</th></tr>"
                table += "".join(
                    f"<tr><td><a href='/armory/character/{H.e(r['name'])}'>{H.e(r['name'])}</a></td>"
                    f"<td>{H.e(r['level'])}</td><td>{H.e(r['class'])}</td><td>{H.e(r['kills'])}</td><td>{H.e(r['rank'])}</td></tr>"
                    for r in rows
                )
                table += "</table>"
            else:
                table = "<p>No honor data on this realm yet. Fight, log out, and the ladder will fill.</p>"
            return self.page("PvP Rankings", table)
        if path == "/wow/media/screenshots":
            shots = assets.screenshots(exp.id)
            if shots:
                grid = "".join(
                    f'<a class="shot" href="{H.e(url)}"><img src="{H.e(url)}" alt=""><span>{H.e(caption)}</span></a>'
                    for url, caption in shots
                )
                body = (
                    '<p>Screenshot of the Day archive.</p>'
                    f'<div class="shot-grid">{grid}</div>'
                    "<p>Submit shots from your adventures on this realm. The old RPSA mailbox is a forum thread now.</p>"
                )
            else:
                body = (
                    '<p>Screenshot of the Day archive.</p><img class="hero" src="/static/img/ssotd-elwynn.jpg" alt="Elwynn">'
                    "<p>Submit shots from your adventures on this realm. The old RPSA mailbox is a forum thread now.</p>"
                )
            return self.page("Screenshots", body)
        if path == "/wow/media/wallpapers":
            return self.page("Wallpapers", '<img class="hero" src="/static/img/' + H.e(exp.hero) + '" alt="">')
        if path == "/wow/search":
            q = (qs.get("q") or [""])[0]
            kind = (qs.get("searchType") or ["site"])[0]
            hits = site_search.search(self.labcfg, exp, self.data_dir, q, kind)
            if hits:
                items = "".join(
                    f"<li><a href='{H.e(hit['href'])}'>{H.e(hit['title'])}</a>"
                    f"<p>{H.e(hit['summary'])}</p></li>"
                    for hit in hits
                )
                body = f"<ul class='search-hits'>{items}</ul>"
            else:
                body = "<p>No matches.</p>"
            return self.page("Search", body)
        if path == "/shop":
            label = "Subscribe" if exp.id in ("bfa", "shadowlands") else "Shop"
            return self.page(label, H.shop_page(exp), crumb=label)
        if path == "/story":
            return self.page("Story", H.story_page(exp), crumb="Story")
        if path == "/esports":
            return self.page("Esports", H.esports_page(exp), crumb="Esports")
        if path == "/classic":
            return self.page("WoW Classic", H.classic_page(exp), crumb="WoW Classic")
        if path == "/support":
            tech = [
                f"<li><a href='/support/{H.e(article['slug'])}'>{H.e(article['title'])}</a>"
                f"<p>{H.e(article['summary'])}</p></li>"
                for article in site_search.support_articles(exp)
                if article["audience"] == "tech"
            ]
            extra = f"<h2>Technical Support</h2><ul>{''.join(tech)}</ul>" if tech else ""
            return self.page("Support", H.support_index(exp) + extra)
        if path.startswith("/support/"):
            slug = path.rsplit("/", 1)[-1]
            body = H.support_article(exp, slug)
            if body is not None:
                article = article_for(exp, slug)
                title = article.title if article else "Support"
                return self.page(title, body)
            article = next((item for item in site_search.support_articles(exp) if item["slug"] == slug), None)
            if article is None:
                return self.page("Support", H.error_page("That support article is not part of this era."), status=404)
            return self.page(article["title"], f"<h2>{H.e(article['title'])}</h2><p>{H.e(article['body'])}</p>")
        if path == "/armory":
            q = (qs.get("q") or [""])[0]
            store_error = "" if not exp.has_armory else armory.character_store(self.labcfg, exp)
            if q and not store_error:
                results, search_error = armory.search_with_status(self.labcfg, exp, q)
                store_error = store_error or search_error
            else:
                results = []
            return self.page(
                "The Armory",
                H.armory_home(exp, results, q, coming=not exp.has_armory, store_error=store_error),
            )
        if path.startswith("/armory/character/"):
            name = path.rsplit("/", 1)[-1]
            char = armory.get_character(self.labcfg, exp, name)
            if not char:
                return self.page("The Armory", H.error_page("Character not found. They must be level 10+ and have logged out once."), status=404)
            return self.page(char["name"], H.character_sheet(exp, char))
        if path.startswith("/armory/guild/"):
            name = path.rsplit("/", 1)[-1]
            g = armory.get_guild(self.labcfg, exp, name)
            if not g:
                return self.page("Guild", H.error_page("Guild not found."), status=404)
            return self.page(g["name"], H.guild_page(g))
        if path == "/armory/arena":
            rows = armory.arena_ladder(self.labcfg, exp)
            if not exp.has_armory:
                return self.page("Arena", "<p>Arenas arrive with The Burning Crusade.</p>")
            table = "".join(f"<tr><td>{H.e(r['name'])}</td><td>{H.e(r['rating'])}</td><td>{H.e(r['type'])}</td></tr>" for r in rows)
            body = table and f"<table class='grid'><tr><th>Team</th><th>Rating</th><th>Type</th></tr>{table}</table>" or "<p>No arena teams on this realm.</p>"
            return self.page("Arena Ladders", body)
        if path == "/armory/auctions":
            if not exp.has_auction:
                return self.page("Auction House", "<p>The remote Auction House arrives with Cataclysm.</p>")
            store_error = armory.character_store(self.labcfg, exp)
            rows = [] if store_error else armory.auctions(self.labcfg, exp)
            table = "".join(
                f"<tr><td><a href='/armory/item/{H.e(r['item_id'])}'>{H.e(r['name'])}</a></td><td>{H.e(r['buyout'])}</td></tr>"
                for r in rows
            )
            if store_error:
                body = f"<p>{H.e(store_error)}</p>"
            elif table:
                body = f"<table class='grid'><tr><th>Item</th><th>Buyout</th></tr>{table}</table>"
            else:
                body = "<p>The auction house is empty.</p>"
            return self.page("Auction House", body)
        if path.startswith("/armory/item/"):
            try:
                iid = int(path.rsplit("/", 1)[-1])
            except ValueError:
                return self.page("Item", H.error_page("Bad item id."), status=404)
            item = armory.get_item(self.labcfg, exp, iid)
            if not item:
                return self.page("Item", H.error_page("Item not in the world database."), status=404)
            return self.page(item["name"], H.item_page(exp, item))
        if path == "/forums":
            conn = forums.connect(self.data_dir)
            forums.seed_if_empty(conn, exp)
            conn.close()
            return self.page("Forums", H.forum_index(exp, forums.boards_for(exp)))
        if path.startswith("/forums/"):
            try:
                page = max(1, int((qs.get("page") or ["1"])[0]))
            except ValueError:
                page = 1
            return self.forum_get(path, user, page)
        if path == "/account":
            mode = "summary" if user else "login"
            return self._account_page(mode)
        if path == "/account/create":
            if not accounts.registration_open():
                return self.page("Create Account", f"<p>{accounts.CLOSED_ACCOUNT}</p>")
            return self._account_page("create")
        if path == "/account/login":
            step = (qs.get("step") or [""])[0]
            ident = (qs.get("identity") or [""])[0]
            if exp.id == "midnight" and step == "password":
                return self._account_page("login-password", identity=ident)
            return self._account_page("login")
        if path == "/account/password":
            if not user:
                return self.redirect("/account/login")
            return self._account_page("password")
        if path == "/account/services":
            return self._services_page()
        if path == "/account/logout":
            return self.redirect("/wow/", [("Set-Cookie", "wowweb=; Path=/; Max-Age=0")])
        if self.exp.id == "vanilla":
            leaf = path.rstrip("/").rsplit("/", 1)[-1]
            for suffix in (".html", ".shtml", ".xml", ".aspx"):
                if leaf.lower().endswith(suffix):
                    leaf = leaf[: -len(suffix)]
            leaf = leaf.replace("-", " ").replace("_", " ").strip()
            title = leaf.title() if leaf else "World of Warcraft"
            return self.page(
                title,
                f"<p>{H.e(title)}</p>"
                '<p><a href="/">Current News</a> · '
                '<a href="/info/">Game Guide</a> · '
                '<a href="/community/">Community</a> · '
                '<a href="/downloads/">Downloads</a></p>',
            )
        return self.page("Not Found", H.error_page("That page is not in this era's site map."), status=404)

    def _account_page(self, mode: str, error: str = "", notice: str = "", identity: str = "") -> None:
        user = self.user()
        summary = (
            accounts.account_summary(self.labcfg, self.exp, user)
            if user
            else {"email": "", "characters": []}
        )
        titles = {
            "summary": "Account Management",
            "login": "Log In",
            "login-password": "Log In",
            "create": "Create Account",
            "password": "Change Password",
        }
        body = render_account(
            self.exp,
            user=user or "",
            error=error,
            notice=notice,
            mode=mode,
            email=identity or summary.get("email") or "",
            characters=summary.get("characters") or [],
            login_kind="email" if accounts.email_login(self.exp) else "account",
            separate_game_name=self.exp.proto == "bnet",
        )
        return self.page(titles.get(mode, "Account"), body)

    def _services_page(self, error: str = "", notice: str = "") -> None:
        user = self.user()
        if not user:
            return self.redirect("/account/login")
        body = services_page(self.labcfg, self.exp, user, self.data_dir, error=error, notice=notice)
        return self.page("Character Services", body)

    def forum_get(self, path: str, user: str | None, page: int = 1) -> None:
        parts = [p for p in path.split("/") if p]
        # forums, board, maybe id
        if len(parts) == 2:
            slug = parts[1]
            title = forums.board_title(self.exp, slug)
            if not title:
                return self.page("Forums", H.error_page("Unknown board."), status=404)
            conn = forums.connect(self.data_dir)
            forums.seed_if_empty(conn, self.exp)
            threads = forums.list_threads(conn, self.exp, slug)
            conn.close()
            return self.page(title, H.forum_board(title, slug, threads, user, page))
        if len(parts) == 3 and parts[2].isdigit():
            slug, tid = parts[1], int(parts[2])
            conn = forums.connect(self.data_dir)
            thread = forums.get_thread(conn, self.exp, tid)
            conn.close()
            if not thread:
                return self.page("Forums", H.error_page("Thread not found."), status=404)
            return self.page(thread["title"], H.forum_thread(slug, thread, user))
        return self.page("Forums", H.error_page("Unknown forum URL."), status=404)

    def route_post(self, path: str) -> None:
        form = self.read_post()
        if path == "/account/create":
            if not accounts.registration_open():
                return self._account_page("create", error=accounts.CLOSED_ACCOUNT)
            identity = (form.get("identity") or form.get("email") or form.get("username") or "").strip()
            password = form.get("password", "")
            confirm = form.get("confirm", "")
            game_name = (form.get("game_name") or "").strip()
            if password != confirm:
                return self._account_page("create", error="The two passwords do not match.")
            email = identity if accounts.email_login(self.exp) else form.get("email", "")
            username = game_name if self.exp.proto == "bnet" else identity
            ok, msg, session_name = accounts.create_account(
                self.labcfg, self.exp, username, password, email, game_name
            )
            if ok and session_name:
                cookie = accounts.sign_session(self.secret, self.exp.id, session_name)
                dest = "/account/completed" if self.exp.id == "vanilla" else "/account/"
                return self.redirect(dest, [("Set-Cookie", f"wowweb={cookie}; Path=/; HttpOnly")])
            return self._account_page("create", error=msg)
        if path == "/account/login":
            identity = (form.get("identity") or form.get("email") or form.get("username") or "").strip()
            password = form.get("password", "")
            if self.exp.id == "midnight" and identity and not password:
                from urllib.parse import quote

                return self.redirect(f"/account/login?step=password&identity={quote(identity)}")
            ok, result = accounts.authenticate(self.labcfg, self.exp, identity, password)
            if not ok:
                if self.exp.id == "alpha" and form.get("stay") == "sidebar":
                    realm = lab.realm_status(self.labcfg, self.exp)
                    news = content.news_for(self.exp)
                    return self.page(
                        "Current News",
                        H.home_page(self.exp, news, realm),
                        login_error=result,
                    )
                if self.exp.id == "midnight" and identity:
                    return self._account_page("login-password", error=result, identity=identity)
                return self._account_page("login", error=result)
            cookie = accounts.sign_session(self.secret, self.exp.id, result)
            return self.redirect("/account/", [("Set-Cookie", f"wowweb={cookie}; Path=/; HttpOnly")])
        if path == "/account/password":
            user = self.user()
            if not user:
                return self.redirect("/account/login")
            password = form.get("password", "")
            confirm = form.get("confirm", "")
            if password != confirm:
                return self._account_page("password", error="The two passwords do not match.")
            ok, msg = accounts.change_password(
                self.labcfg, self.exp, user, form.get("current", ""), password
            )
            if not ok:
                return self._account_page("password", error=msg)
            return self._account_page("summary", notice=msg)
        if path.startswith("/account/services"):
            return self._services_post(path, form)
        if path == "/account/logout":
            return self.redirect("/wow/", [("Set-Cookie", "wowweb=; Path=/; Max-Age=0")])
        if path.endswith("/new") and path.startswith("/forums/"):
            user = self.user()
            if not user:
                return self.redirect("/account/login")
            slug = path.split("/")[2]
            if not forums.board_title(self.exp, slug):
                return self.page("Forums", H.error_page("Unknown board."), status=404)
            conn = forums.connect(self.data_dir)
            tid = forums.create_thread(conn, self.exp, slug, user, form.get("title", "Untitled"), form.get("body", ""))
            conn.close()
            return self.redirect(f"/forums/{slug}/{tid}")
        if path.endswith("/reply") and path.startswith("/forums/"):
            user = self.user()
            if not user:
                return self.redirect("/account/login")
            parts = path.split("/")
            slug, tid = parts[2], int(parts[3])
            conn = forums.connect(self.data_dir)
            forums.add_post(conn, tid, user, form.get("body", ""))
            conn.close()
            return self.redirect(f"/forums/{slug}/{tid}")
        self.page("Not Found", H.error_page("Unknown form."), status=404)

    def _services_post(self, path: str, form: dict) -> None:
        user = self.user()
        if not user:
            return self.redirect("/account/login")
        try:
            guid = int(form.get("guid") or "0")
        except ValueError:
            guid = 0
        try:
            guild_id = int(form.get("guild_id") or "0")
        except ValueError:
            guild_id = 0
        action = path.rstrip("/").rsplit("/", 1)[-1]
        if action == "name":
            ok, msg = service_actions.change_name(self.labcfg, self.exp, user, guid, form.get("name", ""))
        elif action == "appearance":
            ok, msg = service_actions.change_appearance(self.labcfg, self.exp, user, guid)
        elif action == "race":
            ok, msg = service_actions.change_race(self.labcfg, self.exp, user, guid)
        elif action == "faction":
            ok, msg = service_actions.change_faction(self.labcfg, self.exp, user, guid)
        elif action == "guild":
            ok, msg = service_actions.rename_guild(self.labcfg, self.exp, user, guild_id, form.get("name", ""))
        elif action == "transfer":
            ok, msg = service_actions.transfer_character(
                self.labcfg,
                self.exp,
                user,
                guid,
                form.get("dest", ""),
                form.get("password", ""),
                form.get("confirm", ""),
                form.get("dest_email", ""),
                form.get("dest_game", ""),
                form.get("dest_account", ""),
            )
        elif action == "boost":
            ok, msg = service_actions.boost_character(self.labcfg, self.exp, user, guid)
        elif action == "token":
            ok, msg = service_actions.exchange_token(
                self.labcfg, self.exp, user, guid, form.get("side", ""), self.data_dir
            )
        else:
            return self._services_page(error="That service is not available on this realm.")
        if ok:
            return self._services_page(notice=msg)
        return self._services_page(error=msg)

