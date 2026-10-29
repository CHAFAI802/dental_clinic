"""
Tests du modèle StockExit et StockExitAllocation (sorties de stock).

Références (code actuel du dépôt) :
- inventory/models.py : StockExit.clean / save / delete / apply,
  StockExitAllocation.clean
- La sélection est FIFO pour les produits non périssables et FEFO
  pour les produits périssables ; les lots expirés sont exclus des
  sorties mais restent dans le stock physique.
"""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from inventory.models import (
    InventoryItem,
    StockAlert,
    StockEntry,
    StockExit,
    StockExitAllocation,
)

from .base import create_entry, create_item, build_entry, to_decimal


class StockExitCleanTests(TestCase):

    def setUp(self):
        self.item = create_item()
        create_entry(self.item, "10", "2.00")

    def _build_exit(self, **kwargs):
        params = {
            "item": self.item,
            "quantity": to_decimal("1"),
            "usage_type": "soin",
        }
        params.update(kwargs)
        return StockExit(**params)

    def test_quantity_must_be_strictly_positive(self):
        exit_instance = self._build_exit(quantity=to_decimal("0"))

        with self.assertRaises(ValidationError) as ctx:
            exit_instance.clean()

        self.assertIn("quantity", ctx.exception.error_dict)

    def test_inactive_item_is_refused(self):
        item = create_item(name="Produit inactif", is_active=False)
        create_entry(item, "5", "2.00")

        exit_instance = self._build_exit(item=item)

        with self.assertRaises(ValidationError) as ctx:
            exit_instance.clean()

        self.assertIn("item", ctx.exception.error_dict)

    def test_invalid_selection_mode_is_refused(self):
        exit_instance = self._build_exit(selection_mode="autre")

        with self.assertRaises(ValidationError) as ctx:
            exit_instance.clean()

        self.assertIn("selection_mode", ctx.exception.error_dict)


class StockExitFIFOTests(TestCase):
    """Produits non périssables : ordre de réception (FIFO)."""

    def setUp(self):
        self.item = create_item()
        now = timezone.now()

        self.lot_older = create_entry(
            self.item,
            "10",
            "1.00",
            received_at=now - timedelta(days=3),
            batch_number="A",
        )
        self.lot_middle = create_entry(
            self.item,
            "10",
            "2.00",
            received_at=now - timedelta(days=2),
            batch_number="B",
        )
        self.lot_newer = create_entry(
            self.item,
            "10",
            "3.00",
            received_at=now - timedelta(days=1),
            batch_number="C",
        )

    def test_exit_consumes_oldest_lots_first(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("15"),
            usage_type="soin",
        )
        exit_instance.apply()

        self.lot_older.refresh_from_db()
        self.lot_middle.refresh_from_db()
        self.lot_newer.refresh_from_db()

        self.assertEqual(self.lot_older.remaining_quantity, Decimal("0.00"))
        self.assertEqual(self.lot_middle.remaining_quantity, Decimal("5.00"))
        self.assertEqual(self.lot_newer.remaining_quantity, Decimal("10.00"))

    def test_allocations_are_recorded_in_fifo_order(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("15"),
            usage_type="soin",
        )
        exit_instance.apply()

        allocations = list(
            StockExitAllocation.objects
            .filter(stock_exit_id=exit_instance.pk)
            .order_by("pk")
        )

        self.assertEqual(len(allocations), 2)
        self.assertEqual(allocations[0].stock_entry_id, self.lot_older.pk)
        self.assertEqual(allocations[0].quantity, Decimal("10.00"))
        self.assertEqual(allocations[1].stock_entry_id, self.lot_middle.pk)
        self.assertEqual(allocations[1].quantity, Decimal("5.00"))

    def test_exit_updates_item_stock_quantity(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("15"),
            usage_type="soin",
        )
        returned = exit_instance.apply()

        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("15.00"))
        self.assertEqual(returned, Decimal("15.00"))

    def test_exit_exactly_matching_available_quantity_is_allowed(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("30"),
            usage_type="soin",
        )
        exit_instance.apply()

        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("0.00"))


