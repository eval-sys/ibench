FROM ibench-dev:20261011-1

ARG NODE_VERSION=24.20.0
ARG PNPM_VERSION=12.3.4
ARG UV_VERSION=0.10.2

ENV CI=true \
    PATH=/root/.local/bin:$PATH \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libffi-dev libgmp-dev \
      libmagic-dev libmpfr-dev libpq-dev libssl-dev pkg-config postgresql-client \
      python3-dev redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global n \
    && n "${NODE_VERSION}" \
    && hash -r \
    && npm install --global "pnpm@${PNPM_VERSION}" \
    && curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh \
    && test "$(node --version)" = "v${NODE_VERSION}" \
    && test "$(pnpm --version)" = "${PNPM_VERSION}" \
    && uv --version

COPY runtime/ /opt/dify-runtime/

COPY profile.sh /opt/dev-env-profile.sh

WORKDIR /workspace
