from kiini.models.staff import StaffProfile
from django.contrib.auth import get_user_model

User = get_user_model()

def run():
    admin = User.objects.filter(role="INSTITUTION_ADMIN").first()
    if not admin:
        print("No admin found. Run create_admin_user.py first.")
        return

    if StaffProfile.objects.exists():
        print("Staff already created.")
        return

    staff_user = User.objects.create_user(
        email="teacher@jamii-shule.ac.tz",
        full_name="Mwl. Jamii",
        password="teach123",
        role="STAFF",
        institution=admin.institution,
        is_verified=True,
    )

    staff = StaffProfile.objects.create(
        user=staff_user,
        department="Teaching"
    )

    print(f"Staff created: {staff}")