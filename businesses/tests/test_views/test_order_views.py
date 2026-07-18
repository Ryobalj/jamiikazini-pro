import pytest
from rest_framework import status
from rest_framework.test import APIClient
from businesses.models.order import Order, OrderItem
from decimal import Decimal

pytestmark = pytest.mark.django_db


class TestOrderViewSet:

    @pytest.fixture
    def setup(self, business_factory, product_factory, service_factory, user_factory):
        provider = user_factory(role="PROVIDER")
        client = user_factory(role="CLIENT")
        client.is_identity_verified = True
        client.is_phone_verified = True
        client.save(update_fields=["is_identity_verified", "is_phone_verified"])
        # Order payment inatokea kupitia JamiiWallet - hakikisha client ana salio la kutosha.
        client.wallet.balance = Decimal("1000.00")
        client.wallet.save(update_fields=["balance"])
        business = business_factory(owner=provider, is_verified=True)
        product = product_factory(business=business, price=Decimal("100.00"))
        service = service_factory(business=business, price=Decimal("50.00"))
        return {
            "provider": provider,
            "client": client,
            "business": business,
            "product": product,
            "service": service
        }

    def get_url(self, business_id=None, order_id=None, product_slug=None):
        # Flat orders API: /api/v1/businesses/orders/
        base = "/api/v1/orders/"
        return base if not order_id else f"{base}{order_id}/"

    def test_create_order(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["client"])
        url = self.get_url(setup["business"].id, product_slug=setup["product"].slug)
        payload = {
            "business": setup["business"].id,
            "notes": "Deliver early",
            "items": [
                {"product": setup["product"].id, "quantity": 2, "unit_price": "100.00"},
                {"service": setup["service"].id, "quantity": 1, "unit_price": "50.00"}
            ]
        }
        response = client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total_amount"] == "250.00"
        assert len(response.data["items"]) == 2

    def test_retrieve_order(self, setup):
        order = Order.objects.create(client=setup["client"], business=setup["business"], total_amount=Decimal("100.00"))
        OrderItem.objects.create(order=order, product=setup["product"], quantity=1, unit_price=Decimal("100.00"))
        client = APIClient()
        client.force_authenticate(user=setup["client"])
        url = self.get_url(setup["business"].id, order.id, product_slug=setup["product"].slug)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(order.id)

    def test_list_orders_as_provider(self, setup):
        Order.objects.create(client=setup["client"], business=setup["business"], total_amount=Decimal("100.00"))
        client = APIClient()
        client.force_authenticate(user=setup["provider"])
        url = self.get_url(setup["business"].id, product_slug=setup["product"].slug)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_patch_order_by_provider(self, setup):
        order = Order.objects.create(client=setup["client"], business=setup["business"], total_amount=Decimal("100.00"))
        OrderItem.objects.create(order=order, product=setup["product"], quantity=1, unit_price=Decimal("100.00"))
        client = APIClient()
        client.force_authenticate(user=setup["provider"])
        url = self.get_url(setup["business"].id, order.id, product_slug=setup["product"].slug)
        response = client.patch(url, {"notes": "Received"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["notes"] == "Received"

    def test_delete_order_by_owner(self, setup):
        order = Order.objects.create(client=setup["client"], business=setup["business"], total_amount=Decimal("100.00"))
        client = APIClient()
        client.force_authenticate(user=setup["client"])
        url = self.get_url(setup["business"].id, order.id, product_slug=setup["product"].slug)
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_forbidden_delete_by_random_user(self, setup, user_factory):
        order = Order.objects.create(client=setup["client"], business=setup["business"], total_amount=Decimal("100.00"))
        intruder = user_factory(email="hacker@jamii.com")
        client = APIClient()
        client.force_authenticate(user=intruder)
        url = self.get_url(setup["business"].id, order.id, product_slug=setup["product"].slug)
        response = client.delete(url)
        # isolation ya filter: random user haoni order (404)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_unauthenticated_user_blocked(self, setup):
        order = Order.objects.create(client=setup["client"], business=setup["business"], total_amount=Decimal("100.00"))
        url = self.get_url(setup["business"].id, order.id, product_slug=setup["product"].slug)
        response = APIClient().get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_validation_fails_without_items(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["client"])
        url = self.get_url(setup["business"].id, product_slug=setup["product"].slug)
        payload = {
            "business": setup["business"].id,
            "notes": "Empty order",
            "items": []
        }
        response = client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Order lazima iwe na angalau item moja." in str(response.data)
