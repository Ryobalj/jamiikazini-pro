# payments/gateways/__init__.py

import logging

from payments.gateways.registry import register_gateway
from payments.gateways.pawapay.client import PawaPayGateway
from payments.gateways.stripe.client import StripeGateway
from payments.gateways.flutterwave.client import FlutterwaveGateway

logger = logging.getLogger(__name__)

# Register all gateways. Gateway isiyoweza kuanzishwa (mfano key ya API haipo
# kwenye dev/staging) inarukwa kwa onyo — badala ya kuvunja app nzima wakati wa
# import. Itakosekana tu ikitumika (get_gateway) ambako hushughulikiwa kwa usalama.
for _gateway_cls in (PawaPayGateway, StripeGateway, FlutterwaveGateway):
    try:
        register_gateway(_gateway_cls())
    except Exception as _exc:
        logger.warning("Payment gateway %s haijasajiliwa: %s", _gateway_cls.__name__, _exc)

# Optional convenience exports
from payments.gateways.registry import get_gateway, all_gateways

__all__ = ["get_gateway", "all_gateways"]