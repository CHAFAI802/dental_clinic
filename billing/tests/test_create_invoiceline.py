from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from appointments.models import Appointment
from billing.models import (
    PrestationCategory,
    Prestation,
    PrestationTarif,
    Invoice,
    InvoiceLine,
)
from patients.models import Patient
from treatments.models import Treatment


User = get_user_model()


class InvoiceLineCreationTests(APITestCase):

    def setUp(self):
        self.administrator = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            role=User.Role.ADMINISTRATOR,
        )

        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            password="password123",
            first_name="Dentist",
            last_name="User",
            role=User.Role.DENTIST,
        )

        self.patient = Patient.objects.create(
            first_name="patientfirstname",
            last_name="patientlastname",
            birthdate="2000-11-21",
            gender="patientgender",
            phone="12345678",
        )

        self.client.force_authenticate(user=self.administrator)

        response = self.client.post(
            reverse("prestationcategory-list"),
            {
                "name": "Consultation",
                "code": "CONSULT",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.category = PrestationCategory.objects.get(code="CONSULT")

        response = self.client.post(
            reverse("prestation-list"),
            {
                "category": self.category.id,
                "code": "CONSULT-01",
                "label": "Consultation dentaire",
                "description": "Consultation",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.prestation = Prestation.objects.get(code="CONSULT-01")

        response = self.client.post(
            reverse("prestationtarif-list"),
            {
                "prestation": self.prestation.id,
                "amount": "5000.00",
                "tax_rate": "19.00",
                "effective_from": "2026-01-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.tarif = PrestationTarif.objects.get(
            prestation=self.prestation,
            effective_from="2026-01-01",
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

        self.client.force_authenticate(user=self.dentist)

        self.invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            status=Invoice.Status.DRAFT,
            issued_at="2026-09-14",
            due_date="2026-09-21",
        )

    def test_dentist_can_create_invoice_line_from_treatment(self):
        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        invoice_line = InvoiceLine.objects.get(
            invoice=self.invoice,
            treatment=self.treatment,
        )

        self.assertEqual(
            invoice_line.prestation_id,
            self.prestation.id,
        )

        self.assertEqual(
            invoice_line.unit_price,
            Decimal("5000.00"),
        )

        self.assertEqual(
            invoice_line.tax_rate,
            Decimal("19.00"),
        )

        self.assertEqual(
            invoice_line.subtotal,
            Decimal("5000.00"),
        )

        self.assertEqual(
            invoice_line.tax_amount,
            Decimal("950.00"),
        )

        self.assertEqual(
            invoice_line.total,
            Decimal("5950.00"),
        )

    def test_delete_invoice_line_without_invoice(self):
        invoice_line = InvoiceLine(
            treatment=self.treatment,
            prestation=self.prestation,
            description="Ligne sans facture",
            quantity=Decimal("1.00"),
            unit_price=Decimal("5000.00"),
            tax_rate=Decimal("19.00"),
        )
        InvoiceLine.objects.bulk_create([invoice_line])

        invoice_line.refresh_from_db()

        self.assertIsNone(invoice_line.invoice_id)
        self.assertTrue(
            InvoiceLine.objects.filter(pk=invoice_line.pk).exists()
        )
        self.assertEqual(Invoice.objects.count(), 1)

        invoice_line.delete()

        self.assertFalse(
            InvoiceLine.objects.filter(pk=invoice_line.pk).exists()
        )
        self.assertEqual(Invoice.objects.count(), 1)

    def test_invoice_line_keeps_snapshot_when_admin_changes_tariff(self):
        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        invoice_line = InvoiceLine.objects.get(
            invoice=self.invoice,
            treatment=self.treatment,
        )

        self.assertEqual(
            invoice_line.unit_price,
            Decimal("5000.00"),
        )
        self.assertEqual(
            invoice_line.tax_rate,
            Decimal("19.00"),
        )

        self.client.force_authenticate(user=self.administrator)

        response = self.client.patch(
            reverse(
                "prestationtarif-detail",
                args=[self.tarif.id],
            ),
            {
                "amount": "6000.00",
                "tax_rate": "20.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        invoice_line.refresh_from_db()

        self.assertEqual(
            invoice_line.unit_price,
            Decimal("5000.00"),
        )
        self.assertEqual(
            invoice_line.tax_rate,
            Decimal("19.00"),
        )

    def test_new_treatment_uses_new_tariff_after_admin_changes_tariff(self):
    # Première facturation avec le tarif initial
        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        first_invoice_line = InvoiceLine.objects.get(
            invoice=self.invoice,
            treatment=self.treatment,
        )

        self.assertEqual(
            first_invoice_line.unit_price,
            Decimal("5000.00"),
        )
        self.assertEqual(
            first_invoice_line.tax_rate,
            Decimal("19.00"),
        )

        # L'administrateur crée le nouveau tarif
        self.client.force_authenticate(user=self.administrator)

        response = self.client.post(
            reverse("prestationtarif-list"),
            {
                "prestation": self.prestation.id,
                "amount": "6000.00",
                "tax_rate": "20.00",
                "effective_from": "2026-09-15",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        # Le dentiste réalise un nouveau traitement après
        # l'entrée en vigueur du nouveau tarif.
        self.client.force_authenticate(user=self.dentist)

        second_treatment = Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            prestation=self.prestation,
            code="TRT-002",
            label="Consultation dentaire",
            description="Consultation",
            start_at="2026-09-15T10:00:00+01:00",
        )

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": second_treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        second_invoice_line = InvoiceLine.objects.get(
            invoice=self.invoice,
            treatment=second_treatment,
        )

        self.assertEqual(
            second_invoice_line.unit_price,
            Decimal("6000.00"),
        )

        self.assertEqual(
            second_invoice_line.tax_rate,
            Decimal("20.00"),
        )

        self.assertEqual(
            second_invoice_line.subtotal,
            Decimal("6000.00"),
        )

        self.assertEqual(
            second_invoice_line.tax_amount,
            Decimal("1200.00"),
        )

        self.assertEqual(
            second_invoice_line.total,
            Decimal("7200.00"),
        )

        # Le snapshot de la première ligne reste inchangé.
        first_invoice_line.refresh_from_db()

        self.assertEqual(
            first_invoice_line.unit_price,
            Decimal("5000.00"),
        )

        self.assertEqual(
            first_invoice_line.tax_rate,
            Decimal("19.00"),
        )

    def test_invoice_line_creation_rejected_when_treatment_prestation_differs(
        self,
    ):
        other_prestation = Prestation.objects.create(
            category=self.category,
            code="CONSULT-02",
            label="Autre consultation",
            description="Autre prestation",
            is_active=True,
        )

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": other_prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            InvoiceLine.objects.filter(
                invoice=self.invoice,
                treatment=self.treatment,
            ).exists()
        )

    def test_invoice_line_creation_rejected_when_treatment_patient_differs_from_invoice_patient(
        self,
    ):
        other_patient = Patient.objects.create(
            first_name="other",
            last_name="patient",
            birthdate="1995-01-01",
            gender="patientgender",
            phone="87654321",
        )

        other_treatment = Treatment.objects.create(
            patient=other_patient,
            dentist=self.dentist,
            prestation=self.prestation,
            code="TRT-OTHER",
            label="Consultation dentaire",
            description="Consultation",
            start_at="2026-09-14T11:00:00+01:00",
        )

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": other_treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            InvoiceLine.objects.filter(
                invoice=self.invoice,
                treatment=other_treatment,
            ).exists()
        )

    def test_invoice_line_creation_rejected_when_no_applicable_tariff_exists(
        self,
    ):
        prestation_without_tariff = Prestation.objects.create(
            category=self.category,
            code="NO-TARIFF",
            label="Prestation sans tarif",
            description="Aucun tarif applicable",
            is_active=True,
        )

        treatment_without_tariff = Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            prestation=prestation_without_tariff,
            code="TRT-NO-TARIFF",
            label="Prestation sans tarif",
            description="Aucun tarif",
            start_at="2026-09-14T12:00:00+01:00",
        )

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": treatment_without_tariff.id,
                "prestation": prestation_without_tariff.id,
                "description": "Prestation sans tarif",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            InvoiceLine.objects.filter(
                invoice=self.invoice,
                treatment=treatment_without_tariff,
            ).exists()
        )




class InvoiceLinePermissionPositiveTests(APITestCase):

    def setUp(self):
        self.administrator = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            role=User.Role.ADMINISTRATOR,
        )

        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            password="password123",
            first_name="Dentist",
            last_name="User",
            role=User.Role.DENTIST,
        )

        self.accountant = User.objects.create_user(
            email="accountant@example.com",
            password="password123",
            first_name="Accountant",
            last_name="User",
            role=User.Role.ACCOUNTANT,
        )

        self.receptionist = User.objects.create_user(
            email="receptionist@example.com",
            password="password123",
            first_name="Receptionist",
            last_name="User",
            role=User.Role.RECEPTIONIST,
        )

        self.patient = Patient.objects.create(
            first_name="patientfirstname",
            last_name="patientlastname",
            birthdate="2000-11-21",
            gender="patientgender",
            phone="12345678",
        )

        self.client.force_authenticate(user=self.administrator)

        response = self.client.post(
            reverse("prestationcategory-list"),
            {
                "name": "Consultation",
                "code": "CONSULT",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.category = PrestationCategory.objects.get(
            code="CONSULT",
        )

        response = self.client.post(
            reverse("prestation-list"),
            {
                "category": self.category.id,
                "code": "CONSULT-01",
                "label": "Consultation dentaire",
                "description": "Consultation",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.prestation = Prestation.objects.get(
            code="CONSULT-01",
        )

        response = self.client.post(
            reverse("prestationtarif-list"),
            {
                "prestation": self.prestation.id,
                "amount": "5000.00",
                "tax_rate": "19.00",
                "effective_from": "2026-01-01",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
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

        self.invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            status=Invoice.Status.DRAFT,
            issued_at="2026-09-14",
            due_date="2026-09-21",
        )

        # Le dentist crée la InvoiceLine.
        self.client.force_authenticate(user=self.dentist)

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.invoice_line = InvoiceLine.objects.get(
            invoice=self.invoice,
            treatment=self.treatment,
        )

    def test_dentist_can_list_invoice_lines(self):
        self.client.force_authenticate(user=self.dentist)

        response = self.client.get(
            reverse("invoiceline-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_dentist_can_retrieve_invoice_line(self):
        self.client.force_authenticate(user=self.dentist)

        response = self.client.get(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_dentist_can_update_invoice_line(self):
        self.client.force_authenticate(user=self.dentist)

        response = self.client.patch(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
            {
                "description": "Consultation dentaire modifiée",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.invoice_line.refresh_from_db()

        self.assertEqual(
            self.invoice_line.description,
            "Consultation dentaire modifiée",
        )

    def test_accountant_can_list_invoice_lines(self):
        self.client.force_authenticate(user=self.accountant)

        response = self.client.get(
            reverse("invoiceline-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_accountant_can_retrieve_invoice_line(self):
        self.client.force_authenticate(user=self.accountant)

        response = self.client.get(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_receptionist_can_list_invoice_lines(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.get(
            reverse("invoiceline-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_receptionist_can_retrieve_invoice_line(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.get(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_administrator_can_list_invoice_lines(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.get(
            reverse("invoiceline-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_administrator_can_retrieve_invoice_line(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.get(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

class InvoiceLineNegativePermissionTests(APITestCase):

    def setUp(self):
        self.administrator = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            role=User.Role.ADMINISTRATOR,
        )

        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            password="password123",
            first_name="Dentist",
            last_name="User",
            role=User.Role.DENTIST,
        )

        self.accountant = User.objects.create_user(
            email="accountant@example.com",
            password="password123",
            first_name="Accountant",
            last_name="User",
            role=User.Role.ACCOUNTANT,
        )

        self.receptionist = User.objects.create_user(
            email="receptionist@example.com",
            password="password123",
            first_name="Receptionist",
            last_name="User",
            role=User.Role.RECEPTIONIST,
        )

        self.patient = Patient.objects.create(
            first_name="patientfirstname",
            last_name="patientlastname",
            birthdate="2000-11-21",
            gender="patientgender",
            phone="12345678",
        )

        self.client.force_authenticate(user=self.administrator)

        response = self.client.post(
            reverse("prestationcategory-list"),
            {
                "name": "Consultation",
                "code": "CONSULT",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.category = PrestationCategory.objects.get(
            code="CONSULT",
        )

        response = self.client.post(
            reverse("prestation-list"),
            {
                "category": self.category.id,
                "code": "CONSULT-01",
                "label": "Consultation dentaire",
                "description": "Consultation",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.prestation = Prestation.objects.get(
            code="CONSULT-01",
        )

        response = self.client.post(
            reverse("prestationtarif-list"),
            {
                "prestation": self.prestation.id,
                "amount": "5000.00",
                "tax_rate": "19.00",
                "effective_from": "2026-01-01",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
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

        self.invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.dentist,
            status=Invoice.Status.DRAFT,
            issued_at="2026-09-14",
            due_date="2026-09-21",
        )

        # La ligne est créée par le dentist.
        self.client.force_authenticate(user=self.dentist)

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.invoice_line = InvoiceLine.objects.get(
            invoice=self.invoice,
            treatment=self.treatment,
        )

    def test_dentist_cannot_delete_invoice_line(self):
        self.client.force_authenticate(user=self.dentist)

        response = self.client.delete(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.assertTrue(
            InvoiceLine.objects.filter(
                pk=self.invoice_line.id,
            ).exists()
        )

    def test_accountant_cannot_create_invoice_line(self):
        self.client.force_authenticate(user=self.accountant)

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_accountant_cannot_update_invoice_line(self):
        self.client.force_authenticate(user=self.accountant)

        response = self.client.patch(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
            {
                "description": "Modification interdite",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_accountant_cannot_delete_invoice_line(self):
        self.client.force_authenticate(user=self.accountant)

        response = self.client.delete(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_receptionist_cannot_create_invoice_line(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_receptionist_cannot_update_invoice_line(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.patch(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
            {
                "description": "Modification interdite",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_receptionist_cannot_delete_invoice_line(self):
        self.client.force_authenticate(user=self.receptionist)

        response = self.client.delete(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_administrator_cannot_create_invoice_line(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.post(
            reverse("invoiceline-list"),
            {
                "invoice": self.invoice.id,
                "treatment": self.treatment.id,
                "prestation": self.prestation.id,
                "description": "Consultation dentaire",
                "quantity": "1.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_administrator_cannot_update_invoice_line(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.patch(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
            {
                "description": "Modification interdite",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_administrator_cannot_delete_invoice_line(self):
        self.client.force_authenticate(user=self.administrator)

        response = self.client.delete(
            reverse(
                "invoiceline-detail",
                args=[self.invoice_line.id],
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class InvoiceLineAppointmentGroupingTests(APITestCase):
    """
    Les lignes des traitements d'un même rendez-vous sont regroupées
    dans une seule facture, créée ou réutilisée par InvoiceLine.save().
    """

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist@example.com",
            password="password123",
            first_name="Dentist",
            last_name="User",
            role=User.Role.DENTIST,
        )

        self.patient = Patient.objects.create(
            first_name="patientfirstname",
            last_name="patientlastname",
            birthdate="2000-11-21",
            gender="patientgender",
            phone="12345678",
        )

        self.category = PrestationCategory.objects.create(
            name="Consultation",
            code="CONSULT",
            is_active=True,
        )

        self.prestation = Prestation.objects.create(
            category=self.category,
            code="CONSULT-01",
            label="Consultation dentaire",
            description="Consultation",
            is_active=True,
        )

        PrestationTarif.objects.create(
            prestation=self.prestation,
            amount="5000.00",
            tax_rate="19.00",
            effective_from="2026-01-01",
        )

        self.appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at="2026-09-14T10:00:00+01:00",
            end_at="2026-09-14T10:30:00+01:00",
            duration_minutes=30,
        )

        self.treatment_1 = self._create_treatment(
            appointment=self.appointment,
            code="TRT-001",
            start_at="2026-09-14T10:00:00+01:00",
        )

        self.treatment_2 = self._create_treatment(
            appointment=self.appointment,
            code="TRT-002",
            start_at="2026-09-14T10:15:00+01:00",
        )

        self.client.force_authenticate(user=self.dentist)

    def _create_treatment(self, *, appointment, code, start_at):
        return Treatment.objects.create(
            patient=self.patient,
            dentist=self.dentist,
            prestation=self.prestation,
            appointment=appointment,
            code=code,
            label="Consultation dentaire",
            description="Consultation",
            start_at=start_at,
        )

    def _create_line(self, treatment, invoice=None):
        data = {
            "treatment": treatment.id,
            "prestation": self.prestation.id,
            "description": "Consultation dentaire",
            "quantity": "1.00",
        }
        if invoice is not None:
            data["invoice"] = invoice.id

        return self.client.post(
            reverse("invoiceline-list"),
            data,
            format="json",
        )

    def test_treatments_of_same_appointment_share_one_invoice(self):
        response = self._create_line(self.treatment_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        first_invoice_id = response.data["invoice"]

        response = self._create_line(self.treatment_2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["invoice"], first_invoice_id)

        self.assertEqual(Invoice.objects.count(), 1)

        invoice = Invoice.objects.get(pk=first_invoice_id)
        self.assertEqual(invoice.lines.count(), 2)

        # Les totaux couvrent les deux lignes regroupées.
        self.assertEqual(invoice.subtotal, Decimal("10000.00"))
        self.assertEqual(invoice.total_amount, Decimal("11900.00"))

    def test_new_line_for_same_appointment_reuses_invoice(self):
        response = self._create_line(self.treatment_1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invoice_id = response.data["invoice"]

        treatment_3 = self._create_treatment(
            appointment=self.appointment,
            code="TRT-003",
            start_at="2026-09-14T10:30:00+01:00",
        )

        response = self._create_line(treatment_3)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["invoice"], invoice_id)

        # Idempotent : aucune facture en doublon pour le rendez-vous.
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(
            Invoice.objects.filter(pk=invoice_id).count(),
            1,
        )

    def test_explicit_appointment_invoice_is_accepted_when_compatible(self):
        first_response = self._create_line(self.treatment_1)
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        invoice_id = first_response.data["invoice"]

        response = self._create_line(self.treatment_2, invoice=Invoice.objects.get(pk=invoice_id))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["invoice"], invoice_id)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_rejects_invoice_from_another_appointment_of_same_patient(self):
        first_response = self._create_line(self.treatment_1)
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        other_appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at="2026-09-15T10:00:00+01:00",
            end_at="2026-09-15T10:30:00+01:00",
            duration_minutes=30,
        )
        other_treatment = self._create_treatment(
            appointment=other_appointment,
            code="TRT-OTHER-APPOINTMENT",
            start_at="2026-09-15T10:00:00+01:00",
        )
        other_response = self._create_line(other_treatment)
        self.assertEqual(other_response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(
            first_response.data["invoice"],
            other_response.data["invoice"],
        )

        remaining_treatment = self._create_treatment(
            appointment=self.appointment,
            code="TRT-003",
            start_at="2026-09-14T10:20:00+01:00",
        )
        response = self._create_line(
            remaining_treatment,
            invoice=Invoice.objects.get(pk=other_response.data["invoice"]),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invoice", response.data)
        self.assertEqual(InvoiceLine.objects.count(), 2)
        self.assertEqual(Invoice.objects.count(), 2)

    def test_rejects_explicit_invoice_for_different_patient(self):
        other_patient = Patient.objects.create(
            first_name="other",
            last_name="patient",
            birthdate="1990-01-01",
            gender="other",
            phone="87654321",
        )
        other_invoice = Invoice.objects.create(
            patient=other_patient,
            created_by=self.dentist,
            status=Invoice.Status.DRAFT,
            issued_at="2026-09-14",
            due_date="2026-09-21",
        )

        response = self._create_line(self.treatment_1, invoice=other_invoice)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("treatment", response.data)
        self.assertEqual(InvoiceLine.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), 1)

    def test_failed_line_validation_rolls_back_created_invoice(self):
        invalid_prestation = Prestation.objects.create(
            category=self.category,
            code="CONSULT-INVALID",
            label="Prestation incompatible",
            is_active=True,
        )
        PrestationTarif.objects.create(
            prestation=invalid_prestation,
            amount="100.00",
            tax_rate="0.00",
            effective_from="2026-01-01",
        )

        with self.assertRaises(DjangoValidationError):
            InvoiceLine.objects.create(
                treatment=self.treatment_1,
                prestation=invalid_prestation,
                description="Ligne incompatible",
                quantity="1.00",
            )

        self.assertEqual(Invoice.objects.count(), 0)
        self.assertEqual(InvoiceLine.objects.count(), 0)

    def test_treatment_without_appointment_keeps_own_invoice(self):
        solo_treatment = self._create_treatment(
            appointment=None,
            code="TRT-SOLO",
            start_at="2026-09-15T10:00:00+01:00",
        )

        response = self._create_line(solo_treatment)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(
            Invoice.objects.filter(
                pk=response.data["invoice"],
            ).count(),
            1,
        )

    def test_api_created_invoices_receive_unique_generated_references(self):
        first_response = self._create_line(self.treatment_1)
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        first_invoice = Invoice.objects.get(pk=first_response.data["invoice"])

        other_appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at="2026-09-15T10:00:00+01:00",
            end_at="2026-09-15T10:30:00+01:00",
            duration_minutes=30,
        )
        other_treatment = self._create_treatment(
            appointment=other_appointment,
            code="TRT-OTHER-REFERENCE",
            start_at="2026-09-15T10:00:00+01:00",
        )
        second_response = self._create_line(other_treatment)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        second_invoice = Invoice.objects.get(pk=second_response.data["invoice"])

        self.assertNotEqual(first_invoice.pk, second_invoice.pk)
        self.assertRegex(first_invoice.reference_number, r"^[A-Z]+\d+/2026$")
        self.assertRegex(second_invoice.reference_number, r"^[A-Z]+\d+/2026$")
        self.assertNotEqual(
            first_invoice.reference_number,
            second_invoice.reference_number,
        )
        self.assertEqual(
            Invoice.objects.filter(
                reference_number__in=(
                    first_invoice.reference_number,
                    second_invoice.reference_number,
                )
            ).count(),
            2,
        )
