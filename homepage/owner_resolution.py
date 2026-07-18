# homepage/owner_resolution.py

from django.contrib.contenttypes.models import ContentType
from django.http import Http404

from homepage.models.home_page import ALLOWED_OWNER_MODELS


def resolve_owner(owner_type: str, owner_id):
    """
    owner_type: 'institution' au 'business'. Rudisha instance husika au
    inua Http404 - hakuna anayeruhusiwa kubahatisha ni owner gani unavyowepo.
    """
    owner_type = (owner_type or '').lower()
    if owner_type not in ALLOWED_OWNER_MODELS:
        raise Http404("Aina ya owner si sahihi (institution au business pekee).")

    if owner_type == 'institution':
        from kiini.models.institution import Institution
        model = Institution
    else:
        from businesses.models.business import Business
        model = Business

    try:
        return model.objects.get(pk=owner_id)
    except model.DoesNotExist:
        raise Http404("Owner haikupatikana.")


def content_type_for(owner_type: str):
    return ContentType.objects.get_for_model(
        _model_for(owner_type)
    )


def _model_for(owner_type: str):
    if owner_type == 'institution':
        from kiini.models.institution import Institution
        return Institution
    from businesses.models.business import Business
    return Business
