"""Lógica de negocio del POS. Todo lo crítico corre bajo transacción atómica."""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from inventory.models import Product
from .models import Sale, SaleItem, Shift


@transaction.atomic
def create_sale(*, user, shift, payment_method, items):
    """
    items: lista de dicts {"product": <id>, "quantity": <int>}.

    - Bloquea las filas de producto (SELECT ... FOR UPDATE) para evitar
      sobreventa cuando dos cajas venden el mismo producto a la vez.
    - Los precios SIEMPRE se toman de la base de datos, nunca del cliente.
    - Si algo falla, se revierte todo (venta, detalles y stock).
    """
    if shift.status != Shift.Status.OPEN or shift.user_id != user.id:
        raise ValidationError({"shift": "No tienes un turno abierto válido."})

    # Consolidar líneas repetidas del mismo producto
    quantities = {}
    for item in items:
        pid = item["product"]
        quantities[pid] = quantities.get(pid, 0) + item["quantity"]

    # Orden fijo por id para evitar deadlocks entre ventas concurrentes
    products = {
        p.id: p
        for p in Product.objects.select_for_update()
        .filter(id__in=quantities.keys(), is_active=True)
        .order_by("id")
    }

    errors = []
    for pid, qty in quantities.items():
        product = products.get(pid)
        if product is None:
            errors.append(f"Producto {pid} no existe o está inactivo.")
        elif product.stock < qty:
            errors.append(
                f"Stock insuficiente para '{product.name}': "
                f"disponible {product.stock}, solicitado {qty}."
            )
    if errors:
        raise ValidationError({"items": errors})

    sale = Sale.objects.create(
        invoice_number=Sale.temp_invoice_number(),
        user=user,
        shift=shift,
        payment_method=payment_method,
        total=Decimal("0.00"),
    )

    total = Decimal("0.00")
    detail_rows = []
    for pid, qty in quantities.items():
        product = products[pid]
        subtotal = (product.selling_price * qty).quantize(Decimal("0.01"))
        total += subtotal
        detail_rows.append(
            SaleItem(sale=sale, product=product, quantity=qty,
                     unit_price=product.selling_price, subtotal=subtotal)
        )
        product.stock -= qty
    SaleItem.objects.bulk_create(detail_rows)
    Product.objects.bulk_update(products.values(), ["stock", "updated_at"])

    sale.total = total
    sale.invoice_number = f"FAC-{sale.pk:08d}"
    sale.save(update_fields=["total", "invoice_number"])
    return sale


@transaction.atomic
def void_sale(*, sale_id):
    """Anula una venta y devuelve el stock."""
    sale = Sale.objects.select_for_update().get(pk=sale_id)
    if sale.status == Sale.Status.VOIDED:
        raise ValidationError({"detail": "La venta ya está anulada."})

    items = list(sale.items.all())
    products = {
        p.id: p
        for p in Product.objects.select_for_update()
        .filter(id__in=[i.product_id for i in items])
        .order_by("id")
    }
    for item in items:
        products[item.product_id].stock += item.quantity
    Product.objects.bulk_update(products.values(), ["stock", "updated_at"])

    sale.status = Sale.Status.VOIDED
    sale.save(update_fields=["status"])
    return sale


@transaction.atomic
def close_shift(*, shift_id, final_cash_real):
    shift = Shift.objects.select_for_update().get(pk=shift_id)
    if shift.status == Shift.Status.CLOSED:
        raise ValidationError({"detail": "El turno ya está cerrado."})

    summary = shift.summary()
    shift.final_cash_calculated = summary["expected_cash"]
    shift.final_cash_real = final_cash_real
    shift.closed_at = timezone.now()
    shift.status = Shift.Status.CLOSED
    shift.save()

    summary["final_cash_real"] = final_cash_real
    summary["difference"] = final_cash_real - summary["expected_cash"]  # >0 sobrante, <0 faltante
    return shift, summary
