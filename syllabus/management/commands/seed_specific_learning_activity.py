# syllabus/management/commands/seed_specific_learning_activity.py

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


CSV_PATH = "syllabus/csv/specific_learning_activity.csv"


class Command(BaseCommand):
    help = "Seed SpecificLearningActivity using FK resolution by name only"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip FK validation and create anyway',
        )
        parser.add_argument(
            '--skip-missing',
            action='store_true',
            help='Skip rows where FK references are missing',
        )

    def parse_subject_version_code(self, code: str):
        """
        Mfano: 2023-JSS007-DRS I
        -> year, subject_code, class_level
        """
        try:
            year, subject_code, class_level = code.split("-", 2)
            # Safisha class_level name (ondoa whitespace za ziada)
            class_level = class_level.strip()
            return int(year), subject_code, class_level
        except ValueError:
            raise ValueError(f"Invalid subject_version_code format: {code}")

    def handle(self, *args, **options):
        force = options['force']
        skip_missing = options['skip_missing']
        
        with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            skipped = 0
            errors = 0
            
            with transaction.atomic():
                for row in reader:
                    try:
                        # 1️⃣ Resolve SubjectVersion
                        year, subject_code, class_level_name = self.parse_subject_version_code(
                            row["subject_version_code"]
                        )

                        syllabus_version = SyllabusVersion.objects.get(year=year)
                        subject = Subject.objects.get(code=subject_code)
                        
                        # Safisha class_level_name kwa kuondoa whitespace
                        class_level_name = class_level_name.strip()
                        
                        try:
                            class_level = ClassLevel.objects.get(name=class_level_name)
                        except ClassLevel.DoesNotExist:
                            # Jaribu variant zingine
                            variants = [
                                class_level_name,
                                class_level_name.replace(" ", ""),
                                class_level_name.upper(),
                            ]
                            for variant in variants:
                                try:
                                    class_level = ClassLevel.objects.get(name=variant)
                                    self.stdout.write(f"⚠️  Found class level using variant: '{variant}'")
                                    break
                                except ClassLevel.DoesNotExist:
                                    continue
                            else:
                                raise ClassLevel.DoesNotExist(
                                    f"ClassLevel '{class_level_name}' not found"
                                )

                        subject_version = SubjectVersion.objects.get(
                            syllabus_version=syllabus_version,
                            subject=subject,
                            class_level=class_level,
                        )

                        # 2️⃣ Resolve MainCompetence
                        main_competence_name = row["main_competence_name"].strip()
                        try:
                            main_competence = MainCompetence.objects.get(
                                subject_version=subject_version,
                                name=main_competence_name,
                            )
                        except MainCompetence.DoesNotExist:
                            if force:
                                # Ukiwa na --force, unda MainCompetence mpya
                                main_competence, created = MainCompetence.objects.get_or_create(
                                    subject_version=subject_version,
                                    name=main_competence_name,
                                    defaults={'description': ''}
                                )
                                self.stdout.write(f"⚠️  Created missing MainCompetence: {main_competence_name}")
                            elif skip_missing:
                                self.stdout.write(
                                    self.style.WARNING(f"⏭️ Skipping row - MainCompetence not found: {main_competence_name}")
                                )
                                skipped += 1
                                continue
                            else:
                                raise

                        # 3️⃣ Resolve SpecificCompetence
                        specific_competence_name = row["specific_competence_name"].strip()
                        try:
                            specific_competence = SpecificCompetence.objects.get(
                                main_competence=main_competence,
                                name=specific_competence_name,
                            )
                        except SpecificCompetence.DoesNotExist:
                            if force:
                                # Ukiwa na --force, unda SpecificCompetence mpya
                                specific_competence, created = SpecificCompetence.objects.get_or_create(
                                    main_competence=main_competence,
                                    name=specific_competence_name,
                                    defaults={'description': ''}
                                )
                                self.stdout.write(f"⚠️  Created missing SpecificCompetence: {specific_competence_name}")
                            elif skip_missing:
                                self.stdout.write(
                                    self.style.WARNING(f"⏭️ Skipping row - SpecificCompetence not found: {specific_competence_name}")
                                )
                                skipped += 1
                                continue
                            else:
                                raise

                        # 4️⃣ Resolve LearningActivity
                        learning_activity_name = row["learning_activity_name"].strip()
                        try:
                            learning_activity = LearningActivity.objects.get(
                                specific_competence=specific_competence,
                                name=learning_activity_name,
                            )
                        except LearningActivity.DoesNotExist:
                            if force:
                                # Ukiwa na --force, unda LearningActivity mpya
                                learning_activity, created = LearningActivity.objects.get_or_create(
                                    specific_competence=specific_competence,
                                    name=learning_activity_name,
                                )
                                self.stdout.write(f"⚠️  Created missing LearningActivity: {learning_activity_name}")
                            elif skip_missing:
                                self.stdout.write(
                                    self.style.WARNING(f"⏭️ Skipping row - LearningActivity not found: {learning_activity_name}")
                                )
                                skipped += 1
                                continue
                            else:
                                raise

                        # 5️⃣ Create / Update SpecificLearningActivity
                        sla_name = row["sla_name"].strip()
                        
                        # Clean up period field - convert to integer, handle empty values
                        periods_str = row.get("sla_periods", "").strip()
                        periods = 1  # default
                        if periods_str:
                            try:
                                periods = int(periods_str)
                            except ValueError:
                                self.stdout.write(f"⚠️  Invalid period value '{periods_str}', using default 1")
                        
                        # Handle empty references
                        references = row.get("sla_references", "").strip()
                        if not references:
                            references = None
                        
                        # Handle empty leading field
                        leading = row.get("sla_leading", "").strip()
                        if not leading:
                            leading = None
                        
                        sla, created = SpecificLearningActivity.objects.update_or_create(
                            learning_activity=learning_activity,
                            name=sla_name,
                            defaults={
                                'method': row.get("sla_method", "").strip(),
                                'leading': leading,
                                'assessment_criteria': row.get("sla_assessment_criteria", "").strip(),
                                'teaching_aids': row.get("sla_teaching_aids", "").strip(),
                                'references': references,
                                'periods': periods,
                            }
                        )

                        count += 1
                        if created:
                            self.stdout.write(f"✅ Created SLA: {sla_name[:50]}...")
                        else:
                            self.stdout.write(f"📝 Updated SLA: {sla_name[:50]}...")

                    except Exception as e:
                        errors += 1
                        self.stdout.write(
                            self.style.ERROR(f"❌ Error on row {count+skipped+errors}: {str(e)[:100]}")
                        )
                        if not skip_missing and not force:
                            raise

            self.stdout.write(self.style.SUCCESS(
                f"\n📊 Summary:\n"
                f"  ✅ Created/Updated: {count}\n"
                f"  ⏭️  Skipped: {skipped}\n"
                f"  ❌ Errors: {errors}\n"
                f"  📄 Total rows processed: {count + skipped + errors}"
            ))