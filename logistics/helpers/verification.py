# logistics/helpers/verificatiin.py
#
# Mamlaka za uthibitisho ni tofauti kwa kila nchi (angalia
# gov_integration.helpers.verification kwa _BY_COUNTRY dicts kamili) -
# country_code lazima ipitishwe na anayeita, si "tz" iliyowekwa ngumu.

from gov_integration.helpers.verification import (
    verify_entity,
    national_id_authority_for,
    driver_license_authority_for,
    business_license_authority_for,
    transport_license_authority_for,
)


def verify_nida(national_id_number, user, country_code="tz"):
    return verify_entity(
        country_code=country_code,
        authority_code=national_id_authority_for(country_code),
        payload={"national_id_number": national_id_number},
        user=user
    )


def verify_driver_license(license_number, user, country_code="tz"):
    return verify_entity(
        country_code=country_code,
        authority_code=driver_license_authority_for(country_code),
        payload={"license_number": license_number},
        user=user
    )


def verify_business_license(business_license_number, user, country_code="tz"):
    return verify_entity(
        country_code=country_code,
        authority_code=business_license_authority_for(country_code),
        payload={"business_license_number": business_license_number},
        user=user
    )


def verify_latra_license(latra_license_number, user, country_code="tz"):
    return verify_entity(
        country_code=country_code,
        authority_code=transport_license_authority_for(country_code),
        payload={"latra_license_number": latra_license_number},
        user=user
    )