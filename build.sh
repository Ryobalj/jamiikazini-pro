#!/usr/bin/env bash
# ==========================================================
# Render build script — jamiikazini-pro
# Hutumika na web, worker na beat services (buildCommand: bash build.sh)
# ==========================================================
set -o errexit   # simamisha mara moja kkiwa kuna kosa

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static files (WhiteNoise)"
python manage.py collectstatic --no-input

echo "==> Applying database migrations"
python manage.py migrate --no-input

echo "==> Build complete"
