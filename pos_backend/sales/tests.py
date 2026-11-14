from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from inventory.models import Product
from .models import Sale

User = get_user_model()


class POSFlowTests(APITestCase):
    def setUp(self):
        self.cashier = User.objects.create_user("caja1", password="x12345678", role="CASHIER")
        self.admin = User.objects.create_user("admin", password="x12345678", role="ADMIN")
        self.p1 = Product.objects.create(code="A1", name="Agua", cost_price="1.00", selling_price="2.50", stock=10)
        self.p2 = Product.objects.create(code="B1", name="Pan", cost_price="0.50", selling_price="1.00", stock=3)
        self.client.force_authenticate(self.cashier)

    def _open(self):
        return self.client.post("/api/shifts/open/", {"initial_cash": "100.00"}, format="json")

    def test_cannot_sell_without_shift(self):
        r = self.client.post("/api/sales/", {"payment_method": "CASH",
                             "items": [{"product": self.p1.id, "quantity": 1}]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_sale_reduces_stock_and_computes_total(self):
        self._open()
        r = self.client.post("/api/sales/", {"payment_method": "CASH", "items": [
            {"product": self.p1.id, "quantity": 2}, {"product": self.p2.id, "quantity": 1}]}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(Decimal(r.data["total"]), Decimal("6.00"))
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, 8)

    def test_insufficient_stock_rolls_back_everything(self):
        self._open()
        r = self.client.post("/api/sales/", {"payment_method": "CARD", "items": [
            {"product": self.p1.id, "quantity": 2}, {"product": self.p2.id, "quantity": 99}]}, format="json")
        self.assertEqual(r.status_code, 400)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, 10)       # no se descontó nada
        self.assertEqual(Sale.objects.count(), 0)

    def test_close_shift_totals_by_payment_method(self):
        self._open()
        for method in ("CASH", "CARD", "TRANSFER"):
            self.client.post("/api/sales/", {"payment_method": method,
                             "items": [{"product": self.p1.id, "quantity": 1}]}, format="json")
        r = self.client.post("/api/shifts/close/", {"final_cash_real": "102.00"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        s = r.data["summary"]
        self.assertEqual(Decimal(s["totals_by_method"]["CASH"]), Decimal("2.50"))
        self.assertEqual(Decimal(s["expected_cash"]), Decimal("102.50"))
        self.assertEqual(Decimal(s["difference"]), Decimal("-0.50"))

    def test_cashier_cannot_void_but_admin_can(self):
        self._open()
        sale = self.client.post("/api/sales/", {"payment_method": "CASH",
                                "items": [{"product": self.p1.id, "quantity": 4}]}, format="json").data
        self.assertEqual(self.client.post(f"/api/sales/{sale['id']}/void/").status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(f"/api/sales/{sale['id']}/void/").status_code, 200)
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock, 10)
