import pytest
from rest_framework.reverse import reverse
from django.contrib.gis.geos import Point

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
def test_categories_route(api_client, category_factory):
    category_factory(name="Afya", slug="afya")
    url = reverse("businesses:business-categories-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1
    assert response.json()[0]["slug"] == "afya"


def test_orders_routes(api_client, order_factory, product_factory):
    order = order_factory()
    product = order.business.products.first() or product_factory(business=order.business)
    url = reverse("businesses:product-orders-list",
                  kwargs={"business_pk": order.business.pk, "product_slug": product.slug})
    response = api_client.get(url)
    assert response.status_code in [200, 403, 401]


def test_bookings_routes(api_client, booking_factory, branch_factory):
    booking = booking_factory()
    branch = branch_factory(business=booking.service.business)
    url = reverse("businesses:service-bookings-list",
                  kwargs={"business_pk": booking.service.business.pk,
                          "branch_pk": branch.pk,
                          "service_pk": booking.service.pk})
    response = api_client.get(url)
    assert response.status_code in [200, 403, 401]


def test_product_public_nearby(api_client, product_factory, branch_factory):
    branch = branch_factory(location=Point(39.278, -6.792))
    product = product_factory(business=branch.business)

    response = api_client.get("/api/v1/businesses/products/nearby-list/", {
        "lat": -6.792,
        "lng": 39.278,
        "radius": 10
    })

    assert response.status_code in [200, 404]  # 404 kama hakuna product zinazotimia


def test_product_generate_url(api_client, product_factory):
    product = product_factory()
    url = reverse("businesses:generate-product-url", kwargs={"slug": product.slug})
    response = api_client.get(url)
    assert response.status_code in [200, 403, 401]


def test_nested_branch_routes(api_client, branch_factory):
    branch = branch_factory()
    url = reverse("businesses:business-branches-list", kwargs={"business_pk": branch.business.pk})
    response = api_client.get(url)
    assert response.status_code in [200, 403, 401]


@pytest.mark.django_db
def test_nested_products_routes(api_client, product_factory, branch_factory):
    product = product_factory()
    branch = branch_factory(business=product.business)  # ensure same business

    url = f"/api/v1/businesses/{product.business.id}/branches/{branch.id}/products/"
    response = api_client.get(url)

    assert response.status_code in [200, 403, 401]


@pytest.mark.django_db
def test_nested_services_routes(api_client, branch_factory, service_factory):
    branch = branch_factory()
    service = service_factory(business=branch.business)
    branch.services.add(service)  # link service to branch

    url = f"/api/v1/businesses/{branch.business.id}/branches/{branch.id}/services/"
    response = api_client.get(url)

    assert response.status_code in [200, 403, 401]


@pytest.mark.django_db
def test_product_review_nested(api_client, product_factory, user_factory):
    user = user_factory()
    product = product_factory()
    api_client.force_authenticate(user=user)

    url = f"/api/v1/businesses/{product.business.id}/products/{product.slug}/reviews/"
    payload = {
        "product": str(product.id),
        "rating": 4,
        "content": "Bidhaa bora kabisa!"
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == 201
    assert response.data["rating"] == 4


@pytest.mark.django_db
def test_product_order_nested(api_client, product_factory, user_factory):
    product = product_factory()
    client = user_factory(role="CLIENT")

    order = product.business.orders.create(client=client, total_amount=product.price)
    order.items.create(
        product=product,
        quantity=1,
        unit_price=product.price,
        total_price=product.price
    )

    url = f"/api/v1/businesses/{product.business.id}/products/{product.id}/orders/"
    response = api_client.get(url)

    assert response.status_code in [200, 403, 401]


@pytest.mark.django_db
def test_service_review_nested(api_client, service_factory, branch_factory, user_factory):
    branch = branch_factory()
    service = service_factory(business=branch.business)
    branch.services.add(service)

    user = user_factory()
    review = service.reviews.create(
        user=user,
        rating=5,
        comment="Huduma nzuri sana",
        is_approved=True
    )

    url = f"/api/v1/businesses/{branch.business.id}/branches/{branch.id}/services/{service.id}/reviews/"
    response = api_client.get(url)

    assert response.status_code in [200, 403, 401]


@pytest.mark.django_db
def test_service_booking_nested(api_client, branch_factory, service_factory, booking_factory):
    branch = branch_factory()
    service = service_factory(business=branch.business)
    branch.services.add(service)

    booking_factory(service=service)

    url = reverse("businesses:service-bookings-list", kwargs={
        "business_pk": branch.business.pk,
        "branch_pk": branch.pk,
        "service_pk": service.pk
    })

    response = api_client.get(url)
    assert response.status_code in [200, 403, 401]
