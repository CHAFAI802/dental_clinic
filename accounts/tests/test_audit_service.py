from django.test import TestCase

from accounts.models import AuditLog, User
from accounts.services.audit import log_audit


class AuditServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="audit@example.com",
            password="StrongPassword123!",
            first_name="Audit",
            last_name="Tester",
            role=User.Role.SUPER_ADMIN,
        )

    def test_log_audit_creates_audit_log(self):
        log = log_audit(
            user=self.user,
            action="user.created",
            model_name="User",
            object_id=self.user.pk,
            changes={
                "email": {
                    "old": None,
                    "new": "audit@example.com",
                },
            },
            context={"source": "api"},
            ip_address="127.0.0.1",
        )

        self.assertIsInstance(log, AuditLog)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "user.created")
        self.assertEqual(log.model_name, "User")
        self.assertEqual(log.object_id, str(self.user.pk))
        self.assertEqual(
            log.changes["email"]["new"],
            "audit@example.com",
        )
        self.assertEqual(log.context["source"], "api")
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertTrue(
            AuditLog.objects.filter(pk=log.pk).exists()
        )

    def test_log_audit_uses_empty_defaults(self):
        log = log_audit(
            action="user.updated",
            model_name="User",
        )

        self.assertIsNone(log.user)
        self.assertIsNone(log.object_id)
        self.assertEqual(log.changes, {})
        self.assertEqual(log.context, {})
        self.assertIsNone(log.ip_address)