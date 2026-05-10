# jamiikazini/api_urls.py

from django.urls import path, include
from django.http import JsonResponse
from institutions.views import MyInstitutionsList

def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('security/', include('security.urls')),
    path("institutions/my/", MyInstitutionsList.as_view(), name="my-institutions"),

    path('auth/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('', include(('businesses.urls', 'businesses'), namespace='businesses')),
    path('gov/', include(('gov_integration.urls', 'gov_integration'), namespace='gov_integration')),
    path('jamiiwallet/', include(('jamiiwallet.urls', 'jamiiwallet'), namespace='jamiiwallet')),
    path('kiini/', include(('kiini.urls', 'kiini'), namespace='kiini')),
    path('logistics/', include(('logistics.urls', 'logistics'), namespace='logistics')),
    path('search/', include(('search.urls', 'search'), namespace='search')),
    path('health/', health_check, name='health_check'),
    path('payments/', include(('payments.urls', 'payments'), namespace='payments')),

    # ================================
    # Syllabus API (Base + Nested Routers)
    # ================================
    path('syllabus/', include(('syllabus.urls', 'syllabus'), namespace='syllabus')),
]