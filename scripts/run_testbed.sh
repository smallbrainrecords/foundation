#!/usr/bin/env bash
# Run local Django against the smallbrain2 test-bed DB (refresh it first with
# scripts/refresh_testdb.sh).
#
# Binds 127.0.0.1 by default — the DB copy is PHI; don't expose it on the LAN
# unless you're testing a physical device:
#   scripts/run_testbed.sh 0.0.0.0:8000
set -euo pipefail
cd "$(dirname "$0")/.."
ADDR="${1:-127.0.0.1:8000}"
exec .venv312/bin/python manage.py runserver "$ADDR" --settings=project._testbed_settings
