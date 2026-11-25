# syntax=docker/dockerfile:1.6
#
# TrinityCore-335 — TrinityCore 3.3.5
# Builds the server binaries and map extraction tools.
# Installs to: /servers/TrinityCore-335/
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/TrinityCore-335/Dockerfile \
#     -t wow-TrinityCore-335 .
#
#   docker build -f docker/TrinityCore-335/Dockerfile -t wow-TrinityCore-335 .
#
# Copy product to host:
#   docker create --name TrinityCore-335-extract wow-TrinityCore-335
#   docker cp TrinityCore-335-extract:/servers/TrinityCore-335 ./servers/TrinityCore-335
#   docker rm TrinityCore-335-extract

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
ARG CORE_BRANCH=3.3.5
ARG BUILD_TYPE=Release
ARG JOBS=

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=TrinityCore-335 \
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

COPY --from=builder /servers/TrinityCore-335 /servers/TrinityCore-335

RUN echo "=== TrinityCore-335 installed at /servers/TrinityCore-335 ===" && \
    du -sh /servers/TrinityCore-335 && \
    ls -la /servers/TrinityCore-335/bin 2>/dev/null || ls -la /servers/TrinityCore-335 || true

WORKDIR /servers/TrinityCore-335
CMD ["bash", "-lc", "echo 'Expansion: TrinityCore-335'; echo 'Install path: /servers/TrinityCore-335'; ls -la /servers/TrinityCore-335/bin 2>/dev/null || ls -la /servers/TrinityCore-335"]
