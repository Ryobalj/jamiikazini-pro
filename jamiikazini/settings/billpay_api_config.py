# jamiikazini/settings/billpay_api_config.py
#
# Env-var driven config kwa kila biller, sawa kabisa na gov_api_config.py -
# kuongeza mamlaka/biller mpya ni env vars + rekodi ya Biller, si code mpya.

from jamiikazini.settings.gov_api_config import load_gov_api_config, STANDARD_FIELDS

# TANZANIA
TZ_LUKU = load_gov_api_config("TZ_LUKU", STANDARD_FIELDS)
TZ_AIRTIME = load_gov_api_config("TZ_AIRTIME", STANDARD_FIELDS)
TZ_DSTV = load_gov_api_config("TZ_DSTV", STANDARD_FIELDS)
TZ_WATER = load_gov_api_config("TZ_WATER", STANDARD_FIELDS)

# KENYA
KE_KPLC = load_gov_api_config("KE_KPLC", STANDARD_FIELDS)
KE_AIRTIME = load_gov_api_config("KE_AIRTIME", STANDARD_FIELDS)

# UGANDA
UG_UMEME = load_gov_api_config("UG_UMEME", STANDARD_FIELDS)
UG_AIRTIME = load_gov_api_config("UG_AIRTIME", STANDARD_FIELDS)

# RWANDA
RW_EUCL = load_gov_api_config("RW_EUCL", STANDARD_FIELDS)
RW_AIRTIME = load_gov_api_config("RW_AIRTIME", STANDARD_FIELDS)
