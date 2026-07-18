# businesses/serializers/product_category_serializer.py

from rest_framework import serializers
from businesses.models.product_category import ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        help_text="Jina la aina ya bidhaa (mf. Vyakula, Vinywaji, Nguo)."
    )
    slug = serializers.SlugField(
        help_text="Slug ya aina ya bidhaa kwa matumizi ya URL (mf. vyakula)."
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Maelezo mafupi kuhusu aina hii ya bidhaa."
    )
    parent_name = serializers.CharField(read_only=True)

    class Meta:
        model = ProductCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "parent_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_slug(self, value):
        qs = ProductCategory.objects.filter(slug=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Slug hii tayari inatumika.")
        return value
