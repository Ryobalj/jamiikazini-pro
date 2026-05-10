# businesses/views/utils.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from businesses.models import Business

@api_view(["GET"])
def check_domain_availability(request):
    domain = request.GET.get("domain")
    if not domain:
        return Response({"available": False})
    is_taken = Business.objects.filter(website__iexact=domain).exists()
    return Response({"available": not is_taken})