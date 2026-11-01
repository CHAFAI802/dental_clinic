from datetime import date, datetime, time, timedelta, timezone as dt_timezone

from django.test import TestCase
from unittest.mock import patch

from accounts.models import User
from appointments.services.appointmentstatus import get_available_slots
from django.utils import timezone
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
        today = timezone.localdate()
        days_until_monday = (0 - today.weekday()) % 7 or 7
        monday = today + timedelta(days=days_until_monday)
        tuesday = monday + timedelta(days=1)

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


class AvailableSlotsPastTimeTests(TestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            first_name="Doctor",
            last_name="PastTime",
            role=User.Role.DENTIST,
            email="pasttime@example.com",
            password="password",
        )

    def test_slots_starting_at_or_before_current_time_are_excluded(self):
        test_date = date(2026, 10, 31)

        WorkingHours.objects.create(
            practitioner=self.doctor,
            weekday=test_date.weekday(),
            start_time=time(8, 0),
            end_time=time(15, 0),
        )

        fixed_now = datetime(
            2026, 10, 31, 12, 0,
            tzinfo=dt_timezone.utc,
        )

        with patch(
            "appointments.services.appointmentstatus.timezone.now",
            return_value=fixed_now,
        ):
            slots = get_available_slots(
                practitioner=self.doctor,
                start_date=test_date,
                end_date=test_date,
            )

        self.assertTrue(slots)
        self.assertTrue(
            all(slot["start_at"] > fixed_now for slot in slots)
        )
        self.assertEqual(
            [slot["start_at"].hour for slot in slots],
            [13, 14, 14],
        )
