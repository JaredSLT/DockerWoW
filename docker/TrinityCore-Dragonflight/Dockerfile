# syntax=docker/dockerfile:1.6
#
# TrinityCore-Dragonflight — Dragonflight 10.x (TrinityCore)
# Builds the server binaries and map extraction tools.
# Installs to: /servers/TrinityCore-Dragonflight/
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/TrinityCore-Dragonflight/Dockerfile \
#     -t wow-trinitycore-dragonflight .
#
#   docker build -f docker/TrinityCore-Dragonflight/Dockerfile -t wow-trinitycore-dragonflight .
#
# Copy product to host:
#   docker create --name TrinityCore-Dragonflight-extract wow-trinitycore-dragonflight
#   docker cp TrinityCore-Dragonflight-extract:/servers/TrinityCore-Dragonflight ./servers/TrinityCore-Dragonflight
#   docker rm TrinityCore-Dragonflight-extract

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
ARG CORE_BRANCH=TDB1027.24051
ARG BUILD_TYPE=Release
ARG JOBS=

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=TrinityCore-Dragonflight \
    CORE_KIND=trinity \
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

COPY --from=builder /servers/TrinityCore-Dragonflight /servers/TrinityCore-Dragonflight

RUN echo "=== TrinityCore-Dragonflight installed at /servers/TrinityCore-Dragonflight ===" && \
    du -sh /servers/TrinityCore-Dragonflight && \
    ls -la /servers/TrinityCore-Dragonflight/bin 2>/dev/null || ls -la /servers/TrinityCore-Dragonflight || true

WORKDIR /servers/TrinityCore-Dragonflight
CMD ["bash", "-lc", "echo 'Expansion: TrinityCore-Dragonflight'; echo 'Install path: /servers/TrinityCore-Dragonflight'; ls -la /servers/TrinityCore-Dragonflight/bin 2>/dev/null || ls -la /servers/TrinityCore-Dragonflight"]
