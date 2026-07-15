from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from appointments.models import Appointment, AppointmentStatusLog
from billing.models import Invoice, Payment
from patients.models import Patient


class StateMachineCharacterizationTests(APITestCase):
    """PHASE B5 characterization tests.

    These tests prove current state transition behavior (or absence of it).
    They do not assume any desired workflow policy.
    """

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

        self.dentist_token = Token.objects.create(user=self.dentist)
        self.accountant_token = Token.objects.create(user=self.accountant)
        self.admin_token = Token.objects.create(user=self.admin)

    def _mk_patient(self, suffix: str) -> Patient:
        return Patient.objects.create(
            first_name="P",
            last_name=f"{suffix}",
            birthdate="1990-01-01",
            gender="other",
            phone=f"+2137000{suffix[-4:]}",
        )

    def test_api_appointment_status_can_jump_between_choices_and_does_not_log(self):
        """Appointment.status has choices but no transition policy.

        Evidence:
        - API allows setting any choice from any other choice.
        - AppointmentStatusLog is not auto-populated on change (no transition hooks found).
        """

        patient = self._mk_patient("APPT")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")

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

        # Jump pending -> completed directly.
        patch_1 = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.COMPLETED},
            format="json",
        )
        self.assertEqual(patch_1.status_code, 200, patch_1.data)
        self.assertEqual(patch_1.data["status"], Appointment.Status.COMPLETED)

        # Jump completed -> pending (reverse) directly.
        patch_2 = self.client.patch(
            f"/api/appointments/{appt_id}/",
            {"status": Appointment.Status.PENDING},
            format="json",
        )
        self.assertEqual(patch_2.status_code, 200, patch_2.data)
        self.assertEqual(patch_2.data["status"], Appointment.Status.PENDING)

        # No automatic status log creation is implemented.
        self.assertEqual(AppointmentStatusLog.objects.count(), 0)

    def test_orm_appointment_status_choices_not_enforced(self):
        """Django model choices are not DB enforced; ORM can store any string."""

        patient = self._mk_patient("APPTORM")

        appt = Appointment.objects.create(
            patient=patient,
            practitioner=self.dentist,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T09:30:00Z",
            status="INVALID_STATUS_VALUE",
        )

        appt.refresh_from_db()
        self.assertEqual(appt.status, "INVALID_STATUS_VALUE")

    def test_api_invoice_status_accepts_arbitrary_values(self):
        """Invoice.status is free-text; API accepts arbitrary values."""

        patient = self._mk_patient("INV")

        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-STATE-AUDIT",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token.key}")
        resp = self.client.patch(
            f"/api/invoices/{invoice.id}/",
            {"status": "totally_custom_status"},
            format="json",
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "totally_custom_status")

    def test_api_payment_status_accepts_arbitrary_values(self):
        """Payment.status is free-text; API accepts arbitrary values."""

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

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token.key}")
        resp = self.client.patch(
            f"/api/payments/{payment.id}/",
            {"status": "reversed"},
            format="json",
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "reversed")

    def test_api_document_status_accepts_arbitrary_values(self):
        """Document.status is free-text; API accepts arbitrary values."""

        patient = self._mk_patient("DOC")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")

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

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

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

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")

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

    def test_api_treatment_status_accepts_arbitrary_values(self):
        """Treatment.status is free-text; API accepts arbitrary values."""

        patient = self._mk_patient("TRT")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")

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

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "nonsense_status_value")
