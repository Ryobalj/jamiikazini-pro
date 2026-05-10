
# python kiini/scripts/reset_database.py

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jamiikazini.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from kiini.models.institution import Institution, InstitutionType, Department

def reset_database():
    print(">>> Clearing all related data...")

    # Order matters due to ForeignKey dependencies
    Department.objects.all().delete()
    Institution.objects.all().delete()
    InstitutionType.objects.all().delete()
    get_user_model().objects.all().delete()

    print(">>> Database reset complete.")

if __name__ == "__main__":
    reset_database()