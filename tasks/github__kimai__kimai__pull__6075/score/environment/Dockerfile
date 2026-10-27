FROM ibench-dev:20261011-1

ARG PNPM_VERSION=11.0.0

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3

# The bundled headless shell keeps native input working across Web navigation.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libssl-dev openssl pkg-config \
      postgresql-client redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "pnpm@${PNPM_VERSION}" \
    && chrome_path="$(find /ms-playwright -type f -name chrome-headless-shell | head -n 1)" \
    && test -n "$chrome_path" \
    && ln -sf "$chrome_path" /usr/local/bin/google-chrome-real

WORKDIR /workspace

COPY --from=composer:2.8.12@sha256:5248900ab8b5f7f880c2d62180e40960cd87f60149ec9a1abfd62ac72a02577c /usr/bin/composer /usr/local/bin/composer

RUN apt-get update \
    && apt-get install -y --no-install-recommends software-properties-common \
    && add-apt-repository -y ppa:ondrej/php \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
      apache2 libapache2-mod-php8.3 php8.3-cli php8.3-curl php8.3-intl \
      php8.3-mysql php8.3-gd php8.3-xml php8.3-mbstring php8.3-zip \
      php8.3-bcmath mariadb-client unzip patch gettext \
    && rm -rf /var/lib/apt/lists/* \
    && a2dissite 000-default \
    && a2enmod rewrite \
    && printf 'Listen 8000\n' > /etc/apache2/ports.conf \
    && sed -i 's/variables_order = .*/variables_order = "EGPCS"/' /etc/php/8.3/apache2/php.ini /etc/php/8.3/cli/php.ini \
    && git config --system url."https://github.com/".insteadOf 'ssh://git@github.com/' \
    && git config --system --add url."https://github.com/".insteadOf 'git@github.com:'

COPY apache-site.conf /etc/apache2/sites-available/kimai.conf
RUN a2ensite kimai
COPY dev-env-profile.sh /opt/dev-env-profile.sh
RUN chmod +x /opt/dev-env-profile.sh

COPY replay /opt/replay
