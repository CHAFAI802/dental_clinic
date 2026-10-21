"""
Tests des serializers de l'application inventory.

Références (code actuel du dépôt) :
- inventory/serializers.py
"""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError

from accounts.models import User
from inventory.models import (
    InventoryItem,
    StockAlert,
    StockDestruction,
    StockDestructionLine,
    StockEntry,
    StockExit,
)
from inventory.serializers import (
    InventoryFamilySerializer,
    InventoryItemSerializer,
    StockAlertSerializer,
    StockDestructionLineSerializer,
    StockDestructionSerializer,
    StockEntrySerializer,
    StockExitAllocationSerializer,
    StockExitSerializer,
    SupplierSerializer,
    UnitSerializer,
)

from .base import create_entry, create_family, create_item, to_decimal


class InventoryItemSerializerTests(TestCase):

    def test_sku_and_stock_quantity_are_read_only(self):
        family = create_family(code="GANT", name="Gants")

        serializer = InventoryItemSerializer(
            data={
                "name": "Gants nitrile",
                "family": family.pk,
                "sku": "DCL-CON-GANT-999999",
                "stock_quantity": "42.00",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        item = serializer.save()

        self.assertEqual(item.sku, "DCL-CON-GANT-000001")
        self.assertEqual(item.stock_quantity, Decimal("0.00"))
        self.assertNotIn("sku", serializer.validated_data)
        self.assertNotIn("stock_quantity", serializer.validated_data)


class InventoryFamilySerializerTests(TestCase):

    def test_next_sku_number_is_read_only(self):
        from inventory.models import InventoryCategory

        category = InventoryCategory.objects.create(
            code="CON",
            name="Consommable",
        )

        serializer = InventoryFamilySerializer(
            data={
                "category": category.pk,
                "name": "Gants",
                "code": "GANT",
                "next_sku_number": "42",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        family = serializer.save()

        self.assertEqual(family.next_sku_number, 1)
        self.assertNotIn("next_sku_number", serializer.validated_data)


class UnitSerializerTests(TestCase):

    def test_created_at_is_read_only(self):
        serializer = UnitSerializer(
            data={
                "name": "Pièce",
                "symbol": "pcs",
                "created_at": "2000-01-01T00:00:00Z",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        unit = serializer.save()

        self.assertNotEqual(
            str(unit.created_at),
            "2000-01-01T00:00:00+00:00",
        )


class StockEntrySerializerTests(TestCase):

    def setUp(self):
        self.item = create_item()
        self.entry = create_entry(self.item, "10", "2.00")

    def test_quantity_must_be_positive(self):
        serializer = StockEntrySerializer(
            data={
                "item": self.item.pk,
                "quantity": "0",
                "unit_cost": "2.00",
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_negative_unit_cost_is_refused(self):
        serializer = StockEntrySerializer(
            data={
                "item": self.item.pk,
                "quantity": "5",
                "unit_cost": "-1.00",
            },
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("unit_cost", serializer.errors)

    def test_managed_fields_are_read_only(self):
        user = User.objects.create_user(
            email="serializer@example.com",
            first_name="Test",
            last_name="Serializer",
            role=User.Role.ACCOUNTANT,
            password="password",
        )

        serializer = StockEntrySerializer(
            data={
                "item": self.item.pk,
                "quantity": "5",
                "unit_cost": "2.00",
                "remaining_quantity": "99.00",
                "total_cost": "999.00",
                "received_by": user.pk,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        for field in ("remaining_quantity", "total_cost", "received_by"):
            self.assertNotIn(field, serializer.validated_data)

    def test_create_applies_the_entry(self):
        serializer = StockEntrySerializer(
            data={
                "item": self.item.pk,
                "quantity": "5",
                "unit_cost": "2.00",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        entry = serializer.save()

        self.assertIsNotNone(entry.pk)
        self.assertEqual(entry.total_cost, Decimal("10.00"))

        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("15.00"))

    def test_update_is_refused(self):
        serializer = StockEntrySerializer(
            instance=self.entry,
            data={"quantity": "5", "unit_cost": "2.00"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(DRFValidationError):
            serializer.save()

    def test_model_validation_errors_are_not_converted_to_drf_errors(self):
        # DOCUMENTÉ (catégorie A du rapport) : les erreurs levées par
        # StockEntry.clean() sont des django ValidationError et ne sont
        # pas traduites en erreurs 400 par ce serializer.
        item = create_item(is_perishable=True)

        serializer = StockEntrySerializer(
            data={
                "item": item.pk,
                "quantity": "5",
                "unit_cost": "2.00",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(DjangoValidationError):
            serializer.save()


class StockExitSerializerTests(TestCase):

    def setUp(self):
        self.item = create_item()
        create_entry(self.item, "10", "2.00")

    def test_create_applies_the_exit(self):
        serializer = StockExitSerializer(
            data={
                "item": self.item.pk,
                "quantity": "3",
                "usage_type": "soin",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        exit_instance = serializer.save()

        self.assertIsNotNone(exit_instance.pk)

        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("7.00"))

    def test_update_is_refused(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("1"),
            usage_type="soin",
        )
        exit_instance.apply()

        serializer = StockExitSerializer(
            instance=exit_instance,
            data={"quantity": "2", "usage_type": "soin"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(DRFValidationError):
            serializer.save()


class StockExitAllocationSerializerTests(TestCase):

    def test_every_field_is_read_only(self):
        serializer = StockExitAllocationSerializer()

        for field_name, field in serializer.fields.items():
            self.assertTrue(
                field.read_only,
                f"Le champ {field_name} devrait être en lecture seule.",
            )


class StockAlertSerializerTests(TestCase):

    def test_current_quantity_and_created_at_are_read_only(self):
        item = create_item()

        serializer = StockAlertSerializer(
            data={
                "item": item.pk,
                "alert_type": StockAlert.AlertType.LOW_STOCK,
                "current_quantity": "5.00",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertNotIn("current_quantity", serializer.validated_data)
        self.assertNotIn("created_at", serializer.validated_data)


class StockDestructionSerializerTests(TestCase):

    def test_status_is_read_only(self):
        serializer = StockDestructionSerializer(
            data={
                "reason": "Produits périmés",
                "status": StockDestruction.DestructionStatus.COMPLETED,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        destruction = serializer.save()

        self.assertEqual(
            destruction.status,
            StockDestruction.DestructionStatus.RECORDED,
        )

    def test_destroyed_by_is_read_only(self):
        user = User.objects.create_user(
            email="destroy@example.com",
            first_name="Test",
            last_name="Destroy",
            role=User.Role.ADMINISTRATOR,
            password="password",
        )

        serializer = StockDestructionSerializer(
            data={
                "reason": "Produits périmés",
                "destroyed_by": user.pk,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        destruction = serializer.save()

        self.assertIsNone(destruction.destroyed_by_id)
        self.assertNotIn("destroyed_by", serializer.validated_data)


class StockDestructionLineSerializerTests(TestCase):

    def setUp(self):
        self.destruction = StockDestruction.objects.create(
            reason="Produits périmés",
        )
        self.item = create_item()
        self.entry = create_entry(self.item, "10", "2.00")

    def test_valid_line_is_created(self):
        serializer = StockDestructionLineSerializer(
            data={
                "destruction": self.destruction.pk,
                "item": self.item.pk,
                "stock_entry": self.entry.pk,
                "quantity": "3.00",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        line = serializer.save()

        self.assertIsNotNone(line.pk)
        self.assertEqual(line.quantity, Decimal("3.00"))

    def test_non_positive_quantity_is_only_refused_at_model_level(self):
        # DOCUMENTÉ : le serializer n'applique pas les règles de
        # StockDestructionLine.clean() ; la quantité 0 passe la
        # validation DRF et seule la création échoue (ValidationError
        # Django levée par model.save()).
        serializer = StockDestructionLineSerializer(
            data={
                "destruction": self.destruction.pk,
                "item": self.item.pk,
                "stock_entry": self.entry.pk,
                "quantity": "0",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(DjangoValidationError):
            serializer.save()

    def test_updated_at_is_read_only(self):
        serializer = StockDestructionLineSerializer(
            data={
                "destruction": self.destruction.pk,
                "item": self.item.pk,
                "stock_entry": self.entry.pk,
                "quantity": "1.00",
                "created_at": "2000-01-01T00:00:00Z",
                "updated_at": "2000-01-01T00:00:00Z",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        self.assertNotIn("updated_at", serializer.validated_data)
        self.assertNotIn("created_at", serializer.validated_data)

    def test_line_cannot_reference_completed_destruction(self):
        StockDestructionLine.objects.create(
            destruction=self.destruction,
            item=self.item,
            stock_entry=self.entry,
            quantity=to_decimal("10"),
        )
        self.destruction.apply()

        serializer = StockDestructionLineSerializer(
            data={
                "destruction": self.destruction.pk,
                "item": self.item.pk,
                "stock_entry": self.entry.pk,
                "quantity": "1.00",
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(DjangoValidationError):
            serializer.save()


class SupplierSerializerTests(TestCase):

    def test_supplier_serializer_fields_match_model(self):
        serializer = SupplierSerializer()

        expected_fields = {
            "id",
            "name",
            "contact_name",
            "phone",
            "email",
            "address",
            "notes",
        }

        self.assertEqual(set(serializer.fields.keys()), expected_fields)
        self.assertEqual(set(serializer.Meta.read_only_fields), {"id"})
