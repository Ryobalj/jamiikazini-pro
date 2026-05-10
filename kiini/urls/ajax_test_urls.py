# kiini/urls/ajax_test_urls.py

from django.urls import path
from kiini.views.ajax_test_view import ajax_test_page


urlpatterns = [
    path('', ajax_test_page, name='ajax_test'),

]

