#!/usr/bin/env bash
# Build a single WoW server core with map extraction tools.
# Installs under ${SERVERS_ROOT}/${CORE_NAME}/
#
# Required env:
#   CORE_NAME   - output folder name (e.g. azerothcore-wotlk)
#   CORE_KIND   - trinity | cmangos | azerothcore | skyfire | alpha | vmangos | mangosthree | rustycore
#   CORE_BRANCH - fallback ref; public builds use docker/common/repos.sh
# Optional:
#   GIT_BASE    - mirror prefix. Empty uses the public URL in repos.sh.
#   SOURCE_REV  - cache-bust token from the host (git ls-remote)
set -euo pipefail

CORE_NAME="${CORE_NAME:?CORE_NAME is required}"
CORE_KIND="${CORE_KIND:?CORE_KIND is required}"
CORE_BRANCH="${CORE_BRANCH:?CORE_BRANCH is required}"

_common_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${_common_dir}/repos.sh"

GIT_BASE="${GIT_BASE:-}"
SERVERS_ROOT="${SERVERS_ROOT:-/servers}"
SRC_ROOT="${SRC_ROOT:-/src}"
BUILD_ROOT="${BUILD_ROOT:-/build}"
BUILD_TYPE="${BUILD_TYPE:-Release}"
JOBS="${JOBS:-$(nproc)}"
WOW_MODULES="${WOW_MODULES:-}"

export BOOST_ROOT="${BOOST_ROOT:-/opt/boost}"
export OPENSSL_ROOT_DIR="${OPENSSL_ROOT_DIR:-/opt/openssl}"

mkdir -p "$SERVERS_ROOT" "$SRC_ROOT" "$BUILD_ROOT"

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# AzerothCore parses mysql_get_server_info() with iostream get() (one char
# per dotted field). MariaDB 11.4 becomes [1, 1, .] and is treated as < 8.0.
patch_azerothcore_mysql_version() {
  local f="${1}/src/server/database/Database/DatabaseWorkerPool.cpp"
  [[ -f "$f" ]] || die "AzerothCore DatabaseWorkerPool.cpp missing at $f"
  python3 - "$f" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = """    auto parse = [](std::string const& input)
    {
        std::vector<uint8> result;
        std::istringstream parser(input);
        result.push_back(parser.get());
        for (int i = 1; i < 3; i++)
        {
            // Skip period
            parser.get();
            // Append int from parser to output
            result.push_back(parser.get());
        }
        return result;
    };"""
new = """    auto parse = [](std::string const& input)
    {
        std::vector<uint32> result;
        std::istringstream parser(input);
        for (int i = 0; i < 3; i++)
        {
            uint32 part = 0;
            parser >> part;
            result.push_back(part);
            if (parser.peek() == '.')
                parser.ignore();
        }
        return result;
    };"""
if old not in text:
    sys.exit("AzerothCore MySQL version parser was not found for patching")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("==> patched AzerothCore DatabaseIncompatibleVersion for MariaDB 11")
PY
}

# SkyFire DBCFile::open() requires recordSize == fieldCount*4. 5.4.8
# GameObjectDisplayInfo.dbc is 21-byte records, so vmap4extractor exits.
patch_skyfire_dbc_record_size() {
  local f="${1}/src/tools/vmap4_extractor/dbcfile.cpp"
  [[ -f "$f" ]] || die "SkyFire dbcfile.cpp missing at $f"
  grep -q 'if (_fieldCount \* 4 != _recordSize)' "$f" || die "SkyFire DBC record-size check not found"
  # Keep going when recordSize is not fieldCount*4 (5.4.8 GameObjectDisplayInfo is 21 bytes).
  sed -i '/if (_fieldCount \* 4 != _recordSize)/,+1 s/return false;/printf("DBC recordSize %u fieldCount %u (continuing)\\n", _recordSize, _fieldCount);/' "$f"
  grep -q 'DBC recordSize' "$f" || die "SkyFire DBC record-size patch did not apply"
  log "patched SkyFire DBCFile::open to accept non-aligned records"
  local go="${1}/src/tools/vmap4_extractor/gameobject_extract.cpp"
  [[ -f "$go" ]] || die "SkyFire gameobject_extract.cpp missing at $go"
  sed -i '/Invalid GameObjectDisplayInfo.dbc file format/,+1 s/exit(1);/printf("skipping GO models\\n"); return;/' "$go"
  grep -q 'skipping GO models' "$go" || die "SkyFire GO-model skip patch did not apply"
  log "patched SkyFire vmap4extractor to continue without GameObjectDisplayInfo"
}

# Public URL and ref from repos.sh, unless GIT_BASE names a mirror.
resolve_core_source() {
  local name="$1"
  CORE_REPO=""
  if [[ -n "$GIT_BASE" ]]; then
    CORE_REPO="${GIT_BASE%/}/${name}.git"
    log "Mirror override: ${CORE_REPO} (${CORE_BRANCH})"
    return 0
  fi
  repo_lookup "$name" || die "No public repo for ${name} (set GIT_BASE to use a mirror)"
  CORE_REPO="$REPO_URL"
  CORE_BRANCH="$REPO_REF"
  log "Public source: ${CORE_REPO} (${REPO_KIND} ${CORE_BRANCH})"
}

clone_repo() {
  local name="$1" branch="$2" dest="$3"
  local url="${CORE_REPO:-}"
  [[ -n "$url" ]] || die "CORE_REPO is empty for ${name}"
  if [[ -d "$dest/.git" ]]; then
    log "Updating existing clone: $name ($branch)"
    git -C "$dest" remote set-url origin "$url"
    git -C "$dest" fetch --depth 1 origin "$branch"
    git -C "$dest" checkout -f FETCH_HEAD
  else
    log "Cloning $name ($branch) from ${url}"
    rm -rf "$dest"
    git clone --depth 1 --branch "$branch" "$url" "$dest"
  fi
}

copy_sql() {
  local src="$1" prefix="$2"
  if [[ -d "$src/sql" ]]; then
    rm -rf "${prefix}/sql"
    cp -a "$src/sql" "${prefix}/sql"
  elif [[ -d "$src/data/sql" ]]; then
    rm -rf "${prefix}/sql"
    cp -a "$src/data/sql" "${prefix}/sql"
  fi
}

# TrinityCore-Legion needs OpenSSL 1.0.x (EVP_CIPHER_CTX is opaque in 1.1+).
# Also patches MySQL 8 + Boost.Asio forward-decl issues on Ubuntu 20.04.
ensure_openssl_1_0_2() {
  local prefix="${LEGION_OPENSSL_ROOT:-/opt/openssl-1.0.2}"
  local ver="${OPENSSL_1_0_VERSION:-1.0.2u}"
  local cache_dir="${OPENSSL_DEPS_CACHE:-/var/cache/openssl-deps}"

  if [[ -x "${prefix}/bin/openssl" && -f "${prefix}/include/openssl/ssl.h" ]]; then
    log "OpenSSL 1.0.2 already present at ${prefix}"
    export LEGION_OPENSSL_ROOT="$prefix"
    return 0
  fi

  log "Building OpenSSL ${ver} -> ${prefix}"
  mkdir -p "$cache_dir" /tmp/openssl-build
  local tgz="${cache_dir}/openssl-${ver}.tar.gz"
  if [[ ! -f "$tgz" ]]; then
    wget -q "https://www.openssl.org/source/old/1.0.2/openssl-${ver}.tar.gz" -O "$tgz" \
      || wget -q "https://github.com/openssl/openssl/releases/download/OpenSSL_1_0_2u/openssl-${ver}.tar.gz" -O "$tgz"
  fi
  tar -xzf "$tgz" -C /tmp/openssl-build
  (
    cd "/tmp/openssl-build/openssl-${ver}"
    ./config --prefix="$prefix" --openssldir="${prefix}/ssl" shared zlib -fPIC
    make -j"${JOBS}"
    make install_sw
  )
  rm -rf /tmp/openssl-build
  export LEGION_OPENSSL_ROOT="$prefix"
  log "OpenSSL ${ver} ready at ${prefix}"
}

