"""
Tests du modèle StockEntry (entrées de stock).

Références (code actuel du dépôt) :
- inventory/models.py : StockEntry.clean / save / delete / apply
"""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import InventoryItem, StockAlert, StockEntry, Supplier

from .base import create_entry, create_item, build_entry, to_decimal


class StockEntryCleanTests(TestCase):

    def setUp(self):
        self.item = create_item()

    def test_quantity_must_be_strictly_positive(self):
        entry = build_entry(self.item, "0", "2.00")

        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()

        self.assertIn("quantity", ctx.exception.error_dict)

    def test_negative_quantity_is_refused(self):
        entry = build_entry(self.item, "-3", "2.00")

        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()

        self.assertIn("quantity", ctx.exception.error_dict)

    def test_negative_unit_cost_is_refused(self):
        entry = build_entry(self.item, "3", "-1.00")

        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()

        self.assertIn("unit_cost", ctx.exception.error_dict)

    def test_total_cost_match_is_checked(self):
        entry = build_entry(
            self.item,
            "3",
            "2.00",
            total_cost=to_decimal("999"),
        )

        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()

        self.assertIn("total_cost", ctx.exception.error_dict)

    def test_total_cost_cannot_have_more_than_two_decimals(self):
        # Règle codée dans le champ total_cost (decimal_places=2).
        # Un produit de deux décimales x deux décimales produit quatre
        # décimales : c'est ce qui bloque la création passant par le
        # serializer DRF (les montants y sont quantifiés à 2 décimales).
        entry = StockEntry(
            item=self.item,
            quantity=to_decimal("5.00"),
            unit_cost=to_decimal("2.00"),
            total_cost=to_decimal("10.0000"),
        )

        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()

        self.assertIn("total_cost", ctx.exception.error_dict)

    def test_perishable_item_requires_expiration_date(self):
        item = create_item(is_perishable=True)
        entry = build_entry(item, "5", "2.00")

        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()

        self.assertIn("expiration_date", ctx.exception.error_dict)

    def test_non_perishable_item_rejects_expiration_date(self):
        entry = build_entry(
            self.item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=30),
        )

        with self.assertRaises(ValidationError) as ctx:
            entry.full_clean()

        self.assertIn("expiration_date", ctx.exception.error_dict)

    def test_valid_entry_passes_clean(self):
        entry = build_entry(self.item, "5", "2.00")

        entry.full_clean()  # ne doit pas lever d'erreur


class StockEntryApplyTests(TestCase):

    def setUp(self):
        self.item = create_item()

    def test_apply_stores_entry_and_updates_stock(self):
        entry = create_entry(self.item, "10", "2.50")

        self.assertIsNotNone(entry.pk)
        self.assertEqual(entry.remaining_quantity, Decimal("10.00"))
        self.assertEqual(entry.total_cost, Decimal("25.00"))

        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("10.00"))

    def test_apply_returns_new_stock_quantity(self):
        create_entry(self.item, "4", "1.00")

        # Seconde entrée : la valeur retournée est le nouveau stock.
        second = build_entry(self.item, "6", "1.00")
        returned = second.apply()

        self.assertEqual(returned, Decimal("10.00"))

    def test_apply_computes_total_cost_server_side(self):
        entry = build_entry(
            self.item,
            "10",
            "2.00",
            total_cost=to_decimal("999"),
        )
        entry.apply()

        self.assertEqual(entry.total_cost, Decimal("20.00"))

    def test_apply_is_refused_twice(self):
        entry = create_entry(self.item, "5", "2.00")

        with self.assertRaises(ValidationError):
            entry.apply()

    def test_apply_requires_an_item(self):
        entry = StockEntry(
            quantity=Decimal("5.00"),
            unit_cost=Decimal("2.00"),
            total_cost=Decimal("10.00"),
        )

        with self.assertRaises(ValidationError):
            entry.apply()

    def test_invalid_entry_leaves_stock_unchanged(self):
        entry = build_entry(self.item, "0", "2.00")

        with self.assertRaises(ValidationError):
            entry.apply()

        self.assertIsNone(entry.pk)
        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("0.00"))
        self.assertEqual(StockEntry.objects.count(), 0)

    def test_apply_stores_supplier_and_received_by(self):
        supplier = Supplier.objects.create(name="Fournisseur A")
        user = User.objects.create_user(
            email="stock@example.com",
            first_name="Stock",
            last_name="Manager",
            role=User.Role.ACCOUNTANT,
            password="password",
        )

        entry = create_entry(
            self.item,
            "5",
            "2.00",
            supplier=supplier,
            received_by=user,
            batch_number="LOT-001",
            comments="Réception du matin",
        )

        self.assertEqual(entry.supplier, supplier)
        self.assertEqual(entry.received_by, user)
        self.assertEqual(entry.batch_number, "LOT-001")

    def test_perishable_entry_requires_expiration_date(self):
        item = create_item(is_perishable=True)
        entry = build_entry(item, "5", "2.00")

        with self.assertRaises(ValidationError):
            entry.apply()

        self.assertIsNone(entry.pk)
        item = InventoryItem.objects.get(pk=item.pk)
        self.assertEqual(item.stock_quantity, Decimal("0.00"))


