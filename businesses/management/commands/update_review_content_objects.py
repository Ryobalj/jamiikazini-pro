from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from businesses.models.review import Review
from businesses.models.business import Business
from businesses.models.product import Product
from businesses.models.service import Service

class Command(BaseCommand):
    help = 'Update content_type and object_id for existing reviews'

    def handle(self, *args, **kwargs):
        updated_count = 0
        for review in Review.objects.filter(content_type__isnull=True):
            if review.business:
                review.content_type = ContentType.objects.get_for_model(Business)
                review.object_id = review.business.pk
            elif review.product:
                review.content_type = ContentType.objects.get_for_model(Product)
                review.object_id = review.product.pk
            elif review.service:
                review.content_type = ContentType.objects.get_for_model(Service)
                review.object_id = review.service.pk
            else:
                self.stdout.write(f"Review {review.pk} has no related business/product/service")
                continue
            review.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated {updated_count} reviews."))