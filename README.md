# WoW private-server lab

One tree runs every catalog expansion against a single MariaDB. `./setup.sh`
is the only command you need. On a terminal it opens a menu. The same actions
are subcommands, so a boot unit and a backup timer can call them.

```bash
./setup.sh                    # menu: packages, access, realms, backups
./setup.sh host               # install Docker and the host files
./setup.sh setup vanilla      # compile, extract, database, start
./setup.sh up vanilla,tbc     # start realms that are already built
./setup.sh help
```

A new clone with no terminal arguments prints help and exits. It does not
build every expansion. That is `./setup.sh setup all`.

Place each client under `clients/` yourself. The menu checks for `Data/` and
does not download a client.

The first menu run asks how players connect:

- This machine uses `vanilla.local` and the other loopback names.
- One public address uses a unique port per realm.
- A DNS name you own needs its own address per realm, because stock ports
  bind once per address.

The GM account is created from `.env` on the first start and then left alone.
Change it with `./setup.sh password <short>`. `./setup.sh update` recompiles
a moved core and runs init so incremental SQL is applied. A realm that was
stopped stays stopped. It does not replace a full world dump by itself.
`update check` only prints drift. `update apply --db world` or `--db full`
is how you replace a database.
The old 30-minute git timer is disabled by `./setup.sh host`.

Paths in this repository are relative to the repo root. Nothing in the
scripts requires a particular username, disk label, or absolute install path.

## What you need

- Linux, Docker Engine, and the `docker compose` plugin
- `rsync`, `python3`, `curl`, and `git`
- `sudo` for the one-time host setup (loopback addresses, `/etc/hosts`, and
  the removable-disk mount)
- Game clients you already own, placed under `clients/` (they are not downloaded)

mmap generation is the slow step. Plan on hours per expansion. A realm will
not start until maps, vmaps, and mmaps for its continents are present.

## 1. Put the tree somewhere stable

Clone or copy the repo anywhere you can keep it. `WOW_TREE` is discovered
from this checkout. It is not a hardcoded `/mnt/wow-nvme/WoW`.

`./setup.sh host` runs `./scripts/host-setup.sh`, which classifies the disk:

- **Internal.** The repo is not under `/run/media` or `/media`. No fstab line
  is written, and the disk is not bind-mounted a second time. `WOW_VOLUME_MOUNT`
  and the compose bind are the repo root. `WOW_TREE` is the repo root. An
  internal checkout is not forced to `/mnt/wow-nvme/WoW`.
- **Removable.** The mount point is under `/run/media` or `/media`. udisks may
  rename that folder after each boot. The filesystem UUID is bind-mounted at
  `WOW_VOLUME_MOUNT` (default `/mnt/wow-nvme` only in this case) so the path
  stays put. The fstab type comes from the disk, not a hardcoded `ext4`.
  `WOW_TREE` is that mount plus the repo's path relative to the filesystem.

Both layouts install loopback addresses `127.0.0.2`–`127.0.0.17`, `/etc/hosts`
names (`short.local` only), and HAProxy config. `/etc/wow/volume.env` records
the discovered `WOW_VOLUME_UUID` (empty on an internal disk unless you pinned
one), `WOW_VOLUME_MOUNT`, `WOW_TREE`, and `WOW_MEDIA_USER`.

Override the removable mount point in `.env` if `/mnt/wow-nvme` is wrong:

```bash
WOW_VOLUME_MOUNT=/srv/wow
```

`WOW_VOLUME_MOUNT` is only the stable mount for a removable disk. An internal
tree uses the repo root even if `.env` still says `/mnt/wow-nvme`.

The desktop automounter names its folder after the filesystem label, and
appends `1` when that name is already taken. On a removable disk,
`wow-media-alias.sh` bind-mounts the stable path onto `/run/media/<you>/<label>`
and `<label>1` so an old container that still mentions those folders sees the
real disk. The label and the username come from the disk and from the user
who runs `host-setup.sh`. An internal disk skips that alias.

