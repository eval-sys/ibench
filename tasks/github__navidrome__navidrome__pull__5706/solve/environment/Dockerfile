FROM ibench-dev:20261011-1

ARG PNPM_VERSION=10.33.0

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libssl-dev openssl pkg-config \
      postgresql-client redis-tools sqlite3 xz-utils libwebp-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://nodejs.org/dist/v24.13.0/node-v24.13.0-linux-x64.tar.xz -o /tmp/node.tar.xz \
    && echo 'e798599612f4bb71333a3397ab0d095fd62214e115aea45aa858a145fc72d67e  /tmp/node.tar.xz' | sha256sum -c - \
    && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 \
    && rm /tmp/node.tar.xz \
    && npm install --global "pnpm@${PNPM_VERSION}"

WORKDIR /workspace

RUN curl -fsSL https://go.dev/dl/go1.26.7.linux-amd64.tar.gz -o /tmp/go.tar.gz \
    && echo 'ffb5f8de10c62550dfddab66b36b57030721e0a44a3218e9e1181d7b59f121ca  /tmp/go.tar.gz' | sha256sum -c - \
    && tar -xzf /tmp/go.tar.gz -C /usr/local \
    && rm /tmp/go.tar.gz

ENV PATH=/usr/local/go/bin:$PATH \
    GOTOOLCHAIN=local \
    GOFLAGS=-mod=readonly \
    CGO_ENABLED=1 \
    GOMAXPROCS=4 \
    ND_DATAFOLDER=/tmp/navidrome-runtime/data \
    ND_MUSICFOLDER=/tmp/navidrome-runtime/music \
    ND_ADDRESS=0.0.0.0 \
    ND_PORT=4533 \
    ND_ENABLEEXTERNALSERVICES=false \
    ND_ENABLEINSIGHTSCOLLECTOR=false \
    ND_ENABLEGRAVATAR=false \
    ND_DEVAUTOCREATEADMINPASSWORD=admin123

COPY dev-env-profile.sh /opt/dev-env-profile.sh
RUN chmod +x /opt/dev-env-profile.sh
