# syllabus/management/commands/seed_exam_formats.py

import glob
import json
from django.core.management.base import BaseCommand

from syllabus.models.class_level import ClassLevel
from syllabus.models.exam_format import ExamFormat, ExamFormatSection, ExamFormatSlot
from syllabus.models.subject import Subject

# One JSON file per real exam format supplied over time (see
# syllabus/fixtures/exam_formats/README or the plan doc for the schema).
FIXTURE_GLOB = "syllabus/fixtures/exam_formats/*.json"


class Command(BaseCommand):
    help = (
        "Seed ExamFormat + sections + slots from JSON fixtures "
        "(syllabus/fixtures/exam_formats/*.json - one file per real exam "
        "format supplied as a structure reference)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture", type=str, default=None,
            help="Seed only this one JSON file, instead of every syllabus/fixtures/exam_formats/*.json file.",
        )

    def handle(self, *args, **options):
        files = [options["fixture"]] if options["fixture"] else sorted(glob.glob(FIXTURE_GLOB))
        if not files:
            self.stdout.write(self.style.WARNING(f"No files matched {FIXTURE_GLOB}"))
            return

        for path in files:
            with open(path, encoding="utf-8") as f:
                spec = json.load(f)
            self._seed_one(path, spec)

    def _seed_one(self, path, spec):
        subject = None
        if spec.get("subject_code"):
            subject = Subject.objects.filter(code=spec["subject_code"]).first()
            if not subject:
                self.stdout.write(self.style.WARNING(
                    f"{path}: subject_code {spec['subject_code']!r} not found - leaving subject blank."
                ))

        class_level = None
        if spec.get("class_level_name"):
            class_level = ClassLevel.objects.filter(name=spec["class_level_name"]).first()
            if not class_level:
                self.stdout.write(self.style.WARNING(
                    f"{path}: class_level_name {spec['class_level_name']!r} not found - leaving class_level blank."
                ))

        exam_format, created = ExamFormat.objects.update_or_create(
            name=spec["name"],
            defaults=dict(
                paper_type=spec["paper_type"],
                subject=subject,
                class_level=class_level,
                time_allowed_minutes=spec.get("time_allowed_minutes"),
                instructions=spec.get("instructions", ""),
                is_active=True,
            ),
        )
        exam_format.sections.all().delete()  # rebuild sections/slots fresh each time, format is small

        for section_spec in spec.get("sections", []):
            section = ExamFormatSection.objects.create(
                exam_format=exam_format,
                name=section_spec["name"],
                order=section_spec.get("order", 1),
            )
            for slot_spec in section_spec.get("slots", []):
                ExamFormatSlot.objects.create(
                    section=section,
                    order=slot_spec.get("order", 1),
                    question_type=slot_spec["question_type"],
                    difficulty=slot_spec.get("difficulty", "medium"),
                    count=slot_spec["count"],
                    marks_per_item=slot_spec.get("marks_per_item", 1),
                )

        exam_format.recompute_total_marks()
        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"✅ {verb}: {exam_format.name} ({exam_format.sections.count()} sections, {exam_format.total_marks} marks)"
        ))
