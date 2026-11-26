# syntax=docker/dockerfile:1.6
#
# TrinityCore-Legion-Preservation — Legion Preservation Project branch 7.3.5
# Builds the server binaries and map extraction tools.
# Installs to: /servers/TrinityCore-Legion-Preservation/
#
# Uses Ubuntu 20.04: OpenSSL 1.1.1, Boost 1.71, GCC 9 — matches this era of TC.
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/TrinityCore-Legion-Preservation/Dockerfile \
#     -t wow-trinitycore-legion .
#
# Copy product to host:
#   docker create --name TrinityCore-Legion-Preservation-extract wow-trinitycore-legion
#   docker cp TrinityCore-Legion-Preservation-extract:/servers/TrinityCore-Legion-Preservation ./servers/TrinityCore-Legion-Preservation
#   docker rm TrinityCore-Legion-Preservation-extract

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
        libboost-all-dev \
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
    && git config --global --add safe.directory '*'

ARG GIT_BASE=
ARG CORE_BRANCH=7.3.5
ARG BUILD_TYPE=Release
ARG JOBS=

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=TrinityCore-Legion-Preservation \
    CORE_KIND=trinity \
    CORE_BRANCH=${CORE_BRANCH} \
    SERVERS_ROOT=/servers \
    SRC_ROOT=/src \
    BUILD_ROOT=/build

COPY docker/common/build-core.sh /usr/local/bin/build-core.sh
COPY docker/common/repos.sh /usr/local/bin/repos.sh
RUN chmod +x /usr/local/bin/build-core.sh

WORKDIR /build

# OpenSSL 1.0.2 is built on demand (Legion requires non-opaque EVP_CIPHER_CTX).
ARG SOURCE_REV=
ARG WOW_MODULES=
RUN --mount=type=cache,target=/root/.ccache \
    --mount=type=cache,target=/var/cache/openssl-deps \
    export JOBS="${JOBS:-$(nproc)}" && \
    echo "SOURCE_REV=${SOURCE_REV}" && /usr/local/bin/build-core.sh

FROM ubuntu:${UBUNTU_VERSION} AS servers

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LD_LIBRARY_PATH=/servers/TrinityCore-Legion-Preservation/lib

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libboost-filesystem1.71.0 \
        libboost-iostreams1.71.0 \
        libboost-program-options1.71.0 \
        libboost-regex1.71.0 \
        libboost-system1.71.0 \
        libboost-thread1.71.0 \
        libboost-atomic1.71.0 \
        libbz2-1.0 \
        libmysqlclient21 \
        libreadline8 \
        libncurses6 \
        zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /servers

COPY --from=builder /servers/TrinityCore-Legion-Preservation /servers/TrinityCore-Legion-Preservation

RUN echo "=== TrinityCore-Legion-Preservation installed at /servers/TrinityCore-Legion-Preservation ===" && \
    du -sh /servers/TrinityCore-Legion-Preservation && \
    ls -la /servers/TrinityCore-Legion-Preservation/bin 2>/dev/null || ls -la /servers/TrinityCore-Legion-Preservation || true

WORKDIR /servers/TrinityCore-Legion-Preservation
CMD ["bash", "-lc", "echo 'Expansion: TrinityCore-Legion-Preservation'; echo 'Install path: /servers/TrinityCore-Legion-Preservation'; ls -la /servers/TrinityCore-Legion-Preservation/bin 2>/dev/null || ls -la /servers/TrinityCore-Legion-Preservation"]
