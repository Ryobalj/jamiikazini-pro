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

echo "==> Seeding business categories (idempotent)"
python manage.py seed_business_categories || echo "seed_business_categories skipped"

echo "==> Ensuring 'Jamiikazini Elimu' business exists (idempotent, first-run only)"
python manage.py ensure_elimu_business || echo "ensure_elimu_business skipped"

# Muhtasari (TET syllabus) reference data for the syllabus/teaching tools
# (Azimio/Andalio/Ratiba/Matokeo). Each command is idempotent
# (get_or_create/update_or_create), safe to run on every deploy. Order
# matters: syllabus_version/subjects/class_level/subject_version must exist
# before seed_specific_learning_activity resolves its FKs; --force lets it
# auto-create the MainCompetence/SpecificCompetence/LearningActivity tree
# from the names in each syllabus/csv/sla_*.csv file.
echo "==> Seeding syllabus reference data (SyllabusVersion, Subjects, ClassLevels, SubjectVersions)"
python manage.py seed_syllabus_version || echo "seed_syllabus_version skipped"
python manage.py seed_subjects || echo "seed_subjects skipped"
python manage.py seed_class_level || echo "seed_class_level skipped"
python manage.py seed_subject_version || echo "seed_subject_version skipped"

# LessonSentence rows (intro/development/conclusion/reflection phrasing
# used to fill in lesson-plan steps) were never seeded on deploy - without
# them LessonSentence.pick_random() returns None and the lesson plan
# builder crashes with a 500 the moment it tries to read a sentence field
# off it. Idempotent (get_or_create on content), safe on every deploy.
echo "==> Seeding lesson sentence phrasing (LessonSentence)"
python manage.py seed_lesson_sentence || echo "seed_lesson_sentence skipped"

echo "==> Seeding annual calendar (exam-week/term-break reference dates)"
python manage.py seed_annual_calendar || echo "seed_annual_calendar skipped"

# DRS I/II (Msingi Darasa la I na la II) use a combined multi-subject
# muhtasari with its own MainCompetence/SpecificCompetence/LearningActivity
# tree per subject (e.g. "Kuhesabu") but no SpecificLearningActivity
# content yet - those come from a pupils' book later, same as DRS III-VI's
# upgrade path. Seed the tree explicitly since seed_specific_learning_activity
# only auto-creates ancestors when a syllabus/csv/sla_*.csv row exists for them.
echo "==> Seeding standalone MainCompetence/SpecificCompetence/LearningActivity trees"
python manage.py seed_main_competence || echo "seed_main_competence skipped"
python manage.py seed_specific_competence || echo "seed_specific_competence skipped"
python manage.py seed_learning_activity || echo "seed_learning_activity skipped"

echo "==> Seeding muhtasari SpecificLearningActivity content (all syllabus/csv/sla_*.csv files)"
python manage.py seed_specific_learning_activity --force || echo "seed_specific_learning_activity skipped"

# Idempotent (update_or_create keyed on learning_activity+prompt), unlike the
# old seed_lesson_sentence gap above - safe to run on every deploy.
echo "==> Seeding quiz/test/examination question bank (all syllabus/csv/questions_*.csv files)"
python manage.py seed_questions || echo "seed_questions skipped"

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
    python manage.py seed_demo_data --clear-only
fi

echo "==> Build complete"
