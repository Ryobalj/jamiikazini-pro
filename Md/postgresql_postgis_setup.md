# Jinsi ya Kusanidi PostGIS + PostgreSQL + Django kwenye Android kupitia Termux

Hii ni muhtasari wa hatua zote tulizopitia hadi kufanikisha PostGIS ifanye kazi vizuri na PostgreSQL ndani ya simu ya Android kwa kutumia Termux, pamoja na Django na dependencies zake.

---

## 1. Kuandaa Mazingira ya Termux

### Sasisha packages

```bash
pkg update && pkg upgrade
```

### Weka packages muhimu

```bash
pkg install python postgresql postgis libgdal clang git
```

---

## 2. Kuanzisha PostgreSQL na PostGIS

```bash
initdb $PREFIX/var/lib/postgresql
pg_ctl -D $PREFIX/var/lib/postgresql start
```

### Tengeneza user na database

```bash
createuser -s root
createdb jamiikazini
```

### Weka PostGIS kwenye database

```bash
psql jamiikazini
```

Kisha ndani ya psql:

```sql
CREATE EXTENSION postgis;
\q
```

---

## 3. Virtual Environment kwa Django

### Weka `virtualenv` na tengeneza mazingira ya kazi

```bash
pip install virtualenv
virtualenv jamiienv
source jamiienv/bin/activate
```

---

## 4. Weka Django na Packages za GIS

```bash
pip install django psycopg2-binary
pip install django-ckeditor
```

---

## 5. Kurekebisha OSError ya GDAL (libgdal.so)

### Tengeneza script ya kurekebisha LD_LIBRARY_PATH

```bash

OSError: /data/data/com.termux/files/usr/lib/libgdal.so: cannot open shared object file: No such file or directory

Ni kwamba Python (au Django) bado inajaribu kuitafuta libgdal.so kwenye path ya Termux badala ya /usr/lib/aarch64-linux-gnu/ ambapo libgdal.so halisi ipo.

Hii inatokea kwa sababu:

Python au Django iliwahi kuseti au kuhifadhi GDAL_LIBRARY_PATH au mazingira ya Termux.

Au environment variable LD_LIBRARY_PATH au GDAL_LIBRARY_PATH bado inaonyesha path ya zamani ya Termux.



---

Hatua za Kutatua:

1. Override path ya GDAL kwa usahihi:

Run amri hizi kabla ya ku-run server au createsuperuser:

export GDAL_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/libgdal.so
export LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH

Unaweza pia kuweka hizo ndani ya faili lako la ~/.jamiienv_export.sh kama:

export GDAL_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/libgdal.so
export LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
export PROJ_LIB=/usr/share/proj

Kisha run:

source ~/.jamiienv_export.sh


---

2. Hakiki kama Django sasa inaweza kupakia GDAL:

python -c "from django.contrib.gis.gdal import GDAL_LIBRARY_PATH; print(GDAL_LIBRARY_PATH)"

Unapaswa kupata output kama:

/usr/lib/aarch64-linux-gnu/libgdal.so


---

3. Sasa jaribu tena:

python manage.py createsuperuser

```


Hifadhi na funga (Ctrl+O, Enter, Ctrl+X)

### Tumia script hiyo kila unapoanza environment

```bash
source ~/.jamiienv_export.sh
```

---

## 6. Kuanzisha Django Project

```bash
git clone <project-url> jamiikazini
cd jamiikazini
```

Au anzisha mpya:

```bash
django-admin startproject jamiikazini
```

---

## 7. Sanidi `DATABASES` kwenye `settings.py`

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'jamiikazini',
        'USER': 'root',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

---

## 8. Tengeneza Superuser

```bash
source jamiienv/bin/activate
source ~/.jamiienv_export.sh
cd ~/jamiikazini
python manage.py createsuperuser
```

---

## 9. Vidokezo vya Ziada

- Ukipata error kama `ModuleNotFoundError`, tumia `pip install <module>` ndani ya environment.
- Kila ukifungua Termux upya, kumbuka kufanya:
  ```bash
  source jamiienv/bin/activate
  source ~/.jamiienv_export.sh
  ```

---

## 10. Hitimisho

Sasa unaweza kutumia Django + PostGIS moja kwa moja kwenye simu yako ya Android kupitia Termux bila kutumia kompyuta. Mfumo huu ni kamili kwa maendeleo ya GIS apps, hasa kwa mazingira ya Afrika Mashariki bila vikwazo vya vifaa vya gharama.