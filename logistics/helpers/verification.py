# logistics/helpers/verificatiin.py

from gov_integration.helpers.verification import verify_entity


def verify_nida(national_id_number, user):
    return verify_entity(
        country_code="tz",
        authority_code="nida",
        payload={"national_id_number": national_id_number},
        user=user
    )


def verify_driver_license(license_number, user):
    return verify_entity(
        country_code="tz",
        authority_code="tra_driver",
        payload={"license_number": license_number},
        user=user
    )


def verify_business_license(business_license_number, user):
    return verify_entity(
        country_code="tz",
        authority_code="brela",
        payload={"business_license_number": business_license_number},
        user=user
    )


def verify_latra_license(latra_license_number, user):
    return verify_entity(
        country_code="tz",
        authority_code="latra",
        payload={"latra_license_number": latra_license_number},
        user=user
    )