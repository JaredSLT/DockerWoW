# haproxy.sh — render a TCP config that exposes each realm on stock client ports.
# Sourced by scripts/host-setup.sh. Requires catalog.sh.
# shellcheck shell=bash

haproxy_render() {
  local dest="$1"
  local short octet auth_fe world_fe rest_fe port
  mkdir -p "$(dirname "$dest")"
  {
    cat <<'EOF'
global
    maxconn 4096
    log stdout format raw local0 info

resolvers docker
    nameserver dns 127.0.0.11:53
    resolve_retries 3
    timeout resolve 1s
    timeout retry 1s
    hold valid 10s
    hold nx 10s
    hold other 10s
    hold refused 10s
    hold timeout 10s
    hold obsolete 10s

defaults
    mode tcp
    log global
    option tcplog
    option clitcpka
    timeout connect 5s
    timeout client 24h
    timeout server 24h
    timeout tunnel 24h
EOF
    while IFS= read -r short; do
      catalog_load "$short"
      octet="${CATALOG_LOOPBACK##*.}"
      auth_fe="$(catalog_proxy_port auth "$CATALOG_LOOPBACK")"
      world_fe="$(catalog_proxy_port world "$CATALOG_LOOPBACK")"
      cat <<EOF

# $(catalog_hostname "$short") ${CATALOG_LOOPBACK}
#   auth  :${CATALOG_AUTH_PORT} -> ${short}:${CATALOG_AUTH_PORT}
#   world :${CATALOG_WORLD_PORT} -> ${short}:${CATALOG_WORLD_PORT}
frontend fe_${short}_auth
    bind :${auth_fe}
    default_backend be_${short}_auth

backend be_${short}_auth
    server ${short} ${short}:${CATALOG_AUTH_PORT} check inter 3s fall 3 rise 2 resolvers docker init-addr none

frontend fe_${short}_world
    bind :${world_fe}
    default_backend be_${short}_world

backend be_${short}_world
    server ${short} ${short}:${CATALOG_WORLD_PORT} check inter 3s fall 3 rise 2 resolvers docker init-addr none
EOF
      if [[ "${CATALOG_REST_PORT}" != "0" ]]; then
        rest_fe="$(catalog_proxy_port rest "$CATALOG_LOOPBACK")"
        cat <<EOF
#   rest  :${CATALOG_REST_PORT} -> ${short}:${CATALOG_REST_PORT}
frontend fe_${short}_rest
    bind :${rest_fe}
    default_backend be_${short}_rest

backend be_${short}_rest
    server ${short} ${short}:${CATALOG_REST_PORT} check inter 3s fall 3 rise 2 resolvers docker init-addr none
EOF
      fi
      if [[ "$short" == "alpha" ]]; then
        for port in 9081 9090 9100; do
          cat <<EOF
frontend fe_alpha_${port}
    bind :${port}
    default_backend be_alpha_${port}

backend be_alpha_${port}
    server alpha alpha:${port} check inter 3s fall 3 rise 2 resolvers docker init-addr none
EOF
        done
      fi
    done < <(catalog_shorts)
  } >"$dest"
}
