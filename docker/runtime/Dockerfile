# syntax=docker/dockerfile:1.6
#
# Thin runtime overlay on top of a built wow-<core> image.
# Adds mysql client + python3 so entrypoint can import DBs, write
# configs, and create a login account. Binaries still come from BASE_IMAGE.
#
# launch-servers.sh stages this context (runtime scripts + that realm's site).
#   docker build -f docker/runtime/Dockerfile \
#     --build-arg BASE_IMAGE=wow-cmangos-classic:latest \
#     -t wow-run-vanilla:latest \
#     /tmp/wow-run-build.XXXXXX

ARG BASE_IMAGE=ubuntu:24.04
FROM ${BASE_IMAGE}

USER root
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        mariadb-client \
        python3 \
    && rm -rf /var/lib/apt/lists/*

# Scripts live in the image. A host bind of docker/runtime disappears when the
# removable disk is unmounted, and the container then exits 127 in a loop.
COPY entrypoint.sh healthcheck.sh init-db.sh lib.sh catalog.sh gen-config.py post-setup.py /opt/runtime/
COPY wowweb-site/ /opt/wowweb/
RUN chmod 0755 /opt/runtime/entrypoint.sh /opt/runtime/healthcheck.sh /opt/runtime/init-db.sh

WORKDIR /opt/wow
ENTRYPOINT ["/bin/bash", "/opt/runtime/entrypoint.sh"]
