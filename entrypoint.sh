#!/usr/bin/env bash
set -e

# ожидание БД
python - <<'PY'
import os, time, socket
host = os.getenv("DB_HOST","db")
port = int(os.getenv("DB_PORT","5432"))
for i in range(60):
    try:
        with socket.create_connection((host, port), timeout=2): break
    except OSError:
        time.sleep(1)
PY

# миграции и статика
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# старт
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${WORKERS:-3} \
  --timeout ${TIMEOUT:-30}
