#!/usr/bin/env bash
set -euo pipefail
# No-op: the native environment setup already loads the shipped demo account,
# enables the payment modules, and has no order or line with ID 999999.
# This experiment owns no server state and does not change shared defaults.
:
