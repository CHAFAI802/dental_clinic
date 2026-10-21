"""
Tests des modèles StockDestruction et StockDestructionLine.

Références (code actuel du dépôt) :
- inventory/models.py : StockDestruction.save / delete / apply,
  StockDestructionLine.clean / save / delete
"""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from inventory.models import (
    InventoryItem,
    StockAlert,
    StockDestruction,
    StockDestructionLine,
    StockEntry,
)

from .base import create_entry, create_item, to_decimal


def create_destruction(reason="Produits périmés"):
    return StockDestruction.objects.create(reason=reason)


class StockDestructionLifecycleTests(TestCase):

    def test_document_is_created_with_recorded_status(self):
        destruction = create_destruction()

        self.assertEqual(
            destruction.status,
            StockDestruction.DestructionStatus.RECORDED,
        )
        self.assertIsNotNone(destruction.destroyed_at)

    def test_reason_is_required(self):
        with self.assertRaises(ValidationError):
            StockDestruction.objects.create(reason="")

    def test_direct_creation_as_completed_is_refused(self):
        with self.assertRaises(ValidationError):
            StockDestruction.objects.create(
                reason="Produits périmés",
                status=StockDestruction.DestructionStatus.COMPLETED,
            )

    def test_completed_document_cannot_be_modified(self):
        destruction = create_destruction()
        item = create_item()
        entry = create_entry(item, "10", "2.00")
        StockDestructionLine.objects.create(
            destruction=destruction,
            item=item,
            stock_entry=entry,
            quantity=to_decimal("5"),
        )
        destruction.apply()

        destruction.reason = "Modification"

        with self.assertRaises(ValidationError):
            destruction.save()

    def test_recorded_document_cannot_be_marked_completed_manually(self):
        destruction = create_destruction()

        destruction.status = StockDestruction.DestructionStatus.COMPLETED

        with self.assertRaises(ValidationError):
            destruction.save()

    def test_recorded_document_can_be_deleted(self):
        destruction = create_destruction()

        destruction.delete()

        self.assertEqual(StockDestruction.objects.count(), 0)

    def test_completed_document_cannot_be_deleted(self):
        destruction = create_destruction()
        item = create_item()
        entry = create_entry(item, "10", "2.00")
        StockDestructionLine.objects.create(
            destruction=destruction,
            item=item,
            stock_entry=entry,
            quantity=to_decimal("5"),
        )
        destruction.apply()

        with self.assertRaises(ValidationError):
            destruction.delete()

        self.assertEqual(StockDestruction.objects.count(), 1)


