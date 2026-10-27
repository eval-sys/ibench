FROM ibench-dev:20261011-1

ARG RUBY_VERSION=3.4.7
ARG RUBY_SHA256=db425a86f6e07546957578f4946cc700a91e7fd51115a86c56e096f30e0530c7
ARG NODE_VERSION=24.13.0
ARG PNPM_VERSION=10.28.0
ARG BUNDLER_VERSION=4.0.11

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    BUNDLE_FROZEN=true \
    BUNDLE_PATH=vendor/bundle \
    BUNDLE_WITHOUT=development:test \
    BUNDLE_JOBS=4 \
    BUNDLE_RETRY=3 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential cargo cmake imagemagick \
      libffi-dev libgdbm-dev libgmp-dev libicu-dev libjemalloc2 libpq-dev libreadline-dev \
      libsqlite3-dev libssl-dev libvips-dev libxml2-dev libxslt1-dev libyaml-dev \
      openssl pkg-config postgresql-client redis-tools rustc xz-utils zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSLo /tmp/ruby.tar.xz "https://cache.ruby-lang.org/pub/ruby/3.4/ruby-${RUBY_VERSION}.tar.xz" \
    && echo "${RUBY_SHA256}  /tmp/ruby.tar.xz" | sha256sum -c - \
    && mkdir /tmp/ruby \
    && tar -xJf /tmp/ruby.tar.xz -C /tmp/ruby --strip-components=1 \
    && cd /tmp/ruby \
    && ./configure --disable-install-doc --enable-shared \
    && make -j4 \
    && make install \
    && cd / \
    && rm -rf /tmp/ruby /tmp/ruby.tar.xz \
    && gem install bundler --no-document --version "${BUNDLER_VERSION}"

RUN mkdir -p /opt/node /tmp/node-runtime \
    && cd /tmp/node-runtime \
    && node_arch="$(dpkg --print-architecture)" \
    && case "$node_arch" in amd64) node_arch=x64 ;; arm64) ;; *) exit 1 ;; esac \
    && archive="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/${archive}" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" \
    && rg " ${archive}$" SHASUMS256.txt | sha256sum -c - \
    && tar -xJf "$archive" -C /opt/node --strip-components=1 \
    && rm -rf /tmp/node-runtime

ENV PATH=/opt/node/bin:$PATH

RUN npm install --global "pnpm@${PNPM_VERSION}"

# Landlock excludes /etc/ld.so.cache; use a default loader directory for ImageMagick libraries.
# The native asset pipeline requires brotli and the ImageMagick 7 magick CLI.
ARG IMAGEMAGICK_VERSION=7.1.2-18
ARG IMAGEMAGICK_SHA256=2db8a1f9bac19831c76574e4fd514ecb80a71a49911ee5dc8c1f3fb6d9d550df
RUN apt-get update \
    && apt-get install -y --no-install-recommends brotli libjpeg-dev libpng-dev libwebp-dev libheif-dev liblcms2-dev libtiff-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSLo /tmp/imagemagick.tar.gz "https://github.com/ImageMagick/ImageMagick/archive/refs/tags/${IMAGEMAGICK_VERSION}.tar.gz" \
    && echo "${IMAGEMAGICK_SHA256}  /tmp/imagemagick.tar.gz" | sha256sum -c - \
    && mkdir /tmp/imagemagick \
    && tar -xzf /tmp/imagemagick.tar.gz -C /tmp/imagemagick --strip-components=1 \
    && cd /tmp/imagemagick \
    && ./configure --libdir=/usr/lib --disable-docs --without-perl --without-x --with-modules \
    && make -j4 \
    && make install \
    && ldconfig \
    && cd / \
    && rm -rf /tmp/imagemagick /tmp/imagemagick.tar.gz

COPY ImageMagick-LICENSE.txt /usr/local/share/licenses/ImageMagick/LICENSE
COPY ImageMagick-NOTICE.txt /usr/local/share/licenses/ImageMagick/NOTICE

COPY profile.sh /opt/dev-env-profile.sh
WORKDIR /workspace
