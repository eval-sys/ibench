ARG PLAYWRIGHT_IMAGE=mcr.microsoft.com/playwright:v1.62.0-noble
FROM ${PLAYWRIGHT_IMAGE}

ARG IBENCH_DEV_VERSION=20261011-1
ARG AGENT_BROWSER_VERSION=0.38.2
ARG PYTEST_VERSION=8.4.1
ARG PYTEST_JSON_CTRF_VERSION=0.3.5

LABEL org.opencontainers.image.title="ibench-dev" \
    org.opencontainers.image.version="${IBENCH_DEV_VERSION}"

ENV DEBIAN_FRONTEND=noninteractive \
    AGENT_BROWSER_EXECUTABLE_PATH=/usr/local/bin/google-chrome \
    AGENT_BROWSER_ARGS=--no-sandbox

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      bash ca-certificates curl ffmpeg git jq python3 python3-venv ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/harbor-verifier \
    && /opt/harbor-verifier/bin/pip install --no-cache-dir \
      "pytest==${PYTEST_VERSION}" "pytest-json-ctrf==${PYTEST_JSON_CTRF_VERSION}" \
    && mkdir -p /opt/ibench-tools \
    && cp "$(command -v node)" /opt/ibench-tools/node \
    && npm install --global --prefix /opt/ibench-tools "agent-browser@${AGENT_BROWSER_VERSION}" \
    && printf '%s\n' '#!/usr/bin/env bash' \
      'exec /opt/ibench-tools/node /opt/ibench-tools/lib/node_modules/agent-browser/bin/agent-browser.js "$@"' \
      > /usr/local/bin/agent-browser \
    && chmod +x /usr/local/bin/agent-browser \
    && chrome_path="$(find /ms-playwright -type f -name chrome | head -n 1)" \
    && test -n "$chrome_path" \
    && ln -s "$chrome_path" /usr/local/bin/google-chrome-real \
    && printf '%s\n' '#!/usr/bin/env bash' \
      'exec /usr/local/bin/google-chrome-real --blink-settings=primaryPointerType=4,availablePointerTypes=4,primaryHoverType=2,availableHoverTypes=2 "$@"' \
      > /usr/local/bin/google-chrome \
    && chmod +x /usr/local/bin/google-chrome \
    && agent-browser --version \
    && /opt/harbor-verifier/bin/python -c 'import pytest, ctrf'

WORKDIR /workspace