Containers wait until `setup.sh` and the realm files are actually visible.
They do not exit and restart-loop while the disk is absent.

Do not run `docker compose down -v`. That deletes the MariaDB volume.

## 2. Configuration

```bash
cp .env.example .env
```

| Variable | Default | Role |
|---|---|---|
| `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD` | `wow` | Shared MariaDB (`wow-db`). Published on `127.0.0.1` at `MYSQL_PUBLISH_PORT` (default `13306`) |
| `ACCOUNT_NAME` / `ACCOUNT_PASSWORD` | `admin` / `admin` | GM account. WoD and Legion+ log in as `admin@<short>.local` |
| `BIND_MODE` | `haproxy` | `haproxy`, `ports`, or `loopback` (see below) |
| `REALM_ADDRESS` | `127.0.0.1` | Advertised address when `BIND_MODE=ports` |
| `POINT_CLIENTS` | `0` | `1` rewrites client realmlist/portal files |
| `GIT_BASE` | empty | Optional mirror prefix. Empty uses the public repositories |
| `GITHUB_TOKEN` or `GH_TOKEN` | empty | Optional. Sent as a bearer token for GitHub release and `git ls-remote` checks |
| `WOW_VOLUME_MOUNT` | `/mnt/wow-nvme` | Stable mount for a removable disk only. An internal tree uses the repo root |
| `WOW_READY_WAIT` | `2700` | Seconds to wait for auth and world after `up` |

MariaDB is published on `127.0.0.1` only. The buffer pool scales with RAM
(25% of memory, at least 256M, at most 4G).

Cores clone the public repositories in `docker/common/repos.sh`. Midnight
tracks TrinityCore `master`. Cataclysm tracks The Cataclysm Preservation
Project. Legion, Battle for Azeroth, Shadowlands, Dragonflight, The War
Within, and Wrath Classic are pinned TDB expansions. A pin advances only when
a newer GitHub release tag exists on both the database release and the core
repo. The two sides do not float independently. Legion's core tag and
`TDB735` move only as that pair. Set `GIT_BASE` only when the build should
clone `${GIT_BASE}/<core name>.git` instead. A tree that already has
`servers/<short>/bin` does not need it to start.

Client files under `clients/` are not rewritten unless `POINT_CLIENTS=1`.

## 3. Install the clients

Each expansion reads exactly one client directory:

| Short | Client directory |
|---|---|
| alpha | `clients/World-of-Warcraft-0.5` |
| vanilla | `clients/World-of-Warcraft-1.12.1` |
| tbc | `clients/World-of-Warcraft-2.4.3` |
| wotlk | `clients/World-of-Warcraft-3.3.5a` |
| cata | `clients/World-of-Warcraft-4.3.4` |
| mop | `clients/World-of-Warcraft-5.4.8` |
| wod | `clients/World-of-Warcraft-6.2.3` |
| legion | `clients/World-of-Warcraft-7.3.5` |
| bfa | `clients/World-of-Warcraft-8.3.7` |
| shadowlands | `clients/World-of-Warcraft-9.2.7` |
| dragonflight | `clients/World-of-Warcraft-10.2.7` |
| warwithin | `clients/World-of-Warcraft-11.2.7` |
| midnight | `clients/World-of-Warcraft-12.x.x` |

The client root is the directory that contains `Data/`. These layouts also
work: `data/`, `World of Warcraft/Data`, `_retail_/Data`, `_classic_/Data`.
Other client folders in `clients/` are ignored.

Extracted data is written into `servers/<short>/` (`maps`, `vmaps`, `mmaps`,
`dbc` or `db2`). Alpha writes `servers/alpha/etc/maps` and `etc/navs`.
Launch refuses to start a realm whose continents are missing. Maps that have
no collision geometry do not get a `.vmtree`; that does not block launch.

Check what is already extracted:

```bash
./scripts/extract-data.sh --list
```

Finish or repeat one expansion without deleting the others:

```bash
./scripts/extract-data.sh --skip-existing legion
./scripts/extract-data.sh --skip-mmaps mop    # maps and vmaps only
```

