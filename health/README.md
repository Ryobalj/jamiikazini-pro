# Health App (Institutions)

## Lengo Kuu
App ya `health` inasimamia huduma zote zinazohusiana na afya kwa taasisi za kiafya kama hospitali na kliniki. Inatoa miundombinu ya kuhifadhi na kufuatilia taarifa za wagonjwa, historia ya matibabu, miadi, idara, na usimamizi wa rasilimali za afya.

---

## Majukumu Mahususi
- Kusimamia taarifa za wagonjwa (`Patient`)
- Kurekodi na kufuatilia historia ya matibabu ya wagonjwa (`MedicalHistory`)
- Kusimamia miadi ya wagonjwa na wataalamu (`Appointment`)
- Kusimamia idara mbalimbali za hospitali (`Department`)
- Usimamizi wa rasilimali za hospitali kama vifaa na dawa (`Inventory`)
- Kusimamia malipo na bili za matibabu (`Billing`)

---

## Mahitaji Muhimu ya Kiufundi
- Models zote zinahitaji uhusiano wa moja kwa moja na `Institution` ili kudhibiti data za hospitali au kliniki
- Watumiaji wanaweza kuwa wafanyakazi wa taasisi kupitia `kiini` + `institutions`
- CRUD views zenye permissions maalum kwa taasisi husika tu
- Validations ili kuhakikisha usahihi wa miadi na historia ya matibabu ya wagonjwa
- Uhusiano kati ya mgonjwa na mtaalamu au idara kudhibitiwa vizuri

---

## Uhusiano na Apps Nyingine
- `institutions`: Hutoa taarifa za taasisi ya afya (hospitali, kliniki)
- `kiini`: Hutoa mtumiaji (`User`) aliye kwenye taasisi
- `accounts`: Huwezesha login ya staff, mgonjwa au mtumaji
- `payments`: Huwezesha malipo ya huduma za afya na bili
- `logistics`: Inaweza kusaidia usafirishaji wa vifaa vya afya au wagonjwa
- `gov_integration`: Kuripoti taarifa za afya kwa mamlaka ya serikali

---

## Checklist ya Utekelezaji

### MODELS
- [ ] Tengeneza model ya `Patient`
- [ ] Tengeneza model ya `MedicalHistory`
- [ ] Tengeneza model ya `Appointment`
- [ ] Tengeneza model ya `Department`
- [ ] Tengeneza model ya `Inventory`
- [ ] Tengeneza model ya `Billing`

### SERIALIZERS
- [ ] Andika `PatientSerializer`
- [ ] Andika `MedicalHistorySerializer`
- [ ] Andika `AppointmentSerializer`
- [ ] Andika `DepartmentSerializer`
- [ ] Andika `InventorySerializer`
- [ ] Andika `BillingSerializer`

### VIEWS
- [ ] CRUD View kwa `Patient`
- [ ] CRUD View kwa `MedicalHistory`
- [ ] CRUD View kwa `Appointment`
- [ ] CRUD View kwa `Department`
- [ ] CRUD View kwa `Inventory`
- [ ] CRUD View kwa `Billing`
- [ ] Ongeza permission checks kwa institution context
- [ ] Tumia decorator `@user_is_in_institution` au mixin ya institution

### URLS
- [ ] Seta route za kila view kwenye `urls.py`

### TESTS
- [ ] Test ya `Patient` model
- [ ] Test ya `MedicalHistory` model
- [ ] Test ya `Appointment` model
- [ ] Test ya `Department` model
- [ ] Test ya `Inventory` model
- [ ] Test ya `Billing` model
- [ ] CRUD view tests kwa kila model
- [ ] Permission tests kwa institution data isolation

### EXTRA
- [ ] Tumia `BaseModel` yenye `institution`, `created_at`, `updated_at`
- [ ] Hakikisha serializers zina validate taasisi kwa usahihi
- [ ] Paginate list views zenye data kubwa

---

## Muundo wa Mafaili

```bash
health/
├── __init__.py
├── admin.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── patient.py           # Taarifa za mgonjwa
│   ├── medical_history.py   # Historia ya matibabu ya mgonjwa
│   ├── appointment.py       # Miadi ya mgonjwa
│   ├── department.py        # Idara za hospitali
│   ├── inventory.py         # Dawa na vifaa vya afya
│   └── billing.py           # Bili na malipo ya matibabu
├── serializers/
│   ├── __init__.py
│   ├── patient.py
│   ├── medical_history.py
│   ├── appointment.py
│   ├── department.py
│   ├── inventory.py
│   └── billing.py
├── views/
│   ├── __init__.py
│   ├── patient.py
│   ├── medical_history.py
│   ├── appointment.py
│   ├── department.py
│   ├── inventory.py
│   └── billing.py
├── urls.py
├── tests/
│   ├── __init__.py
│   ├── test_patient.py
│   ├── test_medical_history.py
│   ├── test_appointment.py
│   ├── test_department.py
│   ├── test_inventory.py
│   └── test_billing.py
└── permissions.py
