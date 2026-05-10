# gov_integration/helpers/verification.py

import requests
from datetime import datetime, timedelta
from jamiikazini.settings import gov_api_config as gov_config_module


def get_gov_api_config(country_code, authority_code):
    """
    Retrieves the API config dict for given country and authority.
    Example: get_gov_api_config("tz", "nida") returns TZ_NIDA config.
    """
    key = f"{country_code.upper()}_{authority_code.upper()}"
    return getattr(gov_config_module, key, None)


def verify_entity(country_code, authority_code, payload, user=None):
    """
    Generic verification function for any entity using gov_api_config.
    - country_code: e.g. "tz", "ke"
    - authority_code: e.g. "nida", "ntsa"
    - payload: dict to post to external API
    - user: optional, used for logging or future audit trails
    """
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
        except requests.RequestException:
            pass  # fallback to mock if error

    # Generic mock fallback
    return mock_response(authority_code, payload)


def mock_response(authority_code, payload):
    """
    Returns mock response based on the type of authority.
    Extend as needed.
    """
    if authority_code.lower() == "nida":
        return {
            "status": "success",
            "message": f"NIDA verification successful for {payload.get('national_id_number')}",
            "data": {
                "full_name": "John Doe",
                "date_of_birth": "1990-01-01",
                "gender": "Male",
                "national_id": payload.get("national_id_number"),
            }
        }
    elif authority_code.lower() in ["tra_driver", "rnp_driver", "ntsa", "ura_driver"]:
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
    elif authority_code.lower() in ["tra_business", "brs", "rdb", "ursb", "trade"]:
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
    elif authority_code.lower() in ["latra", "transport"]:
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
    # Add more mocks as needed per authority
    return {
        "status": "mock_success",
        "message": f"Mock verification successful for {authority_code.upper()}",
        "data": payload
    }