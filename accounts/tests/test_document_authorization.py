from accounts.services.authentication import create_authentication_session
from rest_framework.test import APITestCase

from accounts.models import User
from appointments.models import Appointment
from documents.models import Document
from patients.models import Patient
from treatments.models import Treatment


class DocumentAuthorizationTests(APITestCase):
    """AUTH-001 regression tests: document scoping by role.

    - SUPER_ADMIN / ADMINISTRATOR see all documents.
    - Dentist sees documents of their own patients (via Appointment / Treatment).
    - Assistant sees documents of their own patients (via Appointment / Treatment).
    - Receptionist has no scope-defining relation in the current model.
    - Accountant has no scope-defining relation in the current model.
    - Direct /documents/{id}/ access also respects the scope.
    """

    def setUp(self):
        # --- users ---
        self.superadmin = User.objects.create_superuser(
            email="sa_docscope@example.com",
            password="StrongPassword123!",
            first_name="SA",
            last_name="DocScope",
            role=User.Role.SUPER_ADMIN,
        )
        self.admin = User.objects.create_user(
            email="admin_docscope@example.com",
            password="StrongPassword123!",
            first_name="Admin",
            last_name="DocScope",
            role=User.Role.ADMINISTRATOR,
        )
        self.dentist1 = User.objects.create_user(
            email="dentist1_docscope@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="One",
            role=User.Role.DENTIST,
        )
        self.dentist2 = User.objects.create_user(
            email="dentist2_docscope@example.com",
            password="StrongPassword123!",
            first_name="Dentist",
            last_name="Two",
            role=User.Role.DENTIST,
        )
        self.assistant1 = User.objects.create_user(
            email="assistant1_docscope@example.com",
            password="StrongPassword123!",
            first_name="Assistant",
            last_name="One",
            role=User.Role.ASSISTANT,
        )
        self.assistant2 = User.objects.create_user(
            email="assistant2_docscope@example.com",
            password="StrongPassword123!",
            first_name="Assistant",
            last_name="Two",
            role=User.Role.ASSISTANT,
        )
        self.receptionist = User.objects.create_user(
            email="recep_docscope@example.com",
            password="StrongPassword123!",
            first_name="Recep",
            last_name="DocScope",
            role=User.Role.RECEPTIONIST,
        )
        self.accountant = User.objects.create_user(
            email="acct_docscope@example.com",
            password="StrongPassword123!",
            first_name="Acct",
            last_name="DocScope",
            role=User.Role.ACCOUNTANT,
        )

        # --- tokens ---
        self.superadmin_session, self.superadmin_token = create_authentication_session(self.superadmin)
        self.admin_session, self.admin_token = create_authentication_session(self.admin)
        self.dentist1_session, self.dentist1_token = create_authentication_session(self.dentist1)
        self.dentist2_session, self.dentist2_token = create_authentication_session(self.dentist2)
        self.assistant1_session, self.assistant1_token = create_authentication_session(self.assistant1)
        self.assistant2_session, self.assistant2_token = create_authentication_session(self.assistant2)
        self.receptionist_session, self.receptionist_token = create_authentication_session(self.receptionist)
        self.accountant_session, self.accountant_token = create_authentication_session(self.accountant)

        # --- patients ---
        self.patient_d1 = Patient.objects.create(
            first_name="P_D1",
            last_name="DocScope",
            birthdate="1990-01-01",
            gender="other",
            phone="+213111111111",
        )
        self.patient_d2 = Patient.objects.create(
            first_name="P_D2",
            last_name="DocScope",
            birthdate="1990-01-02",
            gender="other",
            phone="+213222222222",
        )
        self.patient_no_relation = Patient.objects.create(
            first_name="P_NR",
            last_name="DocScope",
            birthdate="1990-01-03",
            gender="other",
            phone="+213333333333",
        )

        # --- appointment linking dentist1 & assistant1 to patient_d1 ---
        Appointment.objects.create(
            patient=self.patient_d1,
            practitioner=self.dentist1,
            assistant=self.assistant1,
            start_at="2035-06-01T09:00:00Z",
            end_at="2035-06-01T09:30:00Z",
            status=Appointment.Status.PENDING,
        )

        # --- treatment linking dentist1 & assistant1 to patient_d1 ---
        Treatment.objects.create(
            patient=self.patient_d1,
            dentist=self.dentist1,
            assistant=self.assistant1,
            status="planned",
            category="consultation",
            code="C001",
            label="Consultation",
        )

        # --- appointment linking dentist2 & assistant2 to patient_d2 ---
        Appointment.objects.create(
            patient=self.patient_d2,
            practitioner=self.dentist2,
            assistant=self.assistant2,
            start_at="2035-06-01T10:00:00Z",
            end_at="2035-06-01T10:30:00Z",
            status=Appointment.Status.PENDING,
        )

        # --- documents ---
        self.doc_d1 = Document.objects.create(
            patient=self.patient_d1,
            created_by=self.dentist1,
            document_type="consent",
            title="Document D1",
            content="For patient_d1",
            status="draft",
        )
        self.doc_d2 = Document.objects.create(
            patient=self.patient_d2,
            created_by=self.dentist2,
            document_type="consent",
            title="Document D2",
            content="For patient_d2",
            status="draft",
        )
        self.doc_no_rel = Document.objects.create(
            patient=self.patient_no_relation,
            created_by=self.superadmin,
            document_type="other",
            title="Document No Relation",
            content="For patient without relations",
            status="draft",
        )

    # ----------------------------------------------------------------
    # Case: Admin voit tous les documents
    # ----------------------------------------------------------------
    def test_superadmin_see_all_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.superadmin_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        ids = [d["id"] for d in resp.data]
        self.assertIn(self.doc_d1.id, ids)
        self.assertIn(self.doc_d2.id, ids)
        self.assertIn(self.doc_no_rel.id, ids)

    def test_administrator_see_all_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.admin_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        ids = [d["id"] for d in resp.data]
        self.assertIn(self.doc_d1.id, ids)
        self.assertIn(self.doc_d2.id, ids)
        self.assertIn(self.doc_no_rel.id, ids)

    # ----------------------------------------------------------------
    # Case: Dentiste voit uniquement ses patients
    # ----------------------------------------------------------------
    def test_dentist_sees_own_patient_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist1_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        ids = [d["id"] for d in resp.data]
        self.assertIn(self.doc_d1.id, ids)

    # ----------------------------------------------------------------
    # Case: Dentiste ne voit pas les patients d'un autre dentiste
    # ----------------------------------------------------------------
    def test_dentist_does_not_see_other_dentist_patient_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist1_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        ids = [d["id"] for d in resp.data]
        self.assertNotIn(self.doc_d2.id, ids)

    def test_dentist_does_not_see_unlinked_patient_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist1_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        ids = [d["id"] for d in resp.data]
        self.assertNotIn(self.doc_no_rel.id, ids)

    # ----------------------------------------------------------------
    # Case: Assistant voit uniquement son périmètre existant
    # ----------------------------------------------------------------
    def test_assistant_sees_own_patient_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.assistant1_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        ids = [d["id"] for d in resp.data]
        self.assertIn(self.doc_d1.id, ids)

    def test_assistant_does_not_see_other_assistant_patient_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.assistant1_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        ids = [d["id"] for d in resp.data]
        self.assertNotIn(self.doc_d2.id, ids)

    # ----------------------------------------------------------------
    # Case: Réceptionniste — périmètre documentaire vide par défaut
    # ----------------------------------------------------------------
    def test_receptionist_sees_no_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)

    # ----------------------------------------------------------------
    # Case: Comptable — périmètre documentaire vide par défaut
    # ----------------------------------------------------------------
    def test_accountant_sees_no_documents(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )
        resp = self.client.get("/api/documents/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)

    # ----------------------------------------------------------------
    # Case: Accès direct /documents/{id}/ respecte également le scope
    # ----------------------------------------------------------------
    def test_dentist_direct_access_own_document_succeeds(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist1_token}"
        )
        resp = self.client.get(f"/api/documents/{self.doc_d1.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], self.doc_d1.id)

    def test_dentist_direct_access_other_dentist_document_refused(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.dentist1_token}"
        )
        resp = self.client.get(f"/api/documents/{self.doc_d2.id}/")
        self.assertEqual(resp.status_code, 404)

    def test_receptionist_direct_access_any_document_refused(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.receptionist_token}"
        )
        resp = self.client.get(f"/api/documents/{self.doc_d1.id}/")
        self.assertEqual(resp.status_code, 404)

    def test_accountant_direct_access_any_document_refused(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.accountant_token}"
        )
        resp = self.client.get(f"/api/documents/{self.doc_d1.id}/")
        self.assertEqual(resp.status_code, 404)
