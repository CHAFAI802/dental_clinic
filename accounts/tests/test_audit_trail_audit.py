from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import AuditLog, User
from patients.models import Patient


class AuditTrailIntegrityTests(APITestCase):
    """PHASE B10 characterization tests.

    These tests document the current audit-trail integrity guarantees and gaps.
    """

    def setUp(self):
        self.superadmin = User.objects.create_superuser(
            email="superadmin_audit@example.com",
            password="StrongPassword123!",
            first_name="Super",
            last_name="Audit",
        )
        self.superadmin_token = Token.objects.create(user=self.superadmin)

    def test_audit_log_api_is_read_only(self):
        """AuditLog API rejects create, update, partial update, and delete."""

        log = AuditLog.objects.create(
            action="audit_probe",
            model_name="Probe",
            context="original",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.superadmin_token.key}"
        )

        create_response = self.client.post(
            "/api/audit-logs/",
            {
                "action": "api_create",
                "model_name": "Probe",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 405)

        put_response = self.client.put(
            f"/api/audit-logs/{log.pk}/",
            {
                "action": "api_update",
                "model_name": "Probe",
            },
            format="json",
        )
        self.assertEqual(put_response.status_code, 405)

        patch_response = self.client.patch(
            f"/api/audit-logs/{log.pk}/",
            {"context": "api_mutated"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 405)

        delete_response = self.client.delete(
            f"/api/audit-logs/{log.pk}/"
        )
        self.assertEqual(delete_response.status_code, 405)

    def test_audit_log_instance_can_be_mutated_via_orm(self):
        """AuditLog instance save permits mutation."""

        log = AuditLog.objects.create(
            action="original_action",
            model_name="Probe",
            context="original",
        )

        log.context = "mutated"
        log.save()
        log.refresh_from_db()

        self.assertEqual(log.context, "mutated")

    def test_audit_log_queryset_update_can_mutate_existing_log(self):
        """QuerySet.update permits bulk mutation of audit records."""

        log = AuditLog.objects.create(
            action="original_action",
            model_name="Probe",
        )

        updated = AuditLog.objects.filter(pk=log.pk).update(
            action="bulk_mutated"
        )

        log.refresh_from_db()

        self.assertEqual(updated, 1)
        self.assertEqual(log.action, "bulk_mutated")

    def test_audit_log_can_be_deleted_via_orm(self):
        """AuditLog ORM deletion physically removes the audit record."""

        log = AuditLog.objects.create(
            action="delete_probe",
            model_name="Probe",
        )
        pk = log.pk

        log.delete()

        self.assertFalse(AuditLog.objects.filter(pk=pk).exists())

    def test_business_operation_does_not_automatically_create_audit_log(self):
        """Creating a business object does not automatically emit AuditLog."""

        before = AuditLog.objects.count()

        Patient.objects.create(
            first_name="Audit",
            last_name="Patient",
            birthdate="1990-01-01",
            gender="other",
            phone="+213333333333",
        )

        after = AuditLog.objects.count()

        self.assertEqual(after, before)
