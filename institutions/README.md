# App: institutions

App ya `institutions` katika mfumo wa *Jamiikazini* inalenga kusimamia taarifa, mipangilio, na watumishi wa taasisi mbalimbali zinazotumia mfumo huu kupitia subdomain zao binafsi. App hii ndio msingi wa mpangilio wa data kwa kila taasisi, ikiwezesha utenganishaji wa taarifa kati ya taasisi kwa usalama na urahisi wa matumizi.

---

## Malengo ya App

- Kusimamia taarifa za taasisi zinazotumia mfumo
- Kuwezesha utawala wa ndani wa kila taasisi kupitia `institution_admin`
- Kuhakikisha data ya kila taasisi inatenganishwa kupitia subdomains
- Kurahisisha usimamizi wa watumishi wa taasisi (staff) na majukumu yao
- Kuweka msingi wa isolation ya huduma kama biashara, vyuo, shule, nk

---

## Mahitaji Muhimu ya Kiufundi

### Muundo wa Data

- Modeli ya `InstitutionType`: Kuhifadhi aina ya taasisi (shule, chuo, duka, huduma nk)
- Modeli ya `Institution`: Kuhifadhi jina, slug, maelezo, anwani, subdomain, na lugha chaguo
- Modeli ya `StaffProfile`: Kuhusiana na `User`, inahifadhi nafasi yake na taarifa nyingine ndani ya taasisi

### Usimamizi wa Taasisi

- Institution admins hupewa jukumu la kusimamia taasisi yao kupitia role yao
- Subdomain-based isolation: kila taasisi ina subdomain yake (`institution.slug.jamiikazini.com`)
- Taarifa na shughuli zote za taasisi hufanyika ndani ya subdomain yake

### Ruhusa (Access Control)

- Decorator `@user_is_in_institution` kudhibiti uhalali wa user kufikia taasisi
- Staff wanapata uwezo wa kuona au kurekebisha kulingana na nafasi yao
- Only institution_admins wanaweza kuongeza au kuondoa staff

### Uthibitishaji wa Data

- Subdomain middleware (InstitutionMiddleware) hutambua taasisi ya mtumiaji
- Wanapofanya login kupitia subdomain, user hubanwa kwenye taasisi hiyo

### Usimamizi wa Lugha

- Kila taasisi inaweza kuweka lugha yake ya default (`language`)
- Lugha hutumika katika mawasiliano ya system (i18n)

---

## Milestones na Checklist ya Utekelezaji

### Milestone 1: Msingi wa Modeli  
- [x] Tengeneza models za `InstitutionType`, `Institution`, `StaffProfile`  
- [x] Ongeza admin interfaces za models hizi  
- [x] Weka relationships kati ya `User`, `Institution`, na `StaffProfile`  

### Milestone 2: API na Serializers  
- [x] Tengeneza serializers za Institution na StaffProfile  
- [x] Tengeneza views na routers kwa taasisi na staff  
- [x] Ongeza permission classes na decorators kulingana na roles  
- [x] Hakikisha data inatoka tu kwa taasisi ya mtumiaji  

### Milestone 3: Middleware ya Subdomain Isolation  
- [x] Tengeneza `InstitutionMiddleware` kwa kutambua taasisi kwa subdomain  
- [x] Ongeza context processor au settings kwa kusaidia subdomain handling  
- [x] Fanya testing za access control kwa subdomains tofauti  

### Milestone 4: Management ya Staff  
- [x] Tengeneza API ya kusajili, kuonyesha, na kuondoa staff  
- [x] Hakikisha staff hawavuki mipaka ya taasisi zao  
- [x] Tengeneza UI (frontend au DRF browsable) ya staff management  

### Milestone 5: Majaribio na Uhakiki  
- [x] Andika unit tests kwa models zote  
- [x] Andika tests kwa views (GET, POST, PATCH, DELETE)  
- [x] Hakikisha tests za access control na isolation zinapita  

---

## Ratiba ya Utekelezaji (Timeline)

| Wiki | Hatua/Milestone                     | Maelezo                                               |
|------|------------------------------------|--------------------------------------------------------|
| 1    | Milestone 1: Modeli                | Tengeneza models zote na admin interface              |
| 2    | Milestone 2: API & Serializers     | Tengeneza serializers, views, routers, na permissions |
| 3    | Milestone 3: Middleware ya Subdomain| Subdomain isolation na context handling               |
| 4    | Milestone 4: Staff Management      | API za staff na ruhusa ndani ya taasisi               |
| 5    | Milestone 5: Majaribio             | Andika na endesha tests zote                          |

---

## Muundo wa Folda

```plaintext
institutions/
├── __init__.py
├── admin.py
├── apps.py
├── decorators.py             # Ruhusa za kuangalia kama user yuko kwenye taasisi
├── helpers/
│   └── institution_helpers.py # Helper functions za institutions
├── middleware.py             # InstitutionMiddleware kwa subdomain isolation
├── models/
│   ├── __init__.py
│   ├── institution_type.py   # Modeli ya aina ya taasisi
│   ├── institution.py        # Modeli ya taasisi
│   └── staff_profile.py      # Profile ya watumishi wa taasisi
├── serializers/
│   ├── __init__.py
│   ├── institution_type.py
│   ├── institution.py
│   └── staff_profile.py
├── urls.py
├── views/
│   ├── __init__.py
│   ├── institution_type_views.py
│   ├── institution_views.py
│   └── staff_views.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_permissions.py