class StockExitFEFOTests(TestCase):
    """Produits périssables : date de péremption la plus proche (FEFO)."""

    def setUp(self):
        self.item = create_item(is_perishable=True)
        today = timezone.localdate()

        self.lot_late = create_entry(
            self.item,
            "10",
            "1.00",
            expiration_date=today + timedelta(days=20),
            batch_number="LATE",
        )
        self.lot_soon = create_entry(
            self.item,
            "10",
            "2.00",
            expiration_date=today + timedelta(days=5),
            batch_number="SOON",
        )
        self.lot_middle = create_entry(
            self.item,
            "10",
            "3.00",
            expiration_date=today + timedelta(days=10),
            batch_number="MIDDLE",
        )

    def test_exit_consumes_nearest_expiration_first(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("15"),
            usage_type="soin",
        )
        exit_instance.apply()

        self.lot_soon.refresh_from_db()
        self.lot_middle.refresh_from_db()
        self.lot_late.refresh_from_db()

        self.assertEqual(self.lot_soon.remaining_quantity, Decimal("0.00"))
        self.assertEqual(self.lot_middle.remaining_quantity, Decimal("5.00"))
        self.assertEqual(self.lot_late.remaining_quantity, Decimal("10.00"))



class StockExitExpiredLotTests(TestCase):
    """Un lot expiré reste au stock physique mais n'est pas
    disponible pour une sortie."""

    def setUp(self):
        self.item = create_item(is_perishable=True)
        self.expired_lot = create_entry(
            self.item,
            "10",
            "1.00",
            expiration_date=timezone.localdate() - timedelta(days=1),
            batch_number="EXPIRED",
        )

    def test_expired_lot_is_excluded_from_exit(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("5"),
            usage_type="soin",
        )

        with self.assertRaises(ValidationError) as ctx:
            exit_instance.apply()

        self.assertIn("quantity", ctx.exception.error_dict)

        self.expired_lot.refresh_from_db()
        self.assertEqual(self.expired_lot.remaining_quantity, Decimal("10.00"))
        self.assertIsNone(exit_instance.pk)

    def test_expired_lot_still_counts_in_physical_stock(self):
        item = InventoryItem.objects.get(pk=self.item.pk)

        self.assertEqual(item.stock_quantity, Decimal("10.00"))
        self.assertEqual(
            self.expired_lot.remaining_quantity,
            Decimal("10.00"),
        )

    def test_exit_succeeds_when_fresh_lot_covers_the_demand(self):
        fresh_lot = create_entry(
            self.item,
            "10",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=10),
            batch_number="FRESH",
        )

        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("5"),
            usage_type="soin",
        )
        exit_instance.apply()

        allocations = StockExitAllocation.objects.filter(
            stock_exit_id=exit_instance.pk,
        )

        self.assertEqual(allocations.count(), 1)
        self.assertEqual(allocations.first().stock_entry_id, fresh_lot.pk)

        self.expired_lot.refresh_from_db()
        self.assertEqual(
            self.expired_lot.remaining_quantity,
            Decimal("10.00"),
        )


class StockExitGuardsTests(TestCase):

    def setUp(self):
        self.item = create_item()
        self.entry = create_entry(self.item, "10", "2.00")

    def _apply_exit(self, quantity="4"):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal(quantity),
            usage_type="soin",
        )
        exit_instance.apply()
        return exit_instance

    def test_exit_requires_usage_type(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("1"),
        )

        with self.assertRaises(ValidationError):
            exit_instance.apply()

        self.assertIsNone(exit_instance.pk)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.remaining_quantity, Decimal("10.00"))

    def test_exit_is_refused_when_stock_is_insufficient(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("15"),
            usage_type="soin",
        )

        with self.assertRaises(ValidationError) as ctx:
            exit_instance.apply()

        self.assertIn("quantity", ctx.exception.error_dict)

        # Transaction : rien n'est enregistré.
        self.assertIsNone(exit_instance.pk)
        self.assertEqual(StockExitAllocation.objects.count(), 0)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.remaining_quantity, Decimal("10.00"))

        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("10.00"))

    def test_exit_exceeding_physical_stock_is_refused(self):
        # Cas limite : les lots restants sont supérieurs au stock
        # physique enregistré (incohérence simulée en base).
        InventoryItem.objects.filter(pk=self.item.pk).update(
            stock_quantity=to_decimal("5"),
        )

        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("8"),
            usage_type="soin",
        )

        with self.assertRaises(ValidationError) as ctx:
            exit_instance.apply()

        self.assertIn("quantity", ctx.exception.error_dict)
        self.assertIsNone(exit_instance.pk)

    def test_direct_save_of_new_exit_is_refused(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("1"),
            usage_type="soin",
        )

        with self.assertRaises(ValidationError):
            exit_instance.save()

    def test_recorded_exit_cannot_be_modified(self):
        exit_instance = self._apply_exit()
        exit_instance.quantity = to_decimal("9")

        with self.assertRaises(ValidationError):
            exit_instance.save()

    def test_recorded_exit_cannot_be_deleted(self):
        exit_instance = self._apply_exit()

        with self.assertRaises(ValidationError):
            exit_instance.delete()

        self.assertEqual(StockExit.objects.count(), 1)

    def test_apply_is_refused_twice(self):
        exit_instance = self._apply_exit()

        with self.assertRaises(ValidationError):
            exit_instance.apply()

    def test_allocation_quantity_must_be_positive(self):
        exit_instance = self._apply_exit()

        allocation = StockExitAllocation(
            stock_exit=exit_instance,
            stock_entry=self.entry,
            quantity=to_decimal("0"),
        )

        with self.assertRaises(ValidationError) as ctx:
            allocation.full_clean()

        self.assertIn("quantity", ctx.exception.error_dict)


