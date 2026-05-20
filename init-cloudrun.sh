#!/usr/bin/env bash
set -euo pipefail

echo "[init-cloudrun] running migrations"
python manage.py migrate --noinput

echo "[init-cloudrun] starting gunicorn"
exec gunicorn project.wsgi:application \
  --bind 0.0.0.0:${PORT:-8080} \
  --workers 2 \
  --threads 2 \
  --access-logfile - \
  --error-logfile -
