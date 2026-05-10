# kiini/helpers/institution.py

def get_institution_by_domain(domain):
    from kiini.models import Institution  # ← import ndani ya function
    try:
        return Institution.objects.get(domain=domain)
    except Institution.DoesNotExist:
        return None