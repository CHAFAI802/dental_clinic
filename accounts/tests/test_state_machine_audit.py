from accounts.services.authentication import create_authentication_session
from rest_framework.test import APITestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.models import User
from appointments.models import Appointment, AppointmentStatusLog
from billing.models import Invoice, Payment
from patients.models import Patient

class StateMachineCharacterizationTests(APITestCase):

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist_state@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="State",
            role=User.Role.DENTIST,
        )
        self.accountant = User.objects.create_user(
            email="accountant_state@example.com",
            password="StrongPassword123!",
            first_name="Accountant",
            last_name="State",
            role=User.Role.ACCOUNTANT,
        )
        self.admin = User.objects.create_user(
            email="admin_state@example.com",
            password="StrongPassword123!",
            first_name="Admin",
            last_name="State",
            role=User.Role.ADMINISTRATOR,
        )

        self.dentist_session, self.dentist_token = create_authentication_session(
            self.dentist
        )
        self.accountant_session, self.accountant_token = create_authentication_session(
            self.accountant
        )
        self.admin_session, self.admin_token = create_authentication_session(
            self.admin
        )

    def _mk_patient(self, suffix: str) -> Patient:
        return Patient.objects.create(
            first_name="P",
            last_name=f"{suffix}",
            birthdate="1990-01-01",
            gender="other",
            phone=f"+2137000{suffix[-4:]}",
        )

    def test_api_appointment_status_allowed_transitions(self):
        """STATE-001: Allowed transitions are accepted and create status logs."""

        patient = self._mk_patient("TRAN")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )

        create = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T09:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201, create.data)
        appt_id = create.data["id"]

        # pending -> confirmed
        patch_1 = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.CONFIRMED},
            format="json",
        )

        self.assertEqual(patch_1.status_code, 200, patch_1.data)
        self.assertEqual(
            patch_1.data["status"],
            Appointment.Status.CONFIRMED,
        )
        self.assertIsNotNone(patch_1.data["confirmed_at"])
        self.assertEqual(
            patch_1.data["confirmed_by"],
            self.dentist.id,
        )

        confirmed_log = AppointmentStatusLog.objects.get(
            appointment_id=appt_id,
            previous_status=Appointment.Status.PENDING,
            new_status=Appointment.Status.CONFIRMED,
        )

        self.assertEqual(
            confirmed_log.changed_by_id,
            self.dentist.id,
        )

        # confirmed -> completed
        patch_2 = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(patch_2.status_code, 200, patch_2.data)
        self.assertEqual(
            patch_2.data["status"],
            Appointment.Status.COMPLETED,
        )
        self.assertIsNotNone(patch_2.data["completed_at"])
        self.assertEqual(
            patch_2.data["completed_by"],
            self.dentist.id,
        )

        completed_log = AppointmentStatusLog.objects.get(
            appointment_id=appt_id,
            previous_status=Appointment.Status.CONFIRMED,
            new_status=Appointment.Status.COMPLETED,
        )

        self.assertEqual(
            completed_log.changed_by_id,
            self.dentist.id,
        )

        # Two status transitions must produce two audit log entries.
        self.assertEqual(
            AppointmentStatusLog.objects.filter(
                appointment_id=appt_id
            ).count(),
            2,
        )

    def test_api_appointment_status_forbidden_transitions(self):
        """STATE-001: Forbidden transitions are rejected."""

        patient = self._mk_patient("FORB")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )

        create = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T10:00:00Z",
                "end_at": "2035-01-15T10:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)
        appt_id = create.data["id"]

        # pending -> completed
        resp = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("status", resp.data)

        # pending -> no_show
        resp = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.NO_SHOW},
            format="json",
        )

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("status", resp.data)

        # No audit log must be created for rejected transitions.
        self.assertEqual(
            AppointmentStatusLog.objects.filter(
                appointment_id=appt_id
            ).count(),
            0,
        )

    def test_api_appointment_terminal_state_immutability(self):
        """STATE-001: Terminal states reject further transitions."""

        patient = self._mk_patient("TERM")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )

        create = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T11:00:00Z",
                "end_at": "2035-01-15T11:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)
        appt_id = create.data["id"]

        # pending -> confirmed
        confirmed = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.CONFIRMED},
            format="json",
        )

        self.assertEqual(confirmed.status_code, 200, confirmed.data)
        self.assertEqual(
            confirmed.data["confirmed_by"],
            self.dentist.id,
        )

        # confirmed -> completed
        completed = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(completed.status_code, 200, completed.data)
        self.assertIsNotNone(completed.data["completed_at"])
        self.assertEqual(
            completed.data["completed_by"],
            self.dentist.id,
        )

        # completed -> pending
        resp = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.PENDING},
            format="json",
        )

        self.assertEqual(resp.status_code, 400, resp.data)

        # Verify no additional status log was created.
        self.assertEqual(
            AppointmentStatusLog.objects.filter(
                appointment_id=appt_id
            ).count(),
            2,
        )

    def test_api_appointment_cancelled_transition_records_actor(self):
        """STATE-001: pending -> cancelled records timestamp, actor and audit actor."""

        patient = self._mk_patient("CANC")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )

        create = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T12:00:00Z",
                "end_at": "2035-01-15T12:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)
        appt_id = create.data["id"]

        response = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.CANCELLED},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["status"],
            Appointment.Status.CANCELLED,
        )
        self.assertIsNotNone(response.data["cancelled_at"])
        self.assertEqual(
            response.data["cancelled_by"],
            self.dentist.id,
        )

        log = AppointmentStatusLog.objects.get(
            appointment_id=appt_id,
            previous_status=Appointment.Status.PENDING,
            new_status=Appointment.Status.CANCELLED,
        )

        self.assertEqual(
            log.changed_by_id,
            self.dentist.id,
        )

    def test_orm_appointment_status_is_rejected(self):
        """Django model choices are not DB enforced; model validation rejects invalid values."""

        patient = self._mk_patient("APPTORM")

        with self.assertRaises(DjangoValidationError):
            Appointment.objects.create(
                patient=patient,
                practitioner=self.dentist,
                start_at="2035-01-15T09:00:00Z",
                end_at="2035-01-15T09:30:00Z",
                status="INVALID_STATUS_VALUE",
            )

    def test_api_invoice_status_rejects_invalid_values(self):
        """STATE-003: Invoice.status vocabulary is enforced; API rejects arbitrary values."""

        patient = self._mk_patient("INV")

        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-STATE-AUDIT",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )

        resp = self.client.patch(
            f"/api/invoices/{invoice.id}/",
            {"status": "totally_custom_status"},
            format="json",
        )

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("status", resp.data)

    def test_api_payment_status_rejects_invalid_values(self):
        """STATE-003: Payment.status vocabulary is enforced; API rejects arbitrary values."""

        patient = self._mk_patient("PAY")

        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-FOR-PAY-STATE",
        )

        payment = Payment.objects.create(
            invoice=invoice,
            patient=patient,
            payment_at="2035-01-16T10:00:00Z",
            amount="1.00",
            method="cash",
            status="completed",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )

        resp = self.client.patch(
            f"/api/payments/{payment.id}/",
            {"status": "reversed"},
            format="json",
        )

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("status", resp.data)

    def test_api_document_status_accepts_arbitrary_values(self):
        """Document.status is free-text; API accepts arbitrary values."""

        patient = self._mk_patient("DOC")

        # Create an appointment linking the dentist to the patient (AUTH-001 scope)
        Appointment.objects.create(
            patient=patient,
            practitioner=self.dentist,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T09:30:00Z",
            status=Appointment.Status.PENDING,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )

        create = self.client.post(
            "/api/documents/",
            {
                "patient": patient.id,
                "document_type": "other",
                "title": "State doc",
                "content": "x",
                "status": "draft",
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)

        doc_id = create.data["id"]

        resp = self.client.patch(
            f"/api/documents/{doc_id}/",
            {"status": "signed"},
            format="json",
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "signed")

    def test_api_notification_status_accepts_arbitrary_values(self):
        """Notification.status is free-text; API accepts arbitrary values."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.admin_token}"
        )

        create = self.client.post(
            "/api/notifications/",
            {
                "channel": "email",
                "status": "pending",
                "payload": {},
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)

        notif_id = create.data["id"]

        resp = self.client.patch(
            f"/api/notifications/{notif_id}/",
            {"status": "sent"},
            format="json",
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "sent")

    def test_api_imaging_study_status_accepts_arbitrary_values(self):
        """ImagingStudy.status is free-text; API accepts arbitrary values."""

        patient = self._mk_patient("IMG")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )

        create = self.client.post(
            "/api/imaging-studies/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "study_type": "panoramic",
                "study_date": "2035-01-15T10:00:00Z",
                "status": "pending",
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)

        study_id = create.data["id"]

        resp = self.client.patch(
            f"/api/imaging-studies/{study_id}/",
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "completed")

    def test_api_treatment_status_rejects_invalid_values(self):
        """STATE-003: Treatment.status vocabulary is enforced; API rejects arbitrary values."""

        patient = self._mk_patient("TRT")

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )

        create = self.client.post(
            "/api/treatments/",
            {
                "status": "planned",
                "category": "consultation",
                "code": "T-STATE",
                "label": "State treatment",
                "patient": patient.id,
                "dentist": self.dentist.id,
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)

        treatment_id = create.data["id"]

        resp = self.client.patch(
            f"/api/treatments/{treatment_id}/",
            {"status": "nonsense_status_value"},
            format="json",
        )

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("status", resp.data)
