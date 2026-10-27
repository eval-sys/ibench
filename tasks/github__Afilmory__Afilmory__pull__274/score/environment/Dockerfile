FROM ibench-dev:20261011-1

ARG PNPM_VERSION=10.33.0

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      make g++ libpq-dev perl libimage-exiftool-perl \
      postgresql-client redis-tools python3-pil python3-pytest \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "pnpm@${PNPM_VERSION}"

COPY fixtures/ /opt/dev-env-fixtures/
RUN python3 /opt/dev-env-fixtures/generate.py /opt/dev-env-fixtures/photos

COPY profile.sh /opt/dev-env-profile.sh

WORKDIR /workspace

COPY replay /opt/replay
