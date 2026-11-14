from rest_framework import serializers

from .models import PaymentMethod, Sale, SaleItem, Shift


class SaleItemInputSerializer(serializers.Serializer):
    product = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class SaleCreateSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    items = SaleItemInputSerializer(many=True, allow_empty=False)


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_code = serializers.CharField(source="product.code", read_only=True)

    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_code", "product_name",
                  "quantity", "unit_price", "subtotal"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    cashier = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Sale
        fields = ["id", "invoice_number", "cashier", "shift", "payment_method",
                  "total", "status", "created_at", "items"]


class ShiftSerializer(serializers.ModelSerializer):
    cashier = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Shift
        fields = ["id", "cashier", "opened_at", "closed_at", "initial_cash",
                  "final_cash_calculated", "final_cash_real", "status"]
        read_only_fields = fields


class OpenShiftSerializer(serializers.Serializer):
    initial_cash = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)


class CloseShiftSerializer(serializers.Serializer):
    final_cash_real = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