# Ubuntu 20.04 libmysqlclient21 NEEDs OpenSSL 1.1. Loading that next to
# OpenSSL 1.0.2 (ARC4 / non-opaque EVP_CIPHER_CTX) in one process segfaults.
# Build MariaDB Connector/C without SSL as the MySQL client used at compile
# and runtime so MYSQL_STMT matches the headers.
ensure_mariadb_connector_nossl() {
  local prefix="${MARIADB_CONNECTOR_ROOT:-/opt/mariadb-connector-c}"
  local ver="${MARIADB_CONNECTOR_VERSION:-3.3.11}"
  local cache_dir="${OPENSSL_DEPS_CACHE:-/var/cache/openssl-deps}"
  local lib="${prefix}/lib/libmariadb.so"
  [[ -f "$lib" ]] || lib="${prefix}/lib/mariadb/libmariadb.so"

  if [[ -f "$lib" && -f "${prefix}/include/mysql/mysql.h" ]]; then
    log "MariaDB Connector/C already present at ${prefix}"
    export MARIADB_CONNECTOR_ROOT="$prefix"
    return 0
  fi

  log "Building MariaDB Connector/C ${ver} (WITH_SSL=OFF) -> ${prefix}"
  mkdir -p "$cache_dir" /tmp/mcc-build "$prefix"
  local tgz="${cache_dir}/mariadb-connector-c-${ver}.tar.gz"
  if [[ ! -f "$tgz" ]]; then
    wget -q "https://github.com/mariadb-corporation/mariadb-connector-c/archive/refs/tags/v${ver}.tar.gz" -O "$tgz"
  fi
  rm -rf /tmp/mcc-build/src
  mkdir -p /tmp/mcc-build/src
  tar -xzf "$tgz" -C /tmp/mcc-build/src --strip-components=1
  cmake -S /tmp/mcc-build/src -B /tmp/mcc-build/build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$prefix" \
    -DWITH_SSL=OFF \
    -DWITH_UNIT_TESTS=OFF \
    -DWITH_EXTERNAL_ZLIB=ON \
    -DINSTALL_LIBDIR=lib
  cmake --build /tmp/mcc-build/build -j"${JOBS}"
  cmake --install /tmp/mcc-build/build
  rm -rf /tmp/mcc-build
  export MARIADB_CONNECTOR_ROOT="$prefix"
  log "MariaDB Connector/C ${ver} ready at ${prefix}"
}

patch_trinitycore_legion() {
  local src="$1"
  local prefix="${LEGION_OPENSSL_ROOT:-/opt/openssl-1.0.2}"
  local find_ssl="${src}/cmake/macros/FindOpenSSL.cmake"
  local db_fwd="${src}/src/server/database/Database/DatabaseEnvFwd.h"
  local asio_fwd="${src}/src/common/Asio/AsioHacksFwd.h"
  local object_guid="${src}/src/server/game/Entities/Object/ObjectGuid.h"

  ensure_openssl_1_0_2
  ensure_mariadb_connector_nossl

  log "Forcing FindOpenSSL.cmake to use OpenSSL 1.0.2 at ${prefix}"
  cat >"$find_ssl" <<EOF
# Forced OpenSSL 1.0.2 for TrinityCore-Legion (1.1+ makes EVP_CIPHER_CTX opaque).
set(OPENSSL_ROOT_DIR "${prefix}" CACHE PATH "OpenSSL root" FORCE)
set(OPENSSL_INCLUDE_DIR "${prefix}/include" CACHE PATH "OpenSSL include" FORCE)
set(OPENSSL_SSL_LIBRARIES "${prefix}/lib/libssl.so" CACHE FILEPATH "libssl" FORCE)
set(OPENSSL_CRYPTO_LIBRARIES "${prefix}/lib/libcrypto.so" CACHE FILEPATH "libcrypto" FORCE)
set(OPENSSL_LIBRARIES \${OPENSSL_SSL_LIBRARIES} \${OPENSSL_CRYPTO_LIBRARIES})
set(OPENSSL_VERSION "1.0.2")
set(OPENSSL_FOUND TRUE)
message(STATUS "Found OpenSSL library: \${OPENSSL_LIBRARIES}")
message(STATUS "Found OpenSSL headers: \${OPENSSL_INCLUDE_DIR}")
EOF

  # Keep st_mysql typedefs: MariaDB Connector/C matches the original headers.
  # MySQL 8's struct MYSQL layout is what crashed PreparedResultSet before.

  local dwp="${src}/src/server/database/Database/DatabaseWorkerPool.cpp"
  if [[ -f "$dwp" ]] && grep -q 'mysql_get_client_version() >= MIN_MYSQL_CLIENT_VERSION' "$dwp"; then
    log "Relaxing DatabaseWorkerPool MySQL client version identity checks"
    python3 - "$dwp" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = """    WPFatal(mysql_thread_safe(), "Used MySQL library isn't thread-safe.");
    WPFatal(mysql_get_client_version() >= MIN_MYSQL_CLIENT_VERSION, "TrinityCore does not support MySQL versions below 5.1");
    WPFatal(mysql_get_client_version() == MYSQL_VERSION_ID, "Used MySQL library version (%s) does not match the version used to compile TrinityCore (%s). Search on forum for TCE00011.",
        mysql_get_client_info(), MYSQL_SERVER_VERSION);
"""
new = """    WPFatal(mysql_thread_safe(), "Used MySQL library isn't thread-safe.");
    // MariaDB Connector/C 3.x reports 30311 (< 50100) and a different
    // MYSQL_VERSION_ID than the Ubuntu MySQL 8 package. The process is
    // linked against the connector we built; skip identity checks.
"""
if old not in text:
    sys.exit("Legion DatabaseWorkerPool client-version checks not found for patching")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("DatabaseWorkerPool.cpp patched (client version identity skipped)")
PY
  fi

  if [[ -f "$asio_fwd" ]] && grep -q 'basic_deadline_timer' "$asio_fwd"; then
    log "Patching AsioHacksFwd.h for modern Boost.Asio"
    cat >"$asio_fwd" <<'EOF'
/*
 * Copyright (C) 2008-2018 TrinityCore <https://www.trinitycore.org/>
 *
 * Patched for Boost 1.66+: include complete Asio types rather than
 * incomplete forward declarations (ssl + Metric compatibility).
 */

#ifndef AsioHacksFwd_h__
#define AsioHacksFwd_h__

#include <boost/version.hpp>
#include <boost/asio/deadline_timer.hpp>
#include <boost/asio/ip/tcp.hpp>

namespace boost
{
    namespace asio
    {
        namespace ip
        {
            typedef basic_endpoint<tcp> tcp_endpoint;
#if BOOST_VERSION >= 107000
            typedef basic_resolver<tcp, executor> tcp_resolver;
#elif BOOST_VERSION >= 106600
            typedef basic_resolver<tcp> tcp_resolver;
#else
            typedef basic_resolver<tcp, resolver_service<tcp>> tcp_resolver;
#endif
        }
    }
}

namespace Trinity
{
    namespace Asio
    {
        class Strand;
    }
}

#endif // AsioHacksFwd_h__
EOF
  fi

  if [[ -f "$object_guid" ]] && ! grep -q '#include <string>' "$object_guid"; then
    log "Patching ObjectGuid.h missing standard includes"
    sed -i '/#include <unordered_set>/a #include <string>\n#include <ostream>' "$object_guid"
  fi

  # Boost 1.66+: get_executor().context() returns execution_context&; cast to io_context&.
  local io_ctx="${src}/src/common/Asio/IoContext.h"
  if [[ -f "$io_ctx" ]] && grep -q 'get_executor().context()' "$io_ctx" && ! grep -q 'static_cast<boost::asio::io_context' "$io_ctx"; then
    log "Patching IoContext.h get_io_context for Boost 1.66+"
    sed -i 's/return ioObject.get_executor().context();/return static_cast<boost::asio::io_context\&>(ioObject.get_executor().context());/' "$io_ctx"
  fi

  # Keep my_bool: MariaDB Connector/C still uses it (char). Replacing with
  # bool breaks MYSQL_BIND::is_null assignment.

  local mysql_conn="${src}/src/server/database/Database/MySQLConnection.cpp"
  if [[ -f "$mysql_conn" ]] && grep -q 'CR_INVALID_CONN_HANDLE' "$mysql_conn" \
      && ! grep -q 'define CR_INVALID_CONN_HANDLE' "$mysql_conn"; then
    log "Defining MySQL CR_* codes missing from MariaDB Connector/C"
    python3 - "$mysql_conn" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
needle = '#include <mysqld_error.h>\n'
patch = """#include <mysqld_error.h>
#ifndef CR_INVALID_CONN_HANDLE
#define CR_INVALID_CONN_HANDLE 2048
#endif
#ifndef CR_SERVER_LOST_EXTENDED
#define CR_SERVER_LOST_EXTENDED 2055
#endif
"""
if needle not in text:
    sys.exit("mysqld_error.h include not found in MySQLConnection.cpp")
path.write_text(text.replace(needle, patch, 1), encoding="utf-8")
print("MySQLConnection.cpp patched (CR_* fallbacks)")
PY
  fi

  # connection_patcher: Boost 1.66+ removed io_service alias and resolver::query.
  local cp_helper="${src}/src/tools/connection_patcher/Helper.cpp"
  if [[ -f "$cp_helper" ]] && grep -q 'io_service io_service' "$cp_helper"; then
    log "Patching connection_patcher Helper.cpp for Boost.Asio 1.66+"
    python3 - "$cp_helper" <<'PY'
import sys
from pathlib import Path
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
old = """        void DownloadFile(const std::string& serverName, int port, const std::string& getCommand, std::ostream& out)
        {
            using namespace boost::asio;
            using boost::asio::ip::tcp;

            io_service io_service;

            // Get a list of endpoints corresponding to the server name.
            tcp::resolver resolver(io_service);
            tcp::resolver::query query(serverName, std::to_string(port));
            tcp::resolver::iterator endpoint_iterator = resolver.resolve(query);
            tcp::resolver::iterator end;

            // Try each endpoint until we successfully establish a connection.
            tcp::socket socket(io_service);
            boost::system::error_code error = boost::asio::error::host_not_found;
            while (error && endpoint_iterator != end)
            {
                socket.close();
                socket.connect(*endpoint_iterator++, error);
            }
"""
new = """        void DownloadFile(const std::string& serverName, int port, const std::string& getCommand, std::ostream& out)
        {
            using namespace boost::asio;
            using boost::asio::ip::tcp;

            io_context ioContext;

            // Get a list of endpoints corresponding to the server name.
            tcp::resolver resolver(ioContext);
            auto endpoints = resolver.resolve(serverName, std::to_string(port));

            // Try each endpoint until we successfully establish a connection.
            tcp::socket socket(ioContext);
            boost::system::error_code error = boost::asio::error::host_not_found;
            for (auto const& endpoint : endpoints)
            {
                socket.close();
                socket.connect(endpoint, error);
                if (!error)
                    break;
            }
"""
if old not in text:
    raise SystemExit("connection_patcher Helper.cpp pattern not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Helper.cpp patched")
PY
  fi
}

