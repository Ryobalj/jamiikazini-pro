Hii hapa .md file yenye milestones + checklist kwa mfumo mpya ulioboreshwa kulingana na models mpya,
hasa ukizingatia kwamba methodologies hazipo tena kama model — sasa zinapatikana moja kwa moja ndani ya SpecificLearningActivity.method

👉 Hii version unaweza kuikopi moja kwa moja kama ROADMAP.md kwenye repo.


---

📘 Jamiikazini Syllabus Engine – Development Roadmap (v1.0)

Dynamic Scheme of Work & Lesson Plan Generator using New Models


---

## 1. Project Foundation

1.1 Cleanup & Preparation

[ ] Archive old 3500-line legacy Django template PDF generator

[ ] Remove any references to old methodologies model

[ ] Apply new reference: SpecificLearningActivity.method

[ ] Replace all legacy UserProfile usage → TeacherWorkstation



---

## 2. New Folder Architecture

syllabus/
    calculators/
    builders/
    services/
    templates/
    serializers.py
    views.py
    urls.py

Checklist

[ ] Create syllabus/

[ ] Create calculators/

[ ] Create builders/

[ ] Create services/

[ ] Create templates/

[ ] Create empty serializer + view + url files



---

## 3. Serializers Needed

Competence + Activity Structure

[ ] MainCompetenceSerializer

[ ] SpecificCompetenceSerializer

[ ] LearningActivitySerializer

[ ] SpecificLearningActivitySerializer (using new fields)


Teacher + Calendar

[ ] TeacherSerializer (from teacher_workstation)

[ ] AcademicCalendarSerializer


Generators

[ ] SchemeRequestSerializer

[ ] LessonPlanRequestSerializer



---

## 4. Business Logic Services

4.1 Competence Tree Service

[ ] Fetch main → specific → learning → specific learning activities

[ ] Attach:

method = specificlearningactivity.method

teaching_aids

references

assessment_criteria

periods


[ ] Produce flattened + nested structures


4.2 Calendar Service

[ ] Validate term start → midterm → termbreak → midannual → annual

[ ] Convert dates → ISO week numbers

[ ] Provide:

studying_weeks

period ranges

break windows




---

## 5. Calculation Engines

5.1 Period Calculator

[ ] total_periods = sum(activity.periods)

[ ] periods_per_week = subject.periods_per_week

[ ] required_weeks = total_periods / periods_per_week

[ ] studying_weeks = (total_learning_days / 5) - adjustments

[ ] kisawazishi formula

[ ] imbalance correction logic

[ ] Overload correction (like vipindi_hitajika vs vipindi_kusoma)


5.2 Week Allocation

[ ] Week block distribution

[ ] Cycling weeks 1–4

[ ] Reset at breaks

[ ] Carry-over logic using “z accumulator”

[ ] Output → array of allocated weeks per learning activity


5.3 Month Allocation

[ ] Map weekly sequences → calendar months

[ ] Handle:

new month when week = 1

cross-month shifts

multi-month coverage




---

## 6. Template Generation

6.1 Scheme Templates

Swahili Template

[ ] "UTARATIBU WA KAZI" header

[ ] Competence → Activity → Student Activity → Method (NEW)

[ ] References + Teaching Aids + Assessment Aids

[ ] Swahili Exam Titles:

[ ] MITIHANI YA ROBO MUHULA

[ ] LIKIZO YA MUHULA WA KWANZA

[ ] MITIHANI YA MUHULA WA PILI

[ ] LIKIZO YA MWAKA



English Template

[ ] FIRST MID-TERM EXAM

[ ] TERMINAL EXAMINATIONS

[ ] SECOND MID-TERM

[ ] ANNUAL EXAMINATIONS


6.2 Lesson Plan Template

[ ] Topic

[ ] Subtopic

[ ] Specific Objectives

[ ] Teaching/Learning Procedures

[ ] Teaching Aids

[ ] Assessment

[ ] Reflection



---

## 7. PDF Builders

Base PDF Builder

[ ] Header/Footer system

[ ] School + Teacher layout

[ ] Page numbering

[ ] Automatic table splitting


Scheme PDF Builder

[ ] Build table rows dynamically

[ ] Insert exam rows at calculated indexes

[ ] Multi-language support

[ ] Auto height management


Lesson Plan PDF Builder

[ ] Generate 1-page or multi-page layout

[ ] Simple margin + grid alignment



---

## 8. API Endpoints (DRF)

Scheme Generation

[ ] POST /api/syllabus/scheme/generate/

Input: class, subject, year

Output: PDF


[ ] POST /api/syllabus/scheme/preview/

Output: JSON without PDF



Lesson Plan

[ ] POST /api/syllabus/lessonplan/generate/

Output: Lesson Plan PDF



Competence Tree

[ ] GET /api/syllabus/competence-tree/?subject=X



---

## 9. System Integrations

Payments (Jamiikazini Payments App)

[ ] Check active subscription

[ ] Fallback message if unpaid

[ ] Deduct credits if using credit-mode


Search App Integration

[ ] Index competencies

[ ] Index subjects

[ ] Index generated schemes



---

## 10. Testing Strategy

10.1 Unit Tests

[ ] Period calculations

[ ] Week allocations

[ ] Month allocations

[ ] Competence tree building


10.2 PDF Tests

[ ] Row count

[ ] Exam row positions

[ ] Correct display of method

[ ] Page numbering



---

## 11. Final Deliverables

[ ] Fully working Syllabus Engine (v1.0)

[ ] Clean modular code

[ ] 100% replacement of old generator

[ ] Developer documentation

[ ] Deployer instructions

[ ] User-friendly error messages



---

🎯 READY

Ukiwa tayari tunaendelea:

Je tuanze milestone ipi kwanza?

1. Kuunda directory structure (syllabus_engine/...)


2. Kuandika serializers mpya?


3. Kuandaa competence tree service?


4. Kuandika period calculator?



Niseme tu—naanza.


🔥 SUMMARY YA MNYORORO (Msingi → Juu)

1. CalendarService (NEXT)


2. PeriodCalculator


3. WeekAllocationEngine


4. MonthAllocationEngine


5. SchemeBuilder


6. LessonPlanBuilder


7. PDF Builders


8. API Endpoints


9. Tests
