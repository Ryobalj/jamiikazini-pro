# 🎓 Education App - Jamiikazini

## 📌 Lengo Kuu  
App ya `education` inasimamia taarifa zote muhimu za elimu ndani ya taasisi
(shule, vyuo n.k). Mfumo huu unatoa miundombinu ya kudhibiti taarifa za
wanafunzi, walimu, idara, tathmini, mtaala, na ripoti za matokeo.

---

## 🎯 Malengo Mahususi  
- Kurekodi na kufuatilia wanafunzi (`Student`)
- Kudhibiti taarifa za walezi wa wanafunzi (`Guardian`)
- Kusimamia walimu na wafanyakazi wa elimu (`Staff`)
- Kusimamia idara za elimu ndani ya taasisi (`Department`)
- Kusimamia tathmini za kitaaluma (`Assessment`)
- Kutengeneza na kuwasilisha ripoti za matokeo (`ReportCard`)
- Kuhifadhi mtaala wa masomo kwa mfumo wa kihierarkia (`Syllabus`)
- Kuwezesha upload ya syllabus kwa njia ya CSV/Excel
- Kuunda scheme of work na lesson plans kutoka kwenye syllabus

---

## ⚙️ Mahitaji ya Kiufundi

- Modeli zote zina `institution` (FK) kwa isolation ya data
- Kutumia `BaseModel` yenye fields: `institution`, `created_at`, `updated_at`
- Watumiaji wanadhibitiwa kupitia `kiini` + `institutions`
- CRUD views zina permissions za taasisi husika
- Mixins: `InstitutionContextMixin` kwa filtering ya data
- Upload na validation ya syllabus via Excel/CSV
- Paginated list views kwa performance nzuri
- Tree views kwa syllabus hierarchy (read-only & nested)
- API support kwa scheme generator

---

## 🔗 Mahusiano ya App

| App             | Uhusiano                                                           |
|------------------|--------------------------------------------------------------------|
| `institutions`   | Kuhifadhi na kudhibiti taasisi zinazotumia mfumo                  |
| `kiini`          | Kutoa context ya mtumiaji ndani ya taasisi (role & access)        |
| `accounts`       | Login na role ya wanafunzi, staff, au wazazi                      |
| `payments`       | Malipo ya ada, huduma, na michango mingine ya shule              |
| `gov_integration`| Kuripoti matokeo au taarifa za wanafunzi kwa mamlaka za elimu    |

---

## ✅ Checklist ya Utekelezaji

### MODELS
- [ ] `Student`, `Guardian`, `Staff`
- [ ] `Department`, `Assessment`, `ReportCard`
- [ ] Syllabus hierarchy:
  - [ ] `GeneralCompetency`
  - [ ] `SpecificCompetency`
  - [ ] `LearningActivity`
  - [ ] `StudentTask`, `TeachingMethod`, `ReferenceMaterial`
  - [ ] `TeachingTool`, `AssessmentTool`, `ActivityRemark`
- [ ] `BaseModel` for all

### SERIALIZERS
- [ ] CRUD serializers for each model
- [ ] Nested serializers for syllabus
- [ ] Bulk upload validation

### VIEWS
- [ ] CRUD views for all core models
- [ ] Tree view for syllabus hierarchy
- [ ] Bulk syllabus upload via Excel/CSV
- [ ] Scheme generator API (lesson plan/scheme)

### URLS
- [ ] Route kila view kwa RESTful endpoints

### TESTS
- [ ] Unit tests for all models
- [ ] View tests for CRUD, syllabus tree, upload
- [ ] Permission tests for institution data isolation
- [ ] Upload & validation tests
- [ ] Scheme generation tests

---

## 🧠 Mpangilio wa Syllabus

Mfumo wa syllabus unafuata muundo wa kihierarkia kama ifuatavyo:

Umahiri Mkuu (General Competency)
└── Umahiri Mahususi (Specific Competency)
    └── Shughuli za Ujifunzaji (Learning Activities)
        └── Shughuli Ndogo za Mwanafunzi (Student Tasks)
            ├── Mwezi (Month)
            ├── Wiki (Week)
            ├── Idadi ya Vipindi (No. of Sessions)
            ├── Mbinu za Ufundishaji (Teaching Methods)
            ├── Marejeleo (Reference Materials)
            ├── Zana za Ufundishaji (Teaching Tools)
            ├── Zana za Upimaji (Assessment Tools)
            └── Maoni/Maswali ya Mwisho (Activity Remarks)