# WodCore-Reforged (WoD / ACE era): needs OpenSSL 1.0.x (EVP_CIPHER_CTX by value
# in ARC4) and my_bool fixes for MySQL 8 client headers.
patch_wodcore_reforged() {
  local src="$1"
  local prefix="${LEGION_OPENSSL_ROOT:-/opt/openssl-1.0.2}"
  local find_ssl="${src}/cmake/macros/FindOpenSSL.cmake"
  local root_cmake="${src}/CMakeLists.txt"

  ensure_openssl_1_0_2
  ensure_mariadb_connector_nossl

  # Upstream pins cmake_minimum_required(VERSION 3.20.4) after project();
  # Ubuntu 20.04 ships 3.16.x which is enough for this tree.
  if [[ -f "$root_cmake" ]] && grep -q 'cmake_minimum_required(VERSION 3.20' "$root_cmake"; then
    log "Relaxing cmake_minimum_required for Ubuntu 20.04 CMake 3.16"
    sed -i 's/cmake_minimum_required(VERSION 3\.[0-9.]*)/cmake_minimum_required(VERSION 3.16)/' "$root_cmake"
  fi

  log "Forcing FindOpenSSL.cmake to use OpenSSL 1.0.2 at ${prefix}"
  cat >"$find_ssl" <<EOF
# Forced OpenSSL 1.0.2 for WodCore-Reforged (ARC4 uses non-opaque EVP_CIPHER_CTX).
set(OPENSSL_ROOT_DIR "${prefix}" CACHE PATH "OpenSSL root" FORCE)
set(OPENSSL_INCLUDE_DIR "${prefix}/include" CACHE PATH "OpenSSL include" FORCE)
set(OPENSSL_SSL_LIBRARIES "${prefix}/lib/libssl.so" CACHE FILEPATH "libssl" FORCE)
set(OPENSSL_CRYPTO_LIBRARIES "${prefix}/lib/libcrypto.so" CACHE FILEPATH "libcrypto" FORCE)
set(OPENSSL_LIBRARIES \${OPENSSL_SSL_LIBRARIES} \${OPENSSL_CRYPTO_LIBRARIES})
set(OPENSSL_VERSION "1.0.2")
set(OPENSSL_FOUND TRUE)
message(STATUS "Found OpenSSL library: \${OPENSSL_LIBRARIES}")
message(STATUS "Found OpenSSL headers: \${OPENSSL_INCLUDE_DIR}")
EOF

  # Keep my_bool for MariaDB Connector/C (MYSQL_BIND::is_null is my_bool*).

  # MySQL client errmsg.h defines CR_UNUSED_1 etc. which clash with CombatRating
  # enum members in Unit.h when mysql.h is pulled in via Field.h.
  local field_h="${src}/src/server/shared/Database/Field.h"
  if [[ -f "$field_h" ]] && grep -q '#include <mysql.h>' "$field_h" && ! grep -q 'CR_UNUSED_1' "$field_h"; then
    log "Undefining MySQL CR_UNUSED_* macros after mysql.h include (CombatRating clash)"
    python3 - "$field_h" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
needle = "#include <mysql.h>\n"
patch = """#include <mysql.h>

// MySQL client headers define CR_* macros that collide with CombatRating enums.
#ifdef CR_UNUSED_1
#  undef CR_UNUSED_1
#endif
#ifdef CR_UNUSED_2
#  undef CR_UNUSED_2
#endif
#ifdef CR_UNUSED_3
#  undef CR_UNUSED_3
#endif
#ifdef CR_UNUSED_4
#  undef CR_UNUSED_4
#endif
"""
if needle not in text:
    raise SystemExit("mysql.h include not found in Field.h")
path.write_text(text.replace(needle, patch, 1), encoding="utf-8")
print("Field.h patched")
PY
  fi

  # AppenderConsole.cpp checks PLATFORM before including CompilerDefs.h.
  # With both macros undefined, the preprocessor treats "#if PLATFORM == PLATFORM_WINDOWS"
  # as "#if 0 == 0" and incorrectly includes windows.h on Linux.
  local app_console="${src}/src/server/shared/Logging/AppenderConsole.cpp"
  if [[ -f "$app_console" ]] && grep -q '#if PLATFORM == PLATFORM_WINDOWS' "$app_console" \
      && ! grep -q 'CompilerDefs.h' "$app_console"; then
    log "Patching AppenderConsole.cpp to define PLATFORM before windows.h guard"
    python3 - "$app_console" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
old = """#include <sstream>
#if PLATFORM == PLATFORM_WINDOWS
#include <windows.h>
#endif
"""
new = """#include <sstream>
#include "CompilerDefs.h"
#if PLATFORM == PLATFORM_WINDOWS
#include <windows.h>
#endif
"""
if old not in text:
    raise SystemExit("AppenderConsole.cpp pattern not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("AppenderConsole.cpp patched")
PY
  fi

  # Util.cpp provides a broken localtime_r shim: on Linux it redefines the POSIX
  # function and calls itself with wrong pointer levels. Keep the shim on Windows only.
  local util_cpp="${src}/src/server/shared/Utilities/Util.cpp"
  local util_h="${src}/src/server/shared/Utilities/Util.h"
  if [[ -f "$util_cpp" ]] && grep -q 'return localtime_r(&time, &result)' "$util_cpp"; then
    log "Patching Util.cpp localtime_r shim for Linux (use system POSIX)"
    python3 - "$util_cpp" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
old = """struct tm* localtime_r(const time_t* time, struct tm *result)
{
#if (defined(WIN32) || defined(_WIN32) || defined(__WIN32__))
    localtime_s(result, time);
    return result;
#else
    return localtime_r(&time, &result); // POSIX
#endif
}
"""
new = """#if (defined(WIN32) || defined(_WIN32) || defined(__WIN32__))
struct tm* localtime_r(const time_t* time, struct tm *result)
{
    localtime_s(result, time);
    return result;
}
#endif
"""
if old not in text:
    raise SystemExit("Util.cpp localtime_r pattern not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Util.cpp patched")
PY
  fi
  if [[ -f "$util_h" ]] && grep -q 'struct tm\* localtime_r' "$util_h" && ! grep -q 'defined(WIN32)' "$util_h"; then
    log "Guarding localtime_r declaration in Util.h for Windows only"
    python3 - "$util_h" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
old = "struct tm* localtime_r(const time_t* time, struct tm* result);"
new = """#if defined(WIN32) || defined(_WIN32) || defined(__WIN32__)
struct tm* localtime_r(const time_t* time, struct tm* result);
#endif"""
if old not in text:
    raise SystemExit("Util.h localtime_r declaration not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Util.h patched")
PY
  fi

  # GCC 9+ is stricter about transitive includes than older toolchains this tree targeted.
  local warden_key="${src}/src/server/shared/Cryptography/WardenKeyGeneration.h"
  if [[ -f "$warden_key" ]] && ! grep -q '#include <cstring>' "$warden_key"; then
    log "Adding <cstring> to WardenKeyGeneration.h"
    sed -i 's|#include "SHA1.h"|#include "SHA1.h"\n#include <cstring>|' "$warden_key"
  fi

  local wow_time_hpp="${src}/src/server/game/World/WowTime.hpp"
  if [[ -f "$wow_time_hpp" ]] && ! grep -q '#include <ctime>' "$wow_time_hpp"; then
    log "Adding <ctime> to WowTime.hpp"
    sed -i 's|#include "Define.h"|#include "Define.h"\n#include <ctime>|' "$wow_time_hpp"
  fi

  # authserver Main.cpp uses PROCESS_HIGH_PRIORITY on Linux but never defines it
  # (worldserver Master.cpp defines it as -15).
  local auth_main="${src}/src/server/authserver/Main.cpp"
  if [[ -f "$auth_main" ]] && grep -q 'PROCESS_HIGH_PRIORITY' "$auth_main" \
      && ! grep -q '#define PROCESS_HIGH_PRIORITY' "$auth_main"; then
    log "Defining PROCESS_HIGH_PRIORITY in authserver Main.cpp"
    sed -i '/#ifndef _TRINITY_REALM_CONFIG/i#ifndef PROCESS_HIGH_PRIORITY\n#define PROCESS_HIGH_PRIORITY -15 // [-20, 19], default is 0\n#endif' "$auth_main"
  fi

  # Master.cpp incorrectly calls ConfigMgr::GetBoolDefault as a static method on Linux.
  local master_cpp="${src}/src/server/worldserver/Master.cpp"
  if [[ -f "$master_cpp" ]] && grep -q 'ConfigMgr::GetBoolDefault("Console.Enable"' "$master_cpp"; then
    log "Fixing Master.cpp ConfigMgr::GetBoolDefault -> sConfigMgr->"
    sed -i 's/ConfigMgr::GetBoolDefault("Console.Enable"/sConfigMgr->GetBoolDefault("Console.Enable"/g' "$master_cpp"
  fi

  # CliRunnable.cpp: empty if(start) body (commented-out code) leaves a dangling else.
  local cli_cpp="${src}/src/server/worldserver/CommandLine/CliRunnable.cpp"
  if [[ -f "$cli_cpp" ]] && grep -q 'if (start)' "$cli_cpp" && grep -q 'rl_completion_matches' "$cli_cpp"; then
    log "Fixing CliRunnable.cpp empty if(start)/else syntax"
    python3 - "$cli_cpp" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
old = """char** cli_completion(const char* text, int start, int /*end*/)
{
    char** matches;

    if (start)
/*#ifdef PLATFORM != PLATFORM_APPLE
       rl_bind_key('\\t', rl_abort);
#endif*/
    else
        matches = rl_completion_matches((char*)text, &command_finder);
    return matches;
}
"""
new = """char** cli_completion(const char* text, int start, int /*end*/)
{
    char** matches = NULL;

    if (!start)
        matches = rl_completion_matches((char*)text, &command_finder);
    return matches;
}
"""
if old not in text:
    # tolerate minor whitespace differences
    import re
    pat = re.compile(
        r"char\*\* cli_completion\(const char\* text, int start, int /\*end\*/\)\s*\{.*?return matches;\s*\}",
        re.S,
    )
    m = pat.search(text)
    if not m:
        raise SystemExit("CliRunnable.cpp cli_completion pattern not found")
    text = text[: m.start()] + new + text[m.end() :]
else:
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("CliRunnable.cpp patched")
PY
  fi

  # Spell scripts call Cell::Visit / Cell(CellCoord) which are inline in CellImpl.h.
  # With USE_SCRIPTPCH=1, ScriptPCH force-includes CellImpl.h. As a belt-and-suspenders
  # fix when PCH is off or incomplete, inject #include "CellImpl.h" into spell scripts
  # that use GridNotifiers without CellImpl.
  log "Ensuring spell scripts include CellImpl.h for Cell::Visit link defs"
  python3 - "$src" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1]) / "src/server/scripts"
