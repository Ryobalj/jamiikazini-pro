#!/bin/bash

# Ingia kwenye Ubuntu (ikiwa bado hujaingia kwenye environment ya Ubuntu)
distro login ubuntu

# Ingia kwenye virtual environment ya jamiikazini
cd /
source jamiienv/bin/activate
cd /storage/emulated/0/movies/jamiikazini
clear

# Zifuatazo ni za kuwasha PostgreSQL server yako

su - postgres <<EOF
export PATH=\$PATH:/usr/lib/postgresql/17/bin
pg_ctl -D /home/postgres/postgres_data_17 -l logfile start
EOF


psql
psql -d jamiikazini_db
\q



pg_restore --verbose --clean --no-acl --no-owner   -d "postgresql://lakhshovjamii:jsJ0nnqkGyyEmwJaUm3mMukOml0HxdD2@dpg-cvohhuh5pdvs739uonl0-a.singapore-postgres.render.com:5432/lakhshovjamii_w6cw"   backup_file.dump
psql "postgresql://lakhshovjamii:jsJ0nnqkGyyEmwJaUm3mMukOml0HxdD2@dpg-cvohhuh5pdvs739uonl0-a.singapore-postgres.render.com:5432/lakhshovjamii_w6cw"



django-admin startproject name
django-admin startapp name


python manage.py showmigrations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
