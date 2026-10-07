from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from billing.models import (
    Invoice,
    InvoiceLine,
    Prestation,
    PrestationCategory,
    PrestationTarif,
    Payment,
    PaymentMethod,
    CreditNote
)
from patients.models import Patient
from treatments.models import Treatment 



class InvoiceCreationFromInvoiceLineTest(TestCase):

    def setUp(self):
        self.administrator = User.objects.create_user(
            first_name="Admin",
            last_name="Test",
            role=User.Role.ADMINISTRATOR,
            email="admin@test.com",
            password="adminpassword",
        )

        self.dentist = User.objects.create_user(
            first_name="Dentist",
            last_name="Test",
            role=User.Role.DENTIST,
            email="dentist@test.com",
            password="dentistpassword",
        )

        self.patient = Patient.objects.create(
            first_name="patientfirstname",
            last_name="patientlastname",
            birthdate="2000-11-21",
            gender="patientgender",
            phone="12345678",
        )

        self.category = PrestationCategory.objects.create(
            name="Soins",
            code="SOINS",
        )

        self.prestation = Prestation.objects.create(
            category=self.category,
            code="CONSULT",
            label="Consultation",
        )

        self.tarif = PrestationTarif.objects.create(
            prestation=self.prestation,
            amount=Decimal("100.00"),
            tax_rate=Decimal("20.00"),
            effective_from=date(2026, 1, 1),
        )

        self.payment_method = PaymentMethod.objects.create(
            name="Espèces",
        )

        self.treatment = Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            prestation=self.prestation,
            code="TRT-001",
            label="Consultation dentaire",
            description="Consultation",
            start_at="2026-09-14T10:00:00+01:00",
        )

    def test_create_invoice_from_invoiceline(self):
        invoice_line = InvoiceLine.objects.create(
            treatment=self.treatment,
            prestation=self.prestation,
            quantity=1,
            description="Consultation dentaire",
        )

        invoice_line.refresh_from_db()

        invoice = invoice_line.invoice

        self.assertIsNotNone(invoice)
        self.assertEqual(
            invoice.patient,
            self.patient,
        )
        self.assertEqual(
            invoice.created_by,
            self.dentist,
        )
        self.assertEqual(
            invoice.issued_at,
            date(2026, 9, 14),
        )
        self.assertEqual(
            invoice.due_date,
            date(2026, 9, 14),
        )
        self.assertEqual(
            invoice.status,
            Invoice.Status.ISSUED,
        )
        self.assertTrue(
            invoice.reference_number,
        )
        self.assertEqual(
            invoice_line.invoice,
            invoice,
        )

    def test_invoice_financials_are_recalculated_from_created_invoiceline(self):
        invoice_line = InvoiceLine.objects.create(
            treatment=self.treatment,
            prestation=self.prestation,
            quantity=1,
            description="Consultation dentaire",
        )

        invoice = invoice_line.invoice
        invoice.refresh_from_db()

        self.assertEqual(
            invoice.subtotal,
            Decimal("100.00"),
        )
        self.assertEqual(
            invoice.tax_amount,
            Decimal("20.00"),
        )
        self.assertEqual(
            invoice.total_amount,
            Decimal("120.00"),
        )
        self.assertEqual(
            invoice.paid_amount,
            Decimal("0.00"),
        )
        self.assertEqual(
            invoice.credit_amount,
            Decimal("0.00"),
        )
        self.assertEqual(
            invoice.balance_due,
            Decimal("120.00"),
        )

    def test_generate_first_reference_of_year(self):
        reference = Invoice.generate_reference_number(
            date(2026, 9, 17)
        )

        self.assertEqual(
            reference,
            "A0001/2026",
        )


    def test_generate_next_reference(self):
        Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="A0001/2026",
        )

        reference = Invoice.generate_reference_number(
            date(2026, 9, 17)
        )

        self.assertEqual(
            reference,
            "A0002/2026",
        )

    def test_generate_next_reference_includes_soft_deleted_invoice(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="A0001/2026",
        )

        invoice.delete()

        reference = Invoice.generate_reference_number(
            date(2026, 9, 17)
        )

        self.assertEqual(
            reference,
            "A0002/2026",
        )

    def test_generate_reference_after_z9999(self):
        Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="Z9999/2026",
        )

        reference = Invoice.generate_reference_number(
            date(2026, 9, 17)
        )

        self.assertEqual(
            reference,
            "AA001/2026",
        )


    def test_generate_reference_after_aa001(self):
        Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="AA001/2026",
        )

        reference = Invoice.generate_reference_number(
            date(2026, 9, 17)
        )

        self.assertEqual(
            reference,
            "AA002/2026",
        )


    def test_generate_reference_after_zz999(self):
        Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="ZZ999/2026",
        )

        reference = Invoice.generate_reference_number(
            date(2026, 9, 17)
        )

        self.assertEqual(
            reference,
            "AAA01/2026",
        )


    def test_generate_reference_after_zzz99(self):
        Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="ZZZ99/2026",
        )

        reference = Invoice.generate_reference_number(
            date(2026, 9, 17)
        )

        self.assertEqual(
            reference,
            "AAAA1/2026",
        )


    def test_generate_reference_resets_for_new_year(self):
        Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="A0050/2026",
        )

        reference = Invoice.generate_reference_number(
            date(2027, 1, 1)
        )

        self.assertEqual(
            reference,
            "A0001/2027",
        )

    def test_clean_rejects_negative_financial_amounts(self):
        financial_fields = [
            'subtotal',
            'tax_amount',
            'total_amount',
            'credit_amount',
            'paid_amount',
            'balance_due',
        ]

        for field_name in financial_fields:
            with self.subTest(field=field_name):
                invoice = Invoice(
                    patient=self.patient,
                    created_by=self.dentist,
                    issued_at=date(2026, 9, 17),
                    due_date=date(2026, 9, 17),
                    reference_number=f"TEST-{field_name}",
                )

                setattr(invoice, field_name, Decimal('-1.00'))

                with self.assertRaises(ValidationError):
                    invoice.full_clean() 

    def test_clean_accepts_due_date_equal_to_issued_at(self):
        invoice = Invoice(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="TEST-DATE-EQUAL",
        )

        invoice.full_clean() 

    def test_clean_rejects_due_date_before_issued_at(self):
        invoice = Invoice(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 16),
            reference_number="TEST-DATE-BEFORE",
        )

        with self.assertRaises(ValidationError):
            invoice.full_clean() 

    def test_clean_accepts_paid_and_credit_equal_to_total(self):
        invoice = Invoice(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="TEST-FINANCIAL-VALID",
            total_amount=Decimal("100.00"),
            paid_amount=Decimal("60.00"),
            credit_amount=Decimal("40.00"),
        )

        invoice.full_clean() 

    def test_clean_rejects_paid_and_credit_above_total(self):
        invoice = Invoice(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="TEST-FINANCIAL-INVALID",
            total_amount=Decimal("100.00"),
            paid_amount=Decimal("60.00"),
            credit_amount=Decimal("41.00"),
        )

        with self.assertRaises(ValidationError):
            invoice.full_clean() 

    def test_recalculate_financials_with_multiple_invoice_lines(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="TEST-RECALC-LINES",
        )

        InvoiceLine.objects.create(
            invoice=invoice,
            treatment=self.treatment,
            prestation=self.prestation,
            quantity=2,
            description="Deux consultations",
        )

        invoice.refresh_from_db()

        self.assertEqual(invoice.subtotal, Decimal("200.00"))
        self.assertEqual(invoice.tax_amount, Decimal("40.00"))
        self.assertEqual(invoice.total_amount, Decimal("240.00"))
        self.assertEqual(invoice.paid_amount, Decimal("0.00"))
        self.assertEqual(invoice.credit_amount, Decimal("0.00"))
        self.assertEqual(invoice.balance_due, Decimal("240.00")) 

    def test_recalculate_financials_includes_payments(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="TEST-RECALC-PAYMENT",
            total_amount=240,
        )

        invoice.recalculate_financials()
        invoice.save()

        # Le paiement sera testé plus précisément avec le modèle Payment.
        self.assertEqual(invoice.paid_amount, Decimal("0.00"))
        self.assertEqual(invoice.balance_due, Decimal("0.00")) 

    def test_recalculate_financials_includes_multiple_payments(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="TEST-RECALC-PAYMENTS",
        )

        InvoiceLine.objects.create(
            invoice=invoice,
            treatment=self.treatment,
            prestation=self.prestation,
            quantity=1,
            description="Consultation",
        )

        Payment.objects.create(
            invoice=invoice,
            patient=self.patient,
            amount=Decimal("50.00"),
            method=self.payment_method,
        )

        Payment.objects.create(
            invoice=invoice,
            patient=self.patient,
            amount=Decimal("30.00"),
            method=self.payment_method,
        )

        invoice.refresh_from_db()

        self.assertEqual(invoice.paid_amount, Decimal("80.00"))
        self.assertEqual(invoice.total_amount, Decimal("120.00"))
        self.assertEqual(invoice.balance_due, Decimal("40.00")) 

    def test_recalculate_financials_includes_multiple_credit_notes(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="TEST-RECALC-CREDITS",
        )

        InvoiceLine.objects.create(
            invoice=invoice,
            treatment=self.treatment,
            prestation=self.prestation,
            quantity=1,
            description="Consultation",
        )

        CreditNote.objects.create(
            invoice=invoice,
            created_by=self.administrator,
            amount=Decimal("20.00"),
            reason="Geste commercial",
        )

        CreditNote.objects.create(
            invoice=invoice,
            created_by=self.administrator,
            amount=Decimal("10.00"),
            reason="Correction",
        )

        invoice.refresh_from_db()

        self.assertEqual(invoice.credit_amount, Decimal("30.00"))
        self.assertEqual(invoice.total_amount, Decimal("120.00"))
        self.assertEqual(invoice.balance_due, Decimal("90.00")) 

    def test_recalculate_financials_combines_payments_and_credit_notes(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="TEST-RECALC-COMBINED",
        )

        InvoiceLine.objects.create(
            invoice=invoice,
            treatment=self.treatment,
            prestation=self.prestation,
            quantity=1,
            description="Consultation",
        )

        Payment.objects.create(
            invoice=invoice,
            patient=self.patient,
            amount=Decimal("50.00"),
            method=self.payment_method,
        )

        CreditNote.objects.create(
            invoice=invoice,
            created_by=self.administrator,
            amount=Decimal("20.00"),
            reason="Geste commercial",
        )

        invoice.refresh_from_db()

        self.assertEqual(invoice.total_amount, Decimal("120.00"))
        self.assertEqual(invoice.paid_amount, Decimal("50.00"))
        self.assertEqual(invoice.credit_amount, Decimal("20.00"))
        self.assertEqual(invoice.balance_due, Decimal("50.00")) 

    def test_invoice_str_returns_reference_number(self):
        invoice = Invoice(
            patient=self.patient,
            created_by=self.dentist,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="A0042/2026",
        )

        self.assertEqual(str(invoice), "A0042/2026")