changed = 0
for path in root.rglob("*.cpp"):
    text = path.read_text(encoding="utf-8", errors="replace")
    if "CellImpl.h" in text:
        continue
    # Heuristic: files that pull grid notifiers or construct Cell need the impl header.
    if ("GridNotifiers" not in text and "Cell " not in text and "Cell(" not in text
            and "VisitWorldObjects" not in text and "VisitGridObjects" not in text):
        continue
    # Prefer after the last #include line near the top.
    lines = text.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines[:80]):
        if line.startswith("#include"):
            insert_at = i + 1
    if insert_at == 0:
        continue
    lines.insert(insert_at, '#include "CellImpl.h"\n')
    path.write_text("".join(lines), encoding="utf-8")
    changed += 1
print(f"CellImpl.h injected into {changed} script sources")
PY
}

# Trinity CASC extractors treat a missing local DOWNLOAD manifest as
# FILE_CORRUPT and abort CascOpenStorage. Copied retail trees often have
# ENCODING+idx but omit DOWNLOAD; the comment already says opening should
# continue. Swallow that error so extractors can use local archives.
# BfA 8.3.7 CASC trees often omit ItemSearchName.db2 and GlobalStrings.db2.
# LoadDB2 then fails the whole store load and worldserver exits. Treat those
# two files as optional so the realm can boot; hotfix DB still supplies rows.
patch_trinitycore_bfa_optional_db2() {
  local src="$1"
  local f="${src}/src/server/game/DataStores/DB2Stores.cpp"
  [[ -f "$f" ]] || die "BfA DB2Stores.cpp missing at $f"
  if grep -q 'Skipping optional DB2' "$f"; then
    log "BfA optional DB2 patch already present"
    return 0
  fi
  python3 - "$f" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = """    catch (std::system_error const& e)
    {
        if (e.code() == std::errc::no_such_file_or_directory)
        {
            errlist.push_back(Trinity::StringFormat("File %s does not exist", db2Path + localeNames[defaultLocale] + '/' + storage->GetFileName()));
        }
        else
            throw;
    }
    catch (std::exception const& e)
    {
        errlist.emplace_back(e.what());
        return;
    }

    // load additional data and enUS strings from db
    storage->LoadFromDB();
"""
new = """    catch (std::system_error const& e)
    {
        std::string fn = storage->GetFileName();
        if (e.code() == std::errc::no_such_file_or_directory)
        {
            if (fn == "ItemSearchName.db2" || fn == "GlobalStrings.db2")
            {
                TC_LOG_ERROR("misc", "Skipping optional DB2 %s (not in client CASC)", fn.c_str());
                return;
            }
            errlist.push_back(Trinity::StringFormat("File %s does not exist", db2Path + localeNames[defaultLocale] + '/' + fn));
        }
        else
            throw;
    }
    catch (std::exception const& e)
    {
        std::string fn = storage->GetFileName();
        if (fn == "ItemSearchName.db2" || fn == "GlobalStrings.db2")
        {
            TC_LOG_ERROR("misc", "Skipping optional DB2 %s: %s", fn.c_str(), e.what());
            return;
        }
        errlist.emplace_back(fn + ": " + e.what());
        return;
    }

    // load additional data and enUS strings from db
    storage->LoadFromDB();
"""
if old not in text:
    sys.exit("BfA LoadDB2 missing-file/exception handlers not found for patching")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("DB2Stores.cpp patched (ItemSearchName/GlobalStrings optional)")
PY
  grep -q 'Skipping optional DB2' "$f" || die "BfA optional DB2 patch did not apply"
  log "patched BfA DB2Stores to allow missing ItemSearchName/GlobalStrings"
}

