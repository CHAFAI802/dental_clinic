from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from appointments.models import Appointment
from billing.models import Invoice
from patients.models import Patient


class BusinessRulesCharacterizationTests(APITestCase):
    """Characterization tests for business rule enforcement.

    These tests do NOT assume best-practice rules.
    They document what the current backend accepts/rejects.

    If a rule is missing, the test typically asserts that the API ACCEPTS the input.
    """

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist_rules@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="Rules",
            role=User.Role.DENTIST,
        )
        self.accountant = User.objects.create_user(
            email="accountant_rules@example.com",
            password="StrongPassword123!",
            first_name="Accountant",
            last_name="Rules",
            role=User.Role.ACCOUNTANT,
        )
        self.dentist_token = Token.objects.create(user=self.dentist)
        self.accountant_token = Token.objects.create(user=self.accountant)

    def _mk_patient(self, suffix: str) -> Patient:
        return Patient.objects.create(
            first_name="P",
            last_name=f"{suffix}",
            birthdate="1990-01-01",
            gender="other",
            phone=f"+2139000{suffix[-4:]}",
        )

    def test_appointment_invalid_status_is_rejected(self):
        """Implemented (ChoiceField): Appointment.status must be one of Status.choices."""

        patient = self._mk_patient("STAT")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")
        resp = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T09:30:00Z",
                "status": "not-a-real-status",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

    def test_appointment_end_before_start_is_accepted(self):
        """[WARN] BUSINESS RULE UNDEFINED: no implementation enforces end_at > start_at."""

        patient = self._mk_patient("TIME")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")
        resp = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T10:00:00Z",
                "end_at": "2035-01-15T09:00:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201, resp.data)

    def test_overlapping_appointments_for_same_practitioner_are_accepted(self):
        """[WARN] BUSINESS RULE UNDEFINED: no overlap/availability checks are implemented."""

        patient = self._mk_patient("OVLP")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")

        first = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T10:00:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(first.status_code, 201, first.data)

        second = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "practitioner": self.dentist.id,
                "start_at": "2035-01-15T09:30:00Z",
                "end_at": "2035-01-15T10:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(second.status_code, 201, second.data)

    def test_negative_payment_amount_is_accepted(self):
        """[WARN] BUSINESS RULE UNDEFINED: no non-negative validator exists for Payment.amount."""

        patient = self._mk_patient("PAYNEG")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-NEG-AMOUNT",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token.key}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "-1.00",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201, resp.data)

    def test_payment_amount_can_exceed_invoice_balance_due_is_accepted(self):
        """[WARN] BUSINESS RULE UNDEFINED: invoice/payment balance logic is not implemented."""

        patient = self._mk_patient("PAYBIG")
        invoice = Invoice.objects.create(
            patient=patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-BIG-PAY",
            balance_due=0,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token.key}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "9999.99",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201, resp.data)

    def test_inventory_item_negative_stock_quantity_is_accepted(self):
        """[WARN] BUSINESS RULE UNDEFINED: InventoryItem.stock_quantity accepts negative values."""

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token.key}")
        resp = self.client.post(
            "/api/inventory-items/",
            {
                "sku": "SKU-NEG-STOCK",
                "name": "Negative Stock",
                "unit": "unit",
                "stock_quantity": "-5.00",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201, resp.data)

    def test_invoice_negative_total_amount_is_accepted(self):
        """[WARN] BUSINESS RULE UNDEFINED: Invoice totals are client-writable and can be negative."""

        patient = self._mk_patient("INVNEG")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token.key}")
        resp = self.client.post(
            "/api/invoices/",
            {
                "patient": patient.id,
                "issued_at": "2035-01-15",
                "due_date": "2035-02-15",
                "status": "draft",
                "reference_number": "INV-NEG-TOTAL",
                "total_amount": "-100.00",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201, resp.data)
