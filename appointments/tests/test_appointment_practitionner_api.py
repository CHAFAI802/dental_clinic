from datetime import time

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from website.models import WorkingHours


class AppointmentPractitionersAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("appointment-practitioners")

        self.doctor_a = User.objects.create_user(
            first_name="Aziza",
            last_name="Chafai",
            role=User.Role.DENTIST,
            email="aziza@example.com",
            password="password",
        )

        self.doctor_b = User.objects.create_user(
            first_name="Ahmed",
            last_name="Test",
            role=User.Role.DENTIST,
            email="ahmed@example.com",
            password="password",
        )

        WorkingHours.objects.create(
            practitioner=self.doctor_a,
            weekday=WorkingHours.Weekday.MONDAY,
            start_time=time(8, 0),
            end_time=time(12, 0),
        )

    def test_returns_only_active_scheduled_dentists(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            [item["id"] for item in response.data],
            [self.doctor_a.id],
        )

    def test_response_exposes_only_required_fields(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            set(response.data[0].keys()),
            {"id", "first_name", "last_name"},
        )

    def test_inactive_working_hours_are_excluded(self):
        WorkingHours.objects.create(
            practitioner=self.doctor_b,
            weekday=WorkingHours.Weekday.TUESDAY,
            start_time=time(8, 0),
            end_time=time(12, 0),
            is_active=False,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data],
            [self.doctor_a.id],
        )

    def test_dentist_without_working_hours_is_excluded(self):
        response = self.client.get(self.url)

        self.assertNotIn(
            self.doctor_b.id,
            [item["id"] for item in response.data],
        )
