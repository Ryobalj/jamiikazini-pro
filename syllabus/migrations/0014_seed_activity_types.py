# syllabus/migrations/0014_seed_activity_types.py
#
# Seeds the fixed built-in list of non-subject activity types (arrival,
# cleaning, assembly, sports, clubs, religion, etc.) used by the master
# timetable feature. Schools needing something not on this list use
# TimetableSlot.custom_label instead.

from django.db import migrations

ACTIVITY_TYPES = [
    dict(
        code="KUWASILI",
        label_sw="Kuwasili kwa Wanafunzi",
        label_en="Student Arrival",
        is_fixed_routine=True,
        is_whole_school=True,
        default_order=1,
    ),
    dict(
        code="MSTARINI_UKAGUZI",
        label_sw="Mstarini na Ukaguzi",
        label_en="Assembly & Inspection",
        is_fixed_routine=True,
        is_whole_school=True,
        default_order=2,
    ),
    dict(
        code="USAFI_MAZINGIRA",
        label_sw="Usafi wa Mazingira",
        label_en="Environmental Cleaning",
        is_fixed_routine=True,
        is_whole_school=True,
        default_order=3,
    ),
    dict(
        code="MICHEZO",
        label_sw="Michezo",
        label_en="Sports",
        is_fixed_routine=False,
        is_whole_school=True,
        default_order=10,
    ),
    dict(
        code="KLABU",
        label_sw="Klabu",
        label_en="Clubs",
        is_fixed_routine=False,
        is_whole_school=True,
        default_order=11,
    ),
    dict(
        code="DINI",
        label_sw="Kipindi cha Dini",
        label_en="Religious Period",
        is_fixed_routine=False,
        is_whole_school=True,
        default_order=12,
    ),
    dict(
        code="ELIMU_KUJITEGEMEA",
        label_sw="Elimu ya Kujitegemea",
        label_en="Self-Reliance Education",
        is_fixed_routine=False,
        is_whole_school=True,
        default_order=13,
    ),
]


def seed_activity_types(apps, schema_editor):
    ActivityType = apps.get_model("syllabus", "ActivityType")
    for spec in ACTIVITY_TYPES:
        ActivityType.objects.get_or_create(code=spec["code"], defaults=spec)


def remove_activity_types(apps, schema_editor):
    ActivityType = apps.get_model("syllabus", "ActivityType")
    ActivityType.objects.filter(code__in=[s["code"] for s in ACTIVITY_TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("syllabus", "0013_activitytype_mastertimetableroster_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_activity_types, remove_activity_types),
    ]
