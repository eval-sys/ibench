FROM caddy:2.11.4-alpine AS caddy

FROM ibench-dev:20261011-1

ARG NODE_VERSION=22.23.2
ARG PNPM_VERSION=11.10.0

ENV NODE_OPTIONS=--max-old-space-size=6144 \
    npm_config_python=/usr/bin/python3 \
    CI=true \
    HUSKY=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential iproute2 libffi-dev libpq-dev \
      libssl-dev libxml2-dev libxmlsec1-dev libxslt1-dev netcat-openbsd openssl pkg-config \
      postgresql-client python3-dev redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig \
    && python3 -c 'import ssl, sys; assert sys.version_info[:2] == (3, 12), sys.version; print(ssl.OPENSSL_VERSION)' \
    && npm install --global "pnpm@${PNPM_VERSION}"

RUN mkdir -p /opt/node /tmp/plane-node \
    && cd /tmp/plane-node \
    && node_arch="$(dpkg --print-architecture)" \
    && case "$node_arch" in amd64) node_arch=x64 ;; arm64) ;; *) exit 1 ;; esac \
    && archive="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/${archive}" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" \
    && rg " ${archive}$" SHASUMS256.txt | sha256sum -c - \
    && tar -xJf "$archive" -C /opt/node --strip-components=1 \
    && rm -rf /tmp/plane-node

ENV PATH=/opt/node/bin:$PATH \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

RUN node --version \
    && pnpm --version \
    && agent-browser --version

COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

COPY runtime/ /opt/plane-runtime/
RUN chmod +x /opt/plane-runtime/*.sh \
    && caddy validate --config /opt/plane-runtime/Caddyfile

COPY profile.sh /opt/dev-env-profile.sh

WORKDIR /workspace
