# ✅ CHECKLIST: KUFIKIA MATOKEO YA ZAMANI (NEW ARCHITECTURE)

Lengo:  
👉 Kupata **Scheme of Work** na **Lesson Plan** zinazotoa matokeo yale yale ya zamani  
👉 Lakini kwa **muundo mpya ulioboreshwa**, unaozingatia `language` na `is_awali`

---

## 🧠 A. ACADEMIC CONTEXT (MSINGI WA KILA KITU)
- [x] Tengeneza `AcademicContext` (dataclass / object)
- [x] Iwe na fields:
  - [x] `language` (`sw` / `en`)
  - [x] `is_awali` (True / False)
  - [x] `is_english` (kutoka `SubjectVersion.is_english`)
  - [x] `class_level`
  - [x] `subject`

> AcademicContext ipitishwe kila mahali (scheme + lessonplan)

---

## 🧩 B. LESSON SENTENCE (CONTENT ENGINE)
- [x] Hakikisha `LessonSentence` ina fields:
  - [x] `category`
  - [x] `language`
  - [x] `is_awali`
  - [x] `is_active`
- [x] Ongeza helper methods ndani ya model:
  - [x] `get_teaching(ctx)`
  - [x] `get_learning(ctx)`
  - [x] `get_indicator_primary(ctx)`
  - [x] `get_indicator_secondary(ctx)`
  - [x] `get_reflection(ctx)`
- [x] Boresha `pick_random()`:
  - [x] chujwa kwa `category`
  - [x] chujwa kwa `language`
  - [x] chujwa kwa `is_awali`
  - [x] iheshimu `is_active=True`

---

## 🛠️ C. LESSON PLAN BUILDER (RUNTIME LOGIC)
- [ ] Ondoa logic zilizotapakaa:
  - [ ] `if is_english`
  - [ ] `if is_song`
  - [ ] `if is_awali`
- [ ] Pitisha `AcademicContext` kama dependency kuu
- [ ] Tumia:
  - [ ] `LessonSentence.pick_random(category, ctx)`
  - [ ] `sentence.get_teaching(ctx)` badala ya `.teaching_sw / .teaching_en`
- [ ] Ruhusu:
  - [ ] mtumiaji kuchagua au kuandika `SpecificLearningActivity`
  - [ ] mfumo urekebike kulingana na mazingira ya mwalimu

---

## 📋 D. SCHEME OF WORK (WEEKLY DISTRIBUTION)
- [ ] Hakikisha `SpecificLearningActivity`:
  - [ ] inaweza kuchukua vipindi zaidi ya wiki 1
- [ ] Scheme iweze:
  - [ ] ku-cover term nzima / mwaka mzima
- [ ] Tumia `ScheduleItem` iliyoboreshwa
- [ ] Ondoa matumizi ya `Methodology` model (sasa ni field)

---

## 🧪 E. ADMIN & SERIALIZER (GUARD RAILS)
- [ ] Admin:
  - [ ] ongeza filters: `language`, `is_awali`
  - [ ] panga fieldsets kulingana na Awali / Non-Awali
- [ ] Serializer:
  - [ ] validate:
    - [ ] consistency ya `language` vs text fields
    - [ ] matumizi sahihi ya `is_awali`
- [ ] Zuia LessonSentence zisizofaa kuingia runtime

---

## 📄 F. PDF / OUTPUT (FINAL RESULT)
- [ ] Lesson Plan:
  - [ ] matokeo yafanane na ya zamani
  - [ ] content ichaguliwe dynamically
- [ ] Scheme of Work:
  - [ ] layout ibaki ile ile
  - [ ] data itoke kwenye models mpya

---

## 🎯 LENGO LA MWISHO
> Mtumiaji apate **Lesson Plan & Scheme sawa na za zamani**,  
> lakini mfumo uwe:
- safi (clean)
- unaopanuka (scalable)
- unaozingatia mazingira halisi ya kazi ya mwalimu