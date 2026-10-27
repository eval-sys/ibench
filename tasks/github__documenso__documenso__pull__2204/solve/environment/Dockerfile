FROM node:22.23.2-bookworm-slim AS node
FROM ibench-dev:20261011-1

COPY --from=node /usr/local/ /usr/local/

ARG NPM_VERSION=11.11.0
ARG PNPM_VERSION=10.33.0

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential cmake fontconfig fonts-liberation libssl-dev openssl pkg-config \
      postgresql-client redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "npm@${NPM_VERSION}" "pnpm@${PNPM_VERSION}"

WORKDIR /workspace

COPY dev-env-profile.sh /opt/dev-env-profile.sh
RUN chmod +x /opt/dev-env-profile.sh
