# jamiikazini/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from kiini.admin import jamiikazini_admin
from django.shortcuts import redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response


schema_view = get_schema_view(
    openapi.Info(
        title="Jamiikazini API",
        default_version='v1',
        description="API documentation for Jamiikazini platform",
        contact=openapi.Contact(email="support@jamiikazini.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny] if settings.DEBUG else [permissions.IsAdminUser],
)


@api_view(['GET'])
def api_home(request):
    return Response({
        "message": "Karibu Jamiikazini 🌍",
        "status": "success",
        "version": "v1.0",
        "description": "API ya huduma za kijamii, biashara, elimu, afya, na zaidi kwa Afrika Mashariki."
    })


urlpatterns = [
    path('', api_home, name='api-home'),

    path('_nested_admin/', include('nested_admin.urls')),
    path('admin/', admin.site.urls),
    path('api/v1/', include('jamiikazini.api_urls')),
]


# Swagger & ReDoc only visible in DEBUG
if settings.DEBUG:
    urlpatterns += [
        path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    ]
    # Serve uploaded media (product images, etc.) locally - in production this
    # is handled by the storage backend/CDN (django-storages), not Django itself.
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "jamiikazini.views.error_views.custom_404_view"
handler403 = "jamiikazini.views.error_views.custom_403_view"
handler500 = "jamiikazini.views.error_views.custom_500_view"
