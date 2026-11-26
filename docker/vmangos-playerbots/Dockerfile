# syntax=docker/dockerfile:1.6
#
# vmangos-playerbots — VMaNGOS playerbots branch
# Builds the server binaries and map extraction tools.
# Installs to: /servers/vmangos-playerbots/
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/vmangos-playerbots/Dockerfile \
#     -t wow-vmangos-playerbots .
#
#   docker build -f docker/vmangos-playerbots/Dockerfile -t wow-vmangos-playerbots .
#
# Copy product to host:
#   docker create --name vmangos-playerbots-extract wow-vmangos-playerbots
#   docker cp vmangos-playerbots-extract:/servers/vmangos-playerbots ./servers/vmangos-playerbots
#   docker rm vmangos-playerbots-extract

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
ARG CORE_BRANCH=vmangos-ike3-playerbots
ARG BUILD_TYPE=Release
ARG JOBS=

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=vmangos-playerbots \
    CORE_KIND=vmangos \
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

COPY --from=builder /servers/vmangos-playerbots /servers/vmangos-playerbots

RUN echo "=== vmangos-playerbots installed at /servers/vmangos-playerbots ===" && \
    du -sh /servers/vmangos-playerbots && \
    ls -la /servers/vmangos-playerbots/bin 2>/dev/null || ls -la /servers/vmangos-playerbots || true

WORKDIR /servers/vmangos-playerbots
CMD ["bash", "-lc", "echo 'Expansion: vmangos-playerbots'; echo 'Install path: /servers/vmangos-playerbots'; ls -la /servers/vmangos-playerbots/bin 2>/dev/null || ls -la /servers/vmangos-playerbots"]
