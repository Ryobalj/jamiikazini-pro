# gov_integration/tasks.py
import requests
from celery import shared_task
from django.utils import timezone
from gov_integration.models import VerificationRequest, ServiceConfig, VerificationLog


@shared_task
def send_verification_request(request_id):
    try:
        v_request = VerificationRequest.objects.select_related('service').get(id=request_id)
        service_type = v_request.service
        institution = v_request.institution

        # Tafuta config ya endpoint hiyo
        config = ServiceConfig.objects.select_related('endpoint').filter(
            endpoint__country=v_request.country,
            endpoint__name__icontains=service_type.name,
            is_enabled=True
        ).first()

        if not config:
            v_request.status = 'FAILED'
            v_request.save()
            VerificationLog.objects.create(
                request=v_request,
                success=False,
                message='Service config not found',
                raw_response=''
            )
            return

        headers = {
            'Authorization': f"Bearer {config.access_token}",
            'Content-Type': 'application/json',
        }

        response = requests.post(
            url=config.endpoint.base_url,
            headers=headers,
            json=v_request.payload,
            timeout=10
        )

        data = response.json()
        v_request.response_data = data
        v_request.status = 'VERIFIED' if response.status_code == 200 else 'FAILED'
        v_request.save()

        VerificationLog.objects.create(
            request=v_request,
            success=(response.status_code == 200),
            message=data.get('message', ''),
            raw_response=str(data)
        )

    except Exception as e:
        VerificationLog.objects.create(
            request_id=request_id,
            success=False,
            message=str(e),
            raw_response=""
        )