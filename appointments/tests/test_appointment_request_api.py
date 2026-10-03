from datetime import date, datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from appointments.models import Appointment
from patients.models import Patient


class AppointmentRequestAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.doctor = User.objects.create_user(
            first_name="Doctor",
            last_name="Test",
            role=User.Role.DENTIST,
            email="doctor@example.com",
            password="password",
        )

        self.url = reverse("appointment-request")

        self.start_at = timezone.make_aware(
            datetime(2026, 9, 22, 10, 0)
        )
        self.end_at = timezone.make_aware(
            datetime(2026, 9, 22, 10, 30)
        )

    def test_first_request_creates_patient_and_pending_appointment(self):
        response = self.client.post(
            self.url,
            {
                "first_request": True,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "0600000000",
                "practitioner": self.doctor.id,
                "start_at": self.start_at.isoformat(),
                "end_at": self.end_at.isoformat(),
                "reason": "First consultation",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Appointment.objects.count(), 1)

        patient = Patient.objects.get()

        self.assertEqual(patient.first_name, "John")
        self.assertEqual(patient.last_name, "Doe")
        self.assertEqual(patient.email, "john@example.com")
        self.assertEqual(patient.phone, "0600000000")
        self.assertTrue(patient.patient_code)

        appointment = Appointment.objects.get()

        self.assertEqual(appointment.patient, patient)
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )
        self.assertEqual(
            appointment.source,
            Appointment.Source.ONLINE,
        )

    def test_existing_patient_can_request_with_patient_code(self):
        patient = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="0600000000",
            birthdate=date(1990, 5, 10),
            gender="M",
        )

        response = self.client.post(
            self.url,
            {
                "first_request": False,
                "patient_code": patient.patient_code,
                "practitioner": self.doctor.id,
                "start_at": self.start_at.isoformat(),
                "end_at": self.end_at.isoformat(),
                "reason": "Follow-up",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Appointment.objects.count(), 1)

        appointment = Appointment.objects.get()

        self.assertEqual(appointment.patient, patient)
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )

    def test_existing_patient_can_request_without_patient_code(self):
        patient = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="0600000000",
            birthdate=date(1990, 5, 10),
            gender="M",
        )

        response = self.client.post(
            self.url,
            {
                "first_request": False,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "0600000000",
                "birthdate": "1990-05-10",
                "gender": "M",
                "practitioner": self.doctor.id,
                "start_at": self.start_at.isoformat(),
                "end_at": self.end_at.isoformat(),
                "reason": "Follow-up",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Appointment.objects.count(), 1)

        appointment = Appointment.objects.get()

        self.assertEqual(appointment.patient, patient)
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )

    def test_nonexistent_patient_returns_error(self):
        response = self.client.post(
            self.url,
            {
                "first_request": False,
                "first_name": "Unknown",
                "last_name": "Patient",
                "email": "unknown@example.com",
                "phone": "0600000000",
                "birthdate": "1990-05-10",
                "gender": "M",
                "practitioner": self.doctor.id,
                "start_at": self.start_at.isoformat(),
                "end_at": self.end_at.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(Patient.objects.count(), 0)
        self.assertEqual(Appointment.objects.count(), 0)