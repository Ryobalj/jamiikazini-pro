# security/views/auth_log.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from accounts.models import LoginHistory
from accounts.serializers import LoginHistorySerializer

class LoginHistoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class LoginHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LoginHistoryPagination

    def get(self, request):
        user = request.user
        is_admin = user.role == 'ADMIN'

        target_user_id = request.query_params.get('user_id')
        was_successful = request.query_params.get('was_successful')
        date = request.query_params.get('date')
        ip_address = request.query_params.get('ip_address')
        user_agent = request.query_params.get('user_agent')

        if is_admin and target_user_id:
            queryset = LoginHistory.objects.filter(user_id=target_user_id)
        else:
            queryset = LoginHistory.objects.filter(user=user)

        if was_successful is not None:
            queryset = queryset.filter(was_successful=(was_successful.lower() == 'true'))

        if date:
            try:
                parsed_date = parse_date(date)
                if not parsed_date:
                    raise ValidationError("Invalid date format. Use YYYY-MM-DD.")
                queryset = queryset.filter(login_time__date=parsed_date)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)

        if user_agent:
            queryset = queryset.filter(user_agent__icontains=user_agent)

        queryset = queryset.order_by('-login_time')

        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = LoginHistorySerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)

    def delete(self, request):
        user = request.user
        if user.role != 'ADMIN':
            return Response({"detail": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)

        target_user_id = request.query_params.get('user_id')

        if target_user_id:
            # Delete login histories for specific user
            deleted_count, _ = LoginHistory.objects.filter(user_id=target_user_id).delete()
        else:
            # Delete all login histories (use with care)
            deleted_count, _ = LoginHistory.objects.all().delete()

        return Response({"detail": f"Deleted {deleted_count} login history records."}, status=status.HTTP_200_OK)