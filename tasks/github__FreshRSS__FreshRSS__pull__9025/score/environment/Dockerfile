FROM node:24@sha256:934240a162082fd8b8a2f90cd5114446443f1eba1c5378f6687167ca405e6584 AS node-runtime

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

COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      apache2 libapache2-mod-php8.3 php8.3-cli php8.3-curl php8.3-gmp php8.3-intl \
      php8.3-mbstring php8.3-xml php8.3-zip php8.3-sqlite3 php8.3-pgsql composer \
    && rm -rf /var/lib/apt/lists/* \
    && a2dissite 000-default \
    && a2enmod deflate expires filter headers mime remoteip setenvif \
    && sed -i '/^[[:space:]]*Listen /d' /etc/apache2/ports.conf
COPY profile.sh /opt/dev-env-profile.sh
RUN chmod +x /opt/dev-env-profile.sh

COPY replay /opt/replay
