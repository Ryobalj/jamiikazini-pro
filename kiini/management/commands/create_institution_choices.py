# kiini/management/commands/create_institution_choices.py

from django.core.management.base import BaseCommand
from kiini.models.institution_tier import InstitutionTier
from kiini.models.institution_type import InstitutionType

class Command(BaseCommand):
    help = 'Create default institution tiers and types'

    def handle(self, *args, **options):
        # Create Tiers
        tiers = [
            ('MICRO', 'Micro Enterprise'),
            ('SMALL', 'Small Enterprise'),
            ('MEDIUM', 'Medium Enterprise'),
            ('LARGE', 'Large Enterprise'),
            ('ENTERPRISE', 'Corporate / Enterprise'),
        ]
        
        for value, label in tiers:
            tier, created = InstitutionTier.objects.get_or_create(
                name=value,
                defaults={'description': label}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created tier: {label}'))
            else:
                self.stdout.write(f'Tier already exists: {label}')

        # Create Types
        types = [
            ('PRIMARY_SCHOOL', 'Primary School'),
            ('SECONDARY_SCHOOL', 'Secondary School'),
            ('COLLEGE', 'College'),
            ('UNIVERSITY', 'University'),
            ('VTC', 'Vocational Training Center'),
            ('HOSPITAL', 'Hospital'),
            ('HEALTH_CENTER', 'Health Center'),
            ('DISPENSARY', 'Dispensary'),
            ('CLINIC', 'Clinic'),
            ('NGO', 'Non-Governmental Organization'),
            ('CBO', 'Community-Based Organization'),
            ('FBO', 'Faith-Based Organization'),
            ('PRIVATE_COMPANY', 'Private Company'),
            ('PUBLIC_CORPORATION', 'Public Corporation'),
            ('COOPERATIVE', 'Cooperative Society'),
            ('GOVERNMENT_MINISTRY', 'Government Ministry'),
            ('MUNICIPAL_COUNCIL', 'Municipal Council'),
            ('PARASTATAL', 'Parastatal Organization'),
            ('RELIGIOUS_INSTITUTION', 'Religious Institution'),
            ('TRAINING_INSTITUTE', 'Training Institute'),
        ]
        
        for value, label in types:
            inst_type, created = InstitutionType.objects.get_or_create(
                name=value,
                defaults={'description': label}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created type: {label}'))
            else:
                self.stdout.write(f'Type already exists: {label}')