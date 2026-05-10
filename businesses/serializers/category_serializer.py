# businesses/serializers/category_serializer.py

from rest_framework import serializers
from businesses.models.category import BusinessCategory


class BusinessCategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        help_text="Jina la aina ya biashara (mf. Migahawa, Usafiri, Afya)."
    )
    slug = serializers.SlugField(
        help_text="Slug ya aina ya biashara kwa matumizi ya URL (mf. migahawa)."
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Maelezo mafupi kuhusu aina hii ya biashara."
    )

    class Meta:
        model = BusinessCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_slug(self, value):
        qs = BusinessCategory.objects.filter(slug=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Slug hii tayari inatumika.")
        return value