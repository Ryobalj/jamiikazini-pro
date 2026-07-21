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

echo "==> Ensuring superuser (from DJANGO_SUPERUSER_* env vars, if set)"
python manage.py ensure_superuser || echo "ensure_superuser skipped"

echo "==> Seeding currencies + initial exchange rates (idempotent)"
python manage.py seed_currencies || echo "seed_currencies skipped"

echo "==> Fetching real market exchange rates (ERAPI)"
python manage.py update_exchange_rates --source ERAPI || echo "update_exchange_rates skipped (using seeded rates)"

echo "==> Seeding transport rate cards (idempotent)"
python manage.py seed_transport_rate_cards || echo "seed_transport_rate_cards skipped"

# Presentation demo data (users/businesses/products/etc.) - OFF by default so
# a real production deploy never gets fake accounts seeded in automatically.
# Set SEED_DEMO_DATA=true in Render's env vars to turn it on for a demo/staging
# deploy; flip it back to false (or unset it) before going fully live. To
# permanently remove an already-seeded demo dataset, run this once via Render
# Shell: python manage.py seed_demo_data --clear-only
if [ "$SEED_DEMO_DATA" = "true" ]; then
    echo "==> Seeding demo data (SEED_DEMO_DATA=true)"
    python manage.py seed_demo_data || echo "seed_demo_data skipped"
else
    echo "==> Skipping demo data (SEED_DEMO_DATA not set to true)"
fi

echo "==> Build complete"
