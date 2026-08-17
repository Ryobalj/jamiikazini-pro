from django.utils import translation
from django.conf import settings
from pathlib import Path
import geoip2.database
from django.http import HttpRequest


class GeoLocationLanguageMiddleware:

    geoip_reader = None

    def __init__(self, get_response):
        self.get_response = get_response

        # Load GeoIP database once only
        if not GeoLocationLanguageMiddleware.geoip_reader:
            db_path = Path(settings.GEOIP_PATH) / "GeoLite2-Country.mmdb"

            if db_path.exists():
                GeoLocationLanguageMiddleware.geoip_reader = geoip2.database.Reader(db_path)
            else:
                GeoLocationLanguageMiddleware.geoip_reader = None

    def __call__(self, request: HttpRequest):

        # 0. Respect an explicit language requested by the client (e.g. the
        # frontend's language switcher, sent as Accept-Language) - takes
        # priority over IP-based geolocation guessing.
        accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE")
        if accept_language:
            requested = accept_language.split(",")[0].split("-")[0].strip().lower()
            if requested in dict(settings.LANGUAGES):
                translation.activate(requested)
                request.LANGUAGE_CODE = requested
                response = self.get_response(request)
                translation.deactivate()
                return response

        # 1. Respect user language preference
        if request.user.is_authenticated and hasattr(request.user, "language"):
            translation.activate(request.user.language)
            request.LANGUAGE_CODE = request.user.language
            return self.get_response(request)

        # 2. Detect language from IP
        ip = self.get_client_ip(request)
        language = self.detect_language_from_ip(ip)

        if language:
            translation.activate(language)
            request.LANGUAGE_CODE = language

        response = self.get_response(request)
        translation.deactivate()

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")

    def detect_language_from_ip(self, ip):
        if not GeoLocationLanguageMiddleware.geoip_reader:
            return settings.LANGUAGE_CODE

        try:
            response = GeoLocationLanguageMiddleware.geoip_reader.country(ip)
            country = response.country.iso_code

            mapping = {
                "TZ": "sw",
                "KE": "sw",
                "UG": "en",
                "RW": "fr",
                "BI": "fr",
                "CD": "fr",
            }

            return mapping.get(country, settings.LANGUAGE_CODE)

        except Exception:
            return settings.LANGUAGE_CODE