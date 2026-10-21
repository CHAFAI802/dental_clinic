"""
Tests du modèle StockAlert (alertes de stock).

Références (code actuel du dépôt) :
- inventory/models.py : StockAlert.clean / sync_for_item / sync_all,
  contraintes d'unicité
"""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from inventory.models import InventoryItem, StockAlert, StockEntry, StockExit

from .base import create_entry, create_item, to_decimal


class StockAlertCleanTests(TestCase):

    def test_valid_low_stock_alert(self):
        item = create_item(reorder_point=to_decimal("10"))

        alert = StockAlert(
            item=item,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            current_quantity=to_decimal("5"),
        )
        alert.full_clean()  # ne doit pas lever d'erreur

    def test_low_stock_alert_requires_reorder_point(self):
        item = create_item()

        alert = StockAlert(
            item=item,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            current_quantity=to_decimal("5"),
        )

        with self.assertRaises(ValidationError) as ctx:
            alert.full_clean()

        self.assertIn("item", ctx.exception.error_dict)

    def test_low_stock_alert_cannot_reference_a_lot(self):
        item = create_item(reorder_point=to_decimal("10"))
        entry = create_entry(item, "5", "2.00")

        alert = StockAlert(
            item=item,
            stock_entry=entry,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            current_quantity=to_decimal("5"),
        )

        with self.assertRaises(ValidationError) as ctx:
            alert.full_clean()

        self.assertIn("stock_entry", ctx.exception.error_dict)

    def test_expiration_alert_requires_a_lot(self):
        item = create_item(is_perishable=True)

        alert = StockAlert(
            item=item,
            alert_type=StockAlert.AlertType.EXPIRATION,
            current_quantity=to_decimal("5"),
        )

        with self.assertRaises(ValidationError) as ctx:
            alert.full_clean()

        self.assertIn("stock_entry", ctx.exception.error_dict)

    def test_expiration_alert_requires_matching_item_and_lot(self):
        item = create_item(is_perishable=True)
        other_item = create_item(name="Autre produit", is_perishable=True)
        entry = create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=90),
        )

        alert = StockAlert(
            item=other_item,
            stock_entry=entry,
            alert_type=StockAlert.AlertType.EXPIRATION,
            current_quantity=to_decimal("5"),
        )

        with self.assertRaises(ValidationError) as ctx:
            alert.full_clean()

        self.assertIn("stock_entry", ctx.exception.error_dict)

    def test_expiration_alert_requires_perishable_item(self):
        item = create_item(is_perishable=True)
        entry = create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=90),
        )
        item.is_perishable = False

        alert = StockAlert(
            item=item,
            stock_entry=entry,
            alert_type=StockAlert.AlertType.EXPIRATION,
            current_quantity=to_decimal("5"),
        )

        with self.assertRaises(ValidationError) as ctx:
            alert.full_clean()

        self.assertIn("item", ctx.exception.error_dict)

    def test_negative_current_quantity_is_refused(self):
        item = create_item(reorder_point=to_decimal("10"))

        alert = StockAlert(
            item=item,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            current_quantity=to_decimal("-1"),
        )

        with self.assertRaises(ValidationError) as ctx:
            alert.full_clean()

        self.assertIn("current_quantity", ctx.exception.error_dict)


