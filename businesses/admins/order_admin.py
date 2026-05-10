from django.contrib import admin
from businesses.models.order import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("total_price",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "business", "status", "payment_status", "total_amount", "scheduled_datetime", "created_at")
    list_filter = ("status", "payment_status", "business")
    search_fields = ("client__email", "business__name")
    ordering = ("-created_at",)
    readonly_fields = ("total_amount",)

    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "service", "quantity", "unit_price", "total_price")
    list_filter = ("order__business",)
    search_fields = ("product__name", "service__name")
    ordering = ("order__created_at",)
    readonly_fields = ("total_price",)