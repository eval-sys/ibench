#!/usr/bin/env bash
set -euxo pipefail

export CI=true
export NODE_ENV=production
export VERSION=dev-env
export VERSION_TAG=dev-env

(
  cd render-wasm
  EMSDK_QUIET=1 . /opt/emsdk/emsdk_env.sh
  ./build
)

cd frontend
pnpm run build:app:main
mkdir -p resources/public/css
pnpm run build:app:libs
pnpm run build:app:assets
cp /opt/penpot-runtime/config.js resources/public/js/config.js

# Penpot's CSS compiler selects the first "app" path segment. Under the
# canonical /workspace/app checkout, that adds frontend_src_app_ even though
# the ClojureScript macros emit class names relative to src/app.
test -s resources/public/css/main.css
sed -i 's/\.frontend_src_app_/\./g' resources/public/css/main.css
! grep -Fq '.frontend_src_app_' resources/public/css/main.css

test -s resources/public/index.html
if grep -Fq 'css/ui.css' resources/public/index.html; then
  test -s resources/public/css/ui.css
fi
test -s resources/public/js/main.js
test -s resources/public/js/libs.js
test -s resources/public/js/render-wasm.wasm

cd ../exporter
pnpm run build
sed -i 's/%version%/dev-env/g' target/app.js
test -s target/app.js
