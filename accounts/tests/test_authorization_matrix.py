from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from accounts.models import AuditLog, User
from accounts.services.authentication import create_authentication_session
from appointments.models import Appointment
from billing.models import Invoice
from patients.models import Patient


class AuthorizationMatrixCharacterizationTests(APITestCase):
    """PHASE B6 characterization tests.

    Goal: prove current role-based and object-scope behavior via real API calls.
    """

    def setUp(self):
        self.superadmin = User.objects.create_superuser(
            email="superadmin_authz@example.com",
            password="StrongPassword123!",
            first_name="Super",
            last_name="Admin",
            role=User.Role.DENTIST,  # manager forces SUPER_ADMIN
        )
        self.admin = User.objects.create_user(
            email="admin_authz@example.com",
            password="StrongPassword123!",
            first_name="Admin",
            last_name="Authz",
            role=User.Role.ADMINISTRATOR,
        )
        self.dentist = User.objects.create_user(
            email="dentist_authz@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="Authz",
            role=User.Role.DENTIST,
        )
        self.assistant = User.objects.create_user(
            email="assistant_authz@example.com",
            password="StrongPassword123!",
            first_name="Assistant",
            last_name="Authz",
            role=User.Role.ASSISTANT,
        )
        self.receptionist = User.objects.create_user(
            email="receptionist_authz@example.com",
            password="StrongPassword123!",
            first_name="Reception",
            last_name="Authz",
            role=User.Role.RECEPTIONIST,
        )
        self.accountant = User.objects.create_user(
            email="accountant_authz@example.com",
            password="StrongPassword123!",
            first_name="Accountant",
            last_name="Authz",
            role=User.Role.ACCOUNTANT,
        )

        (
            self.superadmin_session,
            self.superadmin_token,
        ) = create_authentication_session(self.superadmin)
        self.admin_session, self.admin_token = create_authentication_session(
            self.admin
        )
        self.dentist_session, self.dentist_token = create_authentication_session(
            self.dentist
        )
        self.assistant_session, self.assistant_token = create_authentication_session(
            self.assistant
        )
        (
            self.receptionist_session,
            self.receptionist_token,
        ) = create_authentication_session(self.receptionist)
        (
            self.accountant_session,
            self.accountant_token,
        ) = create_authentication_session(self.accountant)

        self.patient = Patient.objects.create(
            first_name="P",
            last_name="Authz",
            birthdate="1990-01-01",
            gender="other",
            phone="+213111111111",
        )

    def test_users_non_superadmin_retrieve_other_user_is_404(self):
        """UserViewSet.get_queryset scopes non-superadmin to self.

        Expected (from code): retrieving someone else's user should not be allowed.
        Current behavior should be 404 (object not in queryset).
        """

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )
        resp = self.client.get(f"/api/users/{self.dentist.id}/")
        self.assertEqual(resp.status_code, 404)

    def test_users_non_superadmin_cannot_patch_even_self(self):
        """UserViewSet.partial_update explicitly requires SUPER_ADMIN."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )

        resp = self.client.patch(
            f"/api/users/{self.receptionist.id}/",
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(resp.status_code, 403)

    def test_audit_logs_denied_for_non_superadmin(self):
        """AuditLogViewSet is IsSuperAdmin-only."""

        AuditLog.objects.create(action="x", model_name="y")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.admin_token}"
        )
        resp = self.client.get("/api/audit-logs/")
        self.assertEqual(resp.status_code, 403)

    def test_patients_denied_for_accountant(self):
        """PatientViewSet requires IsClinicalStaff."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )
        resp = self.client.get("/api/patients/")
        self.assertEqual(resp.status_code, 403)

    def test_invoices_denied_for_dentist(self):
        """InvoiceViewSet requires IsAccountantOrAdmin."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token}"
        )
        resp = self.client.get("/api/invoices/")
        self.assertEqual(resp.status_code, 403)

    def test_appointments_accessible_to_receptionist_and_not_scoped_by_practitioner(
        self,
    ):
        """AppointmentViewSet uses IsStaffMember and has no object-level scoping.

        Characterization: receptionist can retrieve an appointment assigned to dentist.
        """

        appt = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at="2035-01-15T09:00:00Z",
            end_at="2035-01-15T09:30:00Z",
            status=Appointment.Status.PENDING,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )
        resp = self.client.get(f"/api/appointments/{appt.id}/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], appt.id)

    def test_receptionist_can_create_but_not_retrieve_document(self):
        """AUTH-001: Receptionist can create a document but cannot retrieve it
        (no scope-defining relation in the current model)."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )
        create = self.client.post(
            "/api/documents/",
            {
                "patient": self.patient.id,
                "document_type": "other",
                "title": "Doc",
                "content": "x",
                "status": "draft",
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)

        doc_id = create.data["id"]
        retrieve = self.client.get(f"/api/documents/{doc_id}/")
        self.assertEqual(retrieve.status_code, 404)

    def test_superadmin_can_access_audit_logs(self):
        AuditLog.objects.create(action="x", model_name="y")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.superadmin_token}"
        )
        resp = self.client.get("/api/audit-logs/")
        self.assertEqual(resp.status_code, 200)

    def test_accountant_can_create_invoice_and_retrieve_by_id(self):
        """Billing resources are not scoped by patient/accountant."""

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )
        create = self.client.post(
            "/api/invoices/",
            {
                "patient": self.patient.id,
                "issued_at": "2035-01-15",
                "due_date": "2035-02-15",
                "status": "draft",
                "reference_number": "INV-AUTHZ-1",
            },
            format="json",
        )

        self.assertEqual(create.status_code, 201, create.data)
        inv_id = create.data["id"]
        retrieve = self.client.get(f"/api/invoices/{inv_id}/")
        self.assertEqual(retrieve.status_code, 200)
        self.assertEqual(retrieve.data["id"], inv_id)

    def test_accountant_cannot_delete_invoice(self):
        """Invoice deletion is explicitly forbidden."""

        invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.accountant,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-AUTHZ-DELETE",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )

        response = self.client.delete(
            f"/api/invoices/{invoice.pk}/"
        )

        self.assertEqual(response.status_code, 400)

        self.assertTrue(
            Invoice.objects.filter(pk=invoice.pk).exists()
        )

    def test_appointments_denied_to_unauthorized_roles(self):
        unauthorized = (
            (self.superadmin_token, User.Role.SUPER_ADMIN),
            (self.admin_token, User.Role.ADMINISTRATOR),
            (self.assistant_token, User.Role.ASSISTANT),
            (self.accountant_token, User.Role.ACCOUNTANT),
        )

        for token, role in unauthorized:
            self.client.credentials(
                HTTP_AUTHORIZATION=f"Token {token}"
            )

            response = self.client.get("/api/appointments/")
            self.assertEqual(
                response.status_code,
                403,
                msg=f"{role} should be denied access to appointments",
            )

    def test_receptionist_api_create_appointment_sets_created_by_to_request_user(
        self,
    ):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )

        response = self.client.post(
            "/api/appointments/",
            {
                "patient": self.patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-02-10T09:00:00Z",
                "end_at": "2035-02-10T09:30:00Z",
                "status": "pending",
                "reason": "API creation probe",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)

        appointment = Appointment.objects.get(pk=response.data["id"])

        self.assertEqual(
            appointment.created_by_id,
            self.receptionist.id,
        )

    def test_receptionist_can_currently_modify_appointment_times(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at="2035-03-10T09:00:00Z",
            end_at="2035-03-10T09:30:00Z",
            status=Appointment.Status.PENDING,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )

        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {
                "start_at": "2035-03-10T10:00:00Z",
                "end_at": "2035-03-10T10:30:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)

        appointment.refresh_from_db()

        self.assertEqual(
            appointment.start_at.isoformat(),
            "2035-03-10T10:00:00+00:00",
        )

        self.assertEqual(
            appointment.end_at.isoformat(),
            "2035-03-10T10:30:00+00:00",
        )

    def test_receptionist_cannot_modify_appointment_times_into_practitioner_overlap(
        self,
    ):
        Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at="2035-03-10T10:00:00Z",
            end_at="2035-03-10T10:30:00Z",
            status=Appointment.Status.PENDING,
        )

        appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at="2035-03-10T09:00:00Z",
            end_at="2035-03-10T09:30:00Z",
            status=Appointment.Status.PENDING,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )

        response = self.client.patch(
            f"/api/appointments/{appointment.id}/",
            {
                "start_at": "2035-03-10T10:15:00Z",
                "end_at": "2035-03-10T10:45:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_appointment_rejects_non_assistant_as_assistant(self):
        appointment = Appointment(
            patient=self.patient,
            practitioner=self.dentist,
            assistant=self.receptionist,  # receptionist is not an assistant
            start_at="2042-05-10T09:00:00Z",
            end_at="2042-05-10T09:30:00Z",
        )

        with self.assertRaises(ValidationError) as context:
            appointment.full_clean()
        self.assertIn("assistant", context.exception.message_dict)

    def test_appointment_accepts_assistant_role(self):
        appointment = Appointment(
            patient=self.patient,
            practitioner=self.dentist,
            assistant=self.assistant,
            start_at="2042-05-10T09:00:00Z",
            end_at="2042-05-10T09:30:00Z",
        )

        appointment.full_clean()
