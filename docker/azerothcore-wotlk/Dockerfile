# syntax=docker/dockerfile:1.6
#
# azerothcore-wotlk — Wrath of the Lich King 3.3.5 (AzerothCore)
# Builds the server binaries and map extraction tools.
# Installs to: /servers/azerothcore-wotlk/
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/azerothcore-wotlk/Dockerfile \
#     -t wow-azerothcore-wotlk .
#
#   docker build -f docker/azerothcore-wotlk/Dockerfile -t wow-azerothcore-wotlk .
#
# Copy product to host:
#   docker create --name azerothcore-wotlk-extract wow-azerothcore-wotlk
#   docker cp azerothcore-wotlk-extract:/servers/azerothcore-wotlk ./servers/azerothcore-wotlk
#   docker rm azerothcore-wotlk-extract

ARG UBUNTU_VERSION=24.04

FROM ubuntu:${UBUNTU_VERSION} AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        ccache \
        clang \
        cmake \
        curl \
        g++-14 \
        gcc-14 \
        git \
        libboost-all-dev \
        libbz2-dev \
        libncurses-dev \
        libreadline-dev \
        libssl-dev \
        default-libmysqlclient-dev \
        libmysql++-dev \
        ninja-build \
        pkg-config \
        rsync \
        unzip \
        wget \
        zlib1g-dev \
        liblzma-dev \
        libicu-dev \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*' \
    && git config --global http.sslVerify false

ARG GIT_BASE=
ARG CORE_BRANCH=master
ARG BUILD_TYPE=Release
ARG JOBS=

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=azerothcore-wotlk \
    CORE_KIND=azerothcore \
    CORE_BRANCH=${CORE_BRANCH} \
    SERVERS_ROOT=/servers \
    SRC_ROOT=/src \
    BUILD_ROOT=/build \
    GIT_CONFIG_COUNT=1 \
    GIT_CONFIG_KEY_0=http.sslVerify \
    GIT_CONFIG_VALUE_0=false

COPY docker/common/build-core.sh /usr/local/bin/build-core.sh
COPY docker/common/repos.sh /usr/local/bin/repos.sh
RUN chmod +x /usr/local/bin/build-core.sh

WORKDIR /build

ARG SOURCE_REV=
ARG WOW_MODULES=
COPY docker/runtime/modules.conf /usr/local/share/wow/modules.conf
RUN --mount=type=cache,target=/root/.ccache \
    export JOBS="${JOBS:-$(nproc)}" && \
    echo "SOURCE_REV=${SOURCE_REV}" && /usr/local/bin/build-core.sh

FROM ubuntu:${UBUNTU_VERSION} AS servers

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libboost-filesystem1.83.0 \
        libboost-iostreams1.83.0 \
        libboost-locale1.83.0 \
        libboost-program-options1.83.0 \
        libboost-regex1.83.0 \
        libboost-system1.83.0 \
        libboost-thread1.83.0 \
        libboost-atomic1.83.0 \
        libbz2-1.0 \
        libmysqlclient21 \
        libreadline8t64 \
        libncurses6 \
        libssl3 \
        libicu74 \
        zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /servers

COPY --from=builder /servers/azerothcore-wotlk /servers/azerothcore-wotlk

RUN echo "=== azerothcore-wotlk installed at /servers/azerothcore-wotlk ===" && \
    du -sh /servers/azerothcore-wotlk && \
    ls -la /servers/azerothcore-wotlk/bin 2>/dev/null || ls -la /servers/azerothcore-wotlk || true

WORKDIR /servers/azerothcore-wotlk
CMD ["bash", "-lc", "echo 'Expansion: azerothcore-wotlk'; echo 'Install path: /servers/azerothcore-wotlk'; ls -la /servers/azerothcore-wotlk/bin 2>/dev/null || ls -la /servers/azerothcore-wotlk"]
