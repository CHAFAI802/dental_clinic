from django.test import TestCase
from django.core.exceptions import ValidationError
from patients.models import Patient
from accounts.models import User
from appointments.models import Appointment, Room
from billing.models import Invoice
from documents.models import Document
from imaging.models import ImagingStudy
from prescriptions.models import Prescription, PrescriptionTemplate
from treatment_plans.models import TreatmentPlan
from treatments.models import Treatment


class SoftDeleteTests(TestCase):

    def _create_patient(self):
        return Patient.objects.create(
            first_name="Delete",
            last_name="Test",
            birthdate="1990-01-01",
            gender="other",
            phone="0000000000",
        )

    def test_instance_delete_soft_deletes_record(self):
        patient = self._create_patient()
        patient.delete()
        patient.refresh_from_db()
        self.assertTrue(patient.is_deleted)
        self.assertIsNotNone(patient.deleted_at)

    def test_default_manager_hides_deleted_record(self):
        patient = self._create_patient()
        patient.delete()
        self.assertFalse(
            Patient.objects.filter(pk=patient.pk).exists()
        )
        self.assertTrue(
            Patient.all_objects.filter(pk=patient.pk).exists()
        )

    def test_restore_returns_record_to_default_manager(self):
        patient = self._create_patient()
        patient.delete()
        patient.restore()
        patient.refresh_from_db()
        self.assertFalse(patient.is_deleted)
        self.assertIsNone(patient.deleted_at)
        self.assertTrue(
            Patient.objects.filter(pk=patient.pk).exists()
        )

    def test_queryset_delete_soft_deletes_records(self):
        patient = self._create_patient()
        count = Patient.objects.filter(pk=patient.pk).delete()
        self.assertEqual(count, 1)
        patient.refresh_from_db()
        self.assertTrue(patient.is_deleted)
        self.assertIsNotNone(patient.deleted_at)
        self.assertFalse(
            Patient.objects.filter(pk=patient.pk).exists()
        )
        self.assertTrue(
            Patient.all_objects.filter(pk=patient.pk).exists()
        )

    def test_patient_soft_delete_preserves_related_business_history(self):
        patient = self._create_patient()
        dentist = User.objects.create_user(
            email="del002_dentist@example.com",
            password="StrongPassword123!",
            first_name="Del",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        appointment = Appointment.objects.create(
            patient=patient,
            practitioner=dentist,
            start_at="2035-06-01T09:00:00Z",
            end_at="2035-06-01T09:30:00Z",
            status=Appointment.Status.PENDING,
        )
        treatment = Treatment.objects.create(
            patient=patient,
            dentist=dentist,
            status=Treatment.Status.PLANNED,
            category=Treatment.Category.CONSULTATION,
            code="DEL002",
            label="DEL-002 Test",
        )
        treatment_plan = TreatmentPlan.objects.create(
            patient=patient,
            status=TreatmentPlan.Status.DRAFT,
        )
        template = PrescriptionTemplate.objects.create(
            name="DEL-002 Template",
            content="DEL-002",
        )
        prescription = Prescription.objects.create(
            patient=patient,
            dentist=dentist,
            template=template,
            status=Prescription.Status.DRAFT,
        )
        invoice = Invoice.objects.create(
            patient=patient,
            created_by=dentist,
            issued_at="2035-06-01",
            due_date="2035-06-30",
            status=Invoice.Status.DRAFT,
            reference_number="DEL002-INV-001",
        )
        document = Document.objects.create(
            patient=patient,
            created_by=dentist,
            document_type="other",
            title="DEL-002 Document",
            content="DEL-002",
            status=Document.Status.DRAFT,
        )
        imaging_study = ImagingStudy.objects.create(
            patient=patient,
            practitioner=dentist,
            study_type="xray",
            study_date="2035-06-01T10:00:00Z",
            status=ImagingStudy.Status.PENDING,
        )
        patient.delete()
        patient.refresh_from_db()
        self.assertTrue(patient.is_deleted)
        self.assertIsNotNone(patient.deleted_at)
        self.assertTrue(
            Appointment.all_objects.filter(pk=appointment.pk).exists()
        )
        self.assertTrue(
            Treatment.all_objects.filter(pk=treatment.pk).exists()
        )
        self.assertTrue(
            TreatmentPlan.all_objects.filter(pk=treatment_plan.pk).exists()
        )
        self.assertTrue(
            Prescription.objects.filter(pk=prescription.pk).exists()
        )
        self.assertTrue(
            Invoice.objects.filter(pk=invoice.pk).exists()
        )
        self.assertTrue(
            Document.objects.filter(pk=document.pk).exists()
        )
        self.assertTrue(
            ImagingStudy.objects.filter(pk=imaging_study.pk).exists()
        )

    def test_invoice_instance_delete_is_rejected(self):
        invoice = Invoice.objects.create(
            patient=self._create_patient(),
            issued_at="2035-06-01",
            due_date="2035-06-30",
            status=Invoice.Status.DRAFT,
            reference_number="DEL003-INSTANCE",
        )
        with self.assertRaises(ValidationError):
            invoice.delete()
        self.assertTrue(
            Invoice.objects.filter(pk=invoice.pk).exists()
        )

    def test_invoice_queryset_delete_is_rejected(self):
        invoice = Invoice.objects.create(
            patient=self._create_patient(),
            issued_at="2035-06-01",
            due_date="2035-06-30",
            status=Invoice.Status.DRAFT,
            reference_number="DEL003-QUERYSET",
        )
        with self.assertRaises(ValidationError):
            Invoice.objects.filter(pk=invoice.pk).delete()
        self.assertTrue(
            Invoice.objects.filter(pk=invoice.pk).exists()
        )

    def test_appointment_instance_delete_soft_deletes_record(self):
        patient = self._create_patient()
        dentist = User.objects.create_user(
            email="appointment_delete_dentist@example.com",
            password="StrongPassword123!",
            first_name="Delete",
            last_name="Dentist",
            role=User.Role.DENTIST,
        )
        appointment = Appointment.objects.create(
            patient=patient,
            practitioner=dentist,
            start_at="2035-07-01T09:00:00Z",
            end_at="2035-07-01T09:30:00Z",
            status=Appointment.Status.PENDING,
        )
        appointment_id = appointment.pk
        appointment.delete()
        appointment.refresh_from_db()
        self.assertTrue(appointment.is_deleted)
        self.assertIsNotNone(appointment.deleted_at)
        self.assertTrue(
            Appointment.all_objects.filter(pk=appointment_id).exists()
        )
        self.assertFalse(
            Appointment.objects.filter(pk=appointment_id).exists()
        )

    def test_room_instance_delete_is_rejected(self):
        room = Room.objects.create(
            name="Room Delete Rejected",
        )
        with self.assertRaises(ValidationError):
            room.delete()
        self.assertTrue(
            Room.objects.filter(pk=room.pk).exists()
        )

    def test_room_queryset_delete_is_rejected(self):
        room = Room.objects.create(
            name="Room Queryset Delete Rejected",
        )
        with self.assertRaises(ValidationError):
            Room.objects.filter(pk=room.pk).delete()
        self.assertTrue(
            Room.objects.filter(pk=room.pk).exists()
        )