`--skip-existing` keeps a complete extract and redoes a layer that is missing
continent files. A normal run without that flag deletes the previous maps,
vmaps, and mmaps for the selected realm and extracts them again. It never
deletes `bin/`, `sql/`, or `etc/`.

## 4. Build and start

```bash
./setup.sh vanilla
```

For that realm, in order:

1. Compile the core in Docker and install it under `servers/vanilla/`
2. Fetch world-content SQL
3. Extract maps, vmaps, mmaps, and dbc/db2 from the matching client
4. Start `wow-db` (MariaDB 11.4) if it is not already up
5. Import databases and start `wow-vanilla`

Useful flags:

```bash
./setup.sh --no-start vanilla       # compile, SQL, extract; do not launch
./setup.sh --skip-build vanilla     # client data and database only
./setup.sh --skip-mmaps wotlk       # skip the multi-hour mmap pass
./setup.sh --continue               # keep going after one expansion fails
./setup.sh --help
./setup.sh list
```

The same steps, split:

```bash
./scripts/build-servers.sh --only vanilla,tbc
./docker/runtime/fetch-db.sh vanilla,tbc
./scripts/extract-data.sh vanilla,tbc
./scripts/launch-servers.sh up vanilla,tbc
```

`up vanilla` then `up tbc` leaves both running. Each realm has its own
`<short>_auth`, `<short>_world`, and `<short>_characters` databases on
`wow-db`. Starting a subset does not remove the other containers.

## 5. Point the client at a realm

With the default `BIND_MODE=haproxy`, HAProxy listens on one loopback address
per realm. `/etc/hosts` maps the hostname to that address. The auth database
advertises the same hostname and the stock world port.

| Short | Hostname | Auth | World | REST |
|---|---|---|---|---|
| alpha | alpha.local | 3724 | 8100 | |
| vanilla | vanilla.local | 3724 | 8085 | |
| tbc | tbc.local | 3724 | 8085 | |
| wotlk | wotlk.local | 3724 | 8085 | |
| cata | cata.local | 3724 | 8085 | |
| mop | mop.local | 3724 | 8085 | |
| wod | wod.local | 1119 | 8085 | |
| legion | legion.local | 1119 | 8085 | 8081 |
| bfa | bfa.local | 1119 | 8085 | 8081 |
| shadowlands | shadowlands.local | 1119 | 8085 | 8081 |
| dragonflight | dragonflight.local | 1119 | 8085 | 8081 |
| warwithin | warwithin.local | 1119 | 8085 | 8081 |
| midnight | midnight.local | 1119 | 8085 | 8081 |

Alpha also publishes `9081`, `9090`, and `9100` on `alpha.local`.

Classic and Wrath-era clients, in-game or in `realmlist.wtf`:

```text
set realmlist vanilla.local
```

Legion and later, in `Config.wtf`:

```text
SET portal "legion.local"
```

Log in with `admin` / `admin` until you change it. Warlords of Draenor and
Legion and later use `admin@<short>.local` with the same password, for example
`admin@midnight.local` and `admin@wod.local`. The first successful start
creates that account and then leaves the password alone. `./setup.sh password
<short>` sets a new one without restarting the world server.

`/etc/hosts` is consulted before mDNS, so the names work without a DNS server.
They are local to this machine. A client on another computer needs the same
names pointed at this host, and `BIND_MODE=ports` (below) if it cannot use
these loopback addresses.

## 6. Confirm a realm is actually accepting connections

```bash
./setup.sh status
./setup.sh logs vanilla
```

`wow-<short>` should be `healthy`. Health checks the auth port and the world
port inside the container.

HAProxy accepts a TCP connection even when the realm behind it is down, then
closes it. A successful `nc vanilla.local 3724` only proves the proxy is
listening. To prove the realm itself is up, the container health status is
`healthy`, or from inside the container:

```bash
docker exec wow-vanilla bash -lc 'echo >/dev/tcp/127.0.0.1/3724 && echo auth-open'
docker exec wow-vanilla bash -lc 'echo >/dev/tcp/127.0.0.1/8085 && echo world-open'
```

