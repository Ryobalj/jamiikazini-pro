# syllabus/management/commands/seed_lesson_sentence.py

import csv
from django.core.management.base import BaseCommand
from syllabus.models.lesson_sentence import LessonSentence

CSV_PATH = "syllabus/csv/lesson_sentence.csv"


def to_bool(value, default="0"):
    """
    Convert CSV value to boolean safely.
    Accepts: '0', '1', '', None
    """
    try:
        return bool(int((value or default).strip()))
    except (ValueError, AttributeError):
        return False


def clean(value):
    """
    Safely clean CSV text fields.
    """
    return (value or "").strip()


class Command(BaseCommand):
    help = "Seed Lesson Sentences from CSV file"

    def handle(self, *args, **options):
        created_count = 0

        try:
            with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for index, row in enumerate(reader, start=1):
                    category = clean(row.get("category"))
                    language = clean(row.get("language")).lower() or "sw"

                    # ---- flags ----
                    is_awali = to_bool(row.get("is_awali"), "0")
                    is_active = to_bool(row.get("is_active"), "1")

                    # ---- sw fields ----
                    teaching_sw = clean(row.get("teaching_sw"))
                    learning_sw = clean(row.get("learning_sw"))
                    indicator_primary_sw = clean(row.get("indicator_primary_sw"))
                    indicator_secondary_sw = clean(row.get("indicator_secondary_sw"))
                    reflection_sw = clean(row.get("reflection_sw"))
                    reflection_comment_sw = clean(row.get("reflection_comment_sw"))

                    # ---- en fields ----
                    teaching_en = clean(row.get("teaching_en"))
                    learning_en = clean(row.get("learning_en"))
                    indicator_primary_en = clean(row.get("indicator_primary_en"))
                    indicator_secondary_en = clean(row.get("indicator_secondary_en"))
                    reflection_en = clean(row.get("reflection_en"))
                    reflection_comment_en = clean(row.get("reflection_comment_en"))

                    # ---- enforce language purity ----
                    if language == "sw":
                        teaching_en = ""
                        learning_en = ""
                        indicator_primary_en = ""
                        indicator_secondary_en = ""
                        reflection_en = ""
                        reflection_comment_en = ""

                    elif language == "en":
                        teaching_sw = ""
                        learning_sw = ""
                        indicator_primary_sw = ""
                        indicator_secondary_sw = ""
                        reflection_sw = ""
                        reflection_comment_sw = ""

                    # ---- create record ----
                    sentence = LessonSentence.objects.create(
                        category=category,
                        language=language,
                        is_awali=is_awali,
                        is_active=is_active,

                        teaching_sw=teaching_sw,
                        learning_sw=learning_sw,
                        indicator_primary_sw=indicator_primary_sw,
                        indicator_secondary_sw=indicator_secondary_sw,

                        teaching_en=teaching_en,
                        learning_en=learning_en,
                        indicator_primary_en=indicator_primary_en,
                        indicator_secondary_en=indicator_secondary_en,

                        reflection_sw=reflection_sw,
                        reflection_comment_sw=reflection_comment_sw,
                        reflection_en=reflection_en,
                        reflection_comment_en=reflection_comment_en,
                    )

                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{index}. Created [{sentence.category}] ({sentence.language})"
                        )
                    )

        except FileNotFoundError:
            self.stderr.write(
                self.style.ERROR(f"CSV file not found: {CSV_PATH}")
            )
            return

        self.stdout.write(self.style.SUCCESS(
            f"\nLessonSentence seeding completed → Created: {created_count}"
        ))