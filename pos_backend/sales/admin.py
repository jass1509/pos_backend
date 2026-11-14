from django.contrib import admin
from .models import Sale, SaleItem, Shift


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "subtotal")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "user", "payment_method", "total", "status", "created_at")
    list_filter = ("payment_method", "status")
    inlines = [SaleItemInline]


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "opened_at", "closed_at", "initial_cash")
