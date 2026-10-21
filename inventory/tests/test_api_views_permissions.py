"""
Tests des vues (API) et des permissions de l'application inventory.

Références (code actuel du dépôt) :
- inventory/views.py, inventory/urls.py
- accounts/permissions.py : IsAdministrator, CanManageStock

Les tests nommés `..._returns_...` expriment le comportement attendu
d'après le code des modèles/permissions ; lorsque celui-ci échoue, le
diagnostic est fourni dans le rapport d'audit.
"""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from inventory.models import (
    InventoryCategory,
    InventoryFamily,
    InventoryItem,
    StockDestruction,
    StockDestructionLine,
    StockExit,
)

from .base import create_entry, create_family, create_item, to_decimal


def create_user(role, email):
    return User.objects.create_user(
        email=email,
        first_name="Test",
        last_name=role.replace("_", " ").title().replace(" ", ""),
        role=role,
        password="password",
    )


CAN_MANAGE_STOCK_ROLES = (
    User.Role.SUPER_ADMIN,
    User.Role.ADMINISTRATOR,
    User.Role.ACCOUNTANT,
    User.Role.RECEPTIONIST,
)

CAN_MANAGE_STOCK_ENDPOINTS = (
    "inventory-item-list",
    "stock-entry-list",
    "stock-exit-list",
    "stock-alert-list",
    "stock-exit-allocation-list",
    "stock-destruction-list",
)

ADMIN_ONLY_ENDPOINTS = (
    "inventory-category-list",
    "inventory-family-list",
    "unit-list",
)


