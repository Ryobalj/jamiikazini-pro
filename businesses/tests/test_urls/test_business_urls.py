import pytest
from django.urls import reverse, resolve
from businesses.views.business_views import BusinessViewSet


@pytest.mark.django_db
def test_business_list_url():
    """Hakikisha business-list inapatikana na inaelekeza kwenye BusinessViewSet."""
    url = reverse("businesses:businesses-list")  # DRF DefaultRouter huunda jina hili
    resolved = resolve(url)
    assert resolved.func.cls == BusinessViewSet


@pytest.mark.django_db
def test_business_detail_url(business_factory):
    """Hakikisha business-detail inapatikana na inaelekeza kwenye BusinessViewSet."""
    business = business_factory()
    url = reverse("businesses:businesses-detail", kwargs={"pk": business.pk})
    resolved = resolve(url)
    assert resolved.func.cls == BusinessViewSet


@pytest.mark.django_db
def test_business_stats_url(business_factory):
    """Hakikisha business-stats inapatikana na inaelekeza kwenye BusinessViewSet."""
    business = business_factory()
    url = reverse("businesses:businesses-stats", kwargs={"pk": business.pk})
    resolved = resolve(url)
    assert resolved.func.cls == BusinessViewSet