patch_trinitycore_warwithin() {
  local src="$1"
  local f="${src}/dep/CascLib/src/CascOpenStorage.cpp"
  [[ -f "$f" ]] || die "CascOpenStorage.cpp not found at $f"
  if grep -q 'Offline copied CASC trees often omit DOWNLOAD' "$f"; then
    log "War Within CascLib DOWNLOAD-optional patch already present"
    return 0
  fi
  python3 - "$f" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = """    // If the DOWNLOAD manifest is not present, we won't abort the downloading process.
    return dwErrCode;
"""
new = """    // If the DOWNLOAD manifest is not present, we won't abort the opening process.
    // Offline copied CASC trees often omit DOWNLOAD from local idx files.
    if (dwErrCode == ERROR_FILE_NOT_FOUND || dwErrCode == ERROR_FILE_OFFLINE || dwErrCode == ERROR_FILE_CORRUPT)
        dwErrCode = ERROR_SUCCESS;
    return dwErrCode;
"""
if old not in text:
    sys.exit("Could not locate LoadDownloadManifest trailing return for patching")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("CascOpenStorage.cpp patched (DOWNLOAD optional)")
PY
  grep -q 'Offline copied CASC trees often omit DOWNLOAD' "$f" || die "War Within DOWNLOAD patch did not apply"
  log "patched CascLib LoadDownloadManifest to allow missing local DOWNLOAD"
}

