from unittest.mock import patch

from django.db import IntegrityError
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.services.authentication import create_authentication_session
from appointments.models import Appointment, AppointmentStatusLog
from patients.models import Patient


class AppointmentStatusLogActorTests(APITestCase):
    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist_status_log@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="StatusLog",
            role=User.Role.DENTIST,
        )
        self.receptionist = User.objects.create_user(
            email="receptionist_status_log@example.com",
            password="StrongPassword123!",
            first_name="Receptionist",
            last_name="StatusLog",
            role=User.Role.RECEPTIONIST,
        )
        _, self.dentist_token = create_authentication_session(self.dentist)
        _, self.receptionist_token = create_authentication_session(
            self.receptionist
        )

    def _mk_patient(self, suffix):
        return Patient.objects.create(
            first_name="Patient",
            last_name=suffix,
            birthdate="1990-01-01",
            gender="other",
            phone=f"+2137000{suffix[-4:]}",
        )

    def _create_appointment(self, patient, practitioner):
        response = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": practitioner.id,
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T09:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return Appointment.objects.get(pk=response.data["id"])

    def test_api_dentist_pending_to_confirmed_records_actor(self):
        patient = self._mk_patient("DENTCONF")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        appointment = self._create_appointment(
            patient,
            self.dentist,
        )
        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {"status": Appointment.Status.CONFIRMED},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        appointment.refresh_from_db()
        log = AppointmentStatusLog.objects.get(
            appointment=appointment,
            previous_status=Appointment.Status.PENDING,
            new_status=Appointment.Status.CONFIRMED,
        )
        self.assertEqual(appointment.confirmed_by, self.dentist)
        self.assertEqual(log.changed_by, self.dentist)

    def test_api_receptionist_pending_to_confirmed_records_actor(self):
        patient = self._mk_patient("RECCONF")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )
        appointment = self._create_appointment(
            patient,
            self.dentist,
        )
        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {"status": Appointment.Status.CONFIRMED},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        appointment.refresh_from_db()
        log = AppointmentStatusLog.objects.get(
            appointment=appointment,
            previous_status=Appointment.Status.PENDING,
            new_status=Appointment.Status.CONFIRMED,
        )
        self.assertEqual(appointment.confirmed_by, self.receptionist)
        self.assertEqual(log.changed_by, self.receptionist)

    def test_api_dentist_confirmed_to_cancelled_records_actor(self):
        patient = self._mk_patient("DENTCANC")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        appointment = self._create_appointment(
            patient,
            self.dentist,
        )
        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {"status": Appointment.Status.CONFIRMED},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {"status": Appointment.Status.CANCELLED},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        appointment.refresh_from_db()
        log = AppointmentStatusLog.objects.get(
            appointment=appointment,
            previous_status=Appointment.Status.CONFIRMED,
            new_status=Appointment.Status.CANCELLED,
        )
        self.assertEqual(appointment.cancelled_by, self.dentist)
        self.assertEqual(log.changed_by, self.dentist)

    def test_api_receptionist_confirmed_to_cancelled_records_actor(self):
        patient = self._mk_patient("RECCANC")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )
        appointment = self._create_appointment(
            patient,
            self.dentist,
        )
        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {"status": Appointment.Status.CONFIRMED},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {"status": Appointment.Status.CANCELLED},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        appointment.refresh_from_db()
        log = AppointmentStatusLog.objects.get(
            appointment=appointment,
            previous_status=Appointment.Status.CONFIRMED,
            new_status=Appointment.Status.CANCELLED,
        )
        self.assertEqual(appointment.cancelled_by, self.receptionist)
        self.assertEqual(log.changed_by, self.receptionist)

    def test_status_transition_is_atomic_with_status_log_creation(self):
        patient = self._mk_patient("ATOMIC")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        appointment = self._create_appointment(
            patient,
            self.dentist,
        )
        with patch(
            "appointments.models.AppointmentStatusLog.objects.create",
            side_effect=IntegrityError("forced status log failure"),
        ):
            with self.assertRaises(IntegrityError):
                self.client.patch(
                    f"/api/appointments/{appointment.id}/",
                    {"status": Appointment.Status.CONFIRMED},
                    format="json",
                )
        appointment.refresh_from_db()
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )
        self.assertIsNone(appointment.confirmed_at)
        self.assertIsNone(appointment.confirmed_by)
        self.assertFalse(
            AppointmentStatusLog.objects.filter(
                appointment=appointment,
                previous_status=Appointment.Status.PENDING,
                new_status=Appointment.Status.CONFIRMED,
            ).exists()
        )

    def test_appointment_creation_does_not_create_status_log(self):
        patient = self._mk_patient("CREATELOG")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        appointment = self._create_appointment(
            patient,
            self.dentist,
        )
        self.assertEqual(
            AppointmentStatusLog.objects.filter(
                appointment=appointment
            ).count(),
            0,
        )

    def test_non_status_update_does_not_create_status_log(self):
        patient = self._mk_patient("UPDATELOG")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        appointment = self._create_appointment(
            patient,
            self.dentist,
        )
        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {"notes": "Updated without changing status"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        appointment.refresh_from_db()
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )
        self.assertEqual(
            AppointmentStatusLog.objects.filter(
                appointment=appointment
            ).count(),
            0,
        )

    def test_rejected_transition_does_not_create_status_log(self):
        patient = self._mk_patient("REJECTLOG")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        appointment = self._create_appointment(
            patient,
            self.dentist,
        )
        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {"status": Appointment.Status.COMPLETED},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.data)
        appointment.refresh_from_db()
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )
        self.assertEqual(
            AppointmentStatusLog.objects.filter(
                appointment=appointment
            ).count(),
            0,
        )

    def test_status_history_remains_associated_with_correct_appointment(self):
        patient_a = self._mk_patient("HISTORYA")
        patient_b = self._mk_patient("HISTORYB")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        appointment_a = self._create_appointment(
            patient_a,
            self.dentist,
        )
        response = self.client.post(
            "/api/appointments/",
            {
                "patient": patient_b.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T10:00:00Z",
                "end_at": "2035-01-15T10:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        appointment_b = Appointment.objects.get(
            pk=response.data["id"]
        )
        response = self.client.patch(
            f"/api/appointments/{appointment_a.id}/",
            {"status": Appointment.Status.CONFIRMED},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        log = AppointmentStatusLog.objects.get(
            appointment=appointment_a,
        )
        self.assertEqual(
            log.appointment_id,
            appointment_a.id,
        )
        self.assertEqual(
            appointment_a.status_logs.count(),
            1,
        )
        self.assertEqual(
            appointment_b.status_logs.count(),
            0,
        )
