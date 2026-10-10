from django.core.exceptions import ValidationError
from django.test import TestCase

from documents.models import DocumentTemplate, DocumentTemplateVersion, DocumentType


class DocumentEngineModelTests(TestCase):
    def test_document_type_can_be_created_with_unique_code(self):
        document_type = DocumentType.objects.create(
            code="consultation",
            name="Consultation",
            description="Consultation standard",
        )

        self.assertEqual(document_type.code, "consultation")
        self.assertEqual(document_type.name, "Consultation")

    def test_document_type_slug_is_generated_from_name_when_missing(self):
        document_type = DocumentType(name="Ordonnance")
        document_type.save()

        self.assertEqual(document_type.code, "ordonnance")

    def test_template_version_is_published_with_unique_template_version_number(self):
        document_type = DocumentType.objects.create(
            code="consultation",
            name="Consultation",
        )
        template = DocumentTemplate.objects.create(
            name="Ordonnance standard",
            description="Template de consultation",
            content="Bonjour {{ patient_name }}",
            document_type=document_type,
            code="ordonnance-standard",
        )

        version = DocumentTemplateVersion.objects.create(
            template=template,
            version_number=1,
            status=DocumentTemplateVersion.Status.PUBLISHED,
            schema_version="1.0",
            definition={"pages": [{"elements": []}]},
        )

        self.assertEqual(version.template, template)
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.status, DocumentTemplateVersion.Status.PUBLISHED)

    def test_template_version_requires_pages_in_json_definition(self):
        document_type = DocumentType.objects.create(
            code="consultation",
            name="Consultation",
        )
        template = DocumentTemplate.objects.create(
            name="Ordonnance standard",
            content="Bonjour {{ patient_name }}",
            document_type=document_type,
            code="ordonnance-standard",
        )

        version = DocumentTemplateVersion(
            template=template,
            version_number=2,
            status=DocumentTemplateVersion.Status.DRAFT,
            definition={"title": "No pages"},
        )

        with self.assertRaises(ValidationError):
            version.full_clean()

    def test_template_version_publish_sets_published_status(self):
        document_type = DocumentType.objects.create(
            code="consultation",
            name="Consultation",
        )
        template = DocumentTemplate.objects.create(
            name="Ordonnance standard",
            content="Bonjour {{ patient_name }}",
            document_type=document_type,
            code="ordonnance-standard",
        )
        version = DocumentTemplateVersion(
            template=template,
            version_number=3,
            status=DocumentTemplateVersion.Status.DRAFT,
            definition={"pages": [{"elements": []}]},
        )

        version.publish(commit=False)

        self.assertEqual(version.status, DocumentTemplateVersion.Status.PUBLISHED)
        self.assertIsNotNone(version.published_at)
