import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.gis.geos import Point
from django.urls import reverse
from businesses.models.product import Product
from businesses.models.business import Business
from businesses.models.product_category import ProductCategory
from kiini.models.institution import Institution
from accounts.models import User


@pytest.mark.django_db
class TestProductViews:

    @pytest.fixture
    def setup_products(self):
        institution = Institution.objects.create(name="Jamii Org", domain="jamii.org")
        owner = User.objects.create_user(
            email="owner@jamii.com",
            password="test123",
            full_name="Owner",
            role='PROVIDER',
            institution=institution
        )
        business = Business.objects.create(
            name="Duka Tech",
            owner=owner,
            institution=institution,
            location=Point(39.2806, -6.8206, srid=4326)
        )

        product1 = Product.objects.create(
            business=business,
            name="Laptop ABC",
            description="Intel Core i5",
            price=1500,
            is_available=True,
            is_featured=True,
            tags=["electronics"],
            slug="laptop-abc",
            language_code="en"
        )

        product2 = Product.objects.create(
            business=business,
            name="Printer XYZ",
            description="Color printer",
            price=500,
            is_available=True,
            is_featured=False,
            tags=["office"],
            slug="printer-xyz",
            language_code="en"
        )

        return {
            "institution": institution,
            "owner": owner,
            "business": business,
            "product1": product1,
            "product2": product2,
        }

    def test_list_products(self, setup_products):
        client = APIClient()
        url = f"/api/v1/businesses/{setup_products['business'].pk}/products/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_retrieve_product(self, setup_products):
        client = APIClient()
        url = f"/api/v1/businesses/{setup_products['business'].pk}/products/{setup_products['product1'].slug}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Laptop ABC"

    def test_featured_products(self, setup_products):
        client = APIClient()
        url = f"/api/v1/businesses/{setup_products['business'].pk}/products/featured/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) == 1
        assert data[0]["name"] == "Laptop ABC"

    def test_search_products(self, setup_products):
        client = APIClient()
        url = f"/api/v1/businesses/{setup_products['business'].pk}/products/search/?q=printer"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get("results", response.data) if isinstance(response.data, dict) else response.data
        assert len(data) == 1
        assert data[0]["name"] == "Printer XYZ"

    def test_search_products_no_query(self, setup_products):
        client = APIClient()
        url = f"/api/v1/businesses/{setup_products['business'].pk}/products/search/"
        response = client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "q" in response.data

    def test_nearby_products_success(self, setup_products):
        client = APIClient()
        url = reverse("businesses:product-nearby-list") + "?lat=-6.8206&lng=39.2806"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_nearby_products_missing_coords(self, setup_products):
        client = APIClient()
        url = reverse("businesses:product-nearby-list")
        response = client.get(url)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_generate_product_url_success(self, setup_products):
        client = APIClient()
        client.force_authenticate(user=setup_products["owner"])
        url = reverse("businesses:generate-product-url", kwargs={"slug": setup_products["product1"].slug})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "url" in response.data
        assert setup_products["product1"].slug in response.data["url"]

    def test_generate_product_url_not_found(self, setup_products):
        client = APIClient()
        client.force_authenticate(user=setup_products["owner"])
        url = reverse("businesses:generate-product-url", kwargs={"slug": "non-existent"})
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_filter_products_by_category(self, setup_products):
        electronics = ProductCategory.objects.create(name="Elektroniki", slug="elektroniki")
        setup_products["product1"].category = electronics
        setup_products["product1"].save(update_fields=["category"])

        client = APIClient()
        url = f"/api/v1/businesses/{setup_products['business'].pk}/products/?category=elektroniki"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Laptop ABC"
        assert response.data[0]["category_name"] == "Elektroniki"

    def test_filter_products_by_unknown_category_returns_empty(self, setup_products):
        client = APIClient()
        url = f"/api/v1/businesses/{setup_products['business'].pk}/products/?category=does-not-exist"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_category_name_is_none_when_uncategorized(self, setup_products):
        client = APIClient()
        url = f"/api/v1/businesses/{setup_products['business'].pk}/products/{setup_products['product2'].slug}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["category"] is None
        assert response.data["category_name"] is None