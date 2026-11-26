# syntax=docker/dockerfile:1.6
#
# RustyCore — Rust port of the 3.4.3 Wrath Classic core.
# cargo packages bnet-server and world-server are installed as bnetserver and worldserver.
# This tree has no map extractors. Gameplay is still incomplete.
# Installs to: /servers/RustyCore/
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/RustyCore/Dockerfile \
#     -t wow-RustyCore .
#
#   docker build -f docker/RustyCore/Dockerfile -t wow-RustyCore .

ARG UBUNTU_VERSION=24.04

FROM ubuntu:${UBUNTU_VERSION} AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    PATH="/root/.cargo/bin:${PATH}" \
    CARGO_TERM_COLOR=never

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        git \
        libssl-dev \
        pkg-config \
        unzip \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*' \
    && curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs \
        | sh -s -- -y --default-toolchain none --profile minimal \
    && arch="$(uname -m)" \
    && case "$arch" in \
         x86_64) proto_arch=x86_64 ;; \
         aarch64) proto_arch=aarch_64 ;; \
         *) echo "unsupported arch ${arch}" >&2; exit 1 ;; \
       esac \
    && curl -fsSL -o /tmp/protoc.zip \
        "https://github.com/protocolbuffers/protobuf/releases/download/v28.3/protoc-28.3-linux-${proto_arch}.zip" \
    && unzip -q -d /usr/local /tmp/protoc.zip \
    && rm /tmp/protoc.zip \
    && protoc --version | grep -q 'libprotoc 28.3'

ARG GIT_BASE=
ARG CORE_BRANCH=3.4.3
ARG BUILD_TYPE=Release
ARG JOBS=

ENV GIT_BASE=${GIT_BASE} \
    BUILD_TYPE=${BUILD_TYPE} \
    CORE_NAME=RustyCore \
    CORE_KIND=rustycore \
    CORE_BRANCH=${CORE_BRANCH} \
    SERVERS_ROOT=/servers \
    SRC_ROOT=/src \
    BUILD_ROOT=/build

COPY docker/common/build-core.sh /usr/local/bin/build-core.sh
COPY docker/common/repos.sh /usr/local/bin/repos.sh
RUN chmod +x /usr/local/bin/build-core.sh

WORKDIR /build

ARG SOURCE_REV=
RUN --mount=type=cache,target=/root/.cargo/registry \
    --mount=type=cache,target=/root/.cargo/git \
    export JOBS="${JOBS:-$(nproc)}" && \
    echo "SOURCE_REV=${SOURCE_REV}" && /usr/local/bin/build-core.sh

FROM ubuntu:${UBUNTU_VERSION} AS servers

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        libgcc-s1 \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /servers

COPY --from=builder /servers/RustyCore /servers/RustyCore

RUN echo "=== RustyCore installed at /servers/RustyCore ===" && \
    du -sh /servers/RustyCore && \
    ls -la /servers/RustyCore/bin 2>/dev/null || ls -la /servers/RustyCore || true

WORKDIR /servers/RustyCore
CMD ["bash", "-lc", "echo 'Expansion: RustyCore'; echo 'Install path: /servers/RustyCore'; ls -la /servers/RustyCore/bin 2>/dev/null || ls -la /servers/RustyCore"]
