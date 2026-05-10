import csv
from django.core.management.base import BaseCommand
from syllabus.models.subject import Subject

CSV_PATH = "syllabus/csv/subject.csv"


class Command(BaseCommand):
    help = "Seed Subjects from CSV file"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        try:
            with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    name = row.get("name").strip()
                    code = row.get("code").strip()
                    description = row.get("description", "").strip()
                    periods = row.get("periods_per_week")

                    try:
                        periods = int(periods)
                    except (TypeError, ValueError):
                        periods = 1

                    subject, created = Subject.objects.update_or_create(
                        code=code,
                        defaults={
                            "name": name,
                            "description": description or None,
                            "periods_per_week": periods,
                        }
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Created: {subject.name} ({subject.code})"))
                    else:
                        updated_count += 1
                        self.stdout.write(self.style.WARNING(f"Updated: {subject.name} ({subject.code})"))

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"CSV file not found: {CSV_PATH}"))
            return

        self.stdout.write(self.style.SUCCESS(
            f"\nSeeding completed → Created: {created_count}, Updated: {updated_count}"
        ))