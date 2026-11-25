# syntax=docker/dockerfile:1.6
#
# alpha-core — Friends & Family Alpha 0.5.3 (Python)
# Packages the Python server and map extractors (tools/extractors, main.py -e).
# Installs to: /servers/alpha-core/
#
# From the repo root (WoW/):
#   docker build --network=host \
#     -f docker/alpha-core/Dockerfile \
#     -t wow-alpha-core .
#
# Copy product to host:
#   docker create --name alpha-core-extract wow-alpha-core
#   docker cp alpha-core-extract:/servers/alpha-core ./servers/alpha-core
#   docker rm alpha-core-extract

ARG UBUNTU_VERSION=24.04

FROM ubuntu:${UBUNTU_VERSION} AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        python3 \
        python3-pip \
        python3-venv \
        rsync \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*' \
    && git config --global http.sslVerify false

ARG GIT_BASE=
ARG CORE_BRANCH=master

ENV GIT_BASE=${GIT_BASE} \
    CORE_NAME=alpha-core \
    CORE_KIND=alpha \
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
RUN echo "SOURCE_REV=${SOURCE_REV}" && /usr/local/bin/build-core.sh

FROM ubuntu:${UBUNTU_VERSION} AS servers

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        python3 \
        python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /servers

COPY --from=builder /servers/alpha-core /servers/alpha-core

RUN echo "=== alpha-core installed at /servers/alpha-core ===" && \
    du -sh /servers/alpha-core && \
    ls -la /servers/alpha-core | head -30

WORKDIR /servers/alpha-core
CMD ["bash", "-lc", "echo 'Expansion: alpha-core'; echo 'Run: ./run-server.sh  |  Extract: ./run-extractors.sh'"]
