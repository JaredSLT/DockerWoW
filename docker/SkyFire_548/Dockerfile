# syntax=docker/dockerfile:1.6
#
# SkyFire_548 — Mists of Pandaria 5.4.8 (SkyFire)
# Builds the server binaries and map extraction tools.
# Installs to: /servers/SkyFire_548/
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/SkyFire_548/Dockerfile \
#     -t wow-skyfire-548 .
#
#   docker build -f docker/SkyFire_548/Dockerfile -t wow-skyfire-548 .
#
# Copy product to host:
#   docker create --name SkyFire_548-extract wow-skyfire-548
#   docker cp SkyFire_548-extract:/servers/SkyFire_548 ./servers/SkyFire_548
#   docker rm SkyFire_548-extract

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
        python3 \
        rsync \
        unzip \
        wget \
        zlib1g-dev \
        liblzma-dev \
        libicu-dev \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*'

ARG GIT_BASE=
ARG CORE_BRANCH=main
ARG BUILD_TYPE=Release
ARG JOBS=
ARG BOOST_VERSION=1.91.0
ARG OPENSSL_VERSION=4.0.0

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=SkyFire_548 \
    CORE_KIND=skyfire \
    CORE_BRANCH=${CORE_BRANCH} \
    SERVERS_ROOT=/servers \
    SRC_ROOT=/src \
    BUILD_ROOT=/build \
    BOOST_VERSION=${BOOST_VERSION} \
    OPENSSL_VERSION=${OPENSSL_VERSION} \
    SKYFIRE_DEPS_CACHE=/var/cache/skyfire-deps \
    BOOST_ROOT=/opt/boost \
    OPENSSL_ROOT_DIR=/opt/openssl

COPY docker/common/build-core.sh /usr/local/bin/build-core.sh
COPY docker/common/repos.sh /usr/local/bin/repos.sh
RUN chmod +x /usr/local/bin/build-core.sh

WORKDIR /build

ARG SOURCE_REV=
RUN --mount=type=cache,target=/root/.ccache \
    --mount=type=cache,target=/var/cache/skyfire-deps \
    export JOBS="${JOBS:-$(nproc)}" && \
    echo "SOURCE_REV=${SOURCE_REV}" && /usr/local/bin/build-core.sh

FROM ubuntu:${UBUNTU_VERSION} AS servers

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LD_LIBRARY_PATH=/servers/SkyFire_548/lib

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

COPY --from=builder /servers/SkyFire_548 /servers/SkyFire_548

RUN echo "=== SkyFire_548 installed at /servers/SkyFire_548 ===" && \
    du -sh /servers/SkyFire_548 && \
    ls -la /servers/SkyFire_548/bin 2>/dev/null || ls -la /servers/SkyFire_548 || true

WORKDIR /servers/SkyFire_548
CMD ["bash", "-lc", "echo 'Expansion: SkyFire_548'; echo 'Install path: /servers/SkyFire_548'; ls -la /servers/SkyFire_548/bin 2>/dev/null || ls -la /servers/SkyFire_548"]
