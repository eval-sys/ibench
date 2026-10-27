#!/usr/bin/env bash
set -euo pipefail
# The native profile loads the shipped demo. Verify the semantic Given without
# creating or modifying product data.
fixture_check=$(mariadb -h mariadb -u dolibarr -plocal-development dolibarr -N -e "SELECT (SELECT COUNT(*) FROM llx_prelevement_bons WHERE rowid=999999), (SELECT COUNT(*) FROM llx_prelevement_lignes WHERE rowid=999999), (SELECT COUNT(DISTINCT name) FROM llx_const WHERE entity=1 AND name IN ('MAIN_MODULE_PRELEVEMENT','MAIN_MODULE_PAYMENTBYBANKTRANSFER') AND value='1');")
if [[ "$fixture_check" != $'0\t0\t2' ]]; then
  echo 'Prepared demo does not meet the missing-ID/payment-module preconditions.' >&2
  exit 1
fi
