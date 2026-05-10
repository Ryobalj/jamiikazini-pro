# payments/admin/invoice_admin.py

from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from payments.models.invoice import Invoice


# 🔹 Custom ModelForm ili kufanya description iwe editable
class InvoiceAdminForm(forms.ModelForm):
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label=_("Description"),
    )

    class Meta:
        model = Invoice
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['description'].initial = self.instance.description

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.description = self.cleaned_data.get('description')
        if commit:
            instance.save()
        return instance


# 🔹 Admin
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    form = InvoiceAdminForm

    list_display = (
        "invoice_number",
        "user",
        "status",
        "amount",
        "tax",
        "total_amount",
        "due_date",
        "paid_at",
        "created_at",
    )
    list_filter = ("status", "due_date", "created_at")
    search_fields = ("invoice_number", "user__full_name")
    readonly_fields = ("total_amount", "paid_at", "created_at", "last_modified_by", "created_by")

    ordering = ("-created_at",)

    fieldsets = (
        (_("Invoice Details"), {
            "fields": (
                "invoice_number",
                "user",
                "description",  # editable via custom form
                "status",
                "amount",
                "tax",
                "total_amount",
                "due_date",
                "paid_at",
            )
        }),
        (_("Audit Info"), {
            "fields": (
                "created_by",
                "last_modified_by",
                "created_at",
            ),
            "classes": ("collapse",),
        }),
    )

    actions = ["mark_invoices_as_paid"]

    def mark_invoices_as_paid(self, request, queryset):
        updated = 0
        for invoice in queryset.filter(status__in=[Invoice.InvoiceStatus.PENDING, Invoice.InvoiceStatus.OVERDUE]):
            invoice.mark_as_paid()
            updated += 1
        self.message_user(request, _("%d invoice(s) marked as paid.") % updated)
    mark_invoices_as_paid.short_description = _("Mark selected invoices as paid")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        else:
            obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)