# TrinityCore-Dragonflight: Spell::SearchTargets is a template defined only in
# Spell.cpp, but SpellAuras.cpp calls it for WorldObjectListSearcher<...>.
# Without an explicit instantiation the final link of worldserver fails.
# Upstream master already exports these; Dragonflight fork is missing them.
patch_trinitycore_dragonflight() {
  local src="$1"
  local spell_cpp="${src}/src/server/game/Spells/Spell.cpp"
  local marker="template TC_GAME_API void Spell::SearchTargets<Trinity::WorldObjectListSearcher"

  [[ -f "$spell_cpp" ]] || die "Spell.cpp not found at $spell_cpp"
  if grep -qF "$marker" "$spell_cpp"; then
    log "Dragonflight SearchTargets explicit instantiation already present"
    return 0
  fi

  log "Patching Spell.cpp: explicit SearchTargets instantiations (Dragonflight link fix)"
  # Insert after the closing brace of the SearchTargets template definition.
  # Only Spell.cpp is patched — Spell.h cannot reference WorldObjectListSearcher
  # (defined later in GridNotifiers.h).
  python3 - "$spell_cpp" <<'PY'
import sys
path = sys.argv[1]
with open(path, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

needle = """template<class SEARCHER>
void Spell::SearchTargets(SEARCHER& searcher, uint32 containerMask, WorldObject* referer, Position const* pos, float radius)
{
    if (!containerMask)
        return;

    // search world and grid for possible targets
    bool searchInGrid = (containerMask & (GRID_MAP_TYPE_MASK_CREATURE | GRID_MAP_TYPE_MASK_GAMEOBJECT)) != 0;
    bool searchInWorld = (containerMask & (GRID_MAP_TYPE_MASK_CREATURE | GRID_MAP_TYPE_MASK_PLAYER | GRID_MAP_TYPE_MASK_CORPSE)) != 0;
    if (searchInGrid || searchInWorld)
    {
        float x, y;
        x = pos->GetPositionX();
        y = pos->GetPositionY();

        CellCoord p(Trinity::ComputeCellCoord(x, y));
        Cell cell(p);
        cell.SetNoCreate();

        Map* map = referer->GetMap();

        if (searchInWorld)
            Cell::VisitWorldObjects(x, y, map, searcher, radius);

        if (searchInGrid)
            Cell::VisitGridObjects(x, y, map, searcher, radius);
    }
}
"""

inst = """
template TC_GAME_API void Spell::SearchTargets<Trinity::WorldObjectListSearcher<Trinity::WorldObjectSpellAreaTargetCheck>>(Trinity::WorldObjectListSearcher<Trinity::WorldObjectSpellAreaTargetCheck>& searcher, uint32 containerMask, WorldObject* referer, Position const* pos, float radius);
template TC_GAME_API void Spell::SearchTargets<Trinity::UnitListSearcher<Trinity::WorldObjectSpellAreaTargetCheck>>(Trinity::UnitListSearcher<Trinity::WorldObjectSpellAreaTargetCheck>& searcher, uint32 containerMask, WorldObject* referer, Position const* pos, float radius);
"""

if needle not in text:
    sys.exit("Could not locate Spell::SearchTargets body for patching")
text = text.replace(needle, needle + inst, 1)
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("Spell.cpp patched")
PY
}

build_trinity() {
  local src="${SRC_ROOT}/${CORE_NAME}"
  local bdir="${BUILD_ROOT}/${CORE_NAME}"
  local prefix="${SERVERS_ROOT}/${CORE_NAME}"

  clone_repo "$CORE_NAME" "$CORE_BRANCH" "$src"

  local extra_cmake=()
  local scripts_opt=static
  if [[ "$CORE_NAME" == "TrinityCore-Dragonflight" ]]; then
    patch_trinitycore_dragonflight "$src"
    patch_trinitycore_warwithin "$src"
  elif [[ "$CORE_NAME" == "TrinityCore-BFA" ]]; then
    patch_trinitycore_bfa_optional_db2 "$src"
  elif [[ "$CORE_NAME" == "TrinityCore-WarWithin" || "$CORE_NAME" == "TrinityCore" ]]; then
    patch_trinitycore_warwithin "$src"
  elif [[ "$CORE_NAME" == "TrinityCore-Legion" || "$CORE_NAME" == "TrinityCore-Legion-Preservation" ]]; then
    patch_trinitycore_legion "$src"
    local ossl="${LEGION_OPENSSL_ROOT:-/opt/openssl-1.0.2}"
    local mcc="${MARIADB_CONNECTOR_ROOT:-/opt/mariadb-connector-c}"
    local mcc_inc="${mcc}/include/mysql"
    [[ -f "${mcc_inc}/mysql.h" ]] || mcc_inc="${mcc}/include/mariadb"
    local mcc_lib="${mcc}/lib/libmariadb.so"
    [[ -f "$mcc_lib" ]] || mcc_lib="${mcc}/lib/mariadb/libmariadb.so"
    extra_cmake+=(
      "-DOPENSSL_ROOT_DIR=${ossl}"
      "-DOPENSSL_INCLUDE_DIR=${ossl}/include"
      "-DMYSQL_INCLUDE_DIR=${mcc_inc}"
      "-DMYSQL_LIBRARY=${mcc_lib}"
      "-DCMAKE_CXX_FLAGS=-I${ossl}/include -I${mcc_inc}"
      "-DCMAKE_C_FLAGS=-I${ossl}/include -I${mcc_inc}"
      "-DCMAKE_EXE_LINKER_FLAGS=-L${ossl}/lib -L$(dirname "$mcc_lib") -Wl,-rpath,${ossl}/lib -Wl,-rpath,$(dirname "$mcc_lib")"
    )
    export LD_LIBRARY_PATH="${ossl}/lib:$(dirname "$mcc_lib"):${LD_LIBRARY_PATH:-}"
    export PKG_CONFIG_PATH="${ossl}/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
  elif [[ "$CORE_NAME" == "WodCore-Reforged" ]]; then
    # Boolean SCRIPTS option (not static/dynamic/none).
    scripts_opt=1
    patch_wodcore_reforged "$src"
    local ossl="${LEGION_OPENSSL_ROOT:-/opt/openssl-1.0.2}"
    local mcc="${MARIADB_CONNECTOR_ROOT:-/opt/mariadb-connector-c}"
    local mcc_inc="${mcc}/include/mysql"
    [[ -f "${mcc_inc}/mysql.h" ]] || mcc_inc="${mcc}/include/mariadb"
    local mcc_lib="${mcc}/lib/libmariadb.so"
    [[ -f "$mcc_lib" ]] || mcc_lib="${mcc}/lib/mariadb/libmariadb.so"
    extra_cmake+=(
      "-DOPENSSL_ROOT_DIR=${ossl}"
      "-DOPENSSL_INCLUDE_DIR=${ossl}/include"
      "-DMYSQL_INCLUDE_DIR=${mcc_inc}"
      "-DMYSQL_LIBRARY=${mcc_lib}"
      "-DCMAKE_CXX_FLAGS=-I${ossl}/include -I${mcc_inc}"
      "-DCMAKE_C_FLAGS=-I${ossl}/include -I${mcc_inc}"
      "-DCMAKE_EXE_LINKER_FLAGS=-L${ossl}/lib -L$(dirname "$mcc_lib") -Wl,-rpath,${ossl}/lib -Wl,-rpath,$(dirname "$mcc_lib")"
    )
    export LD_LIBRARY_PATH="${ossl}/lib:$(dirname "$mcc_lib"):${LD_LIBRARY_PATH:-}"
    export PKG_CONFIG_PATH="${ossl}/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
  fi

  rm -rf "$bdir"
  mkdir -p "$bdir" "$prefix"

  log "Configuring ${CORE_NAME} (Trinity-like, servers + map tools)"
  local pch_core=1
  local pch_script=1
  if [[ "$CORE_NAME" == "TrinityCore-Legion" || "$CORE_NAME" == "TrinityCore-Legion-Preservation" ]]; then
    # Cotire PCH is fragile with this era of CMake; build without it.
    pch_core=0
    pch_script=0
  elif [[ "$CORE_NAME" == "WodCore-Reforged" ]]; then
    # PCH generation is fragile on this toolchain; CellImpl is injected into scripts.
    pch_core=0
    pch_script=0
  fi

  if [[ "$CORE_NAME" == "TrinityCore-335" && -n "$WOW_MODULES" ]]; then
    trinity_script_flags "$src" extra_cmake
    scripts_opt=none
  fi

  cmake -S "$src" -B "$bdir" -G Ninja \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_INSTALL_PREFIX="$prefix" \
    -DSERVERS=1 \
    -DTOOLS=1 \
    -DSCRIPTS="${scripts_opt}" \
    -DWITH_WARNINGS=0 \
    -DUSE_COREPCH="${pch_core}" \
    -DUSE_SCRIPTPCH="${pch_script}" \
    -DWITHOUT_GIT=0 \
    "${extra_cmake[@]}"

  log "Building ${CORE_NAME} (jobs=$JOBS)"
  cmake --build "$bdir" --config "$BUILD_TYPE" -j"$JOBS"
  log "Installing ${CORE_NAME}"
  cmake --install "$bdir" --config "$BUILD_TYPE"
  copy_sql "$src" "$prefix"

  if [[ "$CORE_NAME" == "TrinityCore-Legion" || "$CORE_NAME" == "TrinityCore-Legion-Preservation" || "$CORE_NAME" == "WodCore-Reforged" ]]; then
    local ossl="${LEGION_OPENSSL_ROOT:-/opt/openssl-1.0.2}"
    mkdir -p "${prefix}/lib"
    cp -a "${ossl}/lib/"libssl.so* "${ossl}/lib/"libcrypto.so* "${prefix}/lib/" 2>/dev/null || true
    local mcc="${MARIADB_CONNECTOR_ROOT:-/opt/mariadb-connector-c}"
    local srcso="" cand
    for cand in \
      "${mcc}/lib/libmariadb.so.3" \
      "${mcc}/lib/mariadb/libmariadb.so.3" \
      "${mcc}/lib/libmariadb.so" \
      "${mcc}/lib/mariadb/libmariadb.so"
    do
      if [[ -f "$cand" ]]; then
        srcso="$cand"
        break
      fi
    done
    [[ -n "$srcso" ]] || die "MariaDB Connector/C libmariadb missing under ${mcc}/lib (needed next to OpenSSL 1.0.2)"
    cp -a "$(dirname "$srcso")"/libmariadb.so* "${prefix}/lib/"
    ln -sfn "$(basename "$srcso")" "${prefix}/lib/libmariadb.so.3" 2>/dev/null || true
    ln -sfn libmariadb.so.3 "${prefix}/lib/libmysqlclient.so.21"
    [[ -f "${prefix}/lib/libmariadb.so.3" ]] || die "failed to install libmariadb.so.3 into ${prefix}/lib"
    log "installed SSL-free MariaDB Connector/C ($(basename "$srcso")) into ${prefix}/lib"
  fi

  log "Done: ${CORE_NAME} -> ${prefix}"
  ls -la "${prefix}/bin" 2>/dev/null || ls -la "$prefix" || true
}

wow_module_list() {
  local IFS=','
  # shellcheck disable=SC2034
  read -ra WOW_MODULE_TOKENS <<<"${WOW_MODULES}" || true
}

module_selected() {
  local want="$1" token name
  wow_module_list
  for token in "${WOW_MODULE_TOKENS[@]:-}"; do
    name="${token%%@*}"
    [[ "$name" == "$want" ]] && return 0
  done
  return 1
}

clone_pinned() {
  local url="$1" sha="$2" dest="$3"
  [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || die "refusing to clone ${url} without a 40-character commit"
  log "Cloning ${url} at ${sha}"
  rm -rf "$dest"
  mkdir -p "$dest"
  git -C "$dest" init -q
  git -C "$dest" remote add origin "$url"
  GIT_TERMINAL_PROMPT=0 git -C "$dest" fetch --depth 1 origin "$sha"
  git -C "$dest" checkout -q --detach FETCH_HEAD
}

module_field() {
  local id="$1" col="$2" file="/usr/local/share/wow/modules.conf"
  [[ -f "$file" ]] || die "modules.conf was not copied into the image"
  awk -F'|' -v key="$id" -v c="$col" '$1==key { print $c; found=1 } END { exit !found }' "$file"
}

install_azeroth_modules() {
  local src="$1" token name url sha
  [[ -n "$WOW_MODULES" ]] || return 0
  wow_module_list
  mkdir -p "${src}/modules"
  for token in "${WOW_MODULE_TOKENS[@]:-}"; do
    [[ -n "$token" ]] || continue
    if [[ "$token" == *@*@* ]]; then
      name="${token%%@*}"
      sha="${token##*@}"
      url="${token#*@}"
      url="${url%@*}"
    else
      name="$token"
      url="$(module_field "$name" 4)"
      sha="$(module_field "$name" 6)"
    fi
    clone_pinned "$url" "$sha" "${src}/modules/${name}"
  done
}

install_cmangos_playerbots() {
  local src="$1" url sha
  module_selected playerbots || return 0
  url="$(module_field playerbots 4)"
  sha="$(module_field playerbots 6)"
  mkdir -p "${src}/src/modules"
  clone_pinned "$url" "$sha" "${src}/src/modules/Bots"
}

copy_playerbots_sql() {
  local src="$1" prefix="$2" era bots dest f
  case "$CORE_NAME" in
    cmangos-classic) era=classic ;;
    cmangos-tbc) era=tbc ;;
    cmangos-wotlk) era=wotlk ;;
    *) die "playerbots SQL is not wired for ${CORE_NAME}" ;;
  esac
  bots="${src}/src/modules/Bots"
  dest="${prefix}/sql/playerbots"
  rm -rf "$dest"
  mkdir -p "${dest}/world" "${dest}/characters"
  if [[ -d "${bots}/sql/characters" ]]; then
    cp -a "${bots}/sql/characters/." "${dest}/characters/"
  fi
  for f in "${bots}/sql/world/"*.sql; do
    [[ -f "$f" ]] || continue
    cp -a "$f" "${dest}/world/"
  done
  if [[ -d "${bots}/sql/world/${era}" ]]; then
    cp -a "${bots}/sql/world/${era}/." "${dest}/world/"
  else
    die "playerbots sql/world/${era} is missing. Other expansion folders were not copied."
  fi
  log "Playerbots SQL for ${era} copied to ${dest}. sql/updates/mangos is not part of this copy."
}

trinity_script_flags() {
  local src="$1"
  local -n _out=$2
  local token name available
  wow_module_list
  available="$(grep -RhoE 'SCRIPT_[A-Za-z0-9_]+' "$src/src/server/scripts" "$src/cmake" 2>/dev/null \
    | sed 's/^SCRIPT_//' | sort -u || true)"
  for token in "${WOW_MODULE_TOKENS[@]:-}"; do
    [[ -n "$token" ]] || continue
    name="${token%%@*}"
    if [[ -n "$available" ]] && ! grep -qx "$name" <<<"$available"; then
      printf '%s\n' "$available" >&2
      die "TrinityCore script module ${name} is not in this 3.3.5 checkout"
    fi
    _out+=("-DSCRIPT_${name}=static")
  done
  if [[ -z "$available" ]]; then
    log "Could not list SCRIPT_* modules in the checkout. Passing the requested names anyway."
  fi
}

