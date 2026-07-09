# search/tests/test_product_search.py

import pytest
from django.conf import settings

# These tests index into a live Elasticsearch cluster; skip when ES is off (local dev).
if not getattr(settings, "ELASTICSEARCH_ENABLED", False):
    pytest.skip("Requires live Elasticsearch (ELASTICSEARCH_ENABLED=False)", allow_module_level=True)

from payments.models.currency import Currency
from rest_framework.test import APITestCase
from django.contrib.gis.geos import Point
from businesses.models import Product, Business, BusinessCategory
from kiini.models import Institution
from search.documents.product_document import ProductDocument
from search.serializers.product_search_serializer import ProductSearchSerializer


class ProductSearchTest(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="Test Institution")

        self.category = BusinessCategory.objects.create(name="Dairy", slug="dairy")

        self.business1 = Business.objects.create(
            name="Near Shop",
            institution=self.institution,
            location=Point(39.2, -6.8)
        )
        self.business2 = Business.objects.create(
            name="Far Shop",
            institution=self.institution,
            location=Point(40.0, -7.5)
        )

        self.product1 = Product.objects.create(
            name="Maziwa",
            slug="maziwa",
            description="Fresh milk",
            type="food",
            price=2000,
            discount_price=1800,
            currency=Currency.objects.get_or_create(code="TZS")[0],
            quantity_in_stock=20,
            unit="Litre",
            is_available=True,
            is_featured=False,
            image="https://example.com/maziwa.jpg",
            tags=["maziwa", "fresh"],
            tax_inclusive=True,
            tax_rate=18,
            external_link=None,
            language_code="sw",
            business=self.business1,
            category=self.category
        )

        self.product2 = Product.objects.create(
            name="Yoghurt",
            slug="yoghurt",
            description="Fruit yoghurt",
            type="food",
            price=2500,
            discount_price=None,
            currency=Currency.objects.get_or_create(code="TZS")[0],
            quantity_in_stock=15,
            unit="Cup",
            is_available=True,
            is_featured=False,
            image="https://example.com/yoghurt.jpg",
            tags=["yoghurt", "fruity"],
            tax_inclusive=False,
            tax_rate=0,
            external_link=None,
            language_code="sw",
            business=self.business2,
            category=self.category
        )

        ProductDocument().update(Product.objects.all())

    def test_product_document_fields(self):
        doc = ProductDocument()
        self.assertEqual(doc.django.model, Product)
        self.assertIn("name", doc._doc_type.mapping)
        self.assertIn("category", doc._doc_type.mapping)

    def test_product_serializer(self):
        serializer = ProductSearchSerializer(instance=self.product1)
        data = serializer.data
        self.assertEqual(data["name"], "Maziwa")
        self.assertEqual(data["category"]["name"], "Dairy")
        self.assertEqual(data["business_name"], "Near Shop")

    def test_basic_search(self):
        url = '/search/products/?q=maziwa&lang=sw'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Maziwa")

    def test_geo_sorted_search(self):
        url = '/search/products/?q=&lat=-6.8&lon=39.2&lang=sw'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['business_name'], "Near Shop")

    def test_pagination(self):
        url = '/search/products/?q=&lang=sw&page=1&page_size=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_by_language(self):
        # Change product2 to another language
        self.product2.language_code = 'en'
        self.product2.save()
        ProductDocument().update(Product.objects.all())

        url = '/search/products/?q=&lang=sw'
        response = self.client.get(url)
        names = [item['name'] for item in response.data['results']]
        self.assertIn("Maziwa", names)
        self.assertNotIn("Yoghurt", names)

    def test_distance_field_present_if_location_provided(self):
        url = '/search/products/?q=&lat=-6.8&lon=39.2&lang=sw'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('distance', response.data['results'][0])