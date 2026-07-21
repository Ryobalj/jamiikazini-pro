# businesses/serializers/product_serializer.py

from rest_framework import serializers
from businesses.models.product import Product, ProductType, UnitChoices, LanguageChoices
from businesses.models.product_category import ProductCategory
from businesses.models.product_image import ProductImage
from businesses.serializers.business_serializer import BusinessDetailSerializer
from payments.models.currency import Currency


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "caption", "order"]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(help_text="Jina la bidhaa.")
    slug = serializers.SlugField(
        help_text="Slug kwa matumizi ya URL (mf. sabuni-asili).", 
        required=False
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Maelezo mafupi kuhusu bidhaa hii."
    )

    type = serializers.ChoiceField(
        choices=ProductType.choices,
        help_text="Aina ya bidhaa: physical (ya kawaida), digital (kidijitali), au service (huduma)."
    )
    price = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        help_text="Bei ya bidhaa."
    )
    discount_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Bei punguzo (ikijazwa, ndiyo itakayotumika badala ya bei ya kawaida)."
    )

    # ✅ CURRENCY - ForeignKey Field
    currency = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.filter(is_active=True),
        default=Currency.get_by_code,
        help_text="Sarafu inayotumika (mf. TZS, USD)."
    )
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)

    category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.filter(is_active=True),
        required=False,
        allow_null=True,
        help_text="Aina/kabati la bidhaa hii (mf. Vyakula, Vinywaji, Nguo)."
    )
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    quantity_in_stock = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        help_text="Idadi ya bidhaa zilizopo stoo (inaweza kuwa na desimali kwa vipimo kama kg, l, m)."
    )
    
    # ✅ UNIT - ChoiceField
    unit = serializers.ChoiceField(
        choices=UnitChoices.choices,
        default=UnitChoices.PIECES,
        help_text="Kipimo cha bidhaa."
    )
    unit_display = serializers.SerializerMethodField(read_only=True)

    is_available = serializers.BooleanField(
        default=True,
        help_text="Inaonesha kama bidhaa inapatikana."
    )
    is_featured = serializers.BooleanField(
        default=False,
        help_text="Inaonesha kama bidhaa ni maalum/iliyopendekezwa."
    )

    image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Picha kuu ya bidhaa."
    )
    images = ProductImageSerializer(many=True, read_only=True)

    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_null=True,
        help_text="Maneno muhimu au vitambulisho vya bidhaa (mf. asili, ngozi, afya)."
    )

    tax_inclusive = serializers.BooleanField(
        default=True,
        help_text="Je, bei inajumuisha VAT?"
    )
    tax_rate = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Kiwango cha VAT kwa asilimia."
    )

    external_link = serializers.URLField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Kiungo cha manunuzi au tovuti ya nje (ikihitajika)."
    )
    digital_file = serializers.FileField(
        required=False,
        allow_null=True,
        help_text="Faili ya kidijitali kwa bidhaa ya digital (mf. PDF, ZIP)."
    )

    # ✅ LANGUAGE - ChoiceField
    language_code = serializers.ChoiceField(
        choices=LanguageChoices.choices,
        default=LanguageChoices.ENGLISH,
        help_text="Lugha inayotumika kwenye maelezo ya bidhaa."
    )
    language_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "business", "name", "slug", "description", "type",
            "price", "discount_price", "currency", "currency_symbol", "currency_code",
            "category", "category_name",
            "quantity_in_stock", "unit", "unit_display",
            "is_available", "is_featured", "image", "images", "tags",
            "tax_inclusive", "tax_rate", "external_link", "digital_file",
            "language_code", "language_display",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "business", "slug", "created_at", "updated_at",
            "currency_symbol", "currency_code", "unit_display", "language_display", "category_name", "images",
        ]

    def validate(self, data):
        if data.get("discount_price") and data["discount_price"] >= data["price"]:
            raise serializers.ValidationError("Bei punguzo lazima iwe ndogo kuliko bei ya kawaida.")
        return data

    def get_unit_display(self, obj):
        return obj.get_unit_display() if hasattr(obj, 'get_unit_display') else obj.unit

    def get_language_display(self, obj):
        return obj.get_language_display_name() if hasattr(obj, 'get_language_display_name') else obj.language_code

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["final_price"] = instance.final_price()
        rep["has_stock"] = instance.has_stock()
        rep["is_digital"] = instance.is_digital()
        rep["is_service"] = instance.is_service()
        return rep


class ProductListSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    unit_display = serializers.SerializerMethodField(read_only=True)
    language_display = serializers.SerializerMethodField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "price", "discount_price", "final_price",
            "currency", "currency_symbol", "currency_code",
            "category", "category_name",
            "quantity_in_stock", "unit", "unit_display",
            "image", "images", "is_featured", "is_available", "tags",
            "language_code", "language_display",
            "created_at"
        ]

    def get_final_price(self, obj):
        return obj.final_price()

    def get_unit_display(self, obj):
        return obj.get_unit_display() if hasattr(obj, 'get_unit_display') else obj.unit

    def get_language_display(self, obj):
        return obj.get_language_display_name() if hasattr(obj, 'get_language_display_name') else obj.language_code


class TrendingProductSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    business_id = serializers.UUIDField(source='business.id', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    order_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "price", "discount_price", "final_price",
            "currency_symbol", "image", "is_featured",
            "business_id", "business_name", "order_count",
        ]

    def get_final_price(self, obj):
        return obj.final_price()

    def get_language_display(self, obj):
        return obj.get_language_display_name() if hasattr(obj, 'get_language_display_name') else obj.language_code


class ProductDetailSerializer(serializers.ModelSerializer):
    business = BusinessDetailSerializer(read_only=True)
    final_price = serializers.SerializerMethodField()
    has_stock = serializers.SerializerMethodField()
    is_digital = serializers.SerializerMethodField()
    is_service = serializers.SerializerMethodField()
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    unit_display = serializers.SerializerMethodField(read_only=True)
    language_display = serializers.SerializerMethodField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "business", "name", "slug", "description", "type",
            "price", "discount_price", "currency", "currency_symbol", "currency_code",
            "category", "category_name",
            "quantity_in_stock", "unit", "unit_display",
            "is_available", "is_featured", "image", "images", "tags",
            "tax_inclusive", "tax_rate", "external_link", "digital_file",
            "language_code", "language_display",
            "created_at", "updated_at",
            "final_price", "has_stock", "is_digital", "is_service"
        ]

    def get_final_price(self, obj):
        return obj.final_price()

    def get_has_stock(self, obj):
        return obj.has_stock()

    def get_is_digital(self, obj):
        return obj.is_digital()

    def get_is_service(self, obj):
        return obj.is_service()

    def get_unit_display(self, obj):
        return obj.get_unit_display() if hasattr(obj, 'get_unit_display') else obj.unit

    def get_language_display(self, obj):
        return obj.get_language_display_name() if hasattr(obj, 'get_language_display_name') else obj.language_code


class ProductMinimalSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "discount_price",
            "currency",
            "currency_symbol",
            "is_available",
            "is_featured",
            "image",
            "language_code",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["final_price"] = instance.final_price()
        return rep