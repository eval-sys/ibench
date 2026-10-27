#!/usr/bin/env bash
set -euo pipefail

workspace=/workspace/app
mkdir -p /logs/artifacts /opt/data/assets
export JAVA_OPTS="${JAVA_OPTS:-} -Djava.util.logging.manager=org.apache.logging.log4j.jul.LogManager -Dlog4j2.configurationFile=resources/log4j2-devenv.xml -XX:-OmitStackTraceInFastThrow --sun-misc-unsafe-memory-access=allow --enable-native-access=ALL-UNNAMED --enable-preview"

cleanup() {
  jobs -pr | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd "$workspace/backend"
  exec clojure -M -m app.main
) > /logs/artifacts/penpot-backend.log 2>&1 &
backend_pid=$!

(
  cd "$workspace/exporter"
  exec node target/app.js
) > /logs/artifacts/penpot-exporter.log 2>&1 &
exporter_pid=$!

nginx -c /opt/penpot-runtime/nginx.conf -g 'daemon off;' \
  > /logs/artifacts/penpot-nginx.log 2>&1 &
nginx_pid=$!

set +e
wait -n "$backend_pid" "$exporter_pid" "$nginx_pid"
status=$?
set -e
tail -100 /logs/artifacts/penpot-backend.log || true
tail -100 /logs/artifacts/penpot-exporter.log || true
tail -100 /logs/artifacts/penpot-nginx.log || true
exit "$status"