class StockExitSelectionModeTests(TestCase):

    def setUp(self):
        self.item = create_item()
        create_entry(self.item, "10", "2.00")

    def test_manual_mode_requires_allocations(self):
        # DOCUMENTÉ (nouveau comportement) :
        # En mode MANUAL, l'utilisateur doit fournir une liste de lots
        # (manual_allocations). Sans allocations, la sortie est refusée.
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("3"),
            usage_type="soin",
            selection_mode=StockExit.SelectionMode.MANUAL,
        )

        with self.assertRaises(ValidationError) as ctx:
            exit_instance.apply()

        self.assertIn("manual_allocations", ctx.exception.error_dict)

    def test_manual_mode_allocations_are_applied(self):
        # Le mode MANUAL applique les lots explicitement sélectionnés,
        # en respectant toutes les règles métier (quantité, appartenance,
        # péremption, cohérence avec le stock physique).
        fresh_lot = create_entry(
            self.item,
            "10",
            "2.00",
            batch_number="FRESH",
        )

        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("4"),
            usage_type="soin",
            selection_mode=StockExit.SelectionMode.MANUAL,
            manual_allocations=[
                {"stock_entry": fresh_lot.pk, "quantity": 4},
            ],
        )
        exit_instance.apply()

        allocations = StockExitAllocation.objects.filter(
            stock_exit_id=exit_instance.pk,
        )

        self.assertEqual(allocations.count(), 1)
        self.assertEqual(allocations.first().quantity, Decimal("4.00"))

        fresh_lot.refresh_from_db()
        self.assertEqual(fresh_lot.remaining_quantity, Decimal("6.00"))

        item = InventoryItem.objects.get(pk=self.item.pk)
        # setUp() crée un premier lot de 10, puis le test en ajoute un
        # second de 10 : le stock global passe donc de 20 à 16.
        self.assertEqual(item.stock_quantity, Decimal("16.00"))


    def test_default_selection_mode_is_automatic(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("1"),
            usage_type="soin",
        )

        self.assertEqual(
            exit_instance.selection_mode,
            StockExit.SelectionMode.AUTOMATIC,
        )


class StockExitAlertSyncTests(TestCase):

    def test_exit_triggers_low_stock_alert(self):
        item = create_item(reorder_point=to_decimal("100"))
        create_entry(item, "150", "2.00")

        self.assertFalse(StockAlert.objects.exists())

        StockExit(
            item=item,
            quantity=to_decimal("60"),
            usage_type="soin",
        ).apply()

        alert = StockAlert.objects.get(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.LOW_STOCK,
        )
        self.assertEqual(alert.current_quantity, Decimal("90.00"))

    def test_exit_consumed_lot_removes_expiration_alert(self):
        item = create_item(is_perishable=True)
        create_entry(
            item,
            "10",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=5),
        )

        self.assertTrue(
            StockAlert.objects.filter(
                item_id=item.pk,
                alert_type=StockAlert.AlertType.EXPIRATION,
            ).exists()
        )

        StockExit(
            item=item,
            quantity=to_decimal("10"),
            usage_type="soin",
        ).apply()

        self.assertFalse(
            StockAlert.objects.filter(
                item_id=item.pk,
                alert_type=StockAlert.AlertType.EXPIRATION,
            ).exists()
        )

    def test_exit_updates_expiration_alert_quantity(self):
        item = create_item(is_perishable=True)
        create_entry(
            item,
            "10",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=5),
        )

        StockExit(
            item=item,
            quantity=to_decimal("4"),
            usage_type="soin",
        ).apply()

        alert = StockAlert.objects.get(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.EXPIRATION,
        )
        self.assertEqual(alert.current_quantity, Decimal("6.00"))
