#!/usr/bin/env bash
set -euo pipefail

echo "[init] nginx config test"
nginx -t

echo "[init] start nginx (container-safe)"
nginx -g 'daemon off;' &

# Opt-in collectstatic (default off to protect vendored assets)
if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
  echo "[init] collectstatic"
  python manage.py collectstatic --noinput
else
  echo "[init] skip collectstatic (vendored assets)"
fi

echo "[init] start gunicorn as PID 1"
# Cloud Run sets the PORT env variable, defaulting to 8000 if not set
BIND_PORT="${PORT:-8000}"

exec gunicorn project.wsgi:application \
  --bind 0.0.0.0:$BIND_PORT \
  --workers 8 \
  --threads 4 \
  --access-logfile - \
  --error-logfile -