class StockDestructionLineTests(TestCase):

    def setUp(self):
        self.destruction = create_destruction()
        self.item = create_item()
        self.entry = create_entry(self.item, "10", "2.00")

    def _create_line(self, **kwargs):
        params = {
            "destruction": self.destruction,
            "item": self.item,
            "stock_entry": self.entry,
            "quantity": to_decimal("1"),
        }
        params.update(kwargs)
        return StockDestructionLine.objects.create(**params)

    def test_valid_line_is_created(self):
        line = self._create_line(quantity=to_decimal("2"))

        self.assertIsNotNone(line.pk)

    def test_negative_quantity_is_refused(self):
        with self.assertRaises(ValidationError) as ctx:
            self._create_line(quantity=to_decimal("-2"))

        self.assertIn("quantity", ctx.exception.error_dict)

    def test_zero_quantity_is_refused(self):
        with self.assertRaises(ValidationError) as ctx:
            self._create_line(quantity=to_decimal("0"))

        self.assertIn("quantity", ctx.exception.error_dict)

    def test_lot_must_belong_to_line_item(self):
        other_item = create_item(name="Autre produit")
        other_entry = create_entry(other_item, "5", "1.00")

        with self.assertRaises(ValidationError) as ctx:
            self._create_line(stock_entry=other_entry)

        self.assertIn("stock_entry", ctx.exception.error_dict)

    def test_line_requires_an_explicit_lot_at_execution(self):
        line = StockDestructionLine.objects.create(
            destruction=self.destruction,
            item=self.item,
            quantity=to_decimal("2"),
        )

        with self.assertRaises(ValidationError) as ctx:
            self.destruction.apply()

        self.assertIn("stock_entry", ctx.exception.error_dict)
        self.assertIsNotNone(line.pk)

    def test_line_with_low_stock_alert_is_refused(self):
        item = create_item(reorder_point=to_decimal("100"))
        entry = create_entry(item, "10", "2.00")
        alert = StockAlert.objects.get(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.LOW_STOCK,
        )

        with self.assertRaises(ValidationError) as ctx:
            StockDestructionLine.objects.create(
                destruction=self.destruction,
                item=item,
                stock_entry=entry,
                stock_alert=alert,
                quantity=to_decimal("1"),
            )

        self.assertIn("stock_alert", ctx.exception.error_dict)

    def test_alert_of_another_item_is_refused(self):
        alert = StockAlert.objects.create(
            item=self.item,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            current_quantity=to_decimal("10"),
        )

        with self.assertRaises(ValidationError) as ctx:
            StockDestructionLine.objects.create(
                destruction=self.destruction,
                item=self.item,
                stock_entry=self.entry,
                stock_alert=alert,
                quantity=to_decimal("1"),
            )

        self.assertIn("stock_alert", ctx.exception.error_dict)

    def test_alert_without_lot_is_refused(self):
        alert = StockAlert.objects.create(
            item=self.item,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            current_quantity=to_decimal("10"),
        )

        with self.assertRaises(ValidationError) as ctx:
            StockDestructionLine.objects.create(
                destruction=self.destruction,
                item=self.item,
                stock_alert=alert,
                quantity=to_decimal("1"),
            )

        self.assertIn("stock_entry", ctx.exception.error_dict)

    def test_alert_must_target_the_destroyed_lot(self):
        item = create_item(is_perishable=True)
        entry_a = create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=5),
        )
        entry_b = create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=6),
        )

        alert_a = StockAlert.objects.get(stock_entry_id=entry_a.pk)
        alert_b = StockAlert.objects.get(stock_entry_id=entry_b.pk)
        self.assertNotEqual(alert_a.pk, alert_b.pk)

        with self.assertRaises(ValidationError) as ctx:
            StockDestructionLine.objects.create(
                destruction=self.destruction,
                item=item,
                stock_entry=entry_b,
                stock_alert=alert_a,
                quantity=to_decimal("1"),
            )

        self.assertIn("stock_alert", ctx.exception.error_dict)

    def test_valid_expiration_alert_association(self):
        item = create_item(is_perishable=True)
        entry = create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=5),
        )
        alert = StockAlert.objects.get(stock_entry_id=entry.pk)

        line = StockDestructionLine.objects.create(
            destruction=self.destruction,
            item=item,
            stock_entry=entry,
            stock_alert=alert,
            quantity=to_decimal("1"),
        )

        self.assertIsNotNone(line.pk)

    def test_line_of_completed_document_cannot_be_modified(self):
        line = self._create_line(quantity=to_decimal("2"))
        self.destruction.apply()

        line.quantity = to_decimal("1")

        with self.assertRaises(ValidationError):
            line.save()

    def test_line_of_completed_document_cannot_be_deleted(self):
        line = self._create_line(quantity=to_decimal("2"))
        self.destruction.apply()

        with self.assertRaises(ValidationError):
            line.delete()

        self.assertEqual(StockDestructionLine.objects.count(), 1)

    def test_line_can_be_added_to_recorded_document(self):
        self._create_line(quantity=to_decimal("2"))
        line = self._create_line(quantity=to_decimal("3"))

        self.assertEqual(self.destruction.lines.count(), 2)
        self.assertIsNotNone(line.pk)

    def test_recorded_document_lines_can_be_deleted(self):
        line = self._create_line(quantity=to_decimal("2"))

        line.delete()

        self.assertEqual(StockDestructionLine.objects.count(), 0)


