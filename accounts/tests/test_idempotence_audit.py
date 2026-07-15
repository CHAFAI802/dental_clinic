from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from appointments.models import Appointment, Room
from billing.models import Invoice, Payment
from imaging.models import ImagingSeries, ImagingStudy
from patients.models import Patient
from prescriptions.models import PrescriptionTemplate


class IdempotenceDuplicateSubmissionTests(APITestCase):
    """PHASE B8 characterization tests.

    These tests document whether repeated equivalent POST submissions create duplicates.
    """

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist_idem@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="Idem",
            role=User.Role.DENTIST,
        )
        self.receptionist = User.objects.create_user(
            email="receptionist_idem@example.com",
            password="StrongPassword123!",
            first_name="Reception",
            last_name="Idem",
            role=User.Role.RECEPTIONIST,
        )
        self.accountant = User.objects.create_user(
            email="accountant_idem@example.com",
            password="StrongPassword123!",
            first_name="Accountant",
            last_name="Idem",
            role=User.Role.ACCOUNTANT,
        )
        self.admin = User.objects.create_user(
            email="admin_idem@example.com",
            password="StrongPassword123!",
            first_name="Admin",
            last_name="Idem",
            role=User.Role.ADMINISTRATOR,
        )

        self.dentist_token = Token.objects.create(user=self.dentist)
        self.receptionist_token = Token.objects.create(user=self.receptionist)
        self.accountant_token = Token.objects.create(user=self.accountant)
        self.admin_token = Token.objects.create(user=self.admin)

        self.patient = Patient.objects.create(
            first_name="P",
            last_name="Idem",
            birthdate="1990-01-01",
            gender="other",
            phone="+213222222222",
        )

    def test_duplicate_post_appointments_creates_duplicates(self):
        """Equivalent appointment POST repeated creates duplicate appointments."""

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.receptionist_token.key}")

        room = Room.objects.create(name="Idem Room")
        payload = {
            "patient": self.patient.id,
            "practitioner": self.dentist.id,
            "room": room.id,
            "start_at": "2035-01-15T09:00:00Z",
            "end_at": "2035-01-15T09:30:00Z",
            "status": Appointment.Status.PENDING,
        }

        first = self.client.post("/api/appointments/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)

        second = self.client.post("/api/appointments/", payload, format="json")
        self.assertEqual(second.status_code, 201, second.data)

        self.assertNotEqual(first.data["id"], second.data["id"])
        self.assertEqual(
            Appointment.objects.filter(
                patient=self.patient,
                practitioner=self.dentist,
                room=room,
                start_at="2035-01-15T09:00:00Z",
                end_at="2035-01-15T09:30:00Z",
            ).count(),
            2,
        )

    def test_duplicate_post_payments_creates_duplicates(self):
        """Equivalent payment POST repeated creates duplicate payments."""

        invoice = Invoice.objects.create(
            patient=self.patient,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-IDEM-PAY",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token.key}")

        payload = {
            "invoice": invoice.id,
            "patient": self.patient.id,
            "payment_at": "2035-01-16T10:00:00Z",
            "amount": "10.00",
            "method": "cash",
            "status": "completed",
        }

        first = self.client.post("/api/payments/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)

        second = self.client.post("/api/payments/", payload, format="json")
        self.assertEqual(second.status_code, 201, second.data)

        self.assertEqual(Payment.objects.filter(invoice=invoice, amount="10.00").count(), 2)

    def test_invoice_reference_number_unique_prevents_exact_duplicate(self):
        """Invoice.reference_number uniqueness blocks exact duplicate retries (same reference)."""

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token.key}")

        payload = {
            "patient": self.patient.id,
            "issued_at": "2035-01-15",
            "due_date": "2035-02-15",
            "status": "draft",
            "reference_number": "INV-IDEM-REF",
        }

        first = self.client.post("/api/invoices/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)

        second = self.client.post("/api/invoices/", payload, format="json")
        self.assertEqual(second.status_code, 400)

    def test_duplicate_post_notifications_creates_duplicates(self):
        """Equivalent notification POST repeated creates duplicates."""

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

        payload = {
            "channel": "email",
            "status": "pending",
            "payload": {"k": "v"},
        }

        first = self.client.post("/api/notifications/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)

        second = self.client.post("/api/notifications/", payload, format="json")
        self.assertEqual(second.status_code, 201, second.data)

    def test_duplicate_post_documents_creates_duplicates(self):
        """Equivalent document POST repeated creates duplicates."""

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.receptionist_token.key}")

        payload = {
            "patient": self.patient.id,
            "document_type": "other",
            "title": "Same",
            "content": "Same",
            "status": "draft",
        }

        first = self.client.post("/api/documents/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)

        second = self.client.post("/api/documents/", payload, format="json")
        self.assertEqual(second.status_code, 201, second.data)

    def test_duplicate_post_prescriptions_creates_duplicates(self):
        """Equivalent prescription POST repeated creates duplicates."""

        template = PrescriptionTemplate.objects.create(
            name="T",
            content="Hello",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")

        payload = {
            "status": "draft",
            "patient": self.patient.id,
            "dentist": self.dentist.id,
            "template": template.id,
        }

        first = self.client.post("/api/prescriptions/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)

        second = self.client.post("/api/prescriptions/", payload, format="json")
        self.assertEqual(second.status_code, 201, second.data)

    def test_duplicate_post_imaging_instance_creates_duplicates(self):
        """Equivalent imaging upload repeated creates duplicate instances + duplicate stored files."""

        study = ImagingStudy.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            study_type="panoramic",
            study_date="2035-01-15T10:00:00Z",
            status="pending",
        )

        series = ImagingSeries.objects.create(
            study=study,
            series_number=1,
            modality="OT",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}")

        file_1 = SimpleUploadedFile("same.txt", b"same content\n", content_type="text/plain")

        payload = {
            "series": str(series.id),
            "instance_number": "1",
            "file_type": "text/plain",
            "study_date": "2035-01-15T10:00:00Z",
            "file": file_1,
        }

        first = self.client.post("/api/imaging-instances/", payload, format="multipart")
        self.assertEqual(first.status_code, 201, first.data)

        # Need a new UploadedFile object (stream consumed).
        file_2 = SimpleUploadedFile("same.txt", b"same content\n", content_type="text/plain")
        payload["file"] = file_2

        second = self.client.post("/api/imaging-instances/", payload, format="multipart")
        self.assertEqual(second.status_code, 201, second.data)
