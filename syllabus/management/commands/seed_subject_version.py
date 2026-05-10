import csv
from django.core.management.base import BaseCommand
from syllabus.models.subject import Subject
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.class_level import ClassLevel

CSV_PATH = "syllabus/csv/subject_version.csv"


class Command(BaseCommand):
    help = "Seed SubjectVersion from CSV file"

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        try:
            with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    syllabus_year = row.get("syllabus_year")
                    subject_code = row.get("subject_code")
                    class_level_name = row.get("class_level_name")
                    is_english = row.get("is_english", "0")
                    is_awali = row.get("is_awali", "0")

                    # -----------------------------
                    # BASIC VALIDATION
                    # -----------------------------
                    if not (syllabus_year and subject_code and class_level_name):
                        self.stderr.write(
                            self.style.ERROR(f"Invalid row skipped: {row}")
                        )
                        skipped_count += 1
                        continue

                    try:
                        syllabus_year = int(syllabus_year)
                        is_english = bool(int(is_english))
                        is_awali = bool(int(is_awali))
                    except ValueError:
                        self.stderr.write(
                            self.style.ERROR(f"Invalid numeric values: {row}")
                        )
                        skipped_count += 1
                        continue

                    # -----------------------------
                    # FK LOOKUPS
                    # -----------------------------
                    try:
                        syllabus_version = SyllabusVersion.objects.get(year=syllabus_year)
                        subject = Subject.objects.get(code=subject_code)
                        class_level = ClassLevel.objects.get(name=class_level_name)
                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(
                                f"FK not found (year={syllabus_year}, "
                                f"subject={subject_code}, class={class_level_name}) → {e}"
                            )
                        )
                        skipped_count += 1
                        continue

                    # -----------------------------
                    # CREATE SUBJECT VERSION
                    # -----------------------------
                    obj, created = SubjectVersion.objects.get_or_create(
                        syllabus_version=syllabus_version,
                        subject=subject,
                        class_level=class_level,
                        defaults={
                            "is_english": is_english,
                            "is_awali": is_awali,
                        },
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Created: {subject.code} | {class_level.name} | {syllabus_year}"
                            )
                        )
                    else:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipped (exists): {subject.code} | {class_level.name} | {syllabus_year}"
                            )
                        )

        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(f"CSV file not found: {CSV_PATH}")
            )
            return

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeding completed → Created: {created_count}, Skipped: {skipped_count}"
        ))