from django.contrib import admin
from .models import Category, Product

admin.site.register(Category)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "selling_price", "stock", "is_active")
    search_fields = ("code", "name")
    list_filter = ("category", "is_active")
