FROM ibench-dev:20261011-1

ARG NODE_VERSION=24.18.0
ARG PNPM_VERSION=11.9.0
ARG CLOJURE_VERSION=1.12.5.1654
ARG JDK_VERSION=26.0.1
ARG RUST_VERSION=1.91.0
ARG RUSTUP_VERSION=1.28.2
ARG EMSCRIPTEN_VERSION=4.0.6

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    JAVA_HOME=/opt/jdk \
    CARGO_HOME=/opt/cargo \
    RUSTUP_HOME=/opt/rustup \
    CI=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      autoconf build-essential cmake \
      netcat-openbsd nginx ninja-build pkg-config postgresql-client \
      redis-tools rsync unzip wget \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/node /tmp/penpot-node \
    && cd /tmp/penpot-node \
    && node_arch="$(dpkg --print-architecture)" \
    && case "$node_arch" in amd64) node_arch=x64 ;; arm64) ;; *) exit 1 ;; esac \
    && archive="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/${archive}" \
    && curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" \
    && rg " ${archive}$" SHASUMS256.txt | sha256sum -c - \
    && tar -xJf "$archive" -C /opt/node --strip-components=1 \
    && rm -rf /tmp/penpot-node

RUN dpkg_arch="$(dpkg --print-architecture)" \
    && case "$dpkg_arch" in \
      amd64) jdk_arch=x64; jdk_sha=7d6663ea8d4298df65de065e32f9f449745ff607d30ba5d13777cb92e9d4613d ;; \
      arm64) jdk_arch=aarch64; jdk_sha=cc1b459dc442d7422b46a3b5fe52acaea54879fa7913e29a05650cef54687f5f ;; \
      *) exit 1 ;; \
    esac \
    && curl -fsSL "https://cdn.azul.com/zulu/bin/zulu26.30.11-ca-jdk${JDK_VERSION}-linux_${jdk_arch}.tar.gz" -o /tmp/jdk.tar.gz \
    && echo "${jdk_sha}  /tmp/jdk.tar.gz" | sha256sum -c - \
    && mkdir -p /opt/jdk \
    && tar -xzf /tmp/jdk.tar.gz -C /opt/jdk --strip-components=1 \
    && rm /tmp/jdk.tar.gz \
    && curl -fsSL "https://download.clojure.org/install/linux-install-${CLOJURE_VERSION}.sh" -o /tmp/clojure.sh \
    && chmod +x /tmp/clojure.sh \
    && /tmp/clojure.sh --prefix /opt/clojure \
    && rm /tmp/clojure.sh

ENV PATH=/opt/jdk/bin:/opt/clojure/bin:/opt/node/bin:/opt/cargo/bin:$PATH

RUN dpkg_arch="$(dpkg --print-architecture)" \
    && case "$dpkg_arch" in \
      amd64) rust_arch=x86_64-unknown-linux-gnu; rustup_sha=20a06e644b0d9bd2fbdbfd52d42540bdde820ea7df86e92e533c073da0cdd43c ;; \
      arm64) rust_arch=aarch64-unknown-linux-gnu; rustup_sha=e3853c5a25252d07cb23a1bdd9377a8c6f3efa01531109281ae47f841c ;; \
      *) exit 1 ;; \
    esac \
    && curl -fsSL "https://static.rust-lang.org/rustup/archive/${RUSTUP_VERSION}/${rust_arch}/rustup-init" -o /tmp/rustup-init \
    && echo "${rustup_sha}  /tmp/rustup-init" | sha256sum -c - \
    && chmod +x /tmp/rustup-init \
    && /tmp/rustup-init -y --no-modify-path --profile minimal --default-toolchain "${RUST_VERSION}" --default-host "${rust_arch}" \
    && rm /tmp/rustup-init \
    && rustup target add wasm32-unknown-emscripten \
    && git clone --branch "${EMSCRIPTEN_VERSION}" --depth 1 https://github.com/emscripten-core/emsdk.git /opt/emsdk \
    && /opt/emsdk/emsdk install "${EMSCRIPTEN_VERSION}" \
    && /opt/emsdk/emsdk activate "${EMSCRIPTEN_VERSION}"

RUN corepack enable \
    && corepack prepare "pnpm@${PNPM_VERSION}" --activate \
    && test "$(node --version)" = "v${NODE_VERSION}" \
    && test "$(pnpm --version)" = "${PNPM_VERSION}" \
    && java -version \
    && clojure --version \
    && rustc --version \
    && agent-browser --version \
    && ffmpeg -version >/dev/null

ENV PLAYWRIGHT_BROWSERS_PATH=/opt/penpot/browsers

COPY runtime/ /opt/penpot-runtime/
RUN chmod +x /opt/penpot-runtime/*.sh

COPY profile.sh /opt/dev-env-profile.sh

WORKDIR /workspace
