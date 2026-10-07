from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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

