FROM ibench-dev:20261011-1

ARG PNPM_VERSION=10.33.0

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libssl-dev openssl pkg-config \
      postgresql-client redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "pnpm@${PNPM_VERSION}"

WORKDIR /workspace

# Repository toolchains only; application source stays out of this image.
RUN mkdir -p /opt/grist-node \
    && curl -fsSL https://nodejs.org/dist/v22.12.0/node-v22.12.0-linux-x64.tar.xz | tar -xJ --strip-components=1 -C /opt/grist-node \
    && /opt/harbor-verifier/bin/pip install --no-cache-dir uv==0.9.0 \
    && UV_PYTHON_INSTALL_DIR=/opt/python /opt/harbor-verifier/bin/uv python install 3.11.13 \
    && UV_PYTHON_INSTALL_DIR=/opt/python /opt/harbor-verifier/bin/uv venv --python 3.11.13 --seed /opt/grist-python
ENV PATH=/opt/grist-node/bin:/opt/grist-python/bin:${PATH} \
    npm_config_python=/opt/grist-python/bin/python
RUN npm install --global yarn@1.22.22
COPY profile.sh /opt/dev-env-profile.sh

COPY replay /opt/replay
