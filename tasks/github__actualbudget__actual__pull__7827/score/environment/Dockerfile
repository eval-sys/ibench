FROM ibench-dev:20261011-1

ARG PNPM_VERSION=10.33.0

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libssl-dev openssl pkg-config \
      postgresql-client python3-pytest \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "pnpm@${PNPM_VERSION}"

RUN corepack prepare yarn@4.17.1 --activate

ENV CI=true \
    BROWSER=none \
    ELECTRON_SKIP_BINARY_DOWNLOAD=1 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    HUSKY=0

COPY profile.sh /opt/dev-env-profile.sh

WORKDIR /workspace

COPY replay /opt/replay
