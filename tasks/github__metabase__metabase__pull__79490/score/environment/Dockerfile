FROM ibench-dev:20261011-1

ARG BUN_VERSION=1.3.14
ARG CLOJURE_VERSION=1.12.0.1488
ARG UV_VERSION=0.10.2

ENV NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3 \
    PATH=/root/.local/bin:$PATH \
    CI=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential fontconfig gnupg libssl-dev \
      openssl pkg-config postgresql-client python3-pytest wget \
    && wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public \
      | gpg --dearmor -o /etc/apt/trusted.gpg.d/adoptium.gpg \
    && echo "deb https://packages.adoptium.net/artifactory/deb noble main" \
      > /etc/apt/sources.list.d/adoptium.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends temurin-25-jdk \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSLO "https://download.clojure.org/install/linux-install-${CLOJURE_VERSION}.sh" \
    && bash "linux-install-${CLOJURE_VERSION}.sh" \
    && rm "linux-install-${CLOJURE_VERSION}.sh" \
    && curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh \
    && npm install --global "bun@${BUN_VERSION}" \
    && java -version \
    && clojure --version \
    && bun --version \
    && uv --version

COPY profile.sh /opt/dev-env-profile.sh

WORKDIR /workspace

COPY replay /opt/replay
