FROM ibench-dev:20261011-1

ARG NODE_VERSION=22.23.2
ARG PNPM_VERSION=10.33.4

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    CI=true \
    HUSKY=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libssl-dev openssl pkg-config \
      postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/node /tmp/hoppscotch-node \
    && cd /tmp/hoppscotch-node \
    && node_arch="$(dpkg --print-architecture)" \
    && case "$node_arch" in amd64) node_arch=x64 ;; arm64) ;; *) exit 1 ;; esac \
    && archive="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/${archive}" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" \
    && rg " ${archive}$" SHASUMS256.txt | sha256sum -c - \
    && tar -xJf "$archive" -C /opt/node --strip-components=1 \
    && rm -rf /tmp/hoppscotch-node

ENV PATH=/opt/node/bin:$PATH

RUN corepack enable \
    && corepack prepare "pnpm@${PNPM_VERSION}" --activate \
    && test "$(node --version)" = "v${NODE_VERSION}" \
    && test "$(pnpm --version)" = "${PNPM_VERSION}"

COPY fixtures/ /opt/dev-env-fixtures/
COPY runtime/ /opt/dev-env-runtime/

COPY profile.sh /opt/dev-env-profile.sh

RUN chmod +x /opt/dev-env-profile.sh /opt/dev-env-runtime/start.sh

WORKDIR /workspace
