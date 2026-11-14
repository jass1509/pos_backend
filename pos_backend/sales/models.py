import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Count, Q, Sum


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Efectivo"
    CARD = "CARD", "Tarjeta"
    TRANSFER = "TRANSFER", "Transferencia"


class Shift(models.Model):
    """Caja / turno de un cajero."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Abierta"
        CLOSED = "CLOSED", "Cerrada"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="shifts")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    initial_cash = models.DecimalField(max_digits=12, decimal_places=2)
    final_cash_calculated = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    final_cash_real = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ["-opened_at"]
        constraints = [
            # Un cajero solo puede tener un turno abierto a la vez (garantizado por la BD).
            models.UniqueConstraint(
                fields=["user"], condition=Q(status="OPEN"), name="one_open_shift_per_user"
            ),
        ]

    def __str__(self):
        return f"Turno #{self.pk} - {self.user} ({self.status})"

    def summary(self):
        """Totales vendidos por método de pago (solo ventas no anuladas)."""
        rows = (
            self.sales.filter(status=Sale.Status.COMPLETED)
            .values("payment_method")
            .annotate(total=Sum("total"), count=Count("id"))
        )
        by_method = {m: Decimal("0.00") for m in PaymentMethod.values}
        count = 0
        for r in rows:
            by_method[r["payment_method"]] = r["total"]
            count += r["count"]
        total_sold = sum(by_method.values(), Decimal("0.00"))
        return {
            "initial_cash": self.initial_cash,
            "sales_count": count,
            "totals_by_method": by_method,
            "total_sold": total_sold,
            "expected_cash": self.initial_cash + by_method[PaymentMethod.CASH],
        }


class Sale(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "COMPLETED", "Completada"
        VOIDED = "VOIDED", "Anulada"

    invoice_number = models.CharField(max_length=30, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales")
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name="sales")
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.invoice_number

    @staticmethod
    def temp_invoice_number():
        return f"TMP-{uuid.uuid4().hex[:20]}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
