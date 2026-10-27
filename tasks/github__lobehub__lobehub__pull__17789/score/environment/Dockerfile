FROM ibench-dev:20261011-1

ARG PNPM_VERSION=10.33.0
ARG BUN_VERSION=1.3.4

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      make g++ postgresql-client python3-pytest redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "pnpm@${PNPM_VERSION}" "bun@${BUN_VERSION}"

COPY profile.sh /opt/dev-env-profile.sh

WORKDIR /workspace

COPY replay /opt/replay
