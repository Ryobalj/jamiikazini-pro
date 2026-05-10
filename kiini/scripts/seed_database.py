# python kiini/scripts/seed_database.py

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jamiikazini.settings.dev")
django.setup()

from kiini.models.institution import InstitutionType, Institution
from accounts.models import User
from django.contrib.gis.geos import Point

def seed_data():
    print(">>> Seeding initial data...")

    # InstitutionType
    school_type, created = InstitutionType.objects.get_or_create(name="School")
    print(f" - InstitutionType: {school_type.name} (created={created})")

    # Institution
    institution, created = Institution.objects.get_or_create(
        name="Shule ya Mfano",
        defaults={
            "type": school_type,
            "domain": "mfano.jamiikazini.com",
            "location": Point(39.280556, -6.821944),  # Example coords
            "is_active": True
        }
    )
    print(f" - Institution: {institution.name} (created={created})")

    # User - Institution Admin
    admin_user, created = User.objects.get_or_create(
        email="admin@mfano.com",
        defaults={
            "full_name": "Admin Mkuu",
            "role": "INSTITUTION_ADMIN",
            "phone_number": "+255700000000",
            "is_verified": True,
            "is_active": True,
            "institution": institution,
        }
    )
    if created:
        admin_user.set_password("admin12345")
        admin_user.save()

    print(f" - Admin User: {admin_user.email} (created={created})")

    print(">>> Seeding complete.")

if __name__ == "__main__":
    seed_data()