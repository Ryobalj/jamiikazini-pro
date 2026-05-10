# syllabus/management/commands/seed_syllabus_version.py

import csv
from django.core.management.base import BaseCommand
from syllabus.models.syllabus_version import SyllabusVersion

CSV_PATH = "syllabus/csv/syllabus_version.csv"

class Command(BaseCommand):
    help = "Seed SyllabusVersion from CSV"

    def handle(self, *args, **options):
        with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                year = int(row['year'])
                evaluation_aid = row.get('evaluation_aid', '').strip()
                is_current = bool(int(row.get('is_current', 0)))

                syllabus, created = SyllabusVersion.objects.update_or_create(
                    year=year,
                    defaults={
                        "evaluation_aid": evaluation_aid,
                        "is_current": is_current
                    }
                )
                count += 1
                self.stdout.write(f"{'Created' if created else 'Updated'}: {syllabus}")

            self.stdout.write(self.style.SUCCESS(f"Total seeded: {count}"))