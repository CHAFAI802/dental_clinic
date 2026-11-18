from datetime import date, timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from appointments.models import Appointment
from billing.models import Prestation, PrestationCategory
from patients.models import Allergy, MedicalHistory, Medication, Patient
from treatments.models import Treatment


class MedicalHistoryAllergyAccessTests(APITestCase):
    """
    Vérifie le cloisonnement des antécédents médicaux et allergies.

    Un dentiste est autorisé si le patient possède au moins :
    - un rendez-vous non supprimé avec ce dentiste ;
    - OU un traitement non supprimé réalisé par ce dentiste.
    """

    def setUp(self):
        self.dentist = User.objects.create_user(
            email="history-dentist@example.test",
            password="test-password",
            first_name="Nadia",
            last_name="Dentiste",
            role=User.Role.DENTIST,
        )
        self.other_dentist = User.objects.create_user(
            email="history-other@example.test",
            password="test-password",
            first_name="Autre",
            last_name="Dentiste",
            role=User.Role.DENTIST,
        )
        self.receptionist = User.objects.create_user(
            email="history-reception@example.test",
            password="test-password",
            first_name="Accueil",
            last_name="Test",
            role=User.Role.RECEPTIONIST,
        )

        self.patient = self.create_patient("Lié")
        self.foreign_patient = self.create_patient("Étranger")

        now = timezone.now()
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            practitioner=self.dentist,
            start_at=now - timedelta(minutes=10),
            end_at=now + timedelta(minutes=30),
            status=Appointment.Status.CONFIRMED,
        )

        foreign_start = now + timedelta(days=2)
        Appointment.objects.create(
            patient=self.foreign_patient,
            practitioner=self.other_dentist,
            start_at=foreign_start,
            end_at=foreign_start + timedelta(minutes=30),
        )

        category = PrestationCategory.objects.create(
            name="Catégorie test cloisonnement",
            code="SEC-TEST",
        )
        self.prestation = Prestation.objects.create(
            category=category,
            code="SEC-TEST-001",
            label="Prestation test cloisonnement",
        )

        self.client.force_authenticate(self.dentist)

    @staticmethod
    def create_patient(suffix):
        return Patient.objects.create(
            first_name="Patient",
            last_name=suffix,
            phone=f"060000{len(suffix):04d}",
        )

    def create_treatment(self, patient, dentist=None):
        return Treatment.objects.create(
            patient=patient,
            dentist=dentist or self.dentist,
            prestation=self.prestation,
            code=self.prestation.code,
            label=self.prestation.label,
            start_at=timezone.now(),
        )

    @staticmethod
    def endpoint(model_name):
        return f"/api/{model_name}/"

    @staticmethod
    def payload(model_name):
        if model_name == "medical-histories":
            return {
                "condition": "Hypertension",
                "status": "Suivi",
                "notes": "Test de cloisonnement",
                "is_chronic": True,
                "is_acute": False,
            }

        if model_name == "allergies":
            return {
                "substance": "Pénicilline",
                "reaction": "Éruption cutanée",
                "severity": "Modérée",
                "notes": "Test de cloisonnement",
            }

        return {
            "name": "Amoxicilline",
            "dosage": "500 mg",
            "frequency": "3 fois par jour",
            "route": "orale",
            "start_date": "2026-10-15",
            "end_date": "2026-10-21",
            "notes": "Test de cloisonnement",
        }

    def create_record(self, model_name, patient):
        if model_name == "medical-histories":
            return MedicalHistory.objects.create(
                patient=patient,
                condition="Antécédent test",
            )

        if model_name == "allergies":
            return Allergy.objects.create(
                patient=patient,
                substance="Substance test",
                reaction="Réaction test",
                severity="Modérée",
            )

        return Medication.objects.create(
            patient=patient,
            prescribed_by=self.dentist,
            name="Médicament test",
            dosage="10 mg",
            frequency="1 fois par jour",
            route="orale",
            start_date=date(2026, 10, 15),
        )

    def test_list_only_returns_records_for_linked_patients(self):
        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                own_record = self.create_record(endpoint_name, self.patient)
                self.create_record(endpoint_name, self.foreign_patient)

                response = self.client.get(self.endpoint(endpoint_name))

                self.assertEqual(response.status_code, 200, response.data)
                returned_ids = {item["id"] for item in response.data}
                self.assertIn(own_record.pk, returned_ids)
                self.assertEqual(len(returned_ids), 1)

                response = self.client.get(
                    self.endpoint(endpoint_name),
                    {"patient": self.foreign_patient.pk},
                )
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data, [])

    def test_foreign_record_cannot_be_retrieved_updated_or_deleted(self):
        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                record = self.create_record(
                    endpoint_name,
                    self.foreign_patient,
                )
                detail_url = f"{self.endpoint(endpoint_name)}{record.pk}/"

                response = self.client.get(detail_url)
                self.assertEqual(response.status_code, 404)

                response = self.client.patch(
                    detail_url,
                    self.payload(endpoint_name),
                    format="json",
                )
                self.assertEqual(response.status_code, 404)

                response = self.client.delete(detail_url)
                self.assertEqual(response.status_code, 404)

                self.assertTrue(
                    type(record).objects.filter(pk=record.pk).exists()
                )

    def test_dentist_can_create_records_for_linked_patient(self):
        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                response = self.client.post(
                    f"{self.endpoint(endpoint_name)}?patient={self.patient.pk}",
                    self.payload(endpoint_name),
                    format="json",
                )

                self.assertEqual(response.status_code, 201, response.data)
                self.assertEqual(response.data["patient"], self.patient.pk)

    def test_dentist_cannot_create_records_for_foreign_patient(self):
        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                response = self.client.post(
                    f"{self.endpoint(endpoint_name)}?patient={self.foreign_patient.pk}",
                    self.payload(endpoint_name),
                    format="json",
                )

                self.assertEqual(response.status_code, 404)
                self.assertFalse(
                    MedicalHistory.objects.filter(
                        patient=self.foreign_patient
                    ).exists()
                    if endpoint_name == "medical-histories"
                    else Allergy.objects.filter(
                        patient=self.foreign_patient
                    ).exists()
                )

    def test_patient_parameter_is_required_for_creation(self):
        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                response = self.client.post(
                    self.endpoint(endpoint_name),
                    self.payload(endpoint_name),
                    format="json",
                )

                self.assertEqual(response.status_code, 400, response.data)

    def test_patient_linked_only_by_active_treatment_is_accessible(self):
        treatment_only_patient = self.create_patient("Traitement actif")
        self.create_treatment(treatment_only_patient)

        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                response = self.client.post(
                    f"{self.endpoint(endpoint_name)}?patient={treatment_only_patient.pk}",
                    self.payload(endpoint_name),
                    format="json",
                )
                self.assertEqual(response.status_code, 201, response.data)

    def test_deleted_appointment_does_not_keep_patient_linked(self):
        self.appointment.delete()

        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                response = self.client.get(
                    self.endpoint(endpoint_name),
                    {"patient": self.patient.pk},
                )
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data, [])

    def test_deleted_treatment_does_not_keep_patient_linked(self):
        treatment_only_patient = self.create_patient("Traitement supprimé")
        treatment = self.create_treatment(treatment_only_patient)
        treatment.delete()

        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                response = self.client.get(
                    self.endpoint(endpoint_name),
                    {"patient": treatment_only_patient.pk},
                )
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data, [])

    def test_active_treatment_keeps_link_when_appointment_is_deleted(self):
        treatment_only_patient = self.create_patient("Lien traitement")
        self.create_treatment(treatment_only_patient)
        self.appointment.delete()

        response = self.client.get(
            self.endpoint("medical-histories"),
            {"patient": treatment_only_patient.pk},
        )
        self.assertEqual(response.status_code, 200, response.data)

    def test_active_appointment_keeps_link_when_treatment_is_deleted(self):
        treatment = self.create_treatment(self.patient)
        treatment.delete()

        response = self.client.get(
            self.endpoint("medical-histories"),
            {"patient": self.patient.pk},
        )
        self.assertEqual(response.status_code, 200, response.data)

    def create_and_check_all_resources(self, patient):
        """Vérifie lecture et création pour les trois ressources."""
        records = {}

        for endpoint_name in (
            "medical-histories",
            "allergies",
            "medications",
        ):
            with self.subTest(endpoint=endpoint_name):
                record = self.create_record(endpoint_name, patient)
                records[endpoint_name] = record

                response = self.client.get(
                    f"{self.endpoint(endpoint_name)}{record.pk}/"
                )
                self.assertEqual(response.status_code, 200, response.data)

                response = self.client.post(
                    f"{self.endpoint(endpoint_name)}?patient={patient.pk}",
                    self.payload(endpoint_name),
                    format="json",
                )
                self.assertEqual(response.status_code, 201, response.data)

        return records

    def assert_all_resources_revoked(self, patient, records):
        """Vérifie que les anciennes données et les nouvelles créations sont refusées."""
        for endpoint_name, record in records.items():
            with self.subTest(endpoint=endpoint_name):
                response = self.client.get(
                    f"{self.endpoint(endpoint_name)}{record.pk}/"
                )
                self.assertEqual(response.status_code, 404, response.data)

                response = self.client.post(
                    f"{self.endpoint(endpoint_name)}?patient={patient.pk}",
                    self.payload(endpoint_name),
                    format="json",
                )
                self.assertEqual(response.status_code, 404, response.data)

                # Le refus d'accès ne doit pas supprimer les données.
                self.assertTrue(
                    type(record).objects.filter(pk=record.pk).exists()
                )

    def test_deleted_last_appointment_revokes_all_resource_access(self):
        records = self.create_and_check_all_resources(self.patient)

        self.appointment.delete()

        self.assert_all_resources_revoked(self.patient, records)

    def test_deleted_last_treatment_revokes_all_resource_access(self):
        patient = self.create_patient("Traitement supprimé")
        treatment = self.create_treatment(patient)

        records = self.create_and_check_all_resources(patient)

        treatment.delete()

        self.assert_all_resources_revoked(patient, records)

    def test_active_treatment_alone_preserves_all_resource_access(self):
        patient = self.create_patient("Traitement seul actif")
        treatment = self.create_treatment(patient)

        # Ce patient n'a aucun rendez-vous : le traitement est son seul lien.
        records = self.create_and_check_all_resources(patient)

        self.assertEqual(treatment.is_deleted, False)
        self.assertEqual(len(records), 3)

    def test_active_appointment_alone_preserves_all_resource_access(self):
        treatment = self.create_treatment(self.patient)
        treatment.delete()

        # Le rendez-vous initial reste actif : c'est le seul lien.
        records = self.create_and_check_all_resources(self.patient)

        self.assertEqual(treatment.is_deleted, True)
        self.assertEqual(len(records), 3)

    def test_receptionist_is_still_forbidden(self):
        self.client.force_authenticate(self.receptionist)

        for endpoint_name in ("medical-histories", "allergies"):
            with self.subTest(endpoint=endpoint_name):
                response = self.client.get(self.endpoint(endpoint_name))
                self.assertEqual(response.status_code, 403)

                response = self.client.post(
                    f"{self.endpoint(endpoint_name)}?patient={self.patient.pk}",
                    self.payload(endpoint_name),
                    format="json",
                )
                self.assertEqual(response.status_code, 403)
