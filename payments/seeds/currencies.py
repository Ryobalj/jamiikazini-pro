# payments/seeds/currencies.py

def seed_currencies(Currency):
    """Ensure all default currencies exist without duplicates."""

    default_currencies = {
        "TZS": "Tanzanian Shilling",
        "KES": "Kenyan Shilling",
        "UGX": "Ugandan Shilling",
        "RWF": "Rwandan Franc",
        "BIF": "Burundi Franc",
        "SSP": "South Sudanese Pound",
        "USD": "US Dollar",
        "EUR": "Euro",
        "GBP": "British Pound",
        "ZAR": "South African Rand",
    }

    for code in default_currencies.keys():
        Currency.objects.get_or_create(code=code)