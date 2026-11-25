# syntax=docker/dockerfile:1.6
#
# WodCore-Reforged — Warlords of Draenor (WodCore Reforged)
# Builds the server binaries and map extraction tools.
# Installs to: /servers/WodCore-Reforged/
#
# Uses Ubuntu 20.04 + ACE + OpenSSL 1.0.2:
#   - ARC4 uses non-opaque EVP_CIPHER_CTX (OpenSSL 1.0.x only)
#   - Networking stack is ACE (not Boost.Asio)
#   - Old FindOpenSSL.cmake cannot parse OpenSSL 3
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/WodCore-Reforged/Dockerfile \
#     -t wow-wodcore-reforged .
#
#   docker build -f docker/WodCore-Reforged/Dockerfile -t wow-wodcore-reforged .
#
# Copy product to host:
#   docker create --name WodCore-Reforged-extract wow-wodcore-reforged
#   docker cp WodCore-Reforged-extract:/servers/WodCore-Reforged ./servers/WodCore-Reforged
#   docker rm WodCore-Reforged-extract

ARG UBUNTU_VERSION=20.04

FROM ubuntu:${UBUNTU_VERSION} AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        ccache \
        cmake \
        curl \
        g++ \
        gcc \
        git \
        libace-dev \
        libbz2-dev \
        libncurses-dev \
        libreadline-dev \
        libssl-dev \
        default-libmysqlclient-dev \
        ninja-build \
        patchelf \
        pkg-config \
        python3 \
        rsync \
        unzip \
        wget \
        zlib1g-dev \
        liblzma-dev \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*' \
    && git config --global http.sslVerify false

ARG GIT_BASE=
ARG CORE_BRANCH=reforged
ARG BUILD_TYPE=Release
ARG JOBS=

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=WodCore-Reforged \
    CORE_KIND=trinity \
    CORE_BRANCH=${CORE_BRANCH} \
    SERVERS_ROOT=/servers \
    SRC_ROOT=/src \
    BUILD_ROOT=/build \
    BOOST_ROOT= \
    OPENSSL_ROOT_DIR= \
    GIT_CONFIG_COUNT=1 \
    GIT_CONFIG_KEY_0=http.sslVerify \
    GIT_CONFIG_VALUE_0=false

COPY docker/common/build-core.sh /usr/local/bin/build-core.sh
COPY docker/common/repos.sh /usr/local/bin/repos.sh
RUN chmod +x /usr/local/bin/build-core.sh

WORKDIR /build

# OpenSSL 1.0.2 is built on demand (ARC4 requires non-opaque EVP_CIPHER_CTX).
ARG SOURCE_REV=
RUN --mount=type=cache,target=/root/.ccache \
    --mount=type=cache,target=/var/cache/openssl-deps \
    export JOBS="${JOBS:-$(nproc)}" && \
    unset BOOST_ROOT OPENSSL_ROOT_DIR && \
    echo "SOURCE_REV=${SOURCE_REV}" && /usr/local/bin/build-core.sh

FROM ubuntu:${UBUNTU_VERSION} AS servers

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LD_LIBRARY_PATH=/servers/WodCore-Reforged/lib

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libace-6.4.5 \
        libbz2-1.0 \
        libmysqlclient21 \
        libreadline8 \
        libncurses6 \
        zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /servers

COPY --from=builder /servers/WodCore-Reforged /servers/WodCore-Reforged

RUN echo "=== WodCore-Reforged installed at /servers/WodCore-Reforged ===" && \
    du -sh /servers/WodCore-Reforged && \
    ls -la /servers/WodCore-Reforged/bin 2>/dev/null || ls -la /servers/WodCore-Reforged || true

WORKDIR /servers/WodCore-Reforged
CMD ["bash", "-lc", "echo 'Expansion: WodCore-Reforged'; echo 'Install path: /servers/WodCore-Reforged'; ls -la /servers/WodCore-Reforged/bin 2>/dev/null || ls -la /servers/WodCore-Reforged"]
