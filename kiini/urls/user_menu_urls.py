# kiini/urls/user_menu_urls.py

from django.urls import path
from kiini.views.menu_view import UserMenuView, DashboardContextView


urlpatterns = [
    path('user-menu/', UserMenuView.as_view(), name='user-menu'),
    path('dashboard-context/', DashboardContextView.as_view(), name='dashboard-context'),
]