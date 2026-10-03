from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from billing.models import Prestation, PrestationCategory


User = get_user_model()


class PrestationCreateAPITests(APITestCase):

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

        self.url = reverse("prestation-list")

    def test_administrator_can_create_prestation_with_existing_category(self):
        self.client.force_authenticate(user=self.administrator)

        data = {
            "category": self.category.pk,
            "code": "CONS-INIT",
            "label": "Consultation initiale",
            "description": "Première consultation du patient.",
            "is_active": True,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        prestation = Prestation.objects.get()

        self.assertEqual(prestation.code, "CONS-INIT")
        self.assertEqual(prestation.label, "Consultation initiale")
        self.assertEqual(
            prestation.description,
            "Première consultation du patient.",
        )
        self.assertTrue(prestation.is_active)

        # La prestation utilise bien la catégorie existante.
        self.assertEqual(prestation.category, self.category)
        self.assertEqual(prestation.category_id, self.category.pk)

    def test_non_administrator_cannot_create_prestation(self):
        self.client.force_authenticate(user=self.dentist)

        data = {
            "category": self.category.pk,
            "code": "CONS-INIT",
            "label": "Consultation initiale",
            "description": "Première consultation du patient.",
            "is_active": True,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Prestation.objects.count(), 0)
