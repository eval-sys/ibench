FROM golang:1.25.11-bookworm AS go-toolchain

FROM ibench-dev:20261011-1

ARG PNPM_VERSION=10.33.3

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libssl-dev openssl pkg-config \
      postgresql-client redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "pnpm@${PNPM_VERSION}"

COPY --from=go-toolchain /usr/local/go /usr/local/go
ENV PATH=/usr/local/go/bin:$PATH \
    GOTOOLCHAIN=local \
    GOFLAGS=-mod=vendor \
    GOMAXPROCS=4
COPY dev-env-profile.sh /opt/dev-env-profile.sh
WORKDIR /workspace
