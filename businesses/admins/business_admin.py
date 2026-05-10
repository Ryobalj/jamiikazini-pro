# businesses/admin/business_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from businesses.models.business import Business
from businesses.models.product import Product


# Product Inline - Onyesho la products ndani ya Business admin
class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ('name', 'type', 'price', 'currency', 'quantity_in_stock', 'is_available', 'is_featured')
    readonly_fields = ('name', 'type', 'price', 'currency')
    can_delete = False
    show_change_link = True
    verbose_name = _("Product")
    verbose_name_plural = _("Products")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'owner',
        'institution',
        'category',
        'phone',
        'email',
        'website',
        'is_verified',
        'is_active',
        'created_at',
    )
    list_filter = (
        'is_verified',
        'is_active',
        'category',
        'institution',
    )
    search_fields = (
        'name',
        'owner__email',
        'owner__full_name',
        'institution__name',
        'phone',
        'email',
    )
    ordering = ('-created_at',)
    readonly_fields = ('slug', 'created_at', 'updated_at')
    list_select_related = ('owner', 'institution', 'category')
    list_per_page = 25
    
    # ✅ Add Product Inline
    inlines = [ProductInline]

    fieldsets = (
        (_("Basic Info"), {
            'fields': (
                'name',
                'owner',
                'institution',
                'category',
                'description',
                'slug',
            )
        }),
        (_("Contact & Online Presence"), {
            'fields': (
                'phone',
                'email',
                'website',
            )
        }),
        (_("Location & Status"), {
            'fields': (
                'location',
                'address',
                'is_verified',
                'is_active',
            )
        }),
        (_("Timestamps"), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('owner', 'institution', 'category')

    def get_readonly_fields(self, request, obj=None):
        """Make owner readonly when editing"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing business
            readonly.append('owner')
        return readonly

    actions = ['verify_businesses', 'unverify_businesses', 'activate_businesses', 'deactivate_businesses']

    @admin.action(description=_("Verify selected businesses"))
    def verify_businesses(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, _(f"{updated} businesses verified successfully."))

    @admin.action(description=_("Unverify selected businesses"))
    def unverify_businesses(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, _(f"{updated} businesses unverified."))

    @admin.action(description=_("Activate selected businesses"))
    def activate_businesses(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f"{updated} businesses activated successfully."))

    @admin.action(description=_("Deactivate selected businesses"))
    def deactivate_businesses(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f"{updated} businesses deactivated."))