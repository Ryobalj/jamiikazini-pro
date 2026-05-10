from django.http import HttpResponseForbidden
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

class InstitutionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        from kiini.models import Institution  # ← lazy import

        host = request.get_host().split(':')[0]
        path = request.path

        # Exempt certain paths
        for exempt_path in getattr(settings, "INSTITUTION_REQUIRED_URLS_EXEMPT", []):
            if path.startswith(exempt_path):
                request.institution = None
                return None

        # Testing mode fallback
        if getattr(settings, 'TESTING', False):
            request.institution = Institution.objects.first()
            return None

        # Allow local dev
        if settings.DEBUG and host in ['127.0.0.1', 'localhost']:
            request.institution = None
            return None

        # Handle root domain
        if host == settings.CENTRAL_DOMAIN:
            request.institution = None
            return None

        # Extract subdomain
        parts = host.split('.')
        if len(parts) < 2:
            logger.warning(f"[InstitutionMiddleware] Invalid domain: {host}")
            return HttpResponseForbidden("Invalid domain.")

        subdomain = parts[0]

        # Reserved or invalid subdomain
        if subdomain in ['www', 'api'] or subdomain.isdigit():
            return HttpResponseForbidden("Reserved or invalid subdomain.")

        # Fetch institution (with cache)
        institution = cache.get(f"institution:{subdomain}")
        if not institution:
            try:
                institution = Institution.objects.get(domain=subdomain)
                cache.set(f"institution:{subdomain}", institution, timeout=300)
            except Institution.DoesNotExist:
                if request.user.is_authenticated and request.user.role == 'ADMIN':
                    logger.info(f"[InstitutionMiddleware] Admin user '{request.user.email}' bypassed institution restriction.")
                    request.institution = None
                    return None

                logger.warning(f"[InstitutionMiddleware] No institution for subdomain '{subdomain}'")
                return HttpResponseForbidden("Invalid institution.")

        request.institution = institution
        logger.info(f"[InstitutionMiddleware] Subdomain '{subdomain}' mapped to institution '{institution.name}'")

        return None