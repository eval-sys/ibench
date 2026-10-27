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

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      apache2 libapache2-mod-php8.3 php8.3-cli php8.3-curl php8.3-mysql \
      php8.3-gd php8.3-xml php8.3-mbstring php8.3-zip php8.3-intl \
      php8.3-soap php8.3-ldap php8.3-bcmath mariadb-client dialog unzip \
    && rm -rf /var/lib/apt/lists/* \
    && a2dissite 000-default \
    && a2enmod rewrite headers \
    && printf 'Listen 8000\n' > /etc/apache2/ports.conf \
    && printf 'memory_limit=512M\nmax_input_vars=5000\ndate.timezone=UTC\nallow_url_fopen=Off\n' > /etc/php/8.3/apache2/conf.d/99-local.ini \
    && cp /etc/php/8.3/apache2/conf.d/99-local.ini /etc/php/8.3/cli/conf.d/99-local.ini
COPY dev-env-profile.sh /opt/dev-env-profile.sh
COPY vendor-lock.py /opt/vendor-lock.py
COPY ready.py /opt/ready.py
RUN chmod +x /opt/dev-env-profile.sh
