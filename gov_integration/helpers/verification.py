# gov_integration/helpers/verification.py

import logging
import requests
from datetime import datetime, timedelta
from django.conf import settings
from jamiikazini.settings import gov_api_config as gov_config_module

logger = logging.getLogger(__name__)


def get_gov_api_config(country_code, authority_code):
    """
    Retrieves the API config dict for given country and authority.
    Example: get_gov_api_config("tz", "nida") returns TZ_NIDA config.
    """
    key = f"{country_code.upper()}_{authority_code.upper()}"
    return getattr(gov_config_module, key, None)


# Mamlaka sahihi ya usajili wa biashara kwa kila nchi (inaendana na majina ya
# key za jamiikazini/settings/gov_api_config.py, mf. TZ_TRA_BUSINESS).
BUSINESS_LICENSE_AUTHORITY_BY_COUNTRY = {
    "TZ": "tra_business",
    "KE": "brs",
    "RW": "rdb",
    "UG": "ursb",
    "BI": "api",     # Agence de Promotion des Investissements -> BI_API
    "SS": "trade",   # Ministry of Trade -> SS_TRADE
}

# Tanzania pekee ina njia mbili tofauti za uthibitisho wa biashara: TIN
# (TRA - mamlaka ya kodi) na namba ya usajili wa BRELA (msajili wa
# makampuni) - ni namba mbili tofauti kabisa, sio sawa. Nchi nyingine bado
# zina mamlaka moja tu iliyounganishwa (angalia BUSINESS_LICENSE_AUTHORITY_BY_COUNTRY
# hapo juu), hivyo id_type inapuuzwa kwao kwa sasa.
TZ_BUSINESS_ID_AUTHORITY_BY_TYPE = {
    "tin": "tra_business",
    "brela": "brela",
}


def business_license_authority_for(country_code, id_type=None):
    """
    Rudisha authority_code sahihi ya usajili wa biashara kwa nchi husika.
    kwa Tanzania, id_type ("tin" au "brela") huchagua kati ya TRA na BRELA -
    nchi nyingine zina mamlaka moja tu, hivyo id_type hazina athari kwao.
    """
    country = (country_code or "").upper()
    if country == "TZ":
        return TZ_BUSINESS_ID_AUTHORITY_BY_TYPE.get((id_type or "tin").lower(), "tra_business")
    return BUSINESS_LICENSE_AUTHORITY_BY_COUNTRY.get(country, "trade")


# Mamlaka sahihi ya kitambulisho cha taifa (NIDA-equivalent) kwa kila nchi.
NATIONAL_ID_AUTHORITY_BY_COUNTRY = {
    "TZ": "nida",
    "KE": "nrb",
    "UG": "nira",
    "RW": "nida",
    "BI": "oni",
    "SS": "nia",
}


def national_id_authority_for(country_code):
    """Rudisha authority_code sahihi ya kitambulisho cha taifa kwa nchi husika."""
    return NATIONAL_ID_AUTHORITY_BY_COUNTRY.get((country_code or "").upper(), "nida")


# Mamlaka sahihi ya leseni ya udereva kwa kila nchi.
DRIVER_LICENSE_AUTHORITY_BY_COUNTRY = {
    "TZ": "tra_driver",
    "KE": "ntsa",
    "UG": "ura_driver",
    "RW": "rnp_driver",
    "BI": "driver",  # -> BI_DRIVER
    "SS": "driver",  # -> SS_DRIVER
}


def driver_license_authority_for(country_code):
    """Rudisha authority_code sahihi ya leseni ya udereva kwa nchi husika."""
    return DRIVER_LICENSE_AUTHORITY_BY_COUNTRY.get((country_code or "").upper(), "driver")


# Mamlaka sahihi ya usajili wa gari (TRA-equivalent) kwa kila nchi - hii ni
# tofauti na usajili wa biashara (BUSINESS_LICENSE_AUTHORITY_BY_COUNTRY):
# inathibitisha namba ya usajili wa GARI mahususi, si biashara/kampuni.
VEHICLE_REGISTRATION_AUTHORITY_BY_COUNTRY = {
    "TZ": "tra_vehicle",
    "KE": "ntsa",
    "UG": "ura_driver",
    "RW": "rnp_driver",
    "BI": "vehicle",   # -> BI_VEHICLE
    "SS": "vehicle",   # -> SS_VEHICLE
}


def vehicle_registration_authority_for(country_code):
    """Rudisha authority_code sahihi ya usajili wa gari kwa nchi husika."""
    return VEHICLE_REGISTRATION_AUTHORITY_BY_COUNTRY.get((country_code or "").upper(), "vehicle")


# Mamlaka sahihi ya leseni ya usafirishaji (LATRA-equivalent) kwa kila nchi.
TRANSPORT_LICENSE_AUTHORITY_BY_COUNTRY = {
    "TZ": "latra",
    "UG": "transport",
    "KE": "ntsa",     # NTSA inasimamia driver na PSV/transport permits zote -> KE_NTSA
    "RW": "rura",     # Rwanda Utilities Regulatory Authority -> RW_RURA
    "BI": "transport",  # -> BI_TRANSPORT
    "SS": "transport",  # -> SS_TRANSPORT
}


