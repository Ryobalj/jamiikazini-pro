# payments/gateways/registry.py

from typing import Dict, Type
from .base import BaseGateway

_REGISTRY: Dict[str, BaseGateway] = {}


def register_gateway(gateway: BaseGateway):
    _REGISTRY[gateway.name] = gateway


def get_gateway(name: str) -> BaseGateway:
    key = (name or "").lower()
    if key not in _REGISTRY:
        raise ValueError(f"Gateway '{name}' not registered")
    return _REGISTRY[key]


def all_gateways() -> Dict[str, BaseGateway]:
    return dict(_REGISTRY)