## Other bind modes

Set `BIND_MODE` in `.env`, then `./setup.sh up`.

- `haproxy` (default). Stock ports on `vanilla.local` and the other names.
  Realm containers publish no host ports.
- `ports`. Unique ports on `0.0.0.0`, and the realm advertises
  `REALM_ADDRESS`. Auth/world: alpha `13700`/`18100`, vanilla `13724`/`18085`,
  tbc `13725`/`18086`, wotlk `13726`/`18087`, cata `13727`/`18088`,
  mop `13728`/`18089`, wod `11119`/`18090`, legion `11120`/`18091`
  (REST `18881`), bfa `11121`/`18092` (`18882`), shadowlands `11122`/`18093`
  (`18883`), dragonflight `11123`/`18094` (`18884`), warwithin `11124`/`18095`
  (`18885`), midnight `11125`/`18096`.
- `loopback`. Stock auth port on that realm's `127.0.0.x`. World and REST
  stay on the unique ports above, because binding `0.0.0.0:8085` also occupies
  `127.0.0.x:8085`.

## Day to day

```bash
./setup.sh status
./setup.sh logs legion
./setup.sh down vanilla          # stop one realm
./setup.sh down                  # stop the stack (keeps the database volume)
./setup.sh restart vanilla
./setup.sh update                   # rebuild cores whose source moved
./setup.sh update check wotlk
./setup.sh update apply wotlk --db skip
./setup.sh backup path /var/backups/wow
./setup.sh backup now
./setup.sh backup schedule on --hour 04
./setup.sh boot enable vanilla,wotlk
./setup.sh password vanilla
./setup.sh website vanilla create off
```

`restart` recreates that realm against the current mount. It does not replay
database imports. Incremental SQL runs from `./setup.sh update` and from
`update apply`, not from `restart` by itself.

`./setup.sh update` recompiles every realm that already has an install when
its core revision differs from the last successful build. Realms that were
never built are skipped. It does not replace a full world dump. Init applies
incremental SQL. A realm that was running is restarted after that and must
become healthy. A realm that was stopped is left stopped. `update check` only
prints whether a public revision moved. `update apply --db skip` migrates in
place (accounts, characters, and world rows stay). `--db world` replaces the
world database after a dump and leaves accounts and characters. `--db full`
replaces that realm's databases after a dump. Both need `--confirm` and the
realm short name. Nothing polls git on a timer.

`erase` asks you to type the realm name. `erase volume` asks you to type
`wow_wow-mariadb` and is the only command that deletes every realm's players.
A failed dump stops the command before a drop.

Backups stay in the directory you chose until you delete them. The boot unit
starts only the realms named in `./setup.sh boot enable`.

Changing a core on a realm that already has players asks what to do with
them: leave the realm alone, dump and reimport it, or keep accounts and
characters when the new core uses the same database kind.

```bash
./setup.sh core set wotlk TrinityCore-335 --on-data refuse
```

The scripts under `scripts/` and `docker/runtime/` are what `setup.sh` calls.
Use `./setup.sh` unless you are changing one of those scripts.

## When something will not start

- **Restart loop right after boot.** The removable disk was not mounted yet.
  Run `./scripts/host-setup.sh`. The realm container logs `Waiting for` the
  volume, then continues. It should not exit 127.
- **`incomplete client data`.** Run `./scripts/extract-data.sh <short>` and
  wait for `Finished (extract complete ...)`. Continents are `000`, `001`,
  `530`, `571`, and Pandaria `870` when that client has them.
- **Compile cannot clone.** The public URL is in `docker/common/repos.sh`.
  Override it with `GIT_BASE` in `.env` only for a mirror, then run
  `./setup.sh <short>` again.
- **Auth port opens, world does not.** Read `./setup.sh logs <short>`. The
  first world start applies SQL updates and can sit at `health: starting`
  for a long time. `WOW_READY_WAIT` is how long `up` waits.
