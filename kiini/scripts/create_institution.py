# python manage.py shell
# from kiini.scripts import create_institution, create_admin_user, create_staff
# create_institution.run()
# create_admin_user.run()
# create_staff.run()

from kiini.models.institution import Institution
from django.contrib.gis.geos import Point

def run():
    if Institution.objects.exists():
        print("Institution already exists.")
        return

    institution = Institution.objects.create(
        name="Jamii Shule",
        domain="jamii-shule",
        phone_number="+255712345678",
        email="info@jamii-shule.ac.tz",
        location=Point(39.2806, -6.8161),  # Example: Dar es Salaam
    )

    print(f"Institution created: {institution.name}") 