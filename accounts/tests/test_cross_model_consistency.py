from accounts.services.authentication import create_authentication_session
from django.utils import timezone
from rest_framework.test import APITestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from appointments.models import Appointment, Room
from billing.models import Invoice, Payment
from patients.models import Patient
from treatment_plans.models import TreatmentPlan, TreatmentPlanApproval
from treatments.models import Treatment
from documents.models import Document, DocumentAttachment

class CrossModelConsistencyTests(APITestCase):
    """Regression tests for cross-model consistency enforcement."""

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="Example",
            role=User.Role.DENTIST,
        )
        self.accountant = User.objects.create_user(
            email="accountant@example.com",
            password="StrongPassword123!",
            first_name="Accountant",
            last_name="Example",
            role=User.Role.ACCOUNTANT,
        )

        self.dentist_session, self.dentist_token = create_authentication_session(self.dentist)
        self.accountant_session, self.accountant_token = create_authentication_session(self.accountant)

    def _mk_patient(self, email_suffix: str) -> Patient:
        return Patient.objects.create(
            first_name="P",
            last_name=f"{email_suffix}",
            birthdate="1990-01-01",
            gender="other",
            phone=f"+2130000{email_suffix[-4:]}",
        )

    def test_api_payment_patient_mismatch_with_invoice_patient_is_accepted(self):
        """Document the currently accepted payment/invoice patient relationship.
        The payment model permits a patient different from the invoice patient.
        This relationship remains a business-rule decision rather than an enforced
        cross-model consistency rule.
        """

        patient_a = self._mk_patient("A")
        patient_b = self._mk_patient("B")

        invoice = Invoice.objects.create(
            patient=patient_a,
            issued_at="2035-01-15",
            due_date="2035-02-15",
            status="draft",
            reference_number="INV-PATH-A",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.accountant_token}")
        resp = self.client.post(
            "/api/payments/",
            {
                "invoice": invoice.id,
                "patient": patient_b.id,
                "payment_at": "2035-01-16T10:00:00Z",
                "amount": "10.00",
                "method": "cash",
                "status": "completed",
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 201, resp.data)

        payment = Payment.objects.get(pk=resp.data["id"])
        self.assertEqual(payment.invoice_id, invoice.id)
        self.assertNotEqual(payment.patient_id, invoice.patient_id)

    def test_api_invoice_patient_mismatch_with_related_treatment_plan_patient_is_rejected(self):
        """Invoice patient must match the related treatment plan patient."""

        patient_a = self._mk_patient("PlanA")
        patient_b = self._mk_patient("InvB")

        plan = TreatmentPlan.objects.create(
            patient=patient_a,
            status="draft",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )

        resp = self.client.post(
            "/api/invoices/",
            {
                "patient": patient_b.id,
                "issued_at": "2035-01-15",
                "due_date": "2035-02-15",
                "status": "draft",
                "reference_number": "INV-PLAN-MISMATCH",
                "related_treatment_plan": plan.id,
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 400, resp.data)
        self.assertIn("related_treatment_plan", resp.data)

        self.assertFalse(
            Invoice.objects.filter(
                reference_number="INV-PLAN-MISMATCH"
            ).exists()
            )

    def test_api_treatment_patient_mismatch_with_appointment_patient_is_rejected(self):
        """Reject a treatment whose patient differs from its appointment."""

        patient_a = self._mk_patient("ApptA")
        patient_b = self._mk_patient("TreatB")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token}")

        room_resp = self.client.post(
            "/api/rooms/",
            {"name": "Room 1", "capacity": 1},
            format="json",
        )
        self.assertEqual(room_resp.status_code, 201, room_resp.data)

        appt_resp = self.client.post(
            "/api/appointments/",
            {
                "patient": patient_a.id,
                "practitioner": self.dentist.id,
                "room": room_resp.data["id"],
                "start_at": "2035-01-15T09:00:00Z",
                "end_at": "2035-01-15T09:30:00Z",
                "status": Appointment.Status.PENDING,
            },
            format="json",
        )
        self.assertEqual(appt_resp.status_code, 201, appt_resp.data)

        treat_resp = self.client.post(
            "/api/treatments/",
            {
                "status": "planned",
                "category": "consultation",
                "code": "TREAT-MISMATCH-APPT",
                "label": "Mismatch",
                "patient": patient_b.id,
                "dentist": self.dentist.id,
                "appointment": appt_resp.data["id"],
            },
            format="json",
        )

        self.assertEqual(treat_resp.status_code, 400, treat_resp.data)

        self.assertIn("appointment", treat_resp.data)

        self.assertFalse(
            Treatment.objects.filter(
                code="TREAT-MISMATCH-APPT"
            ).exists()
        )

    def test_api_treatment_patient_mismatch_with_treatment_plan_patient_is_rejected(self):
        """Reject a treatment whose patient differs from its treatment plan."""

        patient_a = self._mk_patient("PlanA2")
        patient_b = self._mk_patient("TreatB2")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.dentist_token}")

        plan_resp = self.client.post(
            "/api/treatment-plans/",
            {"patient": patient_a.id, "status": "draft"},
            format="json",
        )
        self.assertEqual(plan_resp.status_code, 201, plan_resp.data)

        treat_resp = self.client.post(
            "/api/treatments/",
            {
                "status": "planned",
                "category": "consultation",
                "code": "TREAT-MISMATCH-PLAN",
                "label": "Mismatch",
                "patient": patient_b.id,
                "dentist": self.dentist.id,
                "treatment_plan": plan_resp.data["id"],
            },
            format="json",
        )
        self.assertEqual(treat_resp.status_code, 400, treat_resp.data)

        self.assertIn("treatment_plan", treat_resp.data)

        self.assertFalse(
            Treatment.objects.filter(
                code="TREAT-MISMATCH-PLAN"
            ).exists()
        )

    def test_orm_treatment_plan_approval_patient_mismatch_with_plan_patient_is_rejected(self):
        """Reject an approval whose patient differs from its treatment plan."""

        patient_a = self._mk_patient("PlanApproverA")
        patient_b = self._mk_patient("ApprovalB")

        plan = TreatmentPlan.objects.create(
            patient=patient_a,
            status="draft",
        )

        with self.assertRaises(ValidationError):
            TreatmentPlanApproval.objects.create(
                treatment_plan=plan,
                patient=patient_b,
                approved_by=self.dentist,
                approved_at=timezone.now(),
                signature_type="typed",
            )

        self.assertFalse(
            TreatmentPlanApproval.objects.filter(
                treatment_plan=plan,
                patient=patient_b,
            ).exists()
        )

    def test_orm_treatment_plan_approval_matching_plan_patient_is_accepted(self):
        """Accept an approval whose patient matches its treatment plan."""

        patient = self._mk_patient("PlanApprovalMatch")

        plan = TreatmentPlan.objects.create(
            patient=patient,
            status="draft",
        )

        approval = TreatmentPlanApproval.objects.create(
            treatment_plan=plan,
            patient=patient,
            approved_by=self.dentist,
            approved_at=timezone.now(),
            signature_type="typed",
        )

        self.assertEqual(approval.treatment_plan_id, plan.id)
        self.assertEqual(approval.patient_id, plan.patient_id)
        self.assertEqual(approval.patient_id, patient.id)

    def test_orm_document_attachment_patient_mismatch_with_document_patient_is_rejected(self):
        """Reject an attachment whose patient differs from its document patient."""

        patient_a = self._mk_patient("DocumentA")
        patient_b = self._mk_patient("AttachmentB")

        document = Document.objects.create(
            patient=patient_a,
            document_type="clinical",
            title="Patient A Document",
            content="Document content",
            status=Document.Status.DRAFT,
        )

        attachment = DocumentAttachment(
            patient=patient_b,
            document=document,
            file=SimpleUploadedFile(
                "test.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            file_type="application/pdf",
            description="Mismatched attachment",
        )

        with self.assertRaises(ValidationError) as exc:
            attachment.save()

        self.assertIn("patient", exc.exception.message_dict)

        self.assertFalse(
            DocumentAttachment.objects.filter(
                document=document,
                patient=patient_b,
            ).exists()
        )

    def test_orm_document_attachment_matching_document_patient_is_accepted(self):
        """Accept an attachment whose patient matches its document patient."""

        patient = self._mk_patient("DocumentMatch")

        document = Document.objects.create(
            patient=patient,
            document_type="clinical",
            title="Patient Document",
            content="Document content",
            status=Document.Status.DRAFT,
        )

        attachment = DocumentAttachment.objects.create(
            patient=patient,
            document=document,
            file=SimpleUploadedFile(
                "test.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            file_type="application/pdf",
            description="Matching attachment",
        )

        self.assertEqual(attachment.patient_id, document.patient_id)
        self.assertEqual(attachment.document_id, document.id)

    def test_orm_document_attachment_without_document_is_accepted(self):
        """Accept an attachment without a related document."""

        patient = self._mk_patient("AttachmentOnly")

        attachment = DocumentAttachment.objects.create(
            patient=patient,
            document=None,
            file=SimpleUploadedFile(
                "test.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            file_type="application/pdf",
            description="Standalone attachment",
        )

        self.assertEqual(attachment.patient_id, patient.id)
        self.assertIsNone(attachment.document_id)

    def test_orm_document_attachment_update_patient_mismatch_with_document_is_rejected(self):
        """Reject an attachment update that introduces a patient mismatch."""

        patient_a = self._mk_patient("UpdateDocument")
        patient_b = self._mk_patient("UpdateAttachment")

        document = Document.objects.create(
            patient=patient_a,
            document_type="clinical",
            title="Patient A Document",
            content="Document content",
            status=Document.Status.DRAFT,
        )

        attachment = DocumentAttachment.objects.create(
            patient=patient_a,
            document=document,
            file=SimpleUploadedFile(
                "test.pdf",
                b"%PDF-1.4 test",
                content_type="application/pdf",
            ),
            file_type="application/pdf",
            description="Original matching attachment",
        )

        attachment.patient = patient_b

        with self.assertRaises(ValidationError) as exc:
            attachment.save()

        self.assertIn("patient", exc.exception.message_dict)

        attachment.refresh_from_db()
        self.assertEqual(attachment.patient_id, patient_a.id)
        self.assertEqual(attachment.document_id, document.id)
