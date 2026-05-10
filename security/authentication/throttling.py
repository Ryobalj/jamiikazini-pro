# security/authentication/throttling.py

from rest_framework.throttling import UserRateThrottle

class JamiiThrottle(UserRateThrottle):
    scope = "security_authentication_throttle"