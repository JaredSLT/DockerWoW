# Era WoW websites

Python server that takes a World of Warcraft expansion id and serves that expansion’s **last-patch community site** (game guide, news, talent calculators, realm status, Armory, forums, account create) as it looked at the end of that expansion.

Live widgets read the matching realm in the lab that contains this directory (MariaDB `127.0.0.1:13306`). Set `WOW_LAB` when the site is not inside that tree.

## Run

```bash
python3 serve.py --list
python3 serve.py vanilla
python3 serve.py wotlk --port 18765
```

Open `http://127.0.0.1:18765/wow/` (default port 18765, away from common 8080 services).

Ids: `alpha`, `vanilla`, `tbc`, `wotlk`, `cata`, `mop`, `wod`, `legion`, `bfa`, `shadowlands`, `dragonflight`, `warwithin`, `midnight`.

Aliases include `classic` → vanilla, `wrath` → wotlk, `tww` → warwithin.

## Lab

Account create writes SRP6 verifiers into `{short}_auth.account` (same scheme as the lab’s `post-setup.py`). Forums use that account name. Armory reads `{short}_characters`. If MariaDB or the world port is down, static pages still load and realm status shows Down.

Midnight is treated as TrinityCore (`bnet`, ports 11125 / 18096 / 18886) even if the lab catalog does not list it yet.

This process binds `127.0.0.1` by default. It is a personal archive, not a public rehost of Blizzard’s site.

## Layout

```
serve.py                 CLI
wowweb/
  catalog/               expansion records
  http/                  request handler and routes
  html/                  layout + page bodies
  talents/               talent trees by era
  armory/                character/guild/AH queries
  content/               races, news, copy
  lab.py accounts.py forums.py
static/css/  static/js/  static/img/
```