build_cmangos() {
  local src="${SRC_ROOT}/${CORE_NAME}"
  local bdir="${BUILD_ROOT}/${CORE_NAME}"
  local prefix="${SERVERS_ROOT}/${CORE_NAME}"
  local playerbots=OFF

  clone_repo "$CORE_NAME" "$CORE_BRANCH" "$src"
  if module_selected playerbots; then
    install_cmangos_playerbots "$src"
    playerbots=ON
  fi
  rm -rf "$bdir"
  mkdir -p "$bdir" "$prefix"

  log "Configuring ${CORE_NAME} (CMaNGOS + extractors, playerbots=${playerbots})"
  cmake -S "$src" -B "$bdir" -G Ninja \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_INSTALL_PREFIX="$prefix" \
    -DBUILD_GAME_SERVER=ON \
    -DBUILD_LOGIN_SERVER=ON \
    -DBUILD_EXTRACTORS=ON \
    -DBUILD_SCRIPTDEV=ON \
    -DBUILD_PLAYERBOTS="${playerbots}" \
    -DPCH=ON \
    -DDEBUG=OFF

  log "Building ${CORE_NAME} (jobs=$JOBS)"
  cmake --build "$bdir" --config "$BUILD_TYPE" -j"$JOBS"
  log "Installing ${CORE_NAME}"
  cmake --install "$bdir" --config "$BUILD_TYPE"
  copy_sql "$src" "$prefix"

  if [[ -d "$src/contrib/extractor_scripts" ]]; then
    mkdir -p "${prefix}/bin/tools"
    cp -a "$src/contrib/extractor_scripts/." "${prefix}/bin/tools/" 2>/dev/null || true
  fi
  if [[ "$playerbots" == "ON" ]]; then
    copy_playerbots_sql "$src" "$prefix"
  fi

  log "Done: ${CORE_NAME} -> ${prefix}"
  ls -la "${prefix}/bin" 2>/dev/null || ls -la "$prefix" || true
}

build_azerothcore() {
  local src="${SRC_ROOT}/${CORE_NAME}"
  local bdir="${BUILD_ROOT}/${CORE_NAME}"
  local prefix="${SERVERS_ROOT}/${CORE_NAME}"

  clone_repo "$CORE_NAME" "$CORE_BRANCH" "$src"
  patch_azerothcore_mysql_version "$src"
  install_azeroth_modules "$src"
  rm -rf "$bdir"
  mkdir -p "$bdir" "$prefix"

  log "Configuring ${CORE_NAME} (AzerothCore apps + map tools)"
  cmake -S "$src" -B "$bdir" -G Ninja \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_INSTALL_PREFIX="$prefix" \
    -DAPPS_BUILD=all \
    -DTOOLS_BUILD=all \
    -DSCRIPTS=static \
    -DMODULES=static \
    -DWITH_WARNINGS=0 \
    -DCMAKE_CXX_COMPILER=clang++ \
    -DCMAKE_C_COMPILER=clang

  log "Building ${CORE_NAME} (jobs=$JOBS)"
  cmake --build "$bdir" --config "$BUILD_TYPE" -j"$JOBS"
  log "Installing ${CORE_NAME}"
  cmake --install "$bdir" --config "$BUILD_TYPE"
  copy_sql "$src" "$prefix"

  log "Done: ${CORE_NAME} -> ${prefix}"
  ls -la "${prefix}/bin" 2>/dev/null || ls -la "$prefix" || true
}

build_vmangos() {
  local src="${SRC_ROOT}/${CORE_NAME}"
  local bdir="${BUILD_ROOT}/${CORE_NAME}"
  local prefix="${SERVERS_ROOT}/${CORE_NAME}"

  clone_repo "$CORE_NAME" "$CORE_BRANCH" "$src"
  rm -rf "$bdir"
  mkdir -p "$bdir" "$prefix"

  log "Configuring ${CORE_NAME} (VMaNGOS, extractors on, mail sender and cpptrace off)"
  cmake -S "$src" -B "$bdir" -G Ninja \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_INSTALL_PREFIX="$prefix" \
    -DBUILD_EXTRACTORS=ON \
    -DUSE_SCRIPTS=ON \
    -DUSE_PCH=ON \
    -DENABLE_MAILSENDER=OFF \
    -DENABLE_CPPTRACE=OFF \
    -DSUPPORTED_CLIENT_BUILD=CLIENT_BUILD_1_12_1 \
    -DBUILD_FOR_HOST_CPU=ON

  log "Building ${CORE_NAME} (jobs=$JOBS)"
  cmake --build "$bdir" --config "$BUILD_TYPE" -j"$JOBS"
  log "Installing ${CORE_NAME}"
  cmake --install "$bdir" --config "$BUILD_TYPE"
  copy_sql "$src" "$prefix"
  log "Done: ${CORE_NAME} -> ${prefix}"
  ls -la "${prefix}/bin" 2>/dev/null || ls -la "$prefix" || true
}

build_mangosthree() {
  local src="${SRC_ROOT}/${CORE_NAME}"
  local bdir="${BUILD_ROOT}/${CORE_NAME}"
  local prefix="${SERVERS_ROOT}/${CORE_NAME}"

  clone_repo "$CORE_NAME" "$CORE_BRANCH" "$src"
  rm -rf "$bdir"
  mkdir -p "$bdir" "$prefix"

  log "Configuring ${CORE_NAME} (MaNGOS Three, tools on, playerbots off)"
  cmake -S "$src" -B "$bdir" -G Ninja \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_INSTALL_PREFIX="$prefix" \
    -DBUILD_MANGOSD=ON \
    -DBUILD_REALMD=ON \
    -DBUILD_TOOLS=ON \
    -DSCRIPT_LIB_ELUNA=ON \
    -DSCRIPT_LIB_SD3=ON \
    -DPLAYERBOTS=OFF \
    -DSOAP=OFF \
    -DPCH=ON \
    -DWITH_TESTS=OFF \
    -DWITH_NET_TESTS=OFF

  log "Building ${CORE_NAME} (jobs=$JOBS)"
  cmake --build "$bdir" --config "$BUILD_TYPE" -j"$JOBS"
  log "Installing ${CORE_NAME}"
  cmake --install "$bdir" --config "$BUILD_TYPE"
  copy_sql "$src" "$prefix"
  log "Done: ${CORE_NAME} -> ${prefix}"
  ls -la "${prefix}/bin" 2>/dev/null || ls -la "$prefix" || true
}

ensure_skyfire_deps() {
  local boost_ver="${BOOST_VERSION:-1.91.0}"
  local openssl_ver="${OPENSSL_VERSION:-4.0.0}"
  local cache_dir="${SKYFIRE_DEPS_CACHE:-/var/cache/skyfire-deps}"
  local boost_u
  boost_u=$(echo "$boost_ver" | tr . _)

  if [[ -d "${BOOST_ROOT}/include" && -x "${OPENSSL_ROOT_DIR}/bin/openssl" ]]; then
    log "SkyFire deps already present"
    return 0
  fi

  log "Building SkyFire deps: Boost ${boost_ver} + OpenSSL ${openssl_ver}"
  mkdir -p "$cache_dir" /tmp/skyfire-deps

  if [[ ! -d "${BOOST_ROOT}/include" ]]; then
    local boost_tgz="${cache_dir}/boost_${boost_u}.tar.gz"
    if [[ ! -f "$boost_tgz" ]]; then
      wget -q "https://archives.boost.io/release/${boost_ver}/source/boost_${boost_u}.tar.gz" -O "$boost_tgz"
    fi
    tar -xzf "$boost_tgz" -C /tmp/skyfire-deps
    (
      cd "/tmp/skyfire-deps/boost_${boost_u}"
      ./bootstrap.sh
      ./b2 install --prefix="${BOOST_ROOT}" --with-headers -j"${JOBS}"
      # --with-headers sometimes skips prefix/include; the tree is still in ./boost.
      if [[ ! -d "${BOOST_ROOT}/include/boost" && -d boost ]]; then
        mkdir -p "${BOOST_ROOT}/include"
        cp -a boost "${BOOST_ROOT}/include/"
      fi
    )
  fi

  if [[ ! -x "${OPENSSL_ROOT_DIR}/bin/openssl" ]]; then
    local ssl_tgz="${cache_dir}/openssl-${openssl_ver}.tar.gz"
    if [[ ! -f "$ssl_tgz" ]]; then
      wget -q "https://github.com/openssl/openssl/releases/download/openssl-${openssl_ver}/openssl-${openssl_ver}.tar.gz" \
        -O "$ssl_tgz"
    fi
    tar -xzf "$ssl_tgz" -C /tmp/skyfire-deps
    (
      cd "/tmp/skyfire-deps/openssl-${openssl_ver}"
      ./Configure linux-x86_64 \
        --prefix="${OPENSSL_ROOT_DIR}" \
        --openssldir="${OPENSSL_ROOT_DIR}/ssl" \
        shared \
        enable-legacy
      make -j"${JOBS}"
      make install_sw install_ssldirs
    )
  fi

  rm -rf /tmp/skyfire-deps
  log "SkyFire deps ready"
}

