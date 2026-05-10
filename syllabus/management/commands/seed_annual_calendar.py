# syllabus/management/commands/seed_annual_calendar.py

import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from syllabus.models.annual_calendar import AnnualCalendar

CSV_PATH = "syllabus/csv/annual_calendar_2026.csv"  # badilisha path kama inahitajika

class Command(BaseCommand):
    help = "Seed AnnualCalendar from CSV"

    def handle(self, *args, **options):
        with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                # convert dates from string to date
                def parse_date(d):
                    try:
                        return datetime.strptime(d, "%Y-%m-%d").date()
                    except:
                        return None

                calendar, created = AnnualCalendar.objects.update_or_create(
                    institute=row['institute'],
                    year=int(row['year']),
                    defaults={
                        "total_learning_days": int(row['total_learning_days']),
                        "term_start_month": row['term_start_month'],
                        "term_start_week": int(row['term_start_week']),
                        "term_start_date": parse_date(row['term_start_date']),
                        "midterm_break_start_month": row['midterm_break_start_month'],
                        "midterm_break_start_week": int(row['midterm_break_start_week']),
                        "midterm_break_start_date": parse_date(row['midterm_break_start_date']),
                        "midterm_start_month": row['midterm_start_month'],
                        "midterm_start_week": int(row['midterm_start_week']),
                        "midterm_start_date": parse_date(row['midterm_start_date']),
                        "term_break_start_month": row['term_break_start_month'],
                        "term_break_start_week": int(row['term_break_start_week']),
                        "term_break_start_date": parse_date(row['term_break_start_date']),
                        "annual_startmonth": row['annual_startmonth'],
                        "annual_startweek": int(row['annual_startweek']),
                        "annual_startdate": parse_date(row['annual_startdate']),
                        "midannual_break_start_month": row['midannual_break_start_month'],
                        "midannual_break_start_week": int(row['midannual_break_start_week']),
                        "midannual_break_start_date": parse_date(row['midannual_break_start_date']),
                        "midannual_start_month": row['midannual_start_month'],
                        "midannual_start_week": int(row['midannual_start_week']),
                        "midannual_start_date": parse_date(row['midannual_start_date']),
                        "annual_break_start_month": row['annual_break_start_month'],
                        "annual_break_start_week": int(row['annual_break_start_week']),
                        "annual_break_start_date": parse_date(row['annual_break_start_date']),
                        "status": bool(int(row['status'])),
                    }
                )
                count += 1
                self.stdout.write(f"{'Created' if created else 'Updated'}: {calendar}")

            self.stdout.write(self.style.SUCCESS(f"Total seeded: {count}"))