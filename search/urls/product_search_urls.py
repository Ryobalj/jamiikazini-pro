# search/urls/product_search_urls.py

from django.urls import path
from search.views.product_search_view import ProductSearchView

urlpatterns = [
    path('products/', ProductSearchView.as_view(), name='product-search'),
]