#!/usr/bin/env bash
# ==========================================================
# Render build script — jamiikazini-pro
# buildCommand: bash build.sh
# ==========================================================
set -o errexit   # simamisha mara moja ikiwa kuna kosa

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Ensuring PostGIS extension exists"
# GeoDjango inahitaji postgis. Iwashe kiotomatiki (bila hii, migrate hushindwa).
python manage.py shell -c "from django.db import connection; connection.cursor().execute('CREATE EXTENSION IF NOT EXISTS postgis;'); print('PostGIS OK')" || echo "PostGIS step skipped"

echo "==> Collecting static files (WhiteNoise)"
python manage.py collectstatic --no-input

echo "==> Applying database migrations"
python manage.py migrate --no-input

echo "==> Build complete"