- Inahusishwa na `Subject` na `GradeLevel`
- Inatakiwa kuwe na uwezo wa:
  - Kupakia syllabus kupitia Excel/CSV
  - Kutengeneza lesson plans na scheme of work otomatiki
  - Kuonyesha syllabus kama tree view

---

## 🗂️ Muundo wa Vipengele vya App

App ya `education` imegawanywa katika sehemu zifuatazo kwa utaratibu mzuri wa code:

### 🔹 `models/`
- `base.py` - Base model kwa ajili ya `institution`, `timestamps`
- `student.py`, `guardian.py`, `staff.py` - Watu wanaohusika na elimu
- `department.py`, `assessment.py`, `report_card.py` - Muundo wa shule na tathmini
- `syllabus/` - Module zote za syllabus kihierarkia

### 🔹 `serializers/`
- CRUD serializers kwa kila model
- Nested syllabus serializers
- Validations za upload

### 🔹 `views/`
- CRUD views zenye permission & filtering
- Tree view ya syllabus
- Bulk upload handler
- Scheme generator endpoint

### 🔹 `tests/`
- Test za models, views, uploads, na permissions
- Test za syllabus tree na lesson plan generator

### 🔹 `admin/` *(optional)*
- Custom admin views kwa syllabus au assessment

### 🔹 `bulk_upload/`
- `syllabus_template.xlsx`
- `syllabus_uploader.py` – script ya parse + save syllabus

---
education/
├── __init__.py
├── admin/
│   ├── __init__.py
│   ├── student_admin.py
│   ├── syllabus_admin.py
│   ├── assessment_admin.py
│   └── staff_admin.py
├── apps.py
├── bulk_upload/
│   ├── __init__.py
│   ├── syllabus_template.xlsx
│   └── syllabus_uploader.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── student.py
│   ├── guardian.py
│   ├── staff.py
│   ├── department.py
│   ├── assessment.py
│   ├── report_card.py
│   └── syllabus/
│       ├── __init__.py
│       ├── general_competency.py
│       ├── specific_competency.py
│       ├── learning_activity.py
│       ├── student_task.py
│       ├── teaching_method.py
│       ├── reference_material.py
│       ├── teaching_tool.py
│       ├── assessment_tool.py
│       └── activity_remark.py
├── serializers/
│   ├── __init__.py
│   ├── student_serializers.py
│   ├── guardian_serializers.py
│   ├── staff_serializers.py
│   ├── assessment_serializers.py
│   ├── report_card_serializers.py
│   └── syllabus_serializers.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_syllabus_upload.py
│   ├── test_permissions.py
│   └── test_scheme_generator.py
├── urls.py
├── views/
│   ├── __init__.py
│   ├── student_views.py
│   ├── guardian_views.py
│   ├── staff_views.py
│   ├── department_views.py
│   ├── assessment_views.py
│   ├── report_card_views.py
│   ├── syllabus_views.py
│   └── scheme_generator.py
├── permissions.py
├── filters.py
├── utils.py
└── constants.py


# 🕒 Weekly Timetable System - Jamiikazini Education App

## 📌 Maelezo ya Jumla

Mfumo wa `ratiba` ni sehemu muhimu ya app ya `education`, unaoratibu shughuli za kila siku za masomo kwa walimu, wanafunzi, na madarasa. Ratiba hii inahusiana moja kwa moja na `syllabus`, `scheme of work`, na `lesson plans`.

Ratiba inatengenezwa kwa wiki (Monday–Friday) na inaonyesha vipindi (periods), mapumziko, na inauwezo wa ku-exportiwa kama **PDF iliyo salama (encrypted)** kwa ajili ya usambazaji rasmi.

---

## 🎯 Malengo Mahususi

- Kupanga ratiba ya shule kwa wiki (Monday–Friday)
- Kuwezesha ratiba za darasa, mwalimu na shule nzima
- Kuunganisha ratiba na lesson plan & scheme ya masomo
- Kuhakikisha mapumziko na muda wa masomo unaendana na sera ya taasisi
- Kuwezesha export ya PDF yenye encryption/password na watermark
- Kuruhusu mwalimu au admin kuona ratiba yake binafsi

---

## 🔗 Mahusiano ya Moja kwa Moja

