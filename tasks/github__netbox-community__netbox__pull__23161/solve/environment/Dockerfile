FROM ghcr.io/astral-sh/uv:0.11.19 AS uv
FROM ibench-dev:20261011-1

ARG NODE_VERSION=22.23.2
ARG YARN_VERSION=1.22.22
ENV UV_LINK_MODE=copy \
    NODE_OPTIONS=--max-old-space-size=4096 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    CI=true
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential gettext-base libpq-dev \
      libssl-dev nginx openssl pkg-config postgresql-client python3-dev redis-tools xz-utils \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/node /tmp/node-runtime \
    && cd /tmp/node-runtime \
    && node_arch="$(dpkg --print-architecture)" \
    && case "$node_arch" in amd64) node_arch=x64 ;; arm64) ;; *) exit 1 ;; esac \
    && archive="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/${archive}" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" \
    && rg " ${archive}$" SHASUMS256.txt | sha256sum -c - \
    && tar -xJf "$archive" -C /opt/node --strip-components=1 \
    && rm -rf /tmp/node-runtime
ENV PATH=/opt/node/bin:$PATH
RUN npm install --global "yarn@${YARN_VERSION}"
COPY runtime/ /opt/netbox-runtime/
COPY profile.sh /opt/dev-env-profile.sh
WORKDIR /workspace
