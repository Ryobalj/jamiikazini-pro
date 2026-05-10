# 📝 Milestone – Syllabus Data Seeding & Models Integration

## Overview
Hii milestone inatoa roadmap kamili ya **database seeding** kwa models zinazotokana na syllabus. Inazingatia **utaratibu sahihi wa seeding**, kuunganisha models zilizopo, na kuendesha data kutoka CSV moja kuu.  

---

## ✅ Step 1 – Seed Syllabus Version

- **Model:** `SyllabusVersion`
- **CSV Source:** N/A (tutaunda manually kwa mwaka wa syllabus)
- **Fields:**  
  - `year`  
  - `is_current`
- **Task List:**  
  - [ ] Create SyllabusVersion objects for all years (e.g., 2019, 2023)  
  - [ ] Set `is_current=True` kwa syllabus ya sasa  

---

## ✅ Step 2 – Seed Subjects

- **Model:** `Subject`
- **CSV Source:** Derived from syllabus (majina ya subjects)
- **Fields:**  
  - `name`  
  - `code` (optional, for unique identification)
- **Task List:**  
  - [ ] Extract unique subjects from CSV  
  - [ ] Seed subjects table  
  - [ ] Ensure no duplicates  

---

## ✅ Step 3 – Seed Classes

- **Model:** `ClassLevel`
- **CSV Source:** “Darasa” column
- **Fields:**  
  - `name` (Darasa III, IV, V…)  
  - `code` (optional)
- **Task List:**  
  - [ ] Extract unique classes from CSV  
  - [ ] Seed ClassLevel table  

---

## ✅ Step 4 – Seed Subject Version

- **Model:** `SubjectVersion`
- **CSV Source:** “Darasa” + Subject
- **Fields:**  
  - `syllabus_version` → FK to `SyllabusVersion`  
  - `subject` → FK to `Subject`  
  - `class_level` → FK to `ClassLevel`
- **Task List:**  
  - [ ] Map each subject per syllabus per class  
  - [ ] Seed `SubjectVersion` table  
  - [ ] Ensure duplicates across syllabus_versions are allowed  

---

## ✅ Step 5 – Seed Main Competence

- **Model:** `MainCompetence`
- **CSV Source:** “Umahiri Mkuu” column
- **Fields:**  
  - `subject_version` → FK to `SubjectVersion`  
  - `title` / `description` → from column
- **Task List:**  
  - [ ] Extract main competences per subject_version  
  - [ ] Seed table ensuring FK integrity  

---

## ✅ Step 6 – Seed Specific Competence

- **Model:** `SpecificCompetence`
- **CSV Source:** “Umahiri Mahususi” column
- **Fields:**  
  - `main_competence` → FK to MainCompetence  
  - `description` → column value
- **Task List:**  
  - [ ] Extract specific competences per main competence  
  - [ ] Seed table with FK to `MainCompetence`  

---

## ✅ Step 7 – Seed Learning Activities

- **Model:** `LearningActivity`
- **CSV Source:** “Shughuli za Ujifunzaji” column
- **Fields:**  
  - `specific_competence` → FK to SpecificCompetence  
  - `description` → column value
- **Task List:**  
  - [ ] Extract learning activities  
  - [ ] Seed table ensuring FK integrity  

---

## ✅ Step 8 – Seed Specific Learning Activities

- **Model:** `SpecificLearningActivity`
- **CSV Source:**  
  - “Mbinu” → `teaching_method`  
  - “Shughuli Mahususi za Ujifunzaji” → `extended_activity`  
  - “Vigezo vya Upimaji” → `assessment_criteria`  
  - “Zana” → `tools`  
  - “Rejea / Reference” → `reference`  
  - “Idadi ya Vipindi” → `periods_count`  
- **Fields:**  
  - `learning_activity` → FK to LearningActivity  
  - Others → mapped from CSV columns
- **Task List:**  
  - [ ] Parse CSV row by row  
  - [ ] Split “Mbinu za Ufundishaji” into teaching_method and extended_activity  
  - [ ] Map remaining columns directly to fields  
  - [ ] Seed `SpecificLearningActivity` table with FK integrity  

---

## 🔹 Notes

- **CSV must be canonical:** Column names should match fields above for automated seeding.  
- **FK Order Matters:** SyllabusVersion → Subjects → Classes → SubjectVersion → MainCompetence → SpecificCompetence → LearningActivity → SpecificLearningActivity  
- **Duplicate Handling:** `SubjectVersion` ensures duplicate subjects across syllabus_versions are allowed.  
- **Row-wise processing:** Each row in CSV must be processed sequentially to maintain FK dependencies.