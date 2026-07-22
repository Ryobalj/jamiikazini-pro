# jamiikazini/settings/gov_api_config.py 

import os

# Helper to load gov API config per country and authority
def load_gov_api_config(prefix, fields):
    return {
        field.lower(): os.getenv(f"{prefix}_{field}") for field in fields
    }

# Field keys to load for each API
STANDARD_FIELDS = ["API_URL", "API_KEY"]

# TANZANIA
TZ_NIDA = load_gov_api_config("TZ_NIDA", STANDARD_FIELDS)
TZ_TRA_DRIVER = load_gov_api_config("TZ_TRA_DRIVER", STANDARD_FIELDS)
TZ_TRA_BUSINESS = load_gov_api_config("TZ_TRA_BUSINESS", STANDARD_FIELDS)
TZ_TRA_VEHICLE = load_gov_api_config("TZ_TRA_VEHICLE", STANDARD_FIELDS)
TZ_BRELA = load_gov_api_config("TZ_BRELA", STANDARD_FIELDS)
TZ_LATRA = load_gov_api_config("TZ_LATRA", STANDARD_FIELDS)
TZ_NACTE = load_gov_api_config("TZ_NACTE", STANDARD_FIELDS)
TZ_NHIF = load_gov_api_config("TZ_NHIF", STANDARD_FIELDS)

# KENYA
KE_NRB = load_gov_api_config("KE_NRB", STANDARD_FIELDS)
KE_NTSA = load_gov_api_config("KE_NTSA", STANDARD_FIELDS)
KE_BRS = load_gov_api_config("KE_BRS", STANDARD_FIELDS)
KE_KNEC = load_gov_api_config("KE_KNEC", STANDARD_FIELDS)
KE_NHIF = load_gov_api_config("KE_NHIF", STANDARD_FIELDS)

# UGANDA
UG_NIRA = load_gov_api_config("UG_NIRA", STANDARD_FIELDS)
UG_URSB = load_gov_api_config("UG_URSB", STANDARD_FIELDS)
UG_URA_DRIVER = load_gov_api_config("UG_URA_DRIVER", STANDARD_FIELDS)
UG_TRANSPORT = load_gov_api_config("UG_TRANSPORT", STANDARD_FIELDS)
UG_NHIS = load_gov_api_config("UG_NHIS", STANDARD_FIELDS)
UG_UNEB = load_gov_api_config("UG_UNEB", STANDARD_FIELDS)

# RWANDA
RW_NIDA = load_gov_api_config("RW_NIDA", STANDARD_FIELDS)
RW_RDB = load_gov_api_config("RW_RDB", STANDARD_FIELDS)
RW_RNP_DRIVER = load_gov_api_config("RW_RNP_DRIVER", STANDARD_FIELDS)
RW_RURA = load_gov_api_config("RW_RURA", STANDARD_FIELDS)  # transport operator permits
RW_REB = load_gov_api_config("RW_REB", STANDARD_FIELDS)
RW_RSSB = load_gov_api_config("RW_RSSB", STANDARD_FIELDS)

# BURUNDI
BI_ONI = load_gov_api_config("BI_ONI", STANDARD_FIELDS)
BI_API = load_gov_api_config("BI_API", STANDARD_FIELDS)
BI_DRIVER = load_gov_api_config("BI_DRIVER", STANDARD_FIELDS)
BI_TRANSPORT = load_gov_api_config("BI_TRANSPORT", STANDARD_FIELDS)
BI_EDU = load_gov_api_config("BI_EDU", STANDARD_FIELDS)
BI_HEALTH = load_gov_api_config("BI_HEALTH", STANDARD_FIELDS)

# SOUTH SUDAN
SS_NIA = load_gov_api_config("SS_NIA", STANDARD_FIELDS)
SS_TRADE = load_gov_api_config("SS_TRADE", STANDARD_FIELDS)
SS_DRIVER = load_gov_api_config("SS_DRIVER", STANDARD_FIELDS)
SS_TRANSPORT = load_gov_api_config("SS_TRANSPORT", STANDARD_FIELDS)
SS_EDU = load_gov_api_config("SS_EDU", STANDARD_FIELDS)
SS_HEALTH = load_gov_api_config("SS_HEALTH", STANDARD_FIELDS)