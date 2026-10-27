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

COPY --from=composer:2.8.12@sha256:5248900ab8b5f7f880c2d62180e40960cd87f60149ec9a1abfd62ac72a02577c /usr/bin/composer /usr/local/bin/composer
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      apache2 libapache2-mod-php8.3 php8.3-cli php8.3-curl php8.3-gd \
      php8.3-intl php8.3-mbstring php8.3-mysql php8.3-xml php8.3-zip \
      php8.3-bcmath php8.3-ldap mariadb-client unzip \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global yarn@1.22.22 \
    && a2dissite 000-default \
    && a2enmod rewrite \
    && printf 'Listen 8000\n' > /etc/apache2/ports.conf \
    && printf 'ServerName localhost\n' > /etc/apache2/conf-available/server-name.conf \
    && a2enconf server-name
COPY apache-site.conf /etc/apache2/sites-available/limesurvey.conf
RUN a2ensite limesurvey
COPY dev-env-profile.sh /opt/dev-env-profile.sh
RUN chmod +x /opt/dev-env-profile.sh

COPY replay /opt/replay
