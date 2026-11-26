# syntax=docker/dockerfile:1.6
#
# TrinityCore-BFA — Battle for Azeroth 8.x (TrinityCore)
# Builds the server binaries and map extraction tools.
# Installs to: /servers/TrinityCore-BFA/
#
# Uses Ubuntu 20.04: OpenSSL 1.1.1 (old FindOpenSSL.cmake cannot parse OpenSSL 3).
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/TrinityCore-BFA/Dockerfile \
#     -t wow-trinitycore-bfa .
#
# Copy product to host:
#   docker create --name TrinityCore-BFA-extract wow-trinitycore-bfa
#   docker cp TrinityCore-BFA-extract:/servers/TrinityCore-BFA ./servers/TrinityCore-BFA
#   docker rm TrinityCore-BFA-extract

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
ARG CORE_BRANCH=TDB837.20101
ARG BUILD_TYPE=Release
ARG JOBS=

# Avoid bogus /opt/boost / /opt/openssl from build-core.sh defaults.
ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=TrinityCore-BFA \
    CORE_KIND=trinity \
    CORE_BRANCH=${CORE_BRANCH} \
    SERVERS_ROOT=/servers \
    SRC_ROOT=/src \
    BUILD_ROOT=/build \
    BOOST_ROOT= \
    OPENSSL_ROOT_DIR=

COPY docker/common/build-core.sh /usr/local/bin/build-core.sh
COPY docker/common/repos.sh /usr/local/bin/repos.sh
RUN chmod +x /usr/local/bin/build-core.sh

WORKDIR /build

ARG SOURCE_REV=
RUN --mount=type=cache,target=/root/.ccache \
    export JOBS="${JOBS:-$(nproc)}" && \
    unset BOOST_ROOT OPENSSL_ROOT_DIR && \
    echo "SOURCE_REV=${SOURCE_REV}" && /usr/local/bin/build-core.sh

FROM ubuntu:${UBUNTU_VERSION} AS servers

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

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
        libssl1.1 \
        zlib1g \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /servers

COPY --from=builder /servers/TrinityCore-BFA /servers/TrinityCore-BFA

RUN echo "=== TrinityCore-BFA installed at /servers/TrinityCore-BFA ===" && \
    du -sh /servers/TrinityCore-BFA && \
    ls -la /servers/TrinityCore-BFA/bin 2>/dev/null || ls -la /servers/TrinityCore-BFA || true

WORKDIR /servers/TrinityCore-BFA
CMD ["bash", "-lc", "echo 'Expansion: TrinityCore-BFA'; echo 'Install path: /servers/TrinityCore-BFA'; ls -la /servers/TrinityCore-BFA/bin 2>/dev/null || ls -la /servers/TrinityCore-BFA"]
