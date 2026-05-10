# payments/apps.py
from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    name = "payments"

    def ready(self):
        # triggers registry import
        from payments.gateways import __init__  # noqa