# billpay/helpers/biller_api.py

import logging
import uuid
import requests
from django.conf import settings

from jamiikazini.settings import billpay_api_config as billpay_config_module

logger = logging.getLogger(__name__)


def get_billpay_api_config(config_key):
    return getattr(billpay_config_module, config_key, None)


def purchase(biller, account_number, amount):
    """
    Lipia huduma (LUKU/airtime/DSTV/maji) kupitia mamlaka husika. Production ni
    fail-closed: config ikikosekana au API ikishindwa, tunarudisha FAILED
    badala ya mafanikio ya uongo - sawa kabisa na
    gov_integration/helpers/verification.py::verify_entity. Development/test
    inatumia mock.
    """
    env = getattr(settings, "DJANGO_ENV", "development").lower()
    config = get_billpay_api_config(biller.config_key)

    if config and config.get("api_url") and config.get("api_key"):
        try:
            response = requests.post(
                config["api_url"],
                headers={"Authorization": f"Bearer {config['api_key']}"},
                json={"account_number": account_number, "amount": str(amount)},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Billpay API call failed for {biller.config_key}: {e}")
            if env == "production":
                return {
                    "status": "failed",
                    "error": "Huduma hii haipatikani kwa sasa. Jaribu tena baadaye.",
                }
            # dev/test: endelea kwenye mock hapa chini

    elif env == "production":
        logger.error(f"No billpay config for {biller.config_key} in production.")
        return {
            "status": "failed",
            "error": "Malipo ya huduma hii bado hayajawashwa. Jaribu tena baadaye.",
        }

    return _mock_purchase(biller, account_number)


def _mock_purchase(biller, account_number):
    reference = uuid.uuid4().hex.upper()
    result = {
        "status": "success",
        "external_reference": reference,
        "message": f"Simulated {biller.category} purchase for {account_number}",
    }
    if biller.category == "ELECTRICITY":
        result["token"] = f"MOCK-{uuid.uuid4().hex[:16].upper()}"
    return result