class StockDestructionApplyTests(TestCase):

    def setUp(self):
        self.destruction = create_destruction()
        self.item = create_item()
        self.entry = create_entry(self.item, "10", "2.00")

    def _add_line(self, quantity, item=None, entry=None):
        return StockDestructionLine.objects.create(
            destruction=self.destruction,
            item=item or self.item,
            stock_entry=entry or self.entry,
            quantity=to_decimal(quantity),
        )

    def test_apply_requires_saved_document(self):
        destruction = StockDestruction(reason="Hors base")

        with self.assertRaises(ValidationError):
            destruction.apply()

    def test_apply_requires_at_least_one_line(self):
        with self.assertRaises(ValidationError):
            self.destruction.apply()

        self.assertEqual(
            self.destruction.status,
            StockDestruction.DestructionStatus.RECORDED,
        )

    def test_partial_destruction_updates_quantities(self):
        self._add_line("3")

        result = self.destruction.apply()

        entry =        StockEntry.objects.get(pk=self.entry.pk)
        item = InventoryItem.objects.get(pk=self.item.pk)

        self.assertEqual(entry.remaining_quantity, Decimal("7.00"))
        self.assertEqual(item.stock_quantity, Decimal("7.00"))
        self.assertEqual(
            self.destruction.status,
            StockDestruction.DestructionStatus.COMPLETED,
        )

        self.assertEqual(result["destruction_id"], self.destruction.pk)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            result["destroyed_quantities"][self.item.pk],
            Decimal("3.00"),
        )

    def test_total_destruction_empties_the_lot(self):
        self._add_line("10")

        self.destruction.apply()

        entry =        StockEntry.objects.get(pk=self.entry.pk)
        item = InventoryItem.objects.get(pk=self.item.pk)

        self.assertEqual(entry.remaining_quantity, Decimal("0.00"))
        self.assertEqual(item.stock_quantity, Decimal("0.00"))

    def test_multiple_lines_on_same_lot_are_cumulated(self):
        self._add_line("4")
        self._add_line("6")

        self.destruction.apply()

        entry =        StockEntry.objects.get(pk=self.entry.pk)
        self.assertEqual(entry.remaining_quantity, Decimal("0.00"))

    def test_cumulated_lines_exceeding_lot_quantity_are_refused(self):
        self._add_line("6")
        self._add_line("6")

        with self.assertRaises(ValidationError) as ctx:
            self.destruction.apply()

        self.assertIn("quantity", ctx.exception.error_dict)

        entry =        StockEntry.objects.get(pk=self.entry.pk)
        self.assertEqual(entry.remaining_quantity, Decimal("10.00"))
        self.assertEqual(
            self.destruction.status,
            StockDestruction.DestructionStatus.RECORDED,
        )

    def test_lines_of_several_items_are_supported(self):
        other_item = create_item(name="Autre produit")
        other_entry = create_entry(other_item, "20", "1.00")

        self._add_line("3")
        StockDestructionLine.objects.create(
            destruction=self.destruction,
            item=other_item,
            stock_entry=other_entry,
            quantity=to_decimal("5"),
        )

        result = self.destruction.apply()

        other_item = InventoryItem.objects.get(pk=other_item.pk)
        self.assertEqual(other_item.stock_quantity, Decimal("15.00"))
        self.assertEqual(
            result["destroyed_quantities"][other_item.pk],
            Decimal("5.00"),
        )

    def test_quantity_exceeding_physical_stock_is_refused(self):
        # Incohérence simulée : le stock physique est inférieur aux
        # quantités restantes des lots.
        InventoryItem.objects.filter(pk=self.item.pk).update(
            stock_quantity=to_decimal("4"),
        )
        self._add_line("6")

        with self.assertRaises(ValidationError) as ctx:
            self.destruction.apply()

        self.assertIn("quantity", ctx.exception.error_dict)

        entry =        StockEntry.objects.get(pk=self.entry.pk)
        self.assertEqual(entry.remaining_quantity, Decimal("10.00"))

    def test_second_execution_is_refused(self):
        self._add_line("3")
        self.destruction.apply()

        with self.assertRaises(ValidationError):
            self.destruction.apply()

        entry =        StockEntry.objects.get(pk=self.entry.pk)
        self.assertEqual(entry.remaining_quantity, Decimal("7.00"))


class StockDestructionAlertSyncTests(TestCase):

    def test_destruction_triggers_low_stock_alert(self):
        item = create_item(reorder_point=to_decimal("50"))
        create_entry(item, "60", "2.00")

        self.assertFalse(StockAlert.objects.exists())

        destruction = StockDestruction.objects.create(reason="Perte")
        StockDestructionLine.objects.create(
            destruction=destruction,
            item=item,
            stock_entry=item.entries.first(),
            quantity=to_decimal("20"),
        )
        destruction.apply()

        alert = StockAlert.objects.get(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.LOW_STOCK,
        )
        self.assertEqual(alert.current_quantity, Decimal("40.00"))

    def test_total_destruction_removes_expiration_alert(self):
        item = create_item(is_perishable=True)
        create_entry(
            item,
            "10",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=5),
        )

        self.assertTrue(StockAlert.objects.exists())

        destruction = StockDestruction.objects.create(reason="Péremption")
        StockDestructionLine.objects.create(
            destruction=destruction,
            item=item,
            stock_entry=item.entries.first(),
            quantity=to_decimal("10"),
        )
        destruction.apply()

        self.assertFalse(
            StockAlert.objects.filter(
                item_id=item.pk,
                alert_type=StockAlert.AlertType.EXPIRATION,
            ).exists()
        )