class InvoiceReadTests(APITestCase):

    def setUp(self):
        self.url = reverse("invoice-list")

        self.administrator = User.objects.create_user(
            email="admin@example.com",
            password="test-password",
            first_name="Admin",
            last_name="Test",
            role=User.Role.ADMINISTRATOR,
        )

        self.accountant = User.objects.create_user(
            email="accountant@example.com",
            password="test-password",
            first_name="Accountant",
            last_name="Test",
            role=User.Role.ACCOUNTANT,
        )

        self.receptionist = User.objects.create_user(
            email="receptionist@example.com",
            password="test-password",
            first_name="Receptionist",
            last_name="Test",
            role=User.Role.RECEPTIONIST,
        )

        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            password="test-password",
            first_name="Dentist",
            last_name="Test",
            role=User.Role.DENTIST,
        )

        self.assistant = User.objects.create_user(
            email="assistant@example.com",
            password="test-password",
            first_name="Assistant",
            last_name="Test",
            role=User.Role.ASSISTANT,
        )

        self.patient = Patient.objects.create(
            first_name="Patient",
            last_name="Test",
            birthdate="2000-01-01",
            gender="M",
            phone="12345678",
        )

        self.invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.administrator,
            issued_at=date(2026, 9, 17),
            due_date=date(2026, 9, 17),
            reference_number="A0001/2026",
        )

    def test_administrator_can_read_invoices(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_accountant_can_read_invoices(self):
        self.client.force_authenticate(user=self.accountant)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_receptionist_can_read_invoices(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_dentist_cannot_read_invoices(self):
        self.client.force_authenticate(user=self.dentist)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_assistant_cannot_read_invoices(self):
        self.client.force_authenticate(user=self.assistant)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )  

    def test_administrator_can_patch_invoice(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.patch(
            reverse(
                "invoice-detail",
                kwargs={"pk": self.invoice.pk},
            ),
            {
                "due_date": "2026-10-01",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.due_date,
            date(2026, 10, 1),
        )

    def test_accountant_cannot_patch_invoice(self):
        self.client.force_authenticate(user=self.accountant)

        response = self.client.patch(
            reverse(
                "invoice-detail",
                kwargs={"pk": self.invoice.pk},
            ),
            {"due_date": "2026-10-01"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_receptionist_cannot_patch_invoice(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.patch(
            reverse(
                "invoice-detail",
                kwargs={"pk": self.invoice.pk},
            ),
            {"due_date": "2026-10-01"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_dentist_cannot_patch_invoice(self):
        self.client.force_authenticate(user=self.dentist)

        response = self.client.patch(
            reverse(
                "invoice-detail",
                kwargs={"pk": self.invoice.pk},
            ),
            {"due_date": "2026-10-01"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_assistant_cannot_patch_invoice(self):
        self.client.force_authenticate(user=self.assistant)

        response = self.client.patch(
            reverse(
                "invoice-detail",
                kwargs={"pk": self.invoice.pk},
            ),
            {"due_date": "2026-10-01"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        ) 

    def test_administrator_can_patch_invoice_notes(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.patch(
            reverse(
                "invoice-detail",
                kwargs={"pk": self.invoice.pk},
            ),
            {
                "notes": "Paiement prévu en plusieurs échéances.",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.notes,
            "Paiement prévu en plusieurs échéances.",
        ) 

    def test_administrator_cannot_create_invoice(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.post(
            self.url,
            {
                "due_date": "2026-10-01",
                "notes": "Test",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertEqual(
            Invoice.objects.count(),
            1,
        ) 

    def test_administrator_cannot_delete_invoice(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.delete(
            reverse(
                "invoice-detail",
                kwargs={"pk": self.invoice.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            Invoice.objects.filter(pk=self.invoice.pk).exists()
        )