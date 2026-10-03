from datetime import date, datetime, time

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from appointments.models import Appointment
from appointments.services.appointmentstatus import AppointmentRequestService
from patients.models import Patient


class AppointmentRequestServiceTests(TestCase):

    def setUp(self):
        self.doctor = User.objects.create_user(
            first_name="Doctor",
            last_name="Test",
            role=User.Role.DENTIST,
            email="doctor@example.com",
            password="password",
        )

        self.start_at = timezone.make_aware(
            datetime(2026, 9, 22, 10, 0)
        )
        self.end_at = timezone.make_aware(
            datetime(2026, 9, 22, 10, 30)
        )

    def test_first_request_creates_patient_and_pending_appointment(self):
        appointment = AppointmentRequestService.submit(
            first_request=True,
            practitioner=self.doctor,
            start_at=self.start_at,
            end_at=self.end_at,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="0600000000",
            reason="First consultation",
        )

        self.assertIsNotNone(appointment.patient)
        self.assertEqual(appointment.patient.first_name, "John")
        self.assertEqual(appointment.patient.last_name, "Doe")
        self.assertEqual(appointment.patient.email, "john@example.com")
        self.assertEqual(appointment.patient.phone, "0600000000")

        self.assertTrue(appointment.patient.patient_code)
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )
        self.assertEqual(
            appointment.source,
            Appointment.Source.ONLINE,
        )

        self.assertEqual(
            Appointment.objects.count(),
            1,
        )
        self.assertEqual(
            Patient.objects.count(),
            1,
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

        appointment = AppointmentRequestService.submit(
            first_request=False,
            practitioner=self.doctor,
            start_at=self.start_at,
            end_at=self.end_at,
            patient_code=patient.patient_code,
            reason="Follow-up",
        )

        self.assertEqual(
            appointment.patient,
            patient,
        )
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )

        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_existing_patient_can_request_without_patient_code(self):
        patient = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="0600000000",
            birthdate=date(1990, 5, 10),
            gender="M",
        )

        appointment = AppointmentRequestService.submit(
            first_request=False,
            practitioner=self.doctor,
            start_at=self.start_at,
            end_at=self.end_at,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="0600000000",
            birthdate=date(1990, 5, 10),
            gender="M",
            reason="Follow-up",
        )

        self.assertEqual(
            appointment.patient,
            patient,
        )
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )

        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_nonexistent_patient_raises_error(self):
        with self.assertRaises(Patient.DoesNotExist):
            AppointmentRequestService.submit(
                first_request=False,
                practitioner=self.doctor,
                start_at=self.start_at,
                end_at=self.end_at,
                first_name="Unknown",
                last_name="Patient",
                email="unknown@example.com",
                phone="0600000000",
                birthdate=date(1990, 5, 10),
                gender="M",
            )

        self.assertEqual(Patient.objects.count(), 0)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_multiple_matching_patients_raise_error(self):
        Patient.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="0600000000",
            birthdate=date(1990, 5, 10),
            gender="M",
        )

        Patient.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="0600000000",
            birthdate=date(1990, 5, 10),
            gender="M",
        )

        with self.assertRaisesMessage(
            ValueError,
            "Please call the clinic to identify your patient record.",
        ):
            AppointmentRequestService.submit(
                first_request=False,
                practitioner=self.doctor,
                start_at=self.start_at,
                end_at=self.end_at,
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                phone="0600000000",
                birthdate=date(1990, 5, 10),
                gender="M",
            )

        self.assertEqual(Patient.objects.count(), 2)
        self.assertEqual(Appointment.objects.count(), 0)