# 📘 JAMIIKAZINI — LESSON PLAN & SCHEME SYSTEM DESIGN

## 🎯 LENGO KUU
Kujenga mfumo wa Scheme of Work na Lesson Plan unaoendana na uhalisia wa kazi ya mwalimu shuleni, kwa kuzingatia:
- ratiba halisi ya mwalimu
- lugha ya somo (Kiswahili / Kiingereza)
- awali au la
- mazingira ya shule, wilaya na kata
- matumizi ya competence tree ya mtaala

Mfumo huu unaondoa utegemezi wa ratiba ya shule katika uhalisia wa kufundisha.

---

## 🧍‍♂️ A. MTUMIAJI (MWALIMU)

### A1. Usajili wa Mtumiaji

### A2. TeacherWorkStation
Hifadhi taarifa za mazingira ya mwalimu:

- teacher (User)
- school_name
- district
- ward
- region
- is_active

👉 Taarifa hizi hutumika kwenye:
- Scheme of Work
- Lesson Plan
- PDF headers (jina la shule, wilaya, kata, mwalimu)

TeacherWorkStation ni **identity ya kitaaluma ya mwalimu**.

---

## 🗓️ B. RATIBA YA MWALIMU (TIME TABLE)

### B1. Madhumuni ya TimeTable
- Kutambua masomo ya mwalimu (My Subjects)
- Kuonyesha mzigo wa kufundisha
- Kutoa idadi ya wanafunzi wa darasa

### B2. TimeTable HAIAMUI:
❌ muda halisi wa kufundisha  
❌ uhalali wa lesson plan  

Ratiba ni ya kumbukumbu, si ushahidi wa uhalisia.

---

## 📚 C. SUBJECT VERSION (CHANZO KIKUU CHA LOGIC)

Fields muhimu:
- subject
- class_level
- syllabus_version
- is_english
- is_awali

👉 SubjectVersion inaamua:
- lugha ya sentensi (sw / en)
- aina ya lesson sentence
- competence tree itakayotumika
- aina ya scheme na lesson plan

SubjectVersion ndiyo **kitambulisho cha kitaaluma cha somo**.

---

## 🧠 D. ACADEMIC CONTEXT (GLOBAL CONTEXT OBJECT)

Inabebwa na mfumo wakati wa kujenga scheme au lesson plan.

Fields:
- subject
- class_level
- language (kutokana na is_english)
- is_awali
- syllabus_version
- year
- term (hiari)

👉 AcademicContext:
- hupitishwa kwa builders zote
- huzuia kurudia logic kwenye kila sehemu

---

## 🌳 E. COMPETENCE TREE (READ ONLY DATA)

SubjectVersion ↓ MainCompetence ↓ SpecificCompetence ↓ LearningActivity ↓ SpecificLearningActivity
- Data ya mtaala
- Haibadilishwi na user
- Hutumika kwenye scheme na lesson plan

---

## 🧾 F. SCHEME OF WORK FLOW
User Menu ↓ Scheme Icon ↓ My Subjects (kutoka TimeTable) ↓ Chagua SubjectVersion ↓ Request Scheme ↓ SchemeBuilder ├─ TeacherWorkStation ├─ AcademicContext ├─ Competence Tree ├─ Period Allocation Logic ↓ Scheme of Work Output (PDF / Preview)

### Sifa za Scheme:
- ni ya mwalimu mmoja
- ni ya shule yake
- ina jina la wilaya na kata
- inazingatia syllabus version

---

## 🧠 G. LESSON PLAN FLOW
### G1. USER MENU
User Menu └─ Lesson Plan ├─ Auto └─ Manual

---

### G2. AUTO LESSON PLAN
Auto Lesson Plan ↓ Chagua SubjectVersion (kutoka My Subjects) ↓ Pata Competence Tree ↓ Orodha ya SpecificLearningActivity ↓ User atick: - is_song - will_repeat ↓ User ajaze: - timestart (halisi) - timefinish (halisi) - boys_attended - girls_attended - learners_understood (hiari) ↓ LessonPlanRuntimeBuilder ├─ AcademicContext ├─ LessonSentence ├─ SpecificLearningActivity ↓ Lesson Plan Output

#### Kanuni Muhimu:
- Lugha haichaguliwi na user
- Inatoka SubjectVersion.is_english
- is_awali huamua sentensi za utangulizi

---

### G3. MANUAL LESSON PLAN

Manual Lesson Plan ↓ Chagua SubjectVersion ↓ Chagua LearningActivity ↓ User aandike: - SpecificLearningActivity - Teaching Aids - Teaching Method - Indicators - References ↓ LessonPlanBuilder ↓ Lesson Plan Output
Copy code

Manual inaruhusu:
- mazingira tofauti ya shule
- ubunifu wa mwalimu
- lakini bado hutumia AcademicContext

---

## ⏱️ H. KANUNI YA MUDA (MUHIMU SANA)

### ❌ ZILIZOONDOLEWA KIMAANA:
- TimeTable.timestart
- TimeTable.timefinish
- periodsession kama chanzo cha lesson plan

### ✅ ZINAZOTUMIKA:
- timestart / timefinish kutoka Lesson Plan Form

#### Sababu:
- ratiba hubadilika
- dharura hutokea
- vipindi vinaweza kuunganishwa
- uhalisia wa kufundisha ni muhimu kuliko ratiba

---

## 🏁 HITIMISHO

Mfumo huu:
- una single source of truth (SubjectVersion + AcademicContext)
- unaheshimu uhalisia wa shule
- una scalability
- unaondoa logic ngumu kwenye views
- unatoa scheme na lesson plan zenye uhalali wa kitaaluma
