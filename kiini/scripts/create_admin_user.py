from django.contrib.auth import get_user_model
from kiini.models.institution import Institution

User = get_user_model()

def run():
    if User.objects.filter(email="admin@jamii-shule.ac.tz").exists():
        print("Admin user already exists.")
        return

    institution = Institution.objects.first()
    if not institution:
        print("No institution found. Run create_institution.py first.")
        return

    user = User.objects.create_user(
        email="admin@jamii-shule.ac.tz",
        full_name="Main Admin",
        password="admin123",
        role="INSTITUTION_ADMIN",
        institution=institution,
        is_verified=True,
        is_staff=True,
    )

    print(f"Admin user created: {user.full_name}")