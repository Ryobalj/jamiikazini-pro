# businesses/views/review_views.py

from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from businesses.models.review import Review
from businesses.serializers.review_serializer import ReviewSerializer
from businesses.validators.review_validators import validate_unique_review


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet ya kudhibiti Reviews:
    - List/Retrieve: Reviews zilizopitishwa tu.
    - Create: User anachukuliwa moja kwa moja, review ni is_approved=False.
    - Update/Delete: User pekee anayeweza kubadilisha review yake.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Toa reviews sahihi kulingana na action."""
        if self.action in ["list", "retrieve"]:
            # List & Retrieve: reviews zilizopitishwa pekee
            queryset = Review.objects.filter(is_approved=True)

            target_type = self.request.query_params.get("target_type")
            target_id = self.request.query_params.get("target_id")
            if target_type and target_id:
                filter_kwargs = {f"{target_type}_id": target_id}
                queryset = queryset.filter(**filter_kwargs)

            return queryset
        else:
            # Kwa update/destroy: Toa reviews zote (user pekee anayeweza kubadilisha review yake)
            return Review.objects.all()

    def perform_create(self, serializer):
        """Hakikisha user anachukuliwa moja kwa moja, review ni is_approved=False,
           na review ni unique."""
        user = self.request.user
        if not user.is_authenticated:
            raise ValidationError({"user": "Lazima uingie kwanza kabla ya kuongeza review."})
        # Hakikisha review ni unique
        validate_unique_review(
            user,
            product=serializer.validated_data.get("product"),
            service=serializer.validated_data.get("service"),
            business=serializer.validated_data.get("business"),
        )
        serializer.save(user=user, is_approved=False)

    def perform_update(self, serializer):
        """Ruhusu mtumiaji pekee kubadilisha review yake."""
        if self.request.user != serializer.instance.user:
            raise PermissionDenied("Huwezi kubadilisha review ambayo si yako.")
        serializer.save()

    def perform_destroy(self, instance):
        """Ruhusu mtumiaji pekee kufuta review yake."""
        if self.request.user != instance.user:
            raise PermissionDenied("Huwezi kufuta review ambayo si yako.")
        instance.delete()


class ServiceReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(service_id=self.kwargs["service_pk"], is_approved=True)

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_authenticated:
            raise ValidationError("Lazima uingie kwanza.")
        validate_unique_review(
            user,
            service_id=self.kwargs["service_pk"]
        )
        serializer.save(user=user, service_id=self.kwargs["service_pk"], is_approved=False)

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.user:
            raise PermissionDenied("Huwezi kuhariri review ambayo si yako.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.user:
            raise PermissionDenied("Huwezi kufuta review ambayo si yako.")
        instance.delete()


class ProductReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Rudisha reviews za product husika tu ambazo zimepitishwa."""
        return Review.objects.filter(product_id=self.kwargs["product_pk"], is_approved=True)

    def perform_create(self, serializer):
        """Mteja aongeze review mpya kwa product husika."""
        user = self.request.user
        if not user.is_authenticated:
            raise ValidationError("Lazima uingie kwanza.")
        validate_unique_review(
            user,
            product_id=self.kwargs["product_pk"]
        )
        serializer.save(user=user, product_id=self.kwargs["product_pk"], is_approved=False)

    def perform_update(self, serializer):
        """Ruhusu client pekee kuedit review yake."""
        if self.request.user != serializer.instance.user:
            raise PermissionDenied("Huwezi kuhariri review ambayo si yako.")
        serializer.save()

    def perform_destroy(self, instance):
        """Ruhusu client pekee kufuta review yake."""
        if self.request.user != instance.user:
            raise PermissionDenied("Huwezi kufuta review ambayo si yako.")
        instance.delete()
