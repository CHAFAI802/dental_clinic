from tempfile import TemporaryDirectory

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.test import override_settings
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import User
from documents.admin import DocumentTemplateAdmin
from documents.models import DocumentTemplate
from documents.tests.docx_fixtures import (
    make_docx_with_text,
    make_prescription_docx,
    make_simple_docx,
)


class DocumentTemplatePermissionTests(APITestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.settings_context = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_context.enable()
        self.addCleanup(self.settings_context.disable)

        self.administrator = User.objects.create_user(
            email="admin@example.test",
            password="test-password",
            first_name="Admin",
            last_name="User",
            role=User.Role.ADMINISTRATOR,
        )
        self.dentist = User.objects.create_user(
            email="dentist@example.test",
            password="test-password",
            first_name="Dental",
            last_name="Doctor",
            role=User.Role.DENTIST,
        )
        self.template = DocumentTemplate.objects.create(
            name="Approved",
            file=SimpleUploadedFile(
                "approved.docx",
                make_prescription_docx(),
            ),
        )
        self.unapproved_template = DocumentTemplate.objects.create(
            name="Pending",
            file=SimpleUploadedFile("pending.docx", make_simple_docx()),
        )
        self.client.force_authenticate(self.administrator)
        self.client.post(
            f"/api/document-templates/{self.template.pk}/approve/",
            format="json",
        )

    def test_dentist_sees_only_active_approved_templates(self):
        self.client.force_authenticate(self.dentist)

        response = self.client.get("/api/document-templates/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [template["id"] for template in response.data],
            [self.template.pk],
        )

        self.template.is_active = False
        self.template.save(update_fields=("is_active",))
        response = self.client.get("/api/document-templates/")
        self.assertEqual(response.data, [])

        self.client.force_authenticate(self.administrator)
        update_response = self.client.patch(
            f"/api/document-templates/{self.template.pk}/",
            {"is_active": True},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.template.refresh_from_db()
        self.assertTrue(self.template.is_active)

    def test_dentist_cannot_create_modify_or_approve_templates(self):
        self.client.force_authenticate(self.dentist)

        create_response = self.client.post(
            "/api/document-templates/",
            {"name": "Not allowed"},
            format="multipart",
        )
        update_response = self.client.patch(
            f"/api/document-templates/{self.template.pk}/",
            {"name": "Changed"},
            format="json",
        )
        approve_response = self.client.post(
            f"/api/document-templates/{self.unapproved_template.pk}/approve/",
            format="json",
        )

        self.assertEqual(create_response.status_code, 403)
        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(approve_response.status_code, 403)

    def test_django_admin_template_management_uses_administrator_roles(self):
        model_admin = DocumentTemplateAdmin(DocumentTemplate, AdminSite())
        request = RequestFactory().get("/admin/documents/documenttemplate/")
        request.user = self.dentist

        self.assertFalse(model_admin.has_module_permission(request))
        self.assertFalse(model_admin.has_view_permission(request))
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))

        request.user = self.administrator
        self.assertTrue(model_admin.has_module_permission(request))
        self.assertTrue(model_admin.has_view_permission(request))
        self.assertTrue(model_admin.has_add_permission(request))
        self.assertTrue(model_admin.has_change_permission(request))
        self.assertTrue(model_admin.has_delete_permission(request))

    def test_administrator_can_approve_and_source_change_revokes_approval(self):
        self.client.force_authenticate(self.administrator)

        response = self.client.post(
            f"/api/document-templates/{self.unapproved_template.pk}/approve/",
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.unapproved_template.refresh_from_db()
        self.assertTrue(self.unapproved_template.is_approved)
        self.assertEqual(self.unapproved_template.approved_by, self.administrator)
        self.assertIsNotNone(self.unapproved_template.approved_at)

        self.unapproved_template.file = SimpleUploadedFile(
            "pending.docx",
            make_simple_docx("Version remplacée"),
        )
        self.unapproved_template.save()
        self.unapproved_template.refresh_from_db()

        self.assertFalse(self.unapproved_template.is_approved)
        self.assertIsNone(self.unapproved_template.approved_by)
        self.assertIsNone(self.unapproved_template.approved_at)

    def test_administrator_can_upload_and_edit_valid_docx_template(self):
        response = self.client.post(
            "/api/document-templates/",
            {
                "name": "New template",
                "description": "DOCX upload",
                "file": SimpleUploadedFile("new.docx", make_simple_docx()),
                "is_approved": True,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        created = DocumentTemplate.objects.get(pk=response.data["id"])
        self.assertFalse(created.is_approved)
        self.assertTrue(created.is_active)

        update_response = self.client.patch(
            f"/api/document-templates/{created.pk}/",
            {"description": "Updated"},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        created.refresh_from_db()
        self.assertEqual(created.description, "Updated")

    def test_invalid_or_non_docx_upload_is_rejected(self):
        for filename, content in (
            ("wrong.txt", make_simple_docx()),
            ("corrupt.docx", b"not a DOCX archive"),
            ("empty.docx", b""),
        ):
            with self.subTest(filename=filename):
                response = self.client.post(
                    "/api/document-templates/",
                    {
                        "name": filename,
                        "file": SimpleUploadedFile(filename, content),
                    },
                    format="multipart",
                )
                self.assertEqual(response.status_code, 400)

    def test_unknown_and_malformed_variables_are_rejected(self):
        for text in (
            "{{ patient.secret }}",
            "{{ patient.first_name",
            "{{ medication.name }}",
            "{{ prescription_end }} {{ prescription_start }}",
        ):
            with self.subTest(text=text):
                response = self.client.post(
                    "/api/document-templates/",
                    {
                        "name": "Invalid variable",
                        "file": SimpleUploadedFile(
                            "invalid.docx",
                            make_docx_with_text(text),
                        ),
                    },
                    format="multipart",
                )
                self.assertEqual(response.status_code, 400)

    def test_approval_rejects_corrupted_docx(self):
        corrupt_template = DocumentTemplate.objects.create(
            name="Corrupted",
            file=SimpleUploadedFile("corrupted.docx", b"not a zip archive"),
        )
        response = self.client.post(
            f"/api/document-templates/{corrupt_template.pk}/approve/",
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        corrupt_template.refresh_from_db()
        self.assertFalse(corrupt_template.is_approved)
