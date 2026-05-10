# payments/gateways/__init__.py

from payments.gateways.registry import register_gateway
from payments.gateways.pawapay.client import PawaPayGateway
from payments.gateways.stripe.client import StripeGateway
from payments.gateways.flutterwave.client import FlutterwaveGateway

# Register all gateways
register_gateway(PawaPayGateway())
register_gateway(StripeGateway())
register_gateway(FlutterwaveGateway())

# Optional convenience exports
from payments.gateways.registry import get_gateway, all_gateways

__all__ = ["get_gateway", "all_gateways"]