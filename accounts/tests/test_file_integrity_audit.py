import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User
from documents.models import Document
from imaging.models import ImagingInstance, ImagingSeries, ImagingStudy
from patients.models import Patient
from prescriptions.models import Prescription, PrescriptionTemplate


TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="dental-b9-media-")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class FileIntegrityAuditTests(APITestCase):
    """PHASE B9 characterization tests.

    These tests document current file upload integrity and lifecycle behavior.
    They intentionally characterize accepted unsafe or undefined behavior.
    """

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="dentist_file_audit@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="FileAudit",
            role=User.Role.DENTIST,
        )
        self.receptionist = User.objects.create_user(
            email="receptionist_file_audit@example.com",
            password="StrongPassword123!",
            first_name="Reception",
            last_name="FileAudit",
            role=User.Role.RECEPTIONIST,
        )

        self.dentist_token = Token.objects.create(user=self.dentist)
        self.receptionist_token = Token.objects.create(user=self.receptionist)

        self.patient = Patient.objects.create(
            first_name="File",
            last_name="Audit",
            birthdate="1990-01-01",
            gender="other",
            phone="+213333333333",
        )

        self.prescription_template = PrescriptionTemplate.objects.create(
            name="File audit prescription",
            content="Audit",
        )

        self.study = ImagingStudy.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            study_type="panoramic",
            study_date="2035-01-15T10:00:00Z",
            status="pending",
        )

        self.series = ImagingSeries.objects.create(
            study=self.study,
            series_number=1,
            modality="OT",
        )

    def test_prescription_api_accepts_arbitrary_text_upload_as_pdf_file(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}"
        )

        uploaded = SimpleUploadedFile(
            "not_a_pdf.txt",
            b"plain text, not a PDF",
            content_type="text/plain",
        )

        response = self.client.post(
            "/api/prescriptions/",
            {
                "patient": self.patient.id,
                "dentist": self.dentist.id,
                "template": self.prescription_template.id,
                "status": "draft",
                "pdf_file": uploaded,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.data)

        prescription = Prescription.objects.get(pk=response.data["id"])
        self.assertTrue(prescription.pdf_file.name.endswith(".txt"))

    def test_document_api_accepts_executable_extension_upload(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token.key}"
        )

        uploaded = SimpleUploadedFile(
            "payload.exe",
            b"MZ-not-a-real-executable",
            content_type="application/octet-stream",
        )

        response = self.client.post(
            "/api/documents/",
            {
                "patient": self.patient.id,
                "document_type": "other",
                "title": "Unsafe extension characterization",
                "content": "Audit",
                "status": "draft",
                "pdf_file": uploaded,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.data)

        document = Document.objects.get(pk=response.data["id"])
        self.assertTrue(document.pdf_file.name.endswith(".exe"))

    def test_imaging_api_accepts_mime_extension_mismatch(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}"
        )

        uploaded = SimpleUploadedFile(
            "image.jpg",
            b"this is plain text and not JPEG data",
            content_type="image/jpeg",
        )

        response = self.client.post(
            "/api/imaging-instances/",
            {
                "series": self.series.id,
                "instance_number": 1,
                "file_type": "application/dicom",
                "study_date": "2035-01-15T10:00:00Z",
                "file": uploaded,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.data)

        instance = ImagingInstance.objects.get(pk=response.data["id"])
        self.assertTrue(instance.file.name.endswith(".jpg"))
        self.assertEqual(instance.file_type, "application/dicom")

    def test_imaging_api_accepts_file_larger_than_memory_upload_threshold(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}"
        )

        uploaded = SimpleUploadedFile(
            "large.bin",
            b"x" * (3 * 1024 * 1024),
            content_type="application/octet-stream",
        )

        response = self.client.post(
            "/api/imaging-instances/",
            {
                "series": self.series.id,
                "instance_number": 2,
                "file_type": "application/octet-stream",
                "study_date": "2035-01-15T10:00:00Z",
                "file": uploaded,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.data)

        instance = ImagingInstance.objects.get(pk=response.data["id"])
        self.assertGreater(instance.file.size, 2621440)

    def test_deleting_imaging_instance_leaves_physical_file_on_storage(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist_token.key}"
        )

        uploaded = SimpleUploadedFile(
            "orphan.txt",
            b"orphan file characterization",
            content_type="text/plain",
        )

        response = self.client.post(
            "/api/imaging-instances/",
            {
                "series": self.series.id,
                "instance_number": 3,
                "file_type": "text/plain",
                "study_date": "2035-01-15T10:00:00Z",
                "file": uploaded,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201, response.data)

        instance = ImagingInstance.objects.get(pk=response.data["id"])
        storage = instance.file.storage
        stored_name = instance.file.name

        self.assertTrue(storage.exists(stored_name))

        delete_response = self.client.delete(
            f"/api/imaging-instances/{instance.id}/"
        )

        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(
            ImagingInstance.objects.filter(pk=instance.id).exists()
        )
        self.assertTrue(storage.exists(stored_name))
