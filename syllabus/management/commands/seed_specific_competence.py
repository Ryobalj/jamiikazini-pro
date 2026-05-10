import csv
from django.core.management.base import BaseCommand
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel

CSV_PATH = "syllabus/csv/specific_competence.csv"


class Command(BaseCommand):
    help = "Seed SpecificCompetence from a single CSV file"

    def parse_subject_version_code(self, code: str):
        """
        Example code: 2023-JSS007-DRS I
        Returns: year, subject_code, class_level_name
        """
        try:
            year, subject_code, class_level = code.split("-", 2)
            return int(year), subject_code, class_level
        except ValueError:
            raise ValueError(f"Invalid subject_version_code format: {code}")

    def handle(self, *args, **options):
        with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0

            for row in reader:
                try:
                    year, subject_code, class_level_name = self.parse_subject_version_code(
                        row["subject_version_code"]
                    )

                    syllabus_version = SyllabusVersion.objects.get(year=year)
                    subject = Subject.objects.get(code=subject_code)
                    class_level = ClassLevel.objects.get(name=class_level_name)

                    subject_version = SubjectVersion.objects.get(
                        syllabus_version=syllabus_version,
                        subject=subject,
                        class_level=class_level,
                    )

                    main_competence = MainCompetence.objects.get(
                        subject_version=subject_version,
                        name=row["main_competence_name"],
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Skipping row {row} → {e}")
                    )
                    continue

                specific, created = SpecificCompetence.objects.update_or_create(
                    main_competence=main_competence,
                    name=row["specific_competence_name"],
                )

                count += 1
                self.stdout.write(
                    f"{'Created' if created else 'Updated'}: {specific.name}"
                )

            self.stdout.write(
                self.style.SUCCESS(f"✅ Total SpecificCompetences seeded: {count}")
            )