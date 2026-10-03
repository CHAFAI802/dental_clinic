from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from billing.models import PrestationCategory


class PrestationCategoryCreateTests(APITestCase):

    def setUp(self):
        self.url = reverse("prestationcategory-list")

        self.administrator = User.objects.create_user(
            email="admin@example.com",
            password="test-password",
            first_name="Admin",
            last_name="Test",
            role=User.Role.ADMINISTRATOR,
        )

        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            password="test-password",
            first_name="Dentist",
            last_name="Test",
            role=User.Role.DENTIST,
        )

        self.data = {
            "name": "Consultation",
            "code": "CONSULT",
        }

    def test_administrator_can_create_prestation_category(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.post(
            self.url,
            self.data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            PrestationCategory.objects.count(),
            1,
        )

        category = PrestationCategory.objects.get()

        self.assertEqual(category.name, "Consultation")
        self.assertEqual(category.code, "CONSULT")
        self.assertTrue(category.is_active)

    def test_non_administrator_cannot_create_prestation_category(self):
        self.client.force_authenticate(user=self.dentist)

        response = self.client.post(
            self.url,
            self.data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            PrestationCategory.objects.count(),
            0,
        )