| Kipengele        | Uhusiano wa Kimfumo |
|------------------|----------------------|
| `Subject`        | Husika kwenye kila kipindi (period) |
| `Teacher (Staff)`| Hupangiwa vipindi kwa wiki |
| `ClassLevel`     | Ratiba hutengenezwa kwa kila darasa |
| `Stream`         | Ratiba hutofautiana kwa stream tofauti |
| `LessonPlan`     | Kipindi kinahusishwa na lesson plan |
| `AcademicTerm`   | Ratiba ni ya term husika |
| `Syllabus`       | Chanzo cha lesson plan ya kila kipindi |

---

## 🧩 Muundo wa Models ya Ratiba

### `TimeSlot`  
Muda wa kila kipindi (kwa siku moja)

| Field             | Type     | Maelezo                      |
|------------------|----------|------------------------------|
| `day_of_week`     | Char     | Monday–Friday                |
| `start_time`      | Time     | Mwanzo wa kipindi            |
| `end_time`        | Time     | Mwisho wa kipindi            |
| `is_break`        | Boolean  | Ikiwa ni mapumziko au siyo   |

---

### `TimetableEntry`

| Field              | Type             | Maelezo                               |
|-------------------|------------------|----------------------------------------|
| `academic_term`    | FK (AcademicTerm)| Term husika                          |
| `class_level`      | FK (ClassLevel)  | Darasa husika                         |
| `stream`           | FK (Stream)      | Optionally darasa maalum             |
| `subject`          | FK (Subject)     | Somo la kipindi                       |
| `teacher`          | FK (Staff)       | Mwalimu anayefundisha                 |
| `timeslot`         | FK (TimeSlot)    | Kipindi kimoja kwa wiki               |
| `lesson_plan`      | FK (LessonPlan)  | Inayohusiana na kipindi (optional)    |
| `location`         | CharField        | Mahali (e.g. Room A, Lab 2)           |

---

## 📤 Export Features

- Export ya timetable kwa:
  - [x] Class Level
  - [x] Teacher
  - [x] Stream
  - [x] Whole school

### Format:
- PDF table view (weekly)
- Includes header: school name, class, term, year
- Watermark ya `Jamiikazini Education`
- Encrypted (password configurable per institution)
- Cannot copy-paste contents (DRM enforced via PDF options)

---

## 🖥️ UI & UX Features

- Weekly calendar grid view (Mon–Fri, rows per period)
- Custom colors for breaks, subjects, free periods
- Tooltip kwa kila slot kuonyesha lesson plan
- Teacher view: personalized timetable
- Admin view: drag & drop editor (future)

---

## ✅ Checklist ya Utekelezaji

### MODELS
- [x] `TimeSlot` model (Mon–Fri, start–end time)
- [x] `TimetableEntry` model with FK to class/teacher/subject/etc

### SERIALIZERS
- [ ] CRUD serializers for TimetableEntry & TimeSlot
- [ ] Serializer for weekly export data

### VIEWS
- [ ] CRUD views for ratiba
- [ ] Teacher/Class timetable list endpoints
- [ ] PDF export endpoint (password + watermark + no-copy)

### FRONTEND (Future)
- [ ] Weekly grid for admin
- [ ] Teacher view
- [ ] Export button with password

---

## 📁 Eneo la Mafaili ya Ratiba


education/
├── models/
│   └── timetable/
│       ├── __init__.py
│       ├── timeslot.py
│       └── timetable_entry.py
├── serializers/
│   └── timetable_serializers.py
├── views/
│   └── timetable_views.py
├── pdf_export/
│   └── timetable_pdf_generator.py



## 📚 Hitimisho  
---

## 📚 Hitimisho  
App ya `education` inalenga kusaidia taasisi zote zilizosajiliwa ndani ya
Jamiikazini kuratibu taarifa muhimu za elimu kwa ufanisi mkubwa,
kwa kutumia teknolojia ya kisasa, na kuwaunganisha na mfumo wa kitaifa
au wa ndani ya taasisi.App ya `education` inalenga kusaidia taasisi zote
zilizosajiliwa ndani ya Jamiikazini kuratibu taarifa muhimu za elimu kwa
ufanisi mkubwa, kwa kutumia teknolojia ya kisasa, na kuwaunganisha na mfumo
wa kitaifa au wa ndani ya taasisi.
