FROM ibench-dev:20261011-1

ARG PNPM_VERSION=12.2.1

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential git-lfs libssl-dev openssl pkg-config sqlite3 xz-utils \
      postgresql-client redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://nodejs.org/dist/v26.4.0/node-v26.4.0-linux-x64.tar.xz -o /tmp/node.tar.xz \
    && echo '5c4286dcd5bbd5acb1ccc7eb0e088bd5eb1e3affad671ee9364004f8f6a4a431  /tmp/node.tar.xz' | sha256sum -c - \
    && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 \
    && rm /tmp/node.tar.xz \
    && npm install --global "pnpm@${PNPM_VERSION}"

WORKDIR /workspace

RUN curl -fsSL https://go.dev/dl/go1.27.1.linux-amd64.tar.gz -o /tmp/go.tar.gz \
    && echo '63d339f0da5ab53635a56f2490a7984dfe12dfcff22ad749f63edaf590168445  /tmp/go.tar.gz' | sha256sum -c - \
    && tar -xzf /tmp/go.tar.gz -C /usr/local \
    && rm /tmp/go.tar.gz \
    && useradd --create-home --shell /bin/bash git

ENV PATH=/usr/local/go/bin:$PATH \
    GOTOOLCHAIN=local \
    GOFLAGS=-mod=readonly \
    GOMAXPROCS=4 \
    GITEA_WORK_DIR=/tmp/gitea-runtime

COPY dev-env-profile.sh /opt/dev-env-profile.sh
RUN chmod +x /opt/dev-env-profile.sh

COPY replay /opt/replay
