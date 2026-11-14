from django.db import models
from django.db.models import CheckConstraint, Q


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField("SKU / código de barras", max_length=64, unique=True)
    name = models.CharField(max_length=200, db_index=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            CheckConstraint(check=Q(stock__gte=0), name="product_stock_non_negative"),
            CheckConstraint(check=Q(selling_price__gte=0), name="product_price_non_negative"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
