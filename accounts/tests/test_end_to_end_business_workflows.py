from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from appointments.models import Appointment
from billing.models import Invoice, InvoiceLine, Payment
from patients.models import Patient
from treatment_plans.models import TreatmentPlan
from treatments.models import Treatment


class EndToEndBusinessWorkflowTests(TestCase):
    """PHASE B12 end-to-end business workflow characterization tests."""

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist_workflow@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="Workflow",
            role=User.Role.DENTIST,
        )

        self.patient = Patient.objects.create(
            first_name="Patient",
            last_name="Workflow",
            birthdate=date(1990, 1, 1),
            gender="male",
            phone="0550000000",
        )

        self.other_patient = Patient.objects.create(
            first_name="Other",
            last_name="Patient",
            birthdate=date(1991, 1, 1),
            gender="female",
            phone="0550000001",
        )

    def test_complete_clinical_to_financial_workflow_can_be_persisted(self):
        start_at = timezone.now()
        appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=30),
            status=Appointment.Status.CONFIRMED,
            reason="Consultation",
        )

        treatment_plan = TreatmentPlan.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            status="approved",
            total_estimated_cost=Decimal("5000.00"),
            total_approved_cost=Decimal("5000.00"),
        )

        treatment = Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            appointment=appointment,
            treatment_plan=treatment_plan,
            status="completed",
            category=Treatment.Category.CONSULTATION,
            code="CONS-001",
            label="Consultation",
            price=Decimal("5000.00"),
            total_price=Decimal("5000.00"),
        )

        invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date.today(),
            due_date=date.today(),
            status="issued",
            total_amount=Decimal("5000.00"),
            paid_amount=Decimal("0.00"),
            balance_due=Decimal("5000.00"),
            reference_number="INV-B12-001",
            related_treatment_plan=treatment_plan,
        )

        line = InvoiceLine.objects.create(
            invoice=invoice,
            description="Consultation",
            treatment=treatment,
            quantity=Decimal("1.00"),
            unit_price=Decimal("5000.00"),
            total_price=Decimal("5000.00"),
        )

        payment = Payment.objects.create(
            invoice=invoice,
            patient=self.patient,
            paid_by=self.dentist,
            payment_at=timezone.now(),
            amount=Decimal("5000.00"),
            method="cash",
            status="completed",
        )

        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(treatment.appointment, appointment)
        self.assertEqual(treatment.treatment_plan, treatment_plan)
        self.assertEqual(line.treatment, treatment)
        self.assertEqual(payment.invoice, invoice)

    def test_treatment_can_reference_appointment_for_different_patient(self):
        start_at = timezone.now()
        appointment = Appointment.objects.create(
            patient=self.other_patient,
            practitioner=self.dentist,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=30),
        )

        treatment = Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            appointment=appointment,
            status="planned",
            category=Treatment.Category.CONSULTATION,
            code="CONS-XPAT",
            label="Cross-patient treatment",
        )

        self.assertNotEqual(treatment.patient, treatment.appointment.patient)

    def test_treatment_can_reference_plan_for_different_patient(self):
        treatment_plan = TreatmentPlan.objects.create(
            patient=self.other_patient,
            created_by=self.dentist,
            status="draft",
        )

        treatment = Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            treatment_plan=treatment_plan,
            status="planned",
            category=Treatment.Category.CONSULTATION,
            code="CONS-XPLAN",
            label="Cross-plan treatment",
        )

        self.assertNotEqual(
            treatment.patient,
            treatment.treatment_plan.patient,
        )

    def test_invoice_line_can_reference_treatment_for_different_patient(self):
        treatment = Treatment.objects.create(
            patient=self.other_patient,
            dentist=self.dentist,
            status="completed",
            category=Treatment.Category.CONSULTATION,
            code="CONS-XINV",
            label="Other patient treatment",
        )

        invoice = Invoice.objects.create(
            patient=self.patient,
            issued_at=date.today(),
            due_date=date.today(),
            status="issued",
            reference_number="INV-B12-002",
        )

        line = InvoiceLine.objects.create(
            invoice=invoice,
            description="Cross-patient line",
            treatment=treatment,
        )

        self.assertNotEqual(
            line.invoice.patient,
            line.treatment.patient,
        )

    def test_payment_patient_can_differ_from_invoice_patient(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            issued_at=date.today(),
            due_date=date.today(),
            status="issued",
            reference_number="INV-B12-003",
        )

        payment = Payment.objects.create(
            invoice=invoice,
            patient=self.other_patient,
            payment_at=timezone.now(),
            amount=Decimal("1000.00"),
            method="cash",
            status="completed",
        )

        self.assertNotEqual(payment.patient, payment.invoice.patient)

    def test_payment_does_not_automatically_update_invoice_balances(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            issued_at=date.today(),
            due_date=date.today(),
            status="issued",
            total_amount=Decimal("5000.00"),
            paid_amount=Decimal("0.00"),
            balance_due=Decimal("5000.00"),
            reference_number="INV-B12-004",
        )

        Payment.objects.create(
            invoice=invoice,
            patient=self.patient,
            payment_at=timezone.now(),
            amount=Decimal("2000.00"),
            method="cash",
            status="completed",
        )

        invoice.refresh_from_db()

        self.assertEqual(invoice.paid_amount, Decimal("0.00"))
        self.assertEqual(invoice.balance_due, Decimal("5000.00"))
