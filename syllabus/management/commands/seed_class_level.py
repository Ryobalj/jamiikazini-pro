# syllabus/management/commands/seed_class_level.py

import csv
from django.core.management.base import BaseCommand
from syllabus.models.class_level import ClassLevel

CSV_PATH = "syllabus/csv/class_level.csv"

class Command(BaseCommand):
    help = "Seed ClassLevel from CSV"

    def handle(self, *args, **options):
        with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for position, row in enumerate(reader, start=1):
                name = row.get('class_level_name') or row.get('name')
                description = row.get('class_level_description') or row.get('description')

                if not name:
                    self.stdout.write(self.style.WARNING("Skipped a row with no name"))
                    continue

                # update_or_create ili kuepuka duplicates. "order" hufuata
                # mpangilio wa safu mlalo (row order) kwenye CSV hii - hivyo
                # kuongeza darasa jipya (mfano DRS I/II) kabla ya lililopo
                # kunarekebisha automatiki mpangilio wa yote badala ya
                # kuhitaji fix ya mkono kila mara.
                class_level, created = ClassLevel.objects.update_or_create(
                    name=name.strip(),
                    defaults={
                        "description": description.strip() if description else "",
                        "order": position,
                    }
                )
                count += 1
                self.stdout.write(f"{'Created' if created else 'Updated'}: {class_level} (order={position})")

            self.stdout.write(self.style.SUCCESS(f"Total seeded: {count}"))