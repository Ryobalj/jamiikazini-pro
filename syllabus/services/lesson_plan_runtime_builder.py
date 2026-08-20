# syllabus/services/lesson_plan_runtime_builder.py
from datetime import timedelta
from typing import Optional, List

from syllabus.models.lesson_sentence import LessonSentence
from syllabus.services.data_models import (
    LessonPlanData,
    LessonIdentification,
    LessonSubjectInfo,
    LessonStep,
    LessonReflection,
    StudentCount,
    LessonPlanMeta,  # 🔵 ADD THIS IMPORT
)


class LessonPlanRuntimeBuilder:
    """
    Builds a LessonPlanData instance from:
    - SpecificLearningActivity
    - User inputs
    - AcademicContext

    Language handling is hybrid:
    - Derived from SubjectVersion via AcademicContext
    """

    TRANSLATIONS = {
        "intro_step_name": {"sw": "Utangulizi", "en": "Introduction"},
        "development_step_name": {
            # Must match syllabus/i18n/sw.py LESSON_PLAN["steps"][1] exactly —
            # LessonPlanPDFBuilder looks up steps by this exact string.
            "sw": "Kuendeleza ujenzi wa umahiri",
            "en": "Development"
        },
        "reinforcement_step_name": {
            # Must match syllabus/i18n/sw.py LESSON_PLAN["steps"][2] exactly.
            "sw": "Kubuni",
            "en": "Reinforcement"
        },
        "conclusion_step_name": {"sw": "Tathimini", "en": "Conclusion"},
        # VIGEZO VYA UPIMAJI should only confirm that the paired shughuli
        # ya ujifunzaji (learning_activity) was carried out correctly, not
        # restate curriculum text or the activity name on its own - see
        # _development_step/_reinforcement_step, which append this to that
        # step's own learning_activity string.
        "done_correctly_suffix": {
            "sw": "imefanyika kwa usahihi",
            "en": "was done correctly",
        },
        "next_plan_repeat": {
            "sw": "Nitarudia umahiri huu kipindi kijacho.",
            "en": "I will repeat this skill in the next session."
        },
        "assessment_unknown": {
            "sw": "Wanafunzi ___ kati ya {total} wameweza {activity}.",
            "en": "___ students out of {total} were able to {activity}."
        },
        "assessment_known": {
            "sw": "Wanafunzi {count} kati ya {total} wameweza {activity}.",
            "en": "{count} students out of {total} were able to {activity}."
        },
    }

    def __init__(
        self,
        *,
        specific_activity,
        academic_context,
        date,
        period: int,
        start_time,
        end_time,
        registered_boys: int,
        registered_girls: int,
        attended_boys: int,
        attended_girls: int,
        is_song: bool = False,
        managed_count: Optional[int] = None,
        repeat_next: bool = False,
    ):
        self.sla = specific_activity
        self.ctx = academic_context

        self.date = date
        self.period = period
        self.start_time = start_time
        self.end_time = end_time

        self.registered = StudentCount(registered_boys, registered_girls)
        self.attended = StudentCount(attended_boys, attended_girls)

        self.is_song = is_song
        self.managed_count = managed_count
        self.repeat_next = repeat_next

    # ==================================================
    # PUBLIC API
    # ==================================================

    def build(self) -> LessonPlanData:
        """
        Build the complete LessonPlanData runtime object WITH META FIELD.
        """
        lang = self.ctx.language

        identification = LessonIdentification(
            school_name=self.ctx.school_name,
            teacher_name=self.ctx.teacher_name,
            main_competence=(
                self.sla.learning_activity
                .specific_competence
                .main_competence
                .name
            ),
            class_level=self.ctx.class_level,
            period=self.period,
            date=self.date,
            time_start=self.start_time,
            time_finish=self.end_time,
            language=lang,
        )

        subject_info = LessonSubjectInfo(
            specific_competence=(
                self.sla.learning_activity
                .specific_competence
                .name
            ),
            main_activity=self.sla.learning_activity.name,
            specific_activity=self.sla.name,
            teaching_aids=self.sla.teaching_aids,
            references=self.sla.references or "",
            lesson_notes_intro=self.sla.lesson_notes_intro or "",
            lesson_notes_details=self.sla.lesson_notes_details or "",
            lesson_notes_illustrations=self.sla.lesson_notes_illustrations or "",
            lesson_notes_daily_life=self.sla.lesson_notes_daily_life or "",
            exercise_questions=self.sla.exercise_questions or [],
            diagram_type=self.sla.diagram_type or "",
        )

        steps = self._build_steps(lang)

        reflection = LessonReflection(
            teaching_comment=self._reflection_comment(lang),
            assessment_comment=self._assessment_comment(lang),
            next_plan_comment=self._next_plan_comment(lang),
        )
        
        # 🔴 FIX: CREATE META FIELD (REQUIRED FOR SERIALIZER)
        meta = LessonPlanMeta(
            subject=(
                self.sla.learning_activity
                .specific_competence
                .main_competence
                .subject_version
                .subject
                .name
            ),
            class_level=self.ctx.class_level,
            teacher=self.ctx.teacher_name,
            school=self.ctx.school_name,
            date=self.date,
            period=self.period,
            timestart=self.start_time,
            timefinish=self.end_time,
        )

        return LessonPlanData(
            identification=identification,
            registered_students=self.registered,
            attended_students=self.attended,
            subject_info=subject_info,
            lesson_steps=steps,
            reflection=reflection,
            meta=meta,  # 🔴 MUST INCLUDE THIS
        )

    # ==================================================
    # STEP BUILDERS
    # ==================================================

    def _build_steps(self, lang: str) -> List[LessonStep]:
        total_minutes = self.ctx.duration_minutes

        # Intro/reinforcement/conclusion get fixed allocations; development
        # takes whatever remains, so the four steps always sum exactly to
        # the period's real duration instead of drifting from it.
        intro_minutes = 5
        reinforcement_minutes = 10
        conclusion_minutes = 5
        dev_minutes = max(
            1, total_minutes - intro_minutes - reinforcement_minutes - conclusion_minutes
        )

        return [
            self._intro_step(lang, intro_minutes),
            self._development_step(dev_minutes, lang),
            self._reinforcement_step(lang, reinforcement_minutes),
            self._conclusion_step(lang, conclusion_minutes),
        ]

    def _intro_step(self, lang: str, duration_minutes: int) -> LessonStep:
        competence = (
            self.sla.learning_activity
            .specific_competence
            .name
        )

        if self.is_song:
            if lang == "sw":
                teaching = f"Kuwaongoza wanafunzi kuimba wimbo juu ya {competence}"
                learning = f"Kuimba wimbo juu ya {competence}"
                indicator = f"Wimbo juu ya {competence} umeimbwa kwa usahihi"
            else:
                teaching = f"Guiding students to sing a song about {competence}"
                learning = f"Sing a song about {competence}"
                indicator = f"The song about {competence} was sung correctly"
        else:
            sentence = LessonSentence.pick_random(
                LessonSentence.Category.INTRO,
                self.ctx,
            )
            teaching = f"{sentence.get_teaching(self.ctx)} {competence}"
            learning = f"{sentence.get_learning(self.ctx)} {competence}"
            # Match the is_song branch above: VIGEZO VYA UPIMAJI always
            # confirms the learning_activity was done correctly, not the
            # separately-worded indicator_primary text (which didn't end
            # in "kwa usahihi"/"correctly" on its own).
            indicator = f"{learning} {self.TRANSLATIONS['done_correctly_suffix'][lang]}"

        return LessonStep(
            step_name=self.TRANSLATIONS["intro_step_name"][lang],
            duration=timedelta(minutes=duration_minutes),
            teaching_activity=teaching,
            learning_activity=learning,
            assessment_indicator=indicator,
        )

    def _development_step(self, duration_minutes: int, lang: str) -> LessonStep:
        # leading is a Postgres ArrayField(TextField) on SpecificLearningActivity
        leading_text = ", ".join(self.sla.leading) if self.sla.leading else ""

        return LessonStep(
            step_name=self.TRANSLATIONS["development_step_name"][lang],
            duration=timedelta(minutes=duration_minutes),
            teaching_activity=f"{leading_text} {self.sla.name}",
            learning_activity=self.sla.name,
            # VIGEZO VYA UPIMAJI just confirms the learning_activity above
            # happened correctly - not the muhtasari's own assessment
            # criteria text, which describes something different (what
            # mastery looks like, not "was this activity carried out").
            assessment_indicator=(
                f"{self.sla.name} {self.TRANSLATIONS['done_correctly_suffix'][lang]}"
            ),
        )

    def _reinforcement_step(self, lang: str, duration_minutes: int) -> LessonStep:
        sentence = LessonSentence.pick_random(
            LessonSentence.Category.DEVELOPMENT,
            self.ctx,
        )

        learning_activity = f"{sentence.get_learning(self.ctx)} {self.sla.name}"

        return LessonStep(
            step_name=self.TRANSLATIONS["reinforcement_step_name"][lang],
            duration=timedelta(minutes=duration_minutes),
            teaching_activity=f"{sentence.get_teaching(self.ctx)} {self.sla.name}",
            learning_activity=learning_activity,
            # Confirms the learning_activity above happened correctly,
            # rather than just restating it under a different label (the
            # previous indicator_secondary-based phrasing).
            assessment_indicator=(
                f"{learning_activity} {self.TRANSLATIONS['done_correctly_suffix'][lang]}"
            ),
        )

    def _conclusion_step(self, lang: str, duration_minutes: int) -> LessonStep:
        sentence = LessonSentence.pick_random(
            LessonSentence.Category.CONCLUSION,
            self.ctx,
        )

        return LessonStep(
            step_name=self.TRANSLATIONS["conclusion_step_name"][lang],
            duration=timedelta(minutes=duration_minutes),
            teaching_activity=sentence.get_teaching(self.ctx),
            learning_activity=sentence.get_learning(self.ctx),
            assessment_indicator=sentence.get_indicator_secondary(self.ctx),
        )

    # ==================================================
    # REFLECTION HELPERS
    # ==================================================

    def _assessment_comment(self, lang: str) -> str:
        if self.managed_count is None:
            return self.TRANSLATIONS["assessment_unknown"][lang].format(
                total=self.attended.total,
                activity=self.sla.learning_activity.name,
            )

        return self.TRANSLATIONS["assessment_known"][lang].format(
            count=self.managed_count,
            total=self.attended.total,
            activity=self.sla.learning_activity.name,
        )

    def _reflection_comment(self, lang: str) -> str:
        sentence = LessonSentence.pick_random(
            LessonSentence.Category.REFLECTION,
            self.ctx,
        )
        return sentence.get_reflection(self.ctx)

    def _next_plan_comment(self, lang: str) -> str:
        if self.repeat_next:
            return self.TRANSLATIONS["next_plan_repeat"][lang]

        sentence = LessonSentence.pick_random(
            LessonSentence.Category.REFLECTION,
            self.ctx,
        )
        return sentence.get_reflection_comment(self.ctx)