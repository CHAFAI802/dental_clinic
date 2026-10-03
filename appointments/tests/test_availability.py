from datetime import date, time

from django.test import TestCase

from accounts.models import User
from appointments.services.appointmentstatus import get_available_slots
from website.models import WorkingHours


class AvailableSlotsRestDayTests(TestCase):

    def setUp(self):
        self.doctor_a = User.objects.create_user(
            first_name="Doctor",
            last_name="A",
            role=User.Role.DENTIST,
            email="dentistA@example.com",
            password="passwordA",
        )

        self.doctor_b = User.objects.create_user(
            first_name="Doctor",
            last_name="B",
            role=User.Role.DENTIST,
            email="dentistB@example.com",
            password="passwordB",
        )

        # Médecin A travaille mardi uniquement.
        WorkingHours.objects.create(
            practitioner=self.doctor_a,
            weekday=WorkingHours.Weekday.TUESDAY,
            start_time=time(8, 0),
            end_time=time(10, 0),
        )

        # Médecin B travaille lundi uniquement.
        WorkingHours.objects.create(
            practitioner=self.doctor_b,
            weekday=WorkingHours.Weekday.MONDAY,
            start_time=time(8, 0),
            end_time=time(10, 0),
        )

    def test_each_practitioner_has_individual_rest_days(self):
        monday = date(2026, 9, 21)
        tuesday = date(2026, 9, 22)

        slots = get_available_slots(
            start_date=monday,
            end_date=tuesday,
        )

        monday_slots = [
            slot for slot in slots
            if slot["date"] == monday
        ]

        tuesday_slots = [
            slot for slot in slots
            if slot["date"] == tuesday
        ]

        # Lundi : A est en repos, seul B doit avoir des créneaux.
        self.assertTrue(monday_slots)
        self.assertEqual(
            {slot["practitioner"] for slot in monday_slots},
            {self.doctor_b.id},
        )

        # Mardi : B est en repos, seul A doit avoir des créneaux.
        self.assertTrue(tuesday_slots)
        self.assertEqual(
            {slot["practitioner"] for slot in tuesday_slots},
            {self.doctor_a.id},
        )