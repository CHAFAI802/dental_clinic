"""
Tests des modèles de catalogue de l'application inventory.

Références (code actuel du dépôt) :
- inventory/models.py : InventoryCategory, InventoryFamily, Unit, InventoryItem
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from inventory.models import (
    InventoryCategory,
    InventoryFamily,
    InventoryItem,
    Unit,
)

from .base import create_category, create_family, create_item, to_decimal


class InventoryCategoryTests(TestCase):

    def test_create_category_with_code(self):
        category = create_category(code="CON", name="Consommable")

        self.assertEqual(category.code, "CON")
        self.assertEqual(category.name, "Consommable")

    def test_code_must_be_unique(self):
        create_category(code="CON")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryCategory.objects.create(code="CON", name="Autre")

    def test_multiple_categories_without_code_are_allowed(self):
        # `code` est nullable : Postgres autorise plusieurs NULL.
        InventoryCategory.objects.create(name="Sans code A")
        InventoryCategory.objects.create(name="Sans code B")

        self.assertEqual(InventoryCategory.objects.count(), 2)

    def test_deleting_parent_nullifies_child(self):
        # on_delete=SET_NULL sur le champ `parent`.
        parent = create_category(code="MAT", name="Matériel")
        child = InventoryCategory.objects.create(
            name="Sous-catégorie",
            parent=parent,
        )

        parent.delete()

        child.refresh_from_db()
        self.assertIsNone(child.parent)

    def test_str_returns_name(self):
        category = create_category(name="Consommable")

        self.assertEqual(str(category), "Consommable")


class InventoryFamilyTests(TestCase):

    def test_create_family(self):
        family = create_family(code="GANT", name="Gants")

        self.assertEqual(family.code, "GANT")
        self.assertEqual(family.next_sku_number, 1)
        self.assertTrue(family.is_active)

    def test_code_is_uppercased(self):
        # NOTE : la normalisation (strip/upper) est réalisée dans
        # InventoryFamily.clean(), mais full_clean() valide d'abord
        # la longueur maximale (6) : un code comportant des espaces
        # est rejeté par max_length avant d'être normalisé.
        family = create_family(code="gant", name="Gants")

        self.assertEqual(family.code, "GANT")

    def test_code_must_be_alphanumeric(self):
        with self.assertRaises(ValidationError) as ctx:
            create_family(code="GA-NT", name="Gants")

        self.assertIn("code", ctx.exception.error_dict)

    def test_code_is_required(self):
        with self.assertRaises(ValidationError) as ctx:
            create_family(code="", name="Gants")

        self.assertIn("code", ctx.exception.error_dict)

    def test_code_must_be_unique(self):
        create_family(code="GANT")

        # InventoryFamily.save() appelle full_clean() : l'unicité est
        # vérifiée par Django avant l'écriture en base.
        with self.assertRaises(ValidationError) as ctx:
            InventoryFamily.objects.create(
                category=create_category(),
                name="Autre gants",
                code="GANT",
            )

        self.assertIn("code", ctx.exception.error_dict)

    def test_family_requires_category_with_valid_code(self):
        # InventoryCategory.code est nullable mais une famille exige
        # une catégorie MAT ou CON (InventoryFamily.clean).
        category = InventoryCategory.objects.create(name="Sans code")

        with self.assertRaises(ValidationError) as ctx:
            create_family(category=category, code="GANT")

        self.assertIn("category", ctx.exception.error_dict)

    def test_code_is_immutable_when_items_exist(self):
        family = create_family(code="GANT")
        create_item(family=family)

        family.code = "AUTRE"

        with self.assertRaises(ValidationError) as ctx:
            family.save()

        self.assertIn("code", ctx.exception.error_dict)

    def test_code_can_be_changed_without_items(self):
        family = create_family(code="GANT")

        family.code = "MASQ"
        family.save()

        family.refresh_from_db()
        self.assertEqual(family.code, "MASQ")

    def test_str_includes_category_code_and_name(self):
        category = create_category(code="CON", name="Consommable")
        family = create_family(category=category, code="GANT", name="Gants")

        self.assertEqual(str(family), "CON-GANT — Gants")


class UnitTests(TestCase):

    def test_create_unit_with_defaults(self):
        unit = Unit.objects.create(name="Pièce", symbol="pcs")

        self.assertTrue(unit.is_active)
        self.assertIsNotNone(unit.created_at)

    def test_name_must_be_unique(self):
        Unit.objects.create(name="Pièce", symbol="pcs")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Unit.objects.create(name="Pièce", symbol="pce2")

    def test_symbol_must_be_unique(self):
        Unit.objects.create(name="Pièce", symbol="pcs")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Unit.objects.create(name="Pièce 2", symbol="pcs")

    def test_str_includes_name_and_symbol(self):
        unit = Unit.objects.create(name="Pièce", symbol="pcs")

        self.assertEqual(str(unit), "Pièce (pcs)")


class InventoryItemSKUTests(TestCase):

    def setUp(self):
        self.category = create_category(code="CON", name="Consommable")
        self.family = create_family(
            category=self.category,
            code="GANT",
            name="Gants",
        )

    def test_sku_is_generated_on_creation(self):
        item = create_item(family=self.family, name="Gants nitrile")

        self.assertEqual(item.sku, "DCL-CON-GANT-000001")

    def test_sku_uses_category_code(self):
        category = create_category(code="MAT", name="Matériel")
        family = create_family(category=category, code="TURB", name="Turbines")
        item = create_item(family=family, name="Turbine X")

        self.assertEqual(item.sku, "DCL-MAT-TURB-000001")

    def test_sku_numbering_is_sequential_within_family(self):
        first = create_item(family=self.family, name="Gant S")
        second = create_item(family=self.family, name="Gant M")

        self.assertEqual(first.sku, "DCL-CON-GANT-000001")
        self.assertEqual(second.sku, "DCL-CON-GANT-000002")

        self.family.refresh_from_db()
        self.assertEqual(self.family.next_sku_number, 3)

    def test_sku_numbering_is_independent_per_family(self):
        family_b = create_family(
            category=self.category,
            code="MASQ",
            name="Masques",
        )

        item_a = create_item(family=self.family, name="Gant S")
        item_b = create_item(family=family_b, name="Masque chirurgical")

        self.assertEqual(item_a.sku, "DCL-CON-GANT-000001")
        self.assertEqual(item_b.sku, "DCL-CON-MASQ-000001")

    def test_sku_is_immutable(self):
        item = create_item(family=self.family, name="Gants nitrile")
        item.sku = "DCL-CON-GANT-999999"

        with self.assertRaises(ValidationError) as ctx:
            item.save()

        self.assertIn("sku", ctx.exception.error_dict)

    def test_family_is_immutable_after_creation(self):
        item = create_item(family=self.family, name="Gants nitrile")
        other_family = create_family(
            category=self.category,
            code="MASQ",
            name="Masques",
        )

        item.family = other_family

        with self.assertRaises(ValidationError) as ctx:
            item.save()

        self.assertIn("family", ctx.exception.error_dict)

    def test_family_is_required_on_creation(self):
        with self.assertRaises(ValidationError) as ctx:
            InventoryItem.objects.create(name="Sans famille", family=None)

        self.assertIn("family", ctx.exception.error_dict)

        # Le compteur de la famille n'est pas consommé lorsque la
        # création échoue avant verrouillage.
        self.family.refresh_from_db()
        self.assertEqual(self.family.next_sku_number, 1)

    def test_item_cannot_be_created_in_inactive_family(self):
        family = create_family(category=self.category, is_active=False)

        with self.assertRaises(ValidationError) as ctx:
            create_item(family=family)

        self.assertIn("family", ctx.exception.error_dict)

    def test_item_creation_refuses_invalid_category_code(self):
        # InventoryCategory n'appelle pas full_clean() : un code hors
        # MAT/CON peut exister en base. InventoryItem.save() le refuse.
        InventoryCategory.objects.filter(pk=self.category.pk).update(
            code="XYZ",
        )

        with self.assertRaises(ValidationError) as ctx:
            create_item(family=self.family)

        self.assertIn("family", ctx.exception.error_dict)

    def test_updating_item_keeps_sku_and_counter(self):
        item = create_item(family=self.family, name="Gants nitrile")

        item.name = "Gants nitrile renforcé"
        item.save()

        item.refresh_from_db()
        self.assertEqual(item.sku, "DCL-CON-GANT-000001")
        self.assertEqual(item.name, "Gants nitrile renforcé")

        self.family.refresh_from_db()
        self.assertEqual(self.family.next_sku_number, 2)


class InventoryItemValidationTests(TestCase):

    def test_default_values(self):
        item = create_item()

        self.assertEqual(item.stock_quantity, Decimal("0.00"))
        self.assertEqual(item.reorder_quantity, Decimal("0.00"))
        self.assertEqual(item.expiration_alert_days, 30)
        self.assertFalse(item.is_perishable)
        self.assertTrue(item.is_active)
        self.assertIsNone(item.reorder_point)

    def test_negative_stock_quantity_is_refused(self):
        item = create_item()
        item.stock_quantity = Decimal("-1.00")

        with self.assertRaises(ValidationError) as ctx:
            item.save()

        self.assertIn("stock_quantity", ctx.exception.error_dict)

    def test_database_constraint_refuses_negative_stock(self):
        item = create_item()

        # Bypass de save() pour vérifier la contrainte SQL
        # `inventory_stock_quantity_non_negative`.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryItem.objects.filter(pk=item.pk).update(
                    stock_quantity=to_decimal(-5),
                )

    def test_str_returns_name(self):
        item = create_item(name="Gants nitrile")

        self.assertEqual(str(item), "Gants nitrile")