class StockEntryImmutabilityTests(TestCase):

    def setUp(self):
        self.item = create_item()
        self.entry = create_entry(self.item, "10", "2.00")

    def test_direct_save_of_new_entry_is_refused(self):
        entry = build_entry(self.item, "5", "2.00")

        with self.assertRaises(ValidationError):
            entry.save()

    def test_recorded_entry_cannot_be_modified(self):
        self.entry.quantity = Decimal("99.00")

        with self.assertRaises(ValidationError):
            self.entry.save()

    def test_recorded_entry_can_update_remaining_quantity_with_flag(self):
        # C'est le comportement attendu des mouvements de stock
        # (StockExit.apply / StockDestruction.apply).
        self.entry.remaining_quantity = Decimal("3.00")
        self.entry._updating_stock = True

        try:
            self.entry.save(
                update_fields=["remaining_quantity", "updated_at"],
            )
        finally:
            self.entry._updating_stock = False

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.remaining_quantity, Decimal("3.00"))

    def test_recorded_entry_cannot_be_deleted(self):
        with self.assertRaises(ValidationError):
            self.entry.delete()

        self.assertEqual(StockEntry.objects.count(), 1)


class StockEntryAlertSyncTests(TestCase):

    def test_entry_triggers_low_stock_alert(self):
        item = create_item(reorder_point=to_decimal("100"))

        create_entry(item, "10", "2.00")

        alert = StockAlert.objects.get(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.LOW_STOCK,
        )
        self.assertEqual(alert.current_quantity, Decimal("10.00"))
        self.assertIsNone(alert.stock_entry_id)

    def test_entry_clears_low_stock_alert_when_stock_recovers(self):
        item = create_item(reorder_point=to_decimal("100"))
        create_entry(item, "10", "2.00")

        self.assertTrue(
            StockAlert.objects.filter(
                item_id=item.pk,
                alert_type=StockAlert.AlertType.LOW_STOCK,
            ).exists()
        )

        create_entry(item, "200", "2.00")

        self.assertFalse(
            StockAlert.objects.filter(
                item_id=item.pk,
                alert_type=StockAlert.AlertType.LOW_STOCK,
            ).exists()
        )

    def test_entry_creates_expiration_alert_within_window(self):
        item = create_item(
            is_perishable=True,
            expiration_alert_days=30,
        )
        expiration_date = timezone.localdate() + timedelta(days=10)

        create_entry(
            item,
            "5",
            "2.00",
            expiration_date=expiration_date,
        )

        alert = StockAlert.objects.get(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.EXPIRATION,
        )
        self.assertEqual(alert.current_quantity, Decimal("5.00"))

    def test_entry_without_soon_expiration_creates_no_alert(self):
        item = create_item(
            is_perishable=True,
            expiration_alert_days=30,
        )

        create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=90),
        )

        self.assertEqual(StockAlert.objects.count(), 0)

    def test_entry_on_non_perishable_item_creates_no_expiration_alert(self):
        item = create_item()

        create_entry(item, "5", "2.00")

        self.assertEqual(StockAlert.objects.count(), 0)
