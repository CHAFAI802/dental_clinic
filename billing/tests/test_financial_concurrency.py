from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone

from appointments.models import Appointment
from billing.models import (
    CreditNote,
    Invoice,
    InvoiceLine,
    Payment,
    PaymentMethod,
    Prestation,
    PrestationCategory,
    PrestationTarif,
)
from billing.services.prescription_billing import apply_prescription_billing
from patients.models import Patient
from prescriptions.models import Prescription, PrescriptionTemplate
from treatments.models import Treatment


User = get_user_model()


class InvoiceFinancialConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="financial-dentist@example.test",
            password="test-password",
            first_name="Financial",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        self.patient = Patient.objects.create(
            first_name="Financial",
            last_name="Patient",
            birthdate="2000-01-01",
            gender="other",
            phone="0123456789",
        )
        self.accountant = User.objects.create_user(
            email="financial-accountant@example.test",
            password="test-password",
            first_name="Financial",
            last_name="Accountant",
            role=User.Role.ACCOUNTANT,
        )
        self.payment_method = PaymentMethod.objects.create(name="Cash")
        category = PrestationCategory.objects.create(
            name="Financial tests",
            code="FINANCIAL",
        )
        self.prestation = Prestation.objects.create(
            category=category,
            code="FINANCIAL-01",
            label="Financial test act",
        )
        PrestationTarif.objects.create(
            prestation=self.prestation,
            amount=Decimal("1000.00"),
            tax_rate=Decimal("0.00"),
            effective_from="2026-01-01",
        )
        treatment = Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            prestation=self.prestation,
            code=self.prestation.code,
            label=self.prestation.label,
            start_at="2026-09-14T10:00:00+01:00",
        )
        line = InvoiceLine.objects.create(
            treatment=treatment,
            prestation=self.prestation,
            description=self.prestation.label,
            quantity=Decimal("1.00"),
        )
        self.invoice_id = line.invoice_id

    def _run_simultaneously(self, operation, arguments):
        barrier = Barrier(len(arguments))

        def worker(argument):
            close_old_connections()
            connection = connections["default"]
            connection.ensure_connection()
            backend_pid = connection.connection.get_backend_pid()
            try:
                with transaction.atomic():
                    barrier.wait(timeout=15)
                    result = operation(argument)
                return backend_pid, result
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(arguments)) as executor:
            futures = [
                executor.submit(worker, argument)
                for argument in arguments
            ]
            results = [future.result(timeout=45) for future in futures]

        self.assertEqual(
            len({pid for pid, _ in results}),
            len(arguments),
            "Each concurrent operation must use a distinct PostgreSQL connection.",
        )
        return [result for _, result in results]

    def _create_payment(self, amount):
        Payment.objects.create(
            invoice_id=self.invoice_id,
            patient_id=self.patient.pk,
            amount=amount,
            method_id=self.payment_method.pk,
        )
        return True

    def _create_credit_note(self, amount):
        CreditNote.objects.create(
            invoice_id=self.invoice_id,
            created_by_id=self.accountant.pk,
            amount=amount,
            reason="Concurrent credit note",
        )
        return True

    def test_two_simultaneous_payments_preserve_both_amounts(self):
        results = self._run_simultaneously(
            self._create_payment,
            [Decimal("300.00"), Decimal("300.00")],
        )

        invoice = Invoice.objects.get(pk=self.invoice_id)
        self.assertEqual(results, [True, True])
        self.assertEqual(Payment.objects.filter(invoice=invoice).count(), 2)
        self.assertEqual(invoice.paid_amount, Decimal("600.00"))
        self.assertEqual(invoice.balance_due, Decimal("400.00"))

    def test_two_simultaneous_credit_notes_preserve_both_amounts(self):
        results = self._run_simultaneously(
            self._create_credit_note,
            [Decimal("200.00"), Decimal("200.00")],
        )

        invoice = Invoice.objects.get(pk=self.invoice_id)
        self.assertEqual(results, [True, True])
        self.assertEqual(CreditNote.objects.filter(invoice=invoice).count(), 2)
        self.assertEqual(invoice.credit_amount, Decimal("400.00"))
        self.assertEqual(invoice.balance_due, Decimal("600.00"))

    def test_simultaneous_payment_and_credit_note_preserve_both_amounts(self):
        results = self._run_simultaneously(
            lambda operation: (
                self._create_payment(Decimal("300.00"))
                if operation == "payment"
                else self._create_credit_note(Decimal("200.00"))
            ),
            ["payment", "credit_note"],
        )

        invoice = Invoice.objects.get(pk=self.invoice_id)
        self.assertEqual(results, [True, True])
        self.assertEqual(invoice.paid_amount, Decimal("300.00"))
        self.assertEqual(invoice.credit_amount, Decimal("200.00"))
        self.assertEqual(invoice.balance_due, Decimal("500.00"))

    def test_concurrent_overpayment_rolls_back_losing_payment(self):
        def create_payment(amount):
            try:
                self._create_payment(amount)
            except ValidationError:
                return False
            return True

        results = self._run_simultaneously(
            create_payment,
            [Decimal("600.00"), Decimal("600.00")],
        )

        invoice = Invoice.objects.get(pk=self.invoice_id)
        self.assertEqual(sum(results), 1)
        self.assertEqual(Payment.objects.filter(invoice=invoice).count(), 1)
        self.assertEqual(invoice.paid_amount, Decimal("600.00"))
        self.assertEqual(invoice.balance_due, Decimal("400.00"))

    def test_invalid_credit_note_rolls_back_without_changing_invoice_totals(self):
        with self.assertRaises(ValidationError):
            self._create_credit_note(Decimal("1000.01"))

        invoice = Invoice.objects.get(pk=self.invoice_id)
        self.assertFalse(CreditNote.objects.filter(invoice=invoice).exists())
        self.assertEqual(invoice.credit_amount, Decimal("0.00"))
        self.assertEqual(invoice.balance_due, Decimal("1000.00"))

    def test_deleting_payment_recalculates_amounts_with_existing_credit_note(self):
        payment = Payment.objects.create(
            invoice_id=self.invoice_id,
            patient_id=self.patient.pk,
            amount=Decimal("200.00"),
            method_id=self.payment_method.pk,
        )
        self._create_credit_note(Decimal("100.00"))

        payment.delete()

        invoice = Invoice.objects.get(pk=self.invoice_id)
        self.assertEqual(invoice.paid_amount, Decimal("0.00"))
        self.assertEqual(invoice.credit_amount, Decimal("100.00"))
        self.assertEqual(invoice.balance_due, Decimal("900.00"))

    def test_direct_prescription_billing_is_idempotent_without_caller_lock(self):
        appointment, treatment = self._create_prescription_case()

        self.assertTrue(apply_prescription_billing(appointment=appointment))
        self.assertFalse(apply_prescription_billing(appointment=appointment))
        self.assertEqual(
            InvoiceLine.objects.filter(treatment=treatment).count(),
            1,
        )

    def test_concurrent_direct_prescription_billing_creates_one_line(self):
        appointment, treatment = self._create_prescription_case()

        results = self._run_simultaneously(
            lambda _index: apply_prescription_billing(
                appointment=appointment,
            ),
            [1, 2],
        )

        self.assertEqual(sum(results), 1)
        self.assertEqual(
            InvoiceLine.objects.filter(treatment=treatment).count(),
            1,
        )

    def _create_prescription_case(self):
        now = timezone.now()
        appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at=now - timedelta(minutes=10),
            end_at=now + timedelta(minutes=20),
        )
        presc_prestation = Prestation.objects.create(
            category=self.prestation.category,
            code="PRESC",
            label="Prescription act",
        )
        PrestationTarif.objects.create(
            prestation=presc_prestation,
            amount=Decimal("50.00"),
            tax_rate=Decimal("0.00"),
            effective_from=timezone.localdate() - timedelta(days=30),
        )
        treatment = Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            appointment=appointment,
            prestation=presc_prestation,
            code="PRESC",
            label=presc_prestation.label,
            start_at=appointment.start_at,
        )
        template = PrescriptionTemplate.objects.create(
            name="Financial concurrency prescription",
            content="Prescription",
        )
        Prescription.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            appointment=appointment,
            template=template,
            status=Prescription.Status.GENERATED,
            generated_at=now,
        )
        return appointment, treatment
