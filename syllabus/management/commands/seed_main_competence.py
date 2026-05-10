import csv
from django.db.models import Max
from django.core.management.base import BaseCommand
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel
from syllabus.models.syllabus_version import SyllabusVersion

CSV_PATH = "syllabus/csv/main_competence.csv"

class Command(BaseCommand):
    help = "Seed MainCompetence from CSV with correct order"

    def handle(self, *args, **options):
        with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                parts = row['subject_version_code'].split('-')
                year = int(parts[0])
                subject_code = parts[1]
                class_level_name = "-".join(parts[2:])

                try:
                    syllabus_version = SyllabusVersion.objects.get(year=year)
                    subject = Subject.objects.get(code=subject_code)
                    class_level = ClassLevel.objects.get(name=class_level_name)

                    subject_version = SubjectVersion.objects.get(
                        syllabus_version=syllabus_version,
                        subject=subject,
                        class_level=class_level
                    )

                    # Pata max order ya MainCompetence zilizopo kwa subject_version hii
                    max_order = MainCompetence.objects.filter(
                        subject_version=subject_version
                    ).aggregate(Max('order'))['order__max'] or 0

                    main, created = MainCompetence.objects.update_or_create(
                        subject_version=subject_version,
                        name=row['name'],
                        defaults={"order": max_order + 1}
                    )
                    count += 1
                    self.stdout.write(f"{'Created' if created else 'Updated'}: {main.name} (order={main.order})")

                except SubjectVersion.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f"SubjectVersion not found for {row['subject_version_code']}"
                    ))

            self.stdout.write(self.style.SUCCESS(f"Total seeded: {count}"))