# syntax=docker/dockerfile:1.6
#
# cmangos-tbc — The Burning Crusade 2.4.3 (CMaNGOS)
# Builds the server binaries and map extraction tools.
# Installs to: /servers/cmangos-tbc/
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/cmangos-tbc/Dockerfile \
#     -t wow-cmangos-tbc .
#
#   docker build -f docker/cmangos-tbc/Dockerfile -t wow-cmangos-tbc .
#
# Copy product to host:
#   docker create --name cmangos-tbc-extract wow-cmangos-tbc
#   docker cp cmangos-tbc-extract:/servers/cmangos-tbc ./servers/cmangos-tbc
#   docker rm cmangos-tbc-extract

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
    && git config --global --add safe.directory '*'

ARG GIT_BASE=
ARG CORE_BRANCH=master
ARG BUILD_TYPE=Release
ARG JOBS=

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=cmangos-tbc \
    CORE_KIND=cmangos \
    CORE_BRANCH=${CORE_BRANCH} \
    SERVERS_ROOT=/servers \
    SRC_ROOT=/src \
    BUILD_ROOT=/build

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

COPY --from=builder /servers/cmangos-tbc /servers/cmangos-tbc

RUN echo "=== cmangos-tbc installed at /servers/cmangos-tbc ===" && \
    du -sh /servers/cmangos-tbc && \
    ls -la /servers/cmangos-tbc/bin 2>/dev/null || ls -la /servers/cmangos-tbc || true

WORKDIR /servers/cmangos-tbc
CMD ["bash", "-lc", "echo 'Expansion: cmangos-tbc'; echo 'Install path: /servers/cmangos-tbc'; ls -la /servers/cmangos-tbc/bin 2>/dev/null || ls -la /servers/cmangos-tbc"]
