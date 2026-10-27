FROM ibench-dev:20261011-1

ARG PNPM_VERSION=10.33.0

ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    NODE_OPTIONS=--max-old-space-size=8192 \
    npm_config_python=/usr/bin/python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential libssl-dev openssl pkg-config \
      postgresql-client redis-tools unzip libffi-dev \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "pnpm@${PNPM_VERSION}"

WORKDIR /workspace

# Source-independent, versioned tools from the selected upstream baseline.
RUN /opt/harbor-verifier/bin/pip install --no-cache-dir uv==0.9.0 \
    && UV_PYTHON_INSTALL_DIR=/opt/python /opt/harbor-verifier/bin/uv python install 3.10.16 \
    && /opt/python/cpython-3.10.16-linux-x86_64-gnu/bin/python3 -m venv /opt/oppia-python-310 \
    && ln -s /opt/oppia-python-310 /opt/oppia-python \
    && /opt/oppia-python/bin/pip install --no-cache-dir pip==25.3 setuptools==80.9.0 pip-tools==7.5.2

RUN mkdir -p /opt/oppia-tools/google-cloud-sdk-500.0.0 \
    && curl -fsSL https://nodejs.org/dist/v16.13.0/node-v16.13.0-linux-x64.tar.xz | tar -xJ -C /opt/oppia-tools \
    && mv /opt/oppia-tools/node-v16.13.0-linux-x64 /opt/oppia-tools/node-16.13.0 \
    && curl -fsSL https://nodejs.org/dist/v20.11.1/node-v20.11.1-linux-x64.tar.xz | tar -xJ -C /opt/oppia-tools \
    && mv /opt/oppia-tools/node-v20.11.1-linux-x64 /opt/oppia-tools/node-20.11.1 \
    && curl -fsSL https://github.com/yarnpkg/yarn/releases/download/v1.22.15/yarn-v1.22.15.tar.gz | tar -xz -C /opt/oppia-tools \
    && mv /opt/oppia-tools/yarn-v1.22.15 /opt/oppia-tools/yarn-1.22.15 \
    && curl -fsSL https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-500.0.0-linux-x86_64.tar.gz | tar -xz -C /opt/oppia-tools/google-cloud-sdk-500.0.0 \
    && CLOUDSDK_PYTHON=/opt/oppia-python/bin/python /opt/oppia-tools/google-cloud-sdk-500.0.0/google-cloud-sdk/bin/gcloud components install beta cloud-datastore-emulator app-engine-python app-engine-python-extras --quiet

RUN mkdir -p /opt/java \
    && curl -fsSL https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.26%2B4/OpenJDK11U-jdk_x64_linux_hotspot_11.0.26_4.tar.gz | tar -xz --strip-components=1 -C /opt/java

# Later captured checkouts require Python 3.12; keep both exact runtimes.
RUN /opt/harbor-verifier/bin/pip install --no-cache-dir uv==0.11.19 \
    && UV_PYTHON_INSTALL_DIR=/opt/python /opt/harbor-verifier/bin/uv python install 3.12.13 \
    && /opt/python/cpython-3.12.13-linux-x86_64-gnu/bin/python3 -m venv /opt/oppia-python-312 \
    && /opt/oppia-python-312/bin/pip install --no-cache-dir pip==25.3 setuptools==80.9.0 pip-tools==7.5.2
ENV npm_config_python=/opt/oppia-python/bin/python \
    PATH=/opt/oppia-python/bin:/opt/java/bin:${PATH} \
    JAVA_HOME=/opt/java \
    CLOUDSDK_PYTHON=/opt/oppia-python/bin/python \
    CLOUDSDK_CORE_DISABLE_USAGE_REPORTING=true \
    CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=true \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    FIREBASE_CLI_DISABLE_UPDATE_CHECK=true
COPY profile.sh /opt/dev-env-profile.sh
COPY runtime.py /opt/oppia-runtime.py
COPY runtime-tooling-constraints.txt /opt/runtime-tooling-constraints.txt
