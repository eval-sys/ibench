FROM ibench-dev:20261011-1

ARG NODE_VERSION=20.17.0
ARG YARN_VERSION=4.12.0

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=12288 \
    npm_config_python=/usr/bin/python3 \
    CI=true \
    HUSKY=0 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libssl-dev openssl pkg-config \
      postgresql-client python3-pytest \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/node /tmp/calcom-node \
    && cd /tmp/calcom-node \
    && node_arch="$(dpkg --print-architecture)" \
    && case "$node_arch" in amd64) node_arch=x64 ;; arm64) ;; *) exit 1 ;; esac \
    && archive="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/${archive}" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" \
    && rg " ${archive}$" SHASUMS256.txt | sha256sum -c - \
    && tar -xJf "$archive" -C /opt/node --strip-components=1 \
    && rm -rf /tmp/calcom-node

ENV PATH=/opt/node/bin:$PATH

RUN corepack enable \
    && corepack prepare "yarn@${YARN_VERSION}" --activate

COPY profile.sh /opt/dev-env-profile.sh

WORKDIR /workspace