build_skyfire() {
  local src="${SRC_ROOT}/${CORE_NAME}"
  local bdir="${BUILD_ROOT}/${CORE_NAME}"
  local prefix="${SERVERS_ROOT}/${CORE_NAME}"

  ensure_skyfire_deps
  log "BOOST_ROOT=${BOOST_ROOT} include=$(ls -d ${BOOST_ROOT}/include 2>/dev/null || echo MISSING)"
  log "OPENSSL=${OPENSSL_ROOT_DIR} bin=$(ls ${OPENSSL_ROOT_DIR}/bin/openssl 2>/dev/null || echo MISSING)"
  [[ -d "${BOOST_ROOT}/include" ]] || die "Missing BOOST_ROOT at $BOOST_ROOT"
  [[ -x "${OPENSSL_ROOT_DIR}/bin/openssl" ]] || die "Missing OPENSSL_ROOT_DIR at $OPENSSL_ROOT_DIR"

  clone_repo "$CORE_NAME" "$CORE_BRANCH" "$src"
  patch_skyfire_dbc_record_size "$src"
  rm -rf "$bdir"
  mkdir -p "$bdir" "$prefix"

  export LD_LIBRARY_PATH="${OPENSSL_ROOT_DIR}/lib64:${OPENSSL_ROOT_DIR}/lib:${LD_LIBRARY_PATH:-}"
  export PATH="${OPENSSL_ROOT_DIR}/bin:${PATH}"

  log "Configuring ${CORE_NAME} (SkyFire MoP 5.4.8 + tools)"
  cmake -S "$src" -B "$bdir" -G Ninja \
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_INSTALL_PREFIX="$prefix" \
    -DCMAKE_C_COMPILER=gcc-14 \
    -DCMAKE_CXX_COMPILER=g++-14 \
    -DSERVERS=1 \
    -DTOOLS=1 \
    -DSCRIPTS=1 \
    -DPACKET_LOG_SERVER=0 \
    -DUSE_COREPCH=1 \
    -DUSE_SCRIPTPCH=1 \
    -DSKYFIRE_BUILD_TESTS=OFF \
    -DBOOST_ROOT="$BOOST_ROOT" \
    -DOPENSSL_ROOT_DIR="$OPENSSL_ROOT_DIR"

  log "Building ${CORE_NAME} (jobs=$JOBS)"
  cmake --build "$bdir" --config "$BUILD_TYPE" -j"$JOBS"
  log "Installing ${CORE_NAME}"
  cmake --install "$bdir" --config "$BUILD_TYPE"

  mkdir -p "${prefix}/lib" "${prefix}/lib/ossl-modules"
  cp -a "${OPENSSL_ROOT_DIR}/lib64/"libssl.so* "${OPENSSL_ROOT_DIR}/lib64/"libcrypto.so* "${prefix}/lib/" 2>/dev/null || \
    cp -a "${OPENSSL_ROOT_DIR}/lib/"libssl.so* "${OPENSSL_ROOT_DIR}/lib/"libcrypto.so* "${prefix}/lib/" 2>/dev/null || true
  cp -a "${OPENSSL_ROOT_DIR}/lib64/ossl-modules/"* "${prefix}/lib/ossl-modules/" 2>/dev/null || \
    cp -a "${OPENSSL_ROOT_DIR}/lib/ossl-modules/"* "${prefix}/lib/ossl-modules/" 2>/dev/null || true
  if [[ -d "${OPENSSL_ROOT_DIR}/lib64" ]]; then
    cp -a "${OPENSSL_ROOT_DIR}/lib64/"*.so* "${prefix}/lib/" 2>/dev/null || true
  fi
  if [[ -d "${OPENSSL_ROOT_DIR}/lib" ]]; then
    cp -a "${OPENSSL_ROOT_DIR}/lib/"*.so* "${prefix}/lib/" 2>/dev/null || true
  fi

  copy_sql "$src" "$prefix"
  log "Done: ${CORE_NAME} -> ${prefix}"
  ls -la "${prefix}/bin" 2>/dev/null || ls -la "$prefix" || true
}

build_alpha() {
  local src="${SRC_ROOT}/${CORE_NAME}"
  local prefix="${SERVERS_ROOT}/${CORE_NAME}"

  clone_repo "$CORE_NAME" "$CORE_BRANCH" "$src"
  rm -rf "$prefix"
  mkdir -p "$prefix"

  log "Packaging ${CORE_NAME} (Python + map extractors)"
  rsync -a --exclude='.git' "$src/" "$prefix/"

  python3 -m venv "${prefix}/.venv"
  # shellcheck disable=SC1091
  source "${prefix}/.venv/bin/activate"
  pip install --upgrade pip wheel
  pip install -r "${prefix}/requirements.txt"
  deactivate

  cat > "${prefix}/run-server.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/python main.py "$@"
EOF
  cat > "${prefix}/run-extractors.sh" <<'EOF'
#!/usr/bin/env bash
# Extract .map / .nav from client path configured in etc/config/config.yml
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/python main.py -e "$@"
EOF
  chmod +x "${prefix}/run-server.sh" "${prefix}/run-extractors.sh"

  if [[ -f "${prefix}/etc/config/config.yml.dist" && ! -f "${prefix}/etc/config/config.yml" ]]; then
    cp "${prefix}/etc/config/config.yml.dist" "${prefix}/etc/config/config.yml"
  fi

  log "Done: ${CORE_NAME} -> ${prefix}"
  ls -la "$prefix" | head -30
}

build_rustycore() {
  local src="${SRC_ROOT}/${CORE_NAME}"
  local prefix="${SERVERS_ROOT}/${CORE_NAME}"
  command -v cargo >/dev/null || die "cargo is required to build ${CORE_NAME}"
  command -v protoc >/dev/null || die "protoc 28.3 is required to build ${CORE_NAME}"
  clone_repo "$CORE_NAME" "$CORE_BRANCH" "$src"
  log "Building ${CORE_NAME} (cargo release, jobs=${JOBS})"
  (
    cd "$src"
    PROTOC="$(command -v protoc)" cargo build --locked --release -j"$JOBS" -p bnet-server -p world-server
  )
  mkdir -p "${prefix}/bin"
  # The lab starts bnetserver and worldserver. These packages use hyphenated names.
  cp -a "${src}/target/release/bnet-server" "${prefix}/bin/bnetserver"
  cp -a "${src}/target/release/world-server" "${prefix}/bin/worldserver"
  chmod +x "${prefix}/bin/bnetserver" "${prefix}/bin/worldserver"
  copy_sql "$src" "$prefix"
  log "Done: ${CORE_NAME} -> ${prefix}. This repo has no map extractors."
  ls -la "${prefix}/bin"
}

main() {
  resolve_core_source "$CORE_NAME"
  log "CORE_NAME=${CORE_NAME} CORE_KIND=${CORE_KIND} CORE_BRANCH=${CORE_BRANCH}"
  log "GIT_BASE=${GIT_BASE:-public} SOURCE_REV=${SOURCE_REV:-}"
  log "SERVERS_ROOT=${SERVERS_ROOT} BUILD_TYPE=${BUILD_TYPE} JOBS=${JOBS}"

  case "$CORE_KIND" in
    trinity)     build_trinity ;;
    cmangos)     build_cmangos ;;
    azerothcore) build_azerothcore ;;
    skyfire)     build_skyfire ;;
    alpha)       build_alpha ;;
    vmangos)     build_vmangos ;;
    mangosthree) build_mangosthree ;;
    rustycore)   build_rustycore ;;
    *)           die "Unknown CORE_KIND: $CORE_KIND (expected trinity|cmangos|azerothcore|skyfire|alpha|vmangos|mangosthree|rustycore)" ;;
  esac

  log "Build product: ${SERVERS_ROOT}/${CORE_NAME}"
  du -sh "${SERVERS_ROOT}/${CORE_NAME}" 2>/dev/null || true
}

main "$@"