def transport_license_authority_for(country_code):
    """Rudisha authority_code sahihi ya leseni ya usafirishaji kwa nchi husika."""
    return TRANSPORT_LICENSE_AUTHORITY_BY_COUNTRY.get((country_code or "").upper(), "transport")


def verify_entity(country_code, authority_code, payload, user=None):
    """
    Generic verification function for any entity using gov_api_config.
    - country_code: e.g. "tz", "ke"
    - authority_code: e.g. "nida", "ntsa"
    - payload: dict to post to external API
    - user: optional, used for logging or future audit trails

    Production ni fail-closed: config ikikosekana au API halisi ikishindikana,
    tunarudisha FAILED badala ya mock ya mafanikio - uthibitisho wa uongo ni
    hatari kuliko kumwambia mtumiaji ajaribu tena baadaye. Mock inaruhusiwa
    development/test pekee.
    """
    env = getattr(settings, "DJANGO_ENV", "development").lower()
    config = get_gov_api_config(country_code, authority_code)

    if config and config.get("api_url") and config.get("api_key"):
        try:
            response = requests.post(
                config["api_url"],
                headers={"Authorization": f"Bearer {config['api_key']}"},
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(
                f"Gov API call failed for {country_code.upper()}_{authority_code.upper()}: {e}"
            )
            if env == "production":
                return {
                    "status": "failed",
                    "verified": False,
                    "error": "Mamlaka husika haipatikani kwa sasa. Jaribu tena baadaye.",
                }
            # dev/test: endelea kwenye mock hapa chini

    elif env == "production":
        logger.error(
            f"No gov API config for {country_code.upper()}_{authority_code.upper()} in production."
        )
        return {
            "status": "failed",
            "verified": False,
            "error": "Uthibitisho wa mamlaka hii bado haujawashwa. Jaribu tena baadaye.",
        }

    # Generic mock fallback (development/test only)
    return mock_response(authority_code, payload)


def mock_response(authority_code, payload):
    """
    Returns mock response based on the type of check being performed.

    Baadhi ya mamlaka (mf. NTSA nchini Kenya) zinahusika na aina kadhaa za
    uthibitisho (leseni ya udereva, usajili wa gari, na kibali cha usafirishaji
    yote chini ya mamlaka moja) - hivyo authority_code pekee haitoshi
    kubainisha aina ya ukaguzi. Tunatumia funguo za payload kubainisha kwanza,
    na authority_code kama nyongeza/fallback pale payload haina utata.
    """
    authority = authority_code.lower()

    if "national_id_number" in payload or authority in ["nida", "nrb", "nira", "oni", "nia"]:
        return {
            "status": "success",
            "message": f"National ID verification successful for {payload.get('national_id_number')}",
            "data": {
                "full_name": "John Doe",
                "date_of_birth": "1990-01-01",
                "gender": "Male",
                "national_id": payload.get("national_id_number"),
            }
        }
    elif "registration_number" in payload or authority in ["tra_vehicle", "vehicle"]:
        return {
            "status": "success",
            "message": f"Vehicle registration verified for {payload.get('registration_number')}",
            "data": {
                "registration_number": payload.get("registration_number"),
                "make_model": "Unknown",
                "registered_owner": "Unknown",
                "registration_status": "Active",
            }
        }
    elif "latra_license_number" in payload or "transport_license_number" in payload or authority in ["latra", "transport"]:
        return {
            "status": "success",
            "message": f"Transport License verified for {payload.get('latra_license_number') or payload.get('transport_license_number')}",
            "data": {
                "operator_name": "Express Transport Ltd",
                "route": "Dar es Salaam - Kigali",
                "vehicle_type": "Coach Bus",
                "valid_until": (datetime.now() + timedelta(days=730)).strftime('%Y-%m-%d'),
                "status": "Active",
            }
        }
    elif "license_number" in payload or authority in ["tra_driver", "rnp_driver", "ntsa", "ura_driver"]:
        return {
            "status": "success",
            "message": f"Driver License verification successful for {payload.get('license_number')}",
            "data": {
                "license_status": "Valid",
                "issued_date": "2020-06-15",
                "expiry_date": "2030-06-15",
                "class": "C1",
                "holder_name": "Jane Doe",
            }
        }
    elif authority == "brela":
        return {
            "status": "success",
            "message": f"BRELA registration verification successful for {payload.get('business_license_number')}",
            "data": {
                "business_name": "ABC Group Ltd",
                "registration_number": payload.get("business_license_number"),
                "certificate_type": "Certificate of Incorporation",
                "registered_date": "2022-03-14",
            }
        }
    elif "business_license_number" in payload or authority in ["tra_business", "brs", "rdb", "ursb", "trade"]:
        return {
            "status": "success",
            "message": f"Business License verification successful for {payload.get('business_license_number')}",
            "data": {
                "business_name": "ABC Group Ltd",
                "license_number": payload.get("business_license_number"),
                "license_valid_until": "2027-08-30",
                "registered_activity": "General Trading",
            }
        }
    # Add more mocks as needed per authority
    return {
        "status": "mock_success",
        "message": f"Mock verification successful for {authority_code.upper()}",
        "data": payload
    }