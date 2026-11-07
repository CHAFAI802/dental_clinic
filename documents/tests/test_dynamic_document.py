import json
from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

from docx import Document as WordDocument
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from accounts.models import User
from billing.models import Invoice, InvoiceLine, Payment, PaymentMethod
from documents.services.dynamic_document import (
    build_context,
    discover_model_catalog,
    generate_document,
    get_builtin_catalog,
    get_builtin_exposures,
    parse_definition,
    queryset_hints,
    render_document,
    validate_template,
)
from documents.services.dynamic_document.markers import inspect_docx
from documents.serializers import DocumentTemplateSerializer
from documents.views import DocumentTemplateViewSet
from inventory.models import InventoryCategory, InventoryFamily, InventoryItem, Unit
from patients.models import Medication, Patient
from prescriptions.models import Prescription


def _docx_bytes(document):
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _invoice_docx(*, zone_count=1, nested_table=True):
    document = WordDocument()
    header = document.sections[0].header.paragraphs[0]
    header.add_run("Facture ")
    header.add_run("{{ invoice.reference_")
    header.add_run("number }}")
    document.add_paragraph("Client : {{ invoice.patient.first_name }}")
    document.add_paragraph("Date : {{ invoice.issued_at }}")

    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Désignation"
    table.rows[0].cells[1].text = "Quantité"
    for _ in range(zone_count):
        row = table.add_row()
        start = row.cells[0].paragraphs[0]
        start.add_run("{{ de")
        start.add_run("but }} ")
        name_run = start.add_run("{{ line.description }}")
        name_run.bold = True
        if nested_table:
            nested = row.cells[0].add_table(rows=1, cols=1)
            nested.cell(0, 0).text = "{{ line.subtotal }}"
        end = row.cells[1].paragraphs[0]
        end.add_run("{{ line.quantity }} ")
        end.add_run("{{ fi")
        end.add_run("n }}")
    document.sections[0].footer.paragraphs[0].text = (
        "Référence {{ invoice.reference_number }}"
    )
    return _docx_bytes(document)


def _invoice_config(*, zone_count=1, variables=None):
    return {
        "version": 1,
        "document_type": "invoice",
        "root_model": "billing.Invoice",
        "root_name": "invoice",
        "variables": variables
        or [
            "invoice.reference_number",
            "invoice.issued_at",
            "invoice.patient.first_name",
            "line.description",
            "line.quantity",
        ]
        + (["line.subtotal"] if zone_count and zone_count > 0 else []),
        "zones": [
            {
                "name": f"invoice_lines_{index}",
                "type": "repeat_row",
                "collection": "invoice.lines",
                "item_name": "line",
                "marker_pair": index,
            }
            for index in range(1, zone_count + 1)
        ],
    }


def _invoice_objects():
    patient = Patient(
        first_name="Émilie",
        last_name="Durand",
        phone="0600000000",
        patient_code="PAT-TEST",
    )
    invoice = Invoice(
        patient=patient,
        reference_number="A0012/2026",
        issued_at=date(2026, 11, 4),
        due_date=date(2026, 12, 4),
        status=Invoice.Status.ISSUED,
        subtotal=Decimal("70.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("70.00"),
        paid_amount=Decimal("0.00"),
        balance_due=Decimal("70.00"),
    )
    line = InvoiceLine(
        invoice=invoice,
        description="Détartrage",
        quantity=Decimal("2"),
        unit_price=Decimal("35.00"),
        tax_rate=Decimal("0.00"),
    )
    return patient, invoice, line


def _document_text(content):
    scan = inspect_docx(content)
    return "\n".join(paragraph.text for _, paragraph in scan.paragraphs)


class DynamicDocumentStructureTests(SimpleTestCase):
    def setUp(self):
        self.exposure = get_builtin_exposures()["billing.Invoice"]
        self.catalog = get_builtin_catalog("billing.Invoice", "invoice")

    def test_persistent_structure_is_parsed_and_rejects_incomplete_or_unknown_keys(self):
        structure = parse_definition(_invoice_config())
        self.assertEqual(structure.document_type, "invoice")
        self.assertEqual(structure.zones[0].marker_pair, 1)

        invalid = _invoice_config()
        invalid["unexpected"] = True
        with self.assertRaisesMessage(ValidationError, "Clés de configuration inconnues"):
            parse_definition(invalid)

        invalid = _invoice_config()
        invalid["zones"][0]["marker_pair"] = 2
        with self.assertRaisesMessage(ValidationError, "numérotées sans interruption"):
            parse_definition(invalid)

    def test_catalog_discovers_only_explicitly_exposed_fields_and_relations(self):
        catalog = self.catalog.as_dict()
        self.assertIn("invoice.reference_number", catalog["variables"])
        self.assertIn("invoice.patient.first_name", catalog["variables"])
        self.assertIn("line.subtotal", catalog["variables"])
        self.assertIn("invoice.lines", catalog["collections"])
        self.assertNotIn(
            "invoice.patient.social_security_number",
            catalog["variables"],
        )

        with self.assertRaisesMessage(ValidationError, "n’est pas exposée"):
            definition = parse_definition(
                _invoice_config(
                    variables=["invoice.patient.social_security_number"]
                )
            )
            validate_template(_invoice_docx(), definition, self.catalog)

    def test_discovery_rejects_unknown_fields_and_relation_mismatches(self):
        invalid = type(self.exposure)(
            model=self.exposure.model,
            fields=("does_not_exist",),
        )
        with self.assertRaisesMessage(ValidationError, "n’existe pas"):
            discover_model_catalog(invalid, "invoice")

    def test_queryset_hints_include_related_patient_and_invoice_lines(self):
        select_related, prefetch_related = queryset_hints(self.exposure)
        self.assertIn("patient", select_related)
        self.assertIn("lines", prefetch_related)

    def test_marker_parser_detects_split_tokens_in_headers_and_footers(self):
        content = _invoice_docx()
        scan = inspect_docx(content)
        self.assertEqual(
            [occurrence.name for occurrence in scan.variables],
            [
                "invoice.patient.first_name",
                "invoice.issued_at",
                "line.description",
                "line.subtotal",
                "line.quantity",
                "invoice.reference_number",
                "invoice.reference_number",
            ],
        )
        self.assertEqual(len(scan.marker_pairs), 1)
        self.assertTrue(any("header" in story for story, _ in scan.paragraphs))
        self.assertTrue(any("footer" in story for story, _ in scan.paragraphs))

    def test_marker_parser_rejects_missing_inverted_and_malformed_markers(self):
        cases = (
            ("{{ debut }}", "marqueur de fin est absent"),
            ("{{ fin }} {{ debut }}", "alterner"),
            ("{{ debut }", "mal formé"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                document = WordDocument()
                document.add_paragraph(text)
                with self.assertRaisesMessage(ValidationError, expected):
                    inspect_docx(_docx_bytes(document))

    def test_validator_rejects_collection_variables_outside_their_zone(self):
        document = WordDocument()
        document.add_paragraph("{{ line.description }}")
        table = document.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "{{ debut }}{{ line.description }}"
        table.cell(0, 1).text = "{{ fin }}"
        with self.assertRaisesMessage(ValidationError, "hors de sa ligne répétitive"):
            validate_template(
                _docx_bytes(document),
                _invoice_config(),
                self.catalog,
            )

    def test_validator_accepts_one_global_marker_pair_without_zone_configuration(self):
        config = _invoice_config(zone_count=0)
        config.pop("variables")
        validated = validate_template(
            _invoice_docx(),
            config,
            self.catalog,
        )
        self.assertEqual(len(validated.scan.marker_pairs), 1)

    def test_validator_rejects_multiple_global_marker_pairs(self):
        document = WordDocument()
        document.add_paragraph("{{ debut }} Facture {{ invoice.reference_number }}")
        document.add_paragraph("{{ fin }}")
        document.add_paragraph("{{ debut }}")
        document.add_paragraph("{{ fin }}")
        config = {
            "version": 1,
            "document_type": "invoice",
            "root_model": "billing.Invoice",
            "root_name": "invoice",
        }

        with self.assertRaisesMessage(ValidationError, "qu’une seule paire"):
            validate_template(_docx_bytes(document), config, self.catalog)

    def test_validation_reports_a_global_pair_without_a_zone(self):
        document = WordDocument()
        document.add_paragraph("{{ debut }}Facture {{ invoice.reference_number }}{{ fin }}")
        template = SimpleNamespace(
            structure_config={
                "version": 1,
                "document_type": "invoice",
                "root_model": "billing.Invoice",
                "root_name": "invoice",
            }
        )

        result = DocumentTemplateViewSet._validate_template_content(
            template,
            _docx_bytes(document),
        )

        self.assertEqual(result["marker_pairs"], [{"index": 1, "zone": None}])

    def test_template_serializer_accepts_a_configured_generic_docx(self):
        config = _invoice_config()
        serializer = DocumentTemplateSerializer(
            data={
                "name": "Invoice template",
                "file": SimpleUploadedFile(
                    "invoice.docx",
                    _invoice_docx(),
                ),
                "structure_config": json.dumps(config),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["structure_config"],
            config,
        )


class DynamicDocumentContextAndRenderingTests(SimpleTestCase):
    def setUp(self):
        self.patient, self.invoice, self.line = _invoice_objects()
        self.exposure = get_builtin_exposures()["billing.Invoice"]

    def test_invoice_end_to_end_repeats_rows_formats_values_and_preserves_styles(self):
        output = generate_document(
            SimpleNamespace(
                structure_config=_invoice_config(),
                file=ContentFile(_invoice_docx(nested_table=True)),
            ),
            self.invoice,
            collection_values={"invoice.lines": [self.line]},
        )
        generated = WordDocument(BytesIO(output))
        text = _document_text(output)

        self.assertIn("A0012/2026", text)
        self.assertIn("Émilie", text)
        self.assertIn("04/11/2026", text)
        self.assertIn("Détartrage", text)
        self.assertIn("70.00", text)
        self.assertNotIn("{{", text)
        self.assertEqual(len(generated.tables[0].rows), 2)
        description_run = next(
            run
            for paragraph in generated.tables[0].rows[1].cells[0].paragraphs
            for run in paragraph.runs
            if "Détartrage" in run.text
        )
        self.assertTrue(description_run.bold)

    def test_automatic_collections_repeat_only_their_table_row_and_render_inline_values(self):
        second_line = InvoiceLine(
            invoice=self.invoice,
            description="Composite",
            quantity=Decimal("1"),
            unit_price=Decimal("85.00"),
            tax_rate=Decimal("0.00"),
        )
        document = WordDocument()
        document.add_paragraph("{{ debut }}")
        document.add_paragraph("Détail : {{ line.description }}")
        document.add_paragraph(
            "Facture {{ invoice.reference_number }} — {{ invoice.patient.first_name }}"
        )
        table = document.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "Prestation"
        table.rows[0].cells[1].text = "Quantité"
        row = table.add_row()
        description = row.cells[0].paragraphs[0]
        description.add_run("{{ line.description }}").bold = True
        row.cells[1].text = "{{ line.quantity }}"
        document.add_paragraph("{{ fin }}")
        structure = {
            "version": 1,
            "document_type": "invoice",
            "root_model": "billing.Invoice",
            "root_name": "invoice",
        }

        output = generate_document(
            SimpleNamespace(
                structure_config=structure,
                file=ContentFile(_docx_bytes(document)),
            ),
            self.invoice,
            collection_values={"invoice.lines": [self.line, second_line]},
        )
        generated = WordDocument(BytesIO(output))
        text = _document_text(output)

        self.assertIn("Détail : Détartrage\nComposite", text)
        self.assertEqual(text.count("Détail :"), 1)
        self.assertIn("Facture A0012/2026 — Émilie", text)
        self.assertEqual(len(generated.tables[0].rows), 3)
        self.assertIn("Détartrage", generated.tables[0].rows[1].cells[0].text)
        self.assertIn("Composite", generated.tables[0].rows[2].cells[0].text)
        self.assertNotIn("{{", text)
        self.assertNotIn("}}", text)
        description_run = next(
            run
            for row in generated.tables[0].rows[1:]
            for paragraph in row.cells[0].paragraphs
            for run in paragraph.runs
            if "Détartrage" in run.text
        )
        self.assertTrue(description_run.bold)

    def test_automatic_collection_variables_are_rejected_when_not_in_catalog(self):
        document = WordDocument()
        document.add_paragraph("{{ invoice.patient.social_security_number }}")
        structure = {
            "version": 1,
            "document_type": "invoice",
            "root_model": "billing.Invoice",
            "root_name": "invoice",
        }

        with self.assertRaisesMessage(ValidationError, "n’est pas exposée"):
            validate_template(
                _docx_bytes(document),
                structure,
                get_builtin_catalog("billing.Invoice", "invoice"),
            )

    def test_empty_collection_removes_the_configured_row(self):
        structure = parse_definition(_invoice_config())
        context = build_context(
            self.invoice,
            structure,
            self.exposure,
            collection_values={"invoice.lines": []},
        )

        output = render_document(
            _invoice_docx(),
            structure,
            context,
            get_builtin_catalog("billing.Invoice", "invoice"),
        )
        generated = WordDocument(BytesIO(output))
        self.assertEqual(len(generated.tables[0].rows), 1)
        self.assertNotIn("{{", _document_text(output))

    def test_multiple_zones_bind_to_marker_pairs_by_configuration(self):
        structure = parse_definition(_invoice_config(zone_count=2))
        context = build_context(
            self.invoice,
            structure,
            self.exposure,
            collection_values={"invoice.lines": [self.line]},
        )

        output = render_document(
            _invoice_docx(zone_count=2),
            structure,
            context,
            get_builtin_catalog("billing.Invoice", "invoice"),
        )
        generated = WordDocument(BytesIO(output))
        self.assertEqual(len(generated.tables[0].rows), 3)
        self.assertEqual(_document_text(output).count("Détartrage"), 2)

    def test_multiple_collection_items_keep_order(self):
        second_line = InvoiceLine(
            invoice=self.invoice,
            description="Composite",
            quantity=Decimal("1"),
            unit_price=Decimal("85.00"),
            tax_rate=Decimal("0.00"),
        )
        output = generate_document(
            SimpleNamespace(
                structure_config=_invoice_config(),
                file=ContentFile(_invoice_docx()),
            ),
            self.invoice,
            collection_values={
                "invoice.lines": [self.line, second_line],
            },
        )
        generated = WordDocument(BytesIO(output))
        text = _document_text(output)

        self.assertEqual(len(generated.tables[0].rows), 3)
        self.assertLess(text.index("Détartrage"), text.index("Composite"))

    def test_inventory_list_document_uses_the_same_configured_renderer(self):
        category = InventoryCategory(
            code=InventoryCategory.CategoryCode.MATERIAL,
            name="Matériel",
        )
        family = InventoryFamily(
            category=category,
            name="Gants",
            code="GANT",
        )
        item = InventoryItem(
            family=family,
            unit=Unit(name="Boîte", symbol="boîte"),
            sku="DCL-MAT-GANT-000001",
            name="Gants nitrile",
            stock_quantity=Decimal("24.00"),
        )
        structure = {
            "version": 1,
            "document_type": "inventory",
            "root_model": "inventory.InventoryFamily",
            "root_name": "inventory",
            "variables": [
                "inventory.name",
                "inventory.code",
                "item.sku",
                "item.name",
                "item.stock_quantity",
                "item.unit.symbol",
            ],
            "zones": [
                {
                    "name": "inventory_items",
                    "type": "repeat_row",
                    "collection": "inventory.items",
                    "item_name": "item",
                    "marker_pair": 1,
                }
            ],
        }
        document = WordDocument()
        document.add_paragraph("Famille {{ inventory.name }} ({{ inventory.code }})")
        table = document.add_table(rows=1, cols=2)
        table.cell(0, 0).text = "{{ debut }}{{ item.name }} ({{ item.sku }})"
        table.cell(0, 1).text = "{{ item.stock_quantity }} {{ item.unit.symbol }}{{ fin }}"

        output = generate_document(
            SimpleNamespace(
                structure_config=structure,
                file=ContentFile(_docx_bytes(document)),
            ),
            family,
            collection_values={"inventory.items": [item]},
        )

        self.assertIn("Famille Gants (GANT)", _document_text(output))
        self.assertIn("Gants nitrile (DCL-MAT-GANT-000001)", _document_text(output))
        self.assertIn("24.00 boîte", _document_text(output))

    def test_context_rejects_unexposed_variables_and_external_collections(self):
        structure = parse_definition(
            _invoice_config(
                variables=["invoice.patient.social_security_number"]
            )
        )
        with self.assertRaisesMessage(ValidationError, "n’est pas autorisée"):
            build_context(self.invoice, structure, self.exposure)

        structure = parse_definition(_invoice_config())
        with self.assertRaisesMessage(ValidationError, "non autorisées"):
            build_context(
                self.invoice,
                structure,
                self.exposure,
                collection_values={"invoice.unknown": []},
            )

    def test_context_handles_prescription_collection_and_receipt_relations(self):
        dentist = User(
            email="dentist@example.test",
            first_name="Nadia",
            last_name="Ben Salah",
            phone="0611111111",
            role=User.Role.DENTIST,
        )
        prescription = Prescription(
            patient=self.patient,
            dentist=dentist,
            notes="Après le repas\npendant 7 jours",
            generated_at=datetime(2026, 11, 4, tzinfo=timezone.utc),
            status=Prescription.Status.GENERATED,
        )
        medication = Medication(
            patient=self.patient,
            name="Amoxicilline",
            dosage="500 mg",
            frequency="3 fois par jour",
            route="orale",
            start_date=date(2026, 11, 4),
            notes="7 jours",
        )
        prescription_structure = parse_definition(
            {
                "version": 1,
                "document_type": "prescription",
                "root_model": "prescriptions.Prescription",
                "root_name": "prescription",
                "variables": [
                    "prescription.notes",
                    "prescription.patient.first_name",
                    "prescription.dentist.last_name",
                    "medication.name",
                    "medication.dosage",
                ],
                "zones": [
                    {
                        "name": "medications",
                        "type": "repeat_row",
                        "collection": "prescription.medications",
                        "item_name": "medication",
                        "marker_pair": 1,
                    }
                ],
            }
        )
        prescription_exposure = get_builtin_exposures()[
            "prescriptions.Prescription"
        ]
        prescription_context = build_context(
            prescription,
            prescription_structure,
            prescription_exposure,
            collection_values={"prescription.medications": [medication]},
        )
        self.assertEqual(
            prescription_context["prescription"]["medications"][0]["name"],
            "Amoxicilline",
        )
        self.assertEqual(
            prescription_context["prescription"]["patient"]["first_name"],
            "Émilie",
        )
        prescription_docx = WordDocument()
        prescription_docx.add_paragraph(
            "Patient {{ prescription.patient.first_name }} — "
            "{{ prescription.notes }} — "
            "{{ prescription.dentist.last_name }}"
        )
        medication_table = prescription_docx.add_table(rows=1, cols=2)
        medication_table.cell(0, 0).text = (
            "{{ debut }}{{ medication.name }}"
        )
        medication_table.cell(0, 1).text = (
            "{{ medication.dosage }}{{ fin }}"
        )
        prescription_output = generate_document(
            SimpleNamespace(
                structure_config=prescription_structure,
                file=ContentFile(_docx_bytes(prescription_docx)),
            ),
            prescription,
            collection_values={
                "prescription.medications": [medication],
            },
        )
        self.assertIn("Amoxicilline", _document_text(prescription_output))
        self.assertIn(
            "Après le repas\npendant 7 jours",
            _document_text(prescription_output),
        )

        method = PaymentMethod(name="Carte", provider="terminal")
        payment = Payment(
            invoice=self.invoice,
            patient=self.patient,
            method=method,
            payment_at=datetime(2026, 11, 4, 10, 30, tzinfo=timezone.utc),
            amount=Decimal("35.00"),
            reference="PAY-42",
        )
        receipt_structure = parse_definition(
            {
                "version": 1,
                "document_type": "receipt",
                "root_model": "billing.Payment",
                "root_name": "payment",
                "variables": [
                    "payment.reference",
                    "payment.amount",
                    "payment.invoice.reference_number",
                    "payment.patient.first_name",
                ],
                "zones": [],
            }
        )
        receipt_context = build_context(
            payment,
            receipt_structure,
            get_builtin_exposures()["billing.Payment"],
        )
        self.assertEqual(receipt_context["payment"]["reference"], "PAY-42")
        self.assertEqual(
            receipt_context["payment"]["invoice"]["reference_number"],
            "A0012/2026",
        )
        self.assertEqual(receipt_context["payment"]["amount"], "35.00")
        receipt_docx = WordDocument()
        receipt_docx.add_paragraph("Reçu {{ payment.reference }}")
        receipt_docx.add_paragraph("Patient {{ payment.patient.first_name }}")
        receipt_docx.add_paragraph(
            "Facture {{ payment.invoice.reference_number }}"
        )
        receipt_docx.add_paragraph("Montant {{ payment.amount }}")
        receipt_output = generate_document(
            SimpleNamespace(
                structure_config=receipt_structure,
                file=ContentFile(_docx_bytes(receipt_docx)),
            ),
            payment,
        )
        receipt_text = _document_text(receipt_output)
        self.assertIn("Reçu PAY-42", receipt_text)
        self.assertIn("Facture A0012/2026", receipt_text)
        self.assertIn("Montant 35.00", receipt_text)
