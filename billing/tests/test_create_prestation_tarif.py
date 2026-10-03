from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from billing.models import Prestation, PrestationCategory, PrestationTarif


User = get_user_model()


class PrestationTarifCreateAPITests(APITestCase):

    def setUp(self):
        self.administrator = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            role=User.Role.ADMINISTRATOR,
        )

        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            password="password123",
            first_name="Dentist",
            last_name="User",
            role=User.Role.DENTIST,
        )

        self.category = PrestationCategory.objects.create(
            name="Consultation",
            code="CONSULT",
        )

        self.prestation = Prestation.objects.create(
            category=self.category,
            code="CONS-INIT",
            label="Consultation initiale",
            description="Première consultation du patient.",
            is_active=True,
        )

        self.url = reverse("prestationtarif-list")

    def test_administrator_can_create_tarif_for_existing_prestation(self):
        self.client.force_authenticate(user=self.administrator)

        data = {
            "prestation": self.prestation.pk,
            "amount": "3000.00",
            "tax_rate": "0.00",
            "effective_from": "2026-01-01",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        tarif = PrestationTarif.objects.get()

        self.assertEqual(tarif.prestation, self.prestation)
        self.assertEqual(tarif.prestation_id, self.prestation.pk)
        self.assertEqual(tarif.amount, Decimal("3000.00"))
        self.assertEqual(tarif.tax_rate, Decimal("0.00"))
        self.assertEqual(tarif.effective_from, date(2026, 1, 1))

    def test_non_administrator_cannot_create_tarif(self):
        self.client.force_authenticate(user=self.dentist)

        data = {
            "prestation": self.prestation.pk,
            "amount": "3000.00",
            "tax_rate": "0.00",
            "effective_from": "2026-01-01",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PrestationTarif.objects.count(), 0)

    def test_same_prestation_can_have_tarifs_on_different_dates(self):
        self.client.force_authenticate(user=self.administrator)

        first_data = {
            "prestation": self.prestation.pk,
            "amount": "3000.00",
            "tax_rate": "0.00",
            "effective_from": "2026-01-01",
        }

        second_data = {
            "prestation": self.prestation.pk,
            "amount": "3500.00",
            "tax_rate": "0.00",
            "effective_from": "2026-06-01",
        }

        first_response = self.client.post(
            self.url,
            first_data,
            format="json",
        )

        second_response = self.client.post(
            self.url,
            second_data,
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(PrestationTarif.objects.count(), 2)

    def test_same_prestation_and_same_effective_date_cannot_have_two_tarifs(
        self,
    ):
        self.client.force_authenticate(user=self.administrator)

        data = {
            "prestation": self.prestation.pk,
            "amount": "3000.00",
            "tax_rate": "0.00",
            "effective_from": "2026-01-01",
        }

        first_response = self.client.post(
            self.url,
            data,
            format="json",
        )

        duplicate_data = {
            "prestation": self.prestation.pk,
            "amount": "3500.00",
            "tax_rate": "0.00",
            "effective_from": "2026-01-01",
        }

        second_response = self.client.post(
            self.url,
            duplicate_data,
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(PrestationTarif.objects.count(), 1)
