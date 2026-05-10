# security/helpers/security.py

from helpers.request import get_client_ip, get_user_agent
from accounts.models import LoginHistory

class BaseLoginLogger:
    @staticmethod
    def log_success(request, user):
        LoginHistory.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            was_successful=True
        )

    @staticmethod
    def log_failure(request, user=None):
        LoginHistory.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            was_successful=False
        )
