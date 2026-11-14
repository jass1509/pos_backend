from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductAdminSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "code", "name", "category", "category_name", "cost_price",
                  "selling_price", "stock", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class ProductPOSSerializer(serializers.ModelSerializer):
    """Vista para cajeros: sin precio de costo."""
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "code", "name", "category", "category_name",
                  "selling_price", "stock", "is_active"]
        read_only_fields = fields
