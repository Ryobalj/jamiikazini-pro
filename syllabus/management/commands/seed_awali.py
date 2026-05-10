# syllabus/management/commands/seed_awali.py

import csv
from django.core.management.base import BaseCommand
from django.db import transaction

from syllabus.models.learning_activity import LearningActivity
from syllabus.models.specific_learning_activity import SpecificLearningActivity
from syllabus.models.specific_competence import SpecificCompetence
from syllabus.models.main_competence import MainCompetence
from syllabus.models.subject_version import SubjectVersion
from syllabus.models.syllabus_version import SyllabusVersion
from syllabus.models.subject import Subject
from syllabus.models.class_level import ClassLevel


class Command(BaseCommand):
    help = "Seed SpecificLearningActivity data for Awali from CSV"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='syllabus/csv/awali.csv',
            help='Path to CSV file (default: syllabus/csv/awali.csv)',
        )

    def parse_subject_version_code(self, code: str):
        """
        Parse subject version code (e.g., 2023-JSS057-Awali)
        Returns: year, subject_code, class_level
        """
        try:
            year, subject_code, class_level = code.split("-", 2)
            return int(year), subject_code, class_level.strip()
        except ValueError:
            raise ValueError(f"Invalid subject_version_code format: {code}")

    def handle(self, *args, **options):
        csv_path = options['csv_file']
        
        with open(csv_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            total_rows = 0
            created_count = 0
            updated_count = 0
            error_count = 0
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, 1):
                    total_rows += 1
                    try:
                        # Debug: Show current row
                        self.stdout.write(f"📄 Processing row {row_num}: {row['subject_version_code']}")
                        
                        # 1️⃣ Get or create all parent objects
                        year, subject_code, class_level_name = self.parse_subject_version_code(
                            row["subject_version_code"]
                        )

                        # SyllabusVersion
                        syllabus_version, sv_created = SyllabusVersion.objects.get_or_create(
                            year=year,
                            defaults={'name': f'Syllabus {year}'}
                        )
                        if sv_created:
                            self.stdout.write(f"   ✅ Created SyllabusVersion: {year}")

                        # Subject
                        subject, sub_created = Subject.objects.get_or_create(
                            code=subject_code,
                            defaults={'name': f'Subject {subject_code}'}
                        )
                        if sub_created:
                            self.stdout.write(f"   ✅ Created Subject: {subject_code}")

                        # ClassLevel
                        class_level, cl_created = ClassLevel.objects.get_or_create(
                            name=class_level_name,
                            defaults={'description': class_level_name}
                        )
                        if cl_created:
                            self.stdout.write(f"   ✅ Created ClassLevel: {class_level_name}")

                        # SubjectVersion
                        subject_version, sv_created = SubjectVersion.objects.get_or_create(
                            syllabus_version=syllabus_version,
                            subject=subject,
                            class_level=class_level,
                            defaults={'version': '1.0', 'is_awali': True}
                        )
                        if sv_created:
                            self.stdout.write(f"   ✅ Created SubjectVersion: {subject_code}-{class_level_name}")

                        # 2️⃣ MainCompetence (NO description field - only name)
                        main_competence_name = row["main_competence_name"].strip()
                        main_competence, mc_created = MainCompetence.objects.get_or_create(
                            subject_version=subject_version,
                            name=main_competence_name
                        )
                        if mc_created:
                            self.stdout.write(f"   ✅ Created MainCompetence: {main_competence_name[:50]}...")

                        # 3️⃣ SpecificCompetence (NO description field - only name)
                        specific_competence_name = row["specific_competence_name"].strip()
                        specific_competence, sc_created = SpecificCompetence.objects.get_or_create(
                            main_competence=main_competence,
                            name=specific_competence_name
                        )
                        if sc_created:
                            self.stdout.write(f"   ✅ Created SpecificCompetence: {specific_competence_name[:50]}...")

                        # 4️⃣ LearningActivity
                        learning_activity_name = row["learning_activity_name"].strip()
                        learning_activity, la_created = LearningActivity.objects.get_or_create(
                            specific_competence=specific_competence,
                            name=learning_activity_name
                        )
                        if la_created:
                            self.stdout.write(f"   ✅ Created LearningActivity: {learning_activity_name[:50]}...")

                        # 5️⃣ SpecificLearningActivity
                        sla_name = row["sla_name"].strip()
                        
                        # Handle periods
                        periods = 1
                        periods_str = row.get("sla_periods", "").strip()
                        if periods_str:
                            try:
                                periods = int(periods_str)
                            except ValueError:
                                self.stdout.write(f"   ⚠️  Invalid period value '{periods_str}', using default 1")
                        
                        # Handle optional fields
                        references = row.get("sla_references", "").strip() or None
                        leading = row.get("sla_leading", "").strip() or None
                        method = row.get("sla_method", "").strip() or None

                        # Get or create SpecificLearningActivity
                        sla, sla_created = SpecificLearningActivity.objects.get_or_create(
                            learning_activity=learning_activity,
                            name=sla_name,
                            defaults={
                                'method': method,
                                'leading': leading,
                                'assessment_criteria': row.get("sla_assessment_criteria", "").strip(),
                                'teaching_aids': row.get("sla_teaching_aids", "").strip(),
                                'references': references,
                                'periods': periods,
                            }
                        )

                        # If exists, update it
                        if not sla_created:
                            sla.method = method
                            sla.leading = leading
                            sla.assessment_criteria = row.get("sla_assessment_criteria", "").strip()
                            sla.teaching_aids = row.get("sla_teaching_aids", "").strip()
                            sla.references = references
                            sla.periods = periods
                            sla.save()
                            updated_count += 1
                            self.stdout.write(f"   📝 Updated SLA: {sla_name[:50]}...")
                        else:
                            created_count += 1
                            self.stdout.write(f"   ✅ Created SLA: {sla_name[:50]}...")

                        self.stdout.write(f"   ✓ Row {row_num} completed successfully\n")

                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f"   ❌ Error on row {row_num}: {str(e)}")
                        )
                        self.stdout.write(f"   Row data: {dict(row)}")
                        # Continue with next row instead of stopping
                        continue

            self.stdout.write(self.style.SUCCESS(
                f"\n{'='*60}\n"
                f"📊 SEEDING SUMMARY\n"
                f"{'='*60}\n"
                f"  📄 Total rows in CSV: {total_rows}\n"
                f"  ✅ New records created: {created_count}\n"
                f"  📝 Existing records updated: {updated_count}\n"
                f"  ❌ Errors: {error_count}\n"
                f"  ✓ Success rate: {(created_count + updated_count)/total_rows*100:.1f}%\n"
                f"{'='*60}"
            ))