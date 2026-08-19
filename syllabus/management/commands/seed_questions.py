# syllabus/management/commands/seed_questions.py

import csv
import glob
from django.core.management.base import BaseCommand
from django.db import transaction

from syllabus.models.class_level import ClassLevel
from syllabus.models.learning_activity import LearningActivity
from syllabus.models.main_competence import MainCompetence
from syllabus.models.question import Question
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.subject import Subject
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion

# One CSV per subject (syllabus/csv/questions_<subject>_<year>.csv), same
# convention as sla_*.csv. Without --csv-file, every matching file is
# seeded in one run.
CSV_GLOB = "syllabus/csv/questions_*.csv"


def _parse_pipe_list(value: str) -> list:
    """options (mcq)/word_bank cells: pipe-separated list, e.g.
    'jibu1|jibu2|jibu3'."""
    value = (value or "").strip()
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def _parse_pairs_field(value: str) -> list:
    """options (matching) cells: 'left1::right1||left2::right2||...'
    ('::' separates a pair's left/right, '||' separates pairs) - same
    delimiter convention as exercise_questions on SpecificLearningActivity."""
    value = (value or "").strip()
    if not value:
        return []
    pairs = []
    for chunk in value.split("||"):
        chunk = chunk.strip()
        if not chunk or "::" not in chunk:
            continue
        left, right = chunk.split("::", 1)
        left, right = left.strip(), right.strip()
        if left and right:
            pairs.append({"left": left, "right": right})
    return pairs


class Command(BaseCommand):
    help = (
        "Seed Question (quiz/test/examination bank) using FK resolution by "
        "name only. Without --csv-file, seeds every "
        "syllabus/csv/questions_*.csv file found (one file per subject)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv-file", type=str, default=None,
            help="Seed only this one CSV file, instead of every syllabus/csv/questions_*.csv file.",
        )
        parser.add_argument(
            "--force", action="store_true", help="Skip FK validation and create anyway",
        )
        parser.add_argument(
            "--skip-missing", action="store_true", help="Skip rows where FK references are missing",
        )

    def parse_subject_version_code(self, code: str):
        try:
            year, subject_code, class_level = code.split("-", 2)
            return int(year), subject_code, class_level.strip()
        except ValueError:
            raise ValueError(f"Invalid subject_version_code format: {code}")

    def handle(self, *args, **options):
        force = options["force"]
        skip_missing = options["skip_missing"]

        if options["csv_file"]:
            files = [options["csv_file"]]
        else:
            files = sorted(glob.glob(CSV_GLOB))
            if not files:
                self.stdout.write(self.style.WARNING(f"No files matched {CSV_GLOB}"))
                return

        grand_created = grand_updated = grand_skipped = grand_errors = 0
        for path in files:
            self.stdout.write(f"\n=== Seeding {path} ===")
            created, updated, skipped, errors = self._seed_file(path, force, skip_missing)
            grand_created += created
            grand_updated += updated
            grand_skipped += skipped
            grand_errors += errors

        self.stdout.write(self.style.SUCCESS(
            f"\nTotal → Created: {grand_created}  Updated: {grand_updated}  "
            f"Skipped: {grand_skipped}  Errors: {grand_errors}"
        ))

    def _seed_file(self, path, force, skip_missing):
        created = updated = skipped = errors = 0
        with open(path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row_num, row in enumerate(reader, start=2):
                try:
                    with transaction.atomic():
                        year, subject_code, class_level_name = self.parse_subject_version_code(
                            row["subject_version_code"].strip()
                        )
                        syllabus_version = SyllabusVersion.objects.get(year=year)
                        subject = Subject.objects.get(code=subject_code)
                        class_level = ClassLevel.objects.get(name=class_level_name)
                        subject_version = SubjectVersion.objects.get(
                            syllabus_version=syllabus_version, subject=subject, class_level=class_level,
                        )
                        main_competence = MainCompetence.objects.get(
                            subject_version=subject_version, name=row["main_competence_name"].strip(),
                        )
                        specific_competence = SpecificCompetence.objects.get(
                            main_competence=main_competence, name=row["specific_competence_name"].strip(),
                        )
                        learning_activity = LearningActivity.objects.get(
                            specific_competence=specific_competence, name=row["learning_activity_name"].strip(),
                        )
                except Exception as e:
                    msg = f"Row {row_num}: FK resolution failed - {e}"
                    if skip_missing:
                        self.stdout.write(self.style.WARNING(f"⏭️  {msg}"))
                        skipped += 1
                        continue
                    self.stdout.write(self.style.ERROR(f"❌ {msg}"))
                    errors += 1
                    if not force:
                        continue

                question_type = row["question_type"].strip()
                if question_type == "matching":
                    options = _parse_pairs_field(row.get("options", ""))
                else:
                    options = _parse_pipe_list(row.get("options", ""))
                word_bank = _parse_pipe_list(row.get("word_bank", ""))

                prompt = row["prompt"].strip()
                try:
                    with transaction.atomic():
                        obj, was_created = Question.objects.update_or_create(
                            learning_activity=learning_activity,
                            prompt=prompt,
                            defaults=dict(
                                question_type=question_type,
                                difficulty=row.get("difficulty", "medium").strip() or "medium",
                                options=options,
                                word_bank=word_bank,
                                correct_answer=row["correct_answer"].strip(),
                                solution_steps=row.get("solution_steps", "").strip(),
                                marks=int(row.get("marks") or 1),
                                source=row.get("source", "").strip(),
                                language=row.get("language", "sw").strip() or "sw",
                                is_active=True,
                            ),
                        )
                    if was_created:
                        self.stdout.write(f"✅ Created: {prompt[:50]}...")
                        created += 1
                    else:
                        self.stdout.write(f"♻️  Updated: {prompt[:50]}...")
                        updated += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Row {row_num}: {e}"))
                    errors += 1

        self.stdout.write(
            f"  Created: {created}  Updated: {updated}  Skipped: {skipped}  Errors: {errors}"
        )
        return created, updated, skipped, errors
