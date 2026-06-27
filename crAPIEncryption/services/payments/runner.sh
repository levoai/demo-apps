#!/bin/sh
set -e
echo "[payments] running migrations..."
python3 manage.py migrate --noinput
echo "[payments] starting server on port ${SERVER_PORT:-8001}..."
exec python3 manage.py runserver 0.0.0.0:${SERVER_PORT:-8001}
