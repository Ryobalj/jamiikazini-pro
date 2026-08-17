# businesses/admin/product_admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from businesses.models.product import Product, UnitChoices, LanguageChoices
from businesses.models.product_image import ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ('image', 'image_preview', 'caption', 'order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:4px;" />',
                obj.image.url,
            )
        return "-"
    image_preview.short_description = _("Preview")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_thumbnail',
        'name',
        'business',
        'type',
        'price_display',
        'stock_status',
        'is_available',
        'is_featured',
        'created_at'
    )
    list_filter = (
        'type',
        'is_available',
        'is_featured',
        'business',
        'currency',
        'language_code',
        'created_at'
    )
    search_fields = (
        'name',
        'business__name',
        'tags',
        'description',
        'slug'
    )
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'final_price_display', 'stock_status', 'image_preview_large')
    ordering = ('-created_at',)
    list_per_page = 25
    list_select_related = ('business', 'currency')
    inlines = [ProductImageInline]

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.image.url,
            )
        return "-"
    image_thumbnail.short_description = _("Image")

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;max-height:300px;border-radius:6px;" />',
                obj.image.url,
            )
        return _("No image uploaded.")
    image_preview_large.short_description = _("Current Image")

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'business', 
                'name', 
                'slug', 
                'description', 
                'type'
            )
        }),
        (_('Pricing'), {
            'fields': (
                'price', 
                'discount_price', 
                'currency', 
                'final_price_display',
                'tax_inclusive', 
                'tax_rate'
            )
        }),
        (_('Inventory'), {
            'fields': (
                'quantity_in_stock', 
                'unit', 
                'stock_status'
            )
        }),
        (_('Status'), {
            'fields': (
                'is_available', 
                'is_featured'
            )
        }),
        (_('Media'), {
            'fields': (
                'image',
                'image_preview_large',
                'digital_file',
                'external_link'
            ),
            'description': _("Extra gallery photos are managed below under Product Images."),
        }),
        (_('Tags & Language'), {
            'fields': (
                'tags', 
                'language_code'
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        """Display price with currency symbol"""
        symbol = obj.currency.symbol if obj.currency else "TSh"
        if obj.discount_price:
            return f"{symbol} {obj.discount_price} (was {symbol} {obj.price})"
        return f"{symbol} {obj.price}"
    price_display.short_description = _("Price")
    price_display.admin_order_field = 'price'

    def final_price_display(self, obj):
        """Display final price (readonly)"""
        symbol = obj.currency.symbol if obj.currency else "TSh"
        return f"{symbol} {obj.final_price()}"
    final_price_display.short_description = _("Final Price")

    def stock_status(self, obj):
        """Display stock status with color indicator"""
        if obj.quantity_in_stock <= 0:
            return "❌ Out of Stock"
        elif obj.quantity_in_stock <= 5:
            return f"⚠️ Low Stock ({obj.quantity_in_stock})"
        else:
            return f"✅ In Stock ({obj.quantity_in_stock})"
    stock_status.short_description = _("Stock Status")
    stock_status.admin_order_field = 'quantity_in_stock'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('business', 'currency')

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly when editing"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing product
            readonly.append('business')  # Can't change business after creation
        return readonly

    actions = ['mark_as_available', 'mark_as_unavailable', 'mark_as_featured', 'mark_as_not_featured']

    @admin.action(description=_("Mark selected products as available"))
    def mark_as_available(self, request, queryset):
        queryset.update(is_available=True)
        self.message_user(request, _(f"{queryset.count()} products marked as available."))

    @admin.action(description=_("Mark selected products as unavailable"))
    def mark_as_unavailable(self, request, queryset):
        queryset.update(is_available=False)
        self.message_user(request, _(f"{queryset.count()} products marked as unavailable."))

    @admin.action(description=_("Mark selected products as featured"))
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, _(f"{queryset.count()} products marked as featured."))

    @admin.action(description=_("Mark selected products as not featured"))
    def mark_as_not_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, _(f"{queryset.count()} products marked as not featured."))


# Optional: Inline admin for displaying products in Business admin
class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ('name', 'type', 'price', 'is_available', 'is_featured')
    readonly_fields = ('name', 'type', 'price')
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False