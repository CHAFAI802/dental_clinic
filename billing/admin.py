from django.contrib import admin
from .models import Invoice, Payment


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    readonly_fields = ("reference_number",)


admin.site.register(Payment)
