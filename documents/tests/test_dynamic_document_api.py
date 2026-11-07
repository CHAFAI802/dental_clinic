from datetime import date
from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory

from docx import Document as WordDocument
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from accounts.models import User
from billing.models import (
    Invoice,
    InvoiceLine,
    Payment,
    PaymentMethod,
    Prestation,
    PrestationCategory,
    PrestationTarif,
)
from documents.models import DocumentTemplate
from inventory.models import InventoryCategory, InventoryFamily, InventoryItem, Unit
from patients.models import Patient
from treatments.models import Treatment


def _docx_bytes(document):
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _document_text(content):
    document = WordDocument(BytesIO(content))
    return "\n".join(paragraph.text for paragraph in document.paragraphs) + "\n" + "\n".join(
        cell.text
        for table in document.tables
        for row in table.rows
        for cell in row.cells
    )


class DynamicDocumentGenerationApiTests(APITestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        settings_context = override_settings(MEDIA_ROOT=self.media_dir.name)
        settings_context.enable()
        self.addCleanup(settings_context.disable)

        self.administrator = User.objects.create_user(
            email="dynamic-admin@example.test",
            password="test-password",
            first_name="Admin",
            last_name="Test",
            role=User.Role.ADMINISTRATOR,
        )
        self.accountant = User.objects.create_user(
            email="dynamic-accountant@example.test",
            password="test-password",
            first_name="Compte",
            last_name="Test",
            role=User.Role.ACCOUNTANT,
        )
        self.patient = Patient.objects.create(
            first_name="Emilie",
            last_name="Durand",
            birthdate=date(1990, 1, 2),
            gender="",
            phone="0600000000",
        )
        self.invoice = Invoice.objects.create(
            patient=self.patient,
            created_by=self.administrator,
            issued_at=date(2026, 11, 4),
            due_date=date(2026, 12, 4),
            status=Invoice.Status.ISSUED,
            subtotal=Decimal("70.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("70.00"),
            balance_due=Decimal("70.00"),
            reference_number="A0099/2026",
        )
        prestation_category = PrestationCategory.objects.create(
            name="Test",
            code="DOC-TEST",
        )
        prestation = Prestation.objects.create(
            category=prestation_category,
            code="DOC-TEST",
            label="Soin de test",
        )
        PrestationTarif.objects.create(
            prestation=prestation,
            amount=Decimal("35.00"),
            tax_rate=Decimal("0.00"),
            effective_from=date(2026, 1, 1),
        )
        treatment = Treatment.objects.create(
            patient=self.patient,
            dentist=self.administrator,
            prestation=prestation,
            code="DOC-TEST",
            label="Soin de test",
            start_at="2026-11-04T10:00:00+01:00",
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            treatment=treatment,
            prestation=prestation,
            description="Soin de test",
            quantity=Decimal("2.00"),
        )
        self.payment_method = PaymentMethod.objects.create(name="Espèces")
        self.payment = Payment.objects.create(
            invoice=self.invoice,
            patient=self.patient,
            amount=Decimal("25.00"),
            method=self.payment_method,
            reference="PAY-TEST-1",
        )
        category = InventoryCategory.objects.create(code="MAT", name="Matériel")
        self.family = InventoryFamily.objects.create(
            category=category,
            name="Gants",
            code="GANT",
        )
        self.unit = Unit.objects.create(name="Boîte", symbol="boîte")
        self.inventory_item = InventoryItem.objects.create(
            name="Gants nitrile",
            family=self.family,
            unit=self.unit,
            stock_quantity=Decimal("12.00"),
        )

    def _create_approved_template(self, name, filename, document, config):
        template = DocumentTemplate.objects.create(
            name=name,
            file=SimpleUploadedFile(filename, _docx_bytes(document)),
            structure_config=config,
        )
        self.client.force_authenticate(self.administrator)
        response = self.client.post(
            f"/api/document-templates/{template.pk}/approve/",
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        template.refresh_from_db()
        return template

    def test_invoice_generation_uses_saved_invoice_data_and_downloads_docx(self):
        document = WordDocument()
        document.add_paragraph(
            "Facture {{ invoice.reference_number }} — {{ invoice.patient.first_name }}"
        )
        document.add_paragraph("Total {{ invoice.total_amount }}")
        row = document.add_table(rows=1, cols=3).rows[0]
        row.cells[0].text = "{{ debut }}{{ line.description }}"
        row.cells[1].text = "{{ line.quantity }}"
        row.cells[2].text = "{{ line.subtotal }}{{ fin }}"
        template = self._create_approved_template(
            "Facture dynamique",
            "invoice.docx",
            document,
            {
                "version": 1,
                "document_type": "invoice",
                "root_model": "billing.Invoice",
                "root_name": "invoice",
            },
        )

        self.client.force_authenticate(self.accountant)
        available = self.client.get(
            "/api/document-templates/available/?document_type=invoice"
        )
        self.assertEqual(available.status_code, 200)
        self.assertEqual([item["id"] for item in available.data], [template.pk])

        response = self.client.post(
            f"/api/document-templates/{template.pk}/generate/",
            {"object_id": self.invoice.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertIn(".docx", response["Content-Disposition"])
        rendered_text = _document_text(response.content)
        self.assertIn("A0099/2026", rendered_text)
        self.assertIn("Emilie", rendered_text)
        self.assertIn("70.00", rendered_text)
        self.assertIn("Soin de test", rendered_text)
        self.assertIn("2.00", rendered_text)

    def test_validation_reports_detected_variables_and_configuration_change_revokes_approval(self):
        document = WordDocument()
        document.add_paragraph("Facture {{ invoice.reference_number }}")
        document.add_paragraph("Émis le {{ invoice.issued_at }}")
        config = {
            "version": 1,
            "document_type": "invoice",
            "root_model": "billing.Invoice",
            "root_name": "invoice",
            "variables": ["invoice.reference_number", "invoice.issued_at"],
            "zones": [],
        }
        template = self._create_approved_template(
            "Validation facture",
            "validation-invoice.docx",
            document,
            config,
        )

        validation = self.client.post(
            f"/api/document-templates/{template.pk}/validate/",
            format="json",
        )
        self.assertEqual(validation.status_code, 200, validation.data)
        self.assertEqual(
            validation.data["variables"],
            ["invoice.reference_number", "invoice.issued_at"],
        )
        self.assertEqual(validation.data["marker_pairs"], [])

        changed_config = {**config, "variables": list(reversed(config["variables"]))}
        update = self.client.patch(
            f"/api/document-templates/{template.pk}/",
            {"structure_config": changed_config},
            format="json",
        )
        self.assertEqual(update.status_code, 200, update.data)
        template.refresh_from_db()
        self.assertFalse(template.is_approved)

    def test_payment_receipt_uses_real_payment_and_invoice_values(self):
        document = WordDocument()
        document.add_paragraph(
            "Reçu {{ payment.reference }} — {{ payment.amount }} "
            "Facture {{ payment.invoice.reference_number }}"
        )
        template = self._create_approved_template(
            "Reçu de paiement",
            "receipt.docx",
            document,
            {
                "version": 1,
                "document_type": "payment",
                "root_model": "billing.Payment",
                "root_name": "payment",
                "variables": [
                    "payment.reference",
                    "payment.amount",
                    "payment.invoice.reference_number",
                ],
                "zones": [],
            },
        )

        self.client.force_authenticate(self.accountant)
        response = self.client.post(
            f"/api/document-templates/{template.pk}/generate/",
            {"object_id": self.payment.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        rendered_text = _document_text(response.content)
        self.assertIn("PAY-TEST-1", rendered_text)
        self.assertIn("25.00", rendered_text)
        self.assertIn("A0099/2026", rendered_text)

    def test_inventory_generation_is_read_only_and_role_scoped(self):
        document = WordDocument()
        document.add_paragraph("Famille {{ inventory.name }}")
        row = document.add_table(rows=1, cols=2).rows[0]
        row.cells[0].text = "{{ debut }}{{ item.name }}"
        row.cells[1].text = "{{ item.stock_quantity }}{{ fin }}"
        template = self._create_approved_template(
            "État de stock",
            "inventory.docx",
            document,
            {
                "version": 1,
                "document_type": "inventory",
                "root_model": "inventory.InventoryFamily",
                "root_name": "inventory",
                "variables": [
                    "inventory.name",
                    "item.name",
                    "item.stock_quantity",
                ],
                "zones": [
                    {
                        "name": "stock_items",
                        "type": "repeat_row",
                        "collection": "inventory.items",
                        "item_name": "item",
                        "marker_pair": 1,
                    }
                ],
            },
        )
        initial_stock = InventoryItem.objects.get(pk=self.inventory_item.pk).stock_quantity

        self.client.force_authenticate(self.accountant)
        family_options = self.client.get(
            "/api/inventory-families/document-options/"
        )
        self.assertEqual(family_options.status_code, 200)
        self.assertEqual(family_options.data[0]["id"], self.family.pk)
        response = self.client.post(
            f"/api/document-templates/{template.pk}/generate/",
            {"object_id": self.family.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        rendered_text = _document_text(response.content)
        self.assertIn("Gants nitrile", rendered_text)
        self.assertIn("12.00", rendered_text)
        self.assertEqual(
            InventoryItem.objects.get(pk=self.inventory_item.pk).stock_quantity,
            initial_stock,
        )

    def test_payment_receipt_is_not_available_to_receptionist(self):
        receptionist = User.objects.create_user(
            email="dynamic-reception@example.test",
            password="test-password",
            first_name="Accueil",
            last_name="Test",
            role=User.Role.RECEPTIONIST,
        )
        self.client.force_authenticate(receptionist)

        response = self.client.get(
            "/api/document-templates/available/?document_type=payment"
        )

        self.assertEqual(response.status_code, 403)