class InventoryAPIPermissionTests(APITestCase):

    def setUp(self):
        self.users = {
            role: create_user(role, f"{role}@test.com")
            for role in User.Role.values
        }
        self.item = create_item(name="Gants nitrile")
        create_entry(self.item, "10", "2.00")

    def _get(self, url_name, user=None):
        self.client.force_authenticate(user=user)
        return self.client.get(reverse(url_name))

    def test_anonymous_requests_are_unauthorized(self):
        for url_name in CAN_MANAGE_STOCK_ENDPOINTS + ADMIN_ONLY_ENDPOINTS:
            with self.subTest(endpoint=url_name):
                response = self._get(url_name)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

    def test_can_manage_stock_roles_can_list(self):
        for role in CAN_MANAGE_STOCK_ROLES:
            for url_name in CAN_MANAGE_STOCK_ENDPOINTS:
                with self.subTest(role=role, endpoint=url_name):
                    response = self._get(url_name, self.users[role])
                    self.assertEqual(
                        response.status_code,
                        status.HTTP_200_OK,
                    )

    def test_dentist_and_assistant_are_denied_on_stock_endpoints(self):
        for role in (User.Role.DENTIST, User.Role.ASSISTANT):
            for url_name in CAN_MANAGE_STOCK_ENDPOINTS:
                with self.subTest(role=role, endpoint=url_name):
                    response = self._get(url_name, self.users[role])
                    self.assertEqual(
                        response.status_code,
                        status.HTTP_403_FORBIDDEN,
                    )

    def test_admin_endpoints_are_administrator_only(self):
        for url_name in ADMIN_ONLY_ENDPOINTS:
            with self.subTest(endpoint=url_name, role="administrator"):
                response = self._get(url_name, self.users[User.Role.ADMINISTRATOR])
                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                )

            for role in (
                User.Role.DENTIST,
                User.Role.ASSISTANT,
                User.Role.RECEPTIONIST,
                User.Role.ACCOUNTANT,
            ):
                with self.subTest(endpoint=url_name, role=role):
                    response = self._get(url_name, self.users[role])
                    self.assertEqual(
                        response.status_code,
                        status.HTTP_403_FORBIDDEN,
                    )

    def test_inactive_user_is_denied(self):
        user = self.users[User.Role.ADMINISTRATOR]
        user.is_active = False
        user.save(update_fields=["is_active"])

        response = self._get("inventory-item-list", user)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_deleted_user_is_denied(self):
        user = self.users[User.Role.ADMINISTRATOR]
        user.is_deleted = True
        user.save(update_fields=["is_deleted", "deleted_at"])

        response = self._get("inventory-item-list", user)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CatalogAPITests(APITestCase):

    def setUp(self):
        self.admin = create_user(User.Role.ADMINISTRATOR, "admin@test.com")
        self.receptionist = create_user(
            User.Role.RECEPTIONIST,
            "reception@test.com",
        )

    def test_list_inventory_items(self):
        item = create_item(name="Gants nitrile")

        self.client.force_authenticate(user=self.receptionist)
        response = self.client.get(reverse("inventory-item-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["sku"], item.sku)

    def test_retrieve_inventory_item(self):
        item = create_item(name="Gants nitrile")

        self.client.force_authenticate(user=self.receptionist)
        response = self.client.get(
            reverse("inventory-item-detail", args=[item.pk]),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Gants nitrile")

    def test_create_inventory_item_returns_201_and_generates_sku(self):
        family = create_family()

        self.client.force_authenticate(user=self.receptionist)
        response = self.client.post(
            reverse("inventory-item-list"),
            {"name": "Gants nitrile", "family": family.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["sku"].startswith("DCL-"))
        self.assertEqual(response.data["stock_quantity"], "0.00")

    def test_create_inventory_item_without_family_should_return_400(self):
        self.client.force_authenticate(user=self.receptionist)
        response = self.client.post(
            reverse("inventory-item-list"),
            {"name": "Gants nitrile"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_inventory_family_returns_201(self):
        category = InventoryCategory.objects.create(
            code="CON",
            name="Consommable",
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("inventory-family-list"),
            {
                "category": category.pk,
                "name": "Gants",
                "code": "GANT",
                "next_sku_number": "42",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["next_sku_number"], 1)

        family = InventoryFamily.objects.get(pk=response.data["id"])
        self.assertEqual(family.code, "GANT")

    def test_create_unit_returns_201(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("unit-list"),
            {"name": "Pièce", "symbol": "pcs"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_inventory_category_returns_201(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("inventory-category-list"),
            {"code": "MAT", "name": "Matériel"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_suppliers_should_return_200(self):
        # Au moins un fournisseur est nécessaire : le défaut du
        # serializer Supplier ne se manifeste qu'à la sérialisation
        # d'un objet (champs `contact_email` / `contact_phone`
        # inexistants sur le modèle).
        from inventory.models import Supplier

        Supplier.objects.create(name="Fournisseur A")

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("supplier-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class StockEntryAPITests(APITestCase):

    def setUp(self):
        self.admin = create_user(User.Role.ADMINISTRATOR, "admin@test.com")
        self.item = create_item(name="Gants nitrile")

    def test_list_stock_entries(self):
        create_entry(self.item, "10", "2.00")

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("stock-entry-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_stock_entry(self):
        entry = create_entry(self.item, "10", "2.00")

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            reverse("stock-entry-detail", args=[entry.pk]),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["remaining_quantity"], "10.00")
        self.assertEqual(response.data["total_cost"], "20.00")

    def test_create_stock_entry_returns_201(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("stock-entry-list"),
            {
                "item": self.item.pk,
                "quantity": "10",
                "unit_cost": "2.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("10.00"))

    def test_create_stock_entry_with_invalid_quantity_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("stock-entry-list"),
            {
                "item": self.item.pk,
                "quantity": "0",
                "unit_cost": "2.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_stock_entry_returns_400(self):
        entry = create_entry(self.item, "10", "2.00")

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("stock-entry-detail", args=[entry.pk]),
            {"quantity": "5"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_stock_entry_should_be_refused(self):
        entry = create_entry(self.item, "10", "2.00")

        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("stock-entry-detail", args=[entry.pk]),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StockExitAPITests(APITestCase):

    def setUp(self):
        self.admin = create_user(User.Role.ADMINISTRATOR, "admin@test.com")
        self.item = create_item(name="Gants nitrile")
        create_entry(self.item, "10", "2.00")

    def test_create_stock_exit_returns_201(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("stock-exit-list"),
            {
                "item": self.item.pk,
                "quantity": "3",
                "usage_type": "soin",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        item = InventoryItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.stock_quantity, Decimal("7.00"))

    def test_create_stock_exit_with_insufficient_stock_should_return_400(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("stock-exit-list"),
            {
                "item": self.item.pk,
                "quantity": "50",
                "usage_type": "soin",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_stock_exit_returns_400(self):
        exit_instance = StockExit(
            item=self.item,
            quantity=to_decimal("1"),
            usage_type="soin",
        )
        exit_instance.apply()

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("stock-exit-detail", args=[exit_instance.pk]),
            {"quantity": "2"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_stock_exit_allocations(self):
        StockExit(
            item=self.item,
            quantity=to_decimal("3"),
            usage_type="soin",
        ).apply()

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("stock-exit-allocation-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["quantity"], "3.00")


class StockAlertAPITests(APITestCase):

    def setUp(self):
        self.admin = create_user(User.Role.ADMINISTRATOR, "admin@test.com")
        self.item = create_item(name="Gants nitrile", reorder_point=to_decimal("100"))
        create_entry(self.item, "10", "2.00")

    def test_list_stock_alerts(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("stock-alert-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["alert_type"], "low_stock")

    def test_create_stock_alert_is_not_supported(self):
        # DOCUMENTÉ : StockAlertViewset est un ReadOnlyModelViewSet :
        # la création d'alertes n'est pas exposée par l'API.
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("stock-alert-list"),
            {
                "item": self.item.pk,
                "alert_type": "low_stock",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class StockDestructionAPITests(APITestCase):

    def setUp(self):
        self.admin = create_user(User.Role.ADMINISTRATOR, "admin@test.com")
        self.item = create_item(name="Gants nitrile")
        self.entry = create_entry(self.item, "10", "2.00")

    def test_create_destruction_returns_201_and_ignores_status(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("stock-destruction-list"),
            {
                "reason": "Produits périmés",
                "status": "completed",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "recorded")

        destruction = StockDestruction.objects.get(pk=response.data["id"])
        self.assertEqual(destruction.status, "recorded")

    def test_create_destruction_requires_reason(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("stock-destruction-list"),
            {"reason": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_status_is_ignored(self):
        destruction = StockDestruction.objects.create(reason="Perte")

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("stock-destruction-detail", args=[destruction.pk]),
            {"status": "completed", "reason": "Perte modifiée"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        destruction.refresh_from_db()
        self.assertEqual(destruction.status, "recorded")
        self.assertEqual(destruction.reason, "Perte modifiée")

    def test_create_destruction_line_returns_201(self):
        destruction = StockDestruction.objects.create(reason="Perte")

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("stock-destruction-line-list"),
            {
                "destruction": destruction.pk,
                "item": self.item.pk,
                "stock_entry": self.entry.pk,
                "quantity": "3.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StockDestructionLine.objects.count(), 1)

    def test_list_stock_destruction_lines_should_return_lines(self):
        destruction = StockDestruction.objects.create(reason="Perte")
        StockDestructionLine.objects.create(
            destruction=destruction,
            item=self.item,
            stock_entry=self.entry,
            quantity=to_decimal("3"),
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("stock-destruction-line-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_recorded_destruction_returns_204(self):
        destruction = StockDestruction.objects.create(reason="Perte")

        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("stock-destruction-detail", args=[destruction.pk]),
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(StockDestruction.objects.count(), 0)

    def test_delete_completed_destruction_should_be_refused(self):
        destruction = StockDestruction.objects.create(reason="Perte")
        StockDestructionLine.objects.create(
            destruction=destruction,
            item=self.item,
            stock_entry=self.entry,
            quantity=to_decimal("3"),
        )
        destruction.apply()

        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("stock-destruction-detail", args=[destruction.pk]),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StockDestruction.objects.count(), 1)