class StockAlertPersistenceTests(TestCase):
    """DOCUMENTÉ (catégorie E) : StockAlert ne surcharge pas save(),
    les règles de clean() ne sont donc pas appliquées à l'enregistrement
    direct d'une alerte."""

    def test_direct_create_bypasses_clean_rules(self):
        item = create_item()  # sans seuil de réapprovisionnement

        alert = StockAlert.objects.create(
            item=item,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            current_quantity=to_decimal("5"),
        )

        self.assertIsNotNone(alert.pk)

    def test_unique_low_stock_alert_per_item(self):
        item = create_item(reorder_point=to_decimal("10"))
        StockAlert.objects.create(
            item=item,
            alert_type=StockAlert.AlertType.LOW_STOCK,
            current_quantity=to_decimal("5"),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StockAlert.objects.create(
                    item=item,
                    alert_type=StockAlert.AlertType.LOW_STOCK,
                    current_quantity=to_decimal("4"),
                )

    def test_unique_expiration_alert_per_entry(self):
        item = create_item(is_perishable=True)
        # Date hors fenêtre d'alerte : aucune alerte n'est créée
        # automatiquement par StockEntry.apply().
        entry = create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=90),
        )
        StockAlert.objects.create(
            item=item,
            stock_entry=entry,
            alert_type=StockAlert.AlertType.EXPIRATION,
            current_quantity=to_decimal("5"),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StockAlert.objects.create(
                    item=item,
                    stock_entry=entry,
                    alert_type=StockAlert.AlertType.EXPIRATION,
                    current_quantity=to_decimal("5"),
                )


class StockAlertSyncTests(TestCase):

    def test_low_stock_alert_created_at_or_below_threshold(self):
        item = create_item(reorder_point=to_decimal("10"))
        create_entry(item, "10", "2.00")

        alert = StockAlert.objects.get(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.LOW_STOCK,
        )
        # La règle codée est stock_quantity <= reorder_point.
        self.assertEqual(alert.current_quantity, Decimal("10.00"))

    def test_no_low_stock_alert_above_threshold(self):
        item = create_item(reorder_point=to_decimal("10"))
        create_entry(item, "11", "2.00")

        self.assertFalse(StockAlert.objects.exists())

    def test_low_stock_alert_quantity_is_updated(self):
        item = create_item(reorder_point=to_decimal("100"))
        create_entry(item, "10", "2.00")
        create_entry(item, "5", "2.00")

        alerts = StockAlert.objects.filter(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.LOW_STOCK,
        )

        self.assertEqual(alerts.count(), 1)
        self.assertEqual(alerts.first().current_quantity, Decimal("15.00"))

    def test_low_stock_alert_deleted_when_stock_recovers(self):
        item = create_item(reorder_point=to_decimal("10"))
        create_entry(item, "5", "2.00")

        create_entry(item, "10", "2.00")  # stock = 15 > 10

        self.assertFalse(StockAlert.objects.exists())

    def test_low_stock_alert_deleted_when_reorder_point_removed(self):
        item = create_item(reorder_point=to_decimal("10"))
        create_entry(item, "5", "2.00")

        self.assertTrue(StockAlert.objects.exists())

        InventoryItem.objects.filter(pk=item.pk).update(reorder_point=None)
        StockAlert.sync_for_item(item.pk)

        self.assertFalse(StockAlert.objects.exists())

    def test_expiration_alert_created_for_expired_lot(self):
        item = create_item(is_perishable=True)
        create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() - timedelta(days=1),
        )

        alert = StockAlert.objects.get(
            item_id=item.pk,
            alert_type=StockAlert.AlertType.EXPIRATION,
        )
        self.assertEqual(alert.current_quantity, Decimal("5.00"))

    def test_expiration_alert_not_created_outside_window(self):
        item = create_item(is_perishable=True, expiration_alert_days=30)
        create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=31),
        )

        self.assertFalse(StockAlert.objects.exists())

    def test_expiration_alert_respects_item_window(self):
        item = create_item(is_perishable=True, expiration_alert_days=60)
        create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=45),
        )

        self.assertTrue(
            StockAlert.objects.filter(
                item_id=item.pk,
                alert_type=StockAlert.AlertType.EXPIRATION,
            ).exists()
        )

    def test_expiration_alert_removed_when_lot_is_consumed(self):
        item = create_item(is_perishable=True)
        entry = create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=5),
        )

        StockExit(
            item=item,
            quantity=to_decimal("5"),
            usage_type="soin",
        ).apply()

        entry.refresh_from_db()
        self.assertEqual(entry.remaining_quantity, Decimal("0.00"))
        self.assertFalse(StockAlert.objects.exists())

    def test_non_perishable_item_never_has_expiration_alert(self):
        item = create_item()
        create_entry(item, "5", "2.00")

        StockAlert.sync_for_item(item.pk)

        self.assertFalse(
            StockAlert.objects.filter(
                alert_type=StockAlert.AlertType.EXPIRATION,
            ).exists()
        )

    def test_obsolete_expiration_alert_is_removed(self):
        item = create_item(is_perishable=True, expiration_alert_days=30)
        entry = create_entry(
            item,
            "5",
            "2.00",
            expiration_date=timezone.localdate() + timedelta(days=5),
        )

        self.assertTrue(StockAlert.objects.exists())

        # Le lot ne doit plus être signalé : sa date sort de la fenêtre.
        StockEntry.objects.filter(pk=entry.pk).update(
            expiration_date=timezone.localdate() + timedelta(days=90),
        )
        StockAlert.sync_for_item(item.pk)

        self.assertFalse(StockAlert.objects.exists())

    def test_sync_all_synchronizes_every_item(self):
        item_a = create_item(name="Produit A", reorder_point=to_decimal("10"))
        item_b = create_item(name="Produit B", reorder_point=to_decimal("10"))
        create_entry(item_a, "2", "1.00")
        create_entry(item_b, "3", "1.00")

        StockAlert.sync_all()

        self.assertEqual(StockAlert.objects.count(), 2)

    def test_sync_never_changes_stock_quantities(self):
        item = create_item(reorder_point=to_decimal("10"))
        create_entry(item, "2", "1.00")

        StockAlert.sync_for_item(item.pk)

        item = InventoryItem.objects.get(pk=item.pk)
        self.assertEqual(item.stock_quantity, Decimal("2.00"))
