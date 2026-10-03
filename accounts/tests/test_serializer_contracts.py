from django.test import TestCase
from accounts.serializers import (
    AuditLogSerializer,
    LoginSerializer,
    UserSerializer,
)
from accounts.models import User
from appointments.serializers import AppointmentSerializer, RoomSerializer
from billing.serializers import InvoiceSerializer, PaymentSerializer
from documents.serializers import DocumentSerializer, DocumentTemplateSerializer
from imaging.serializers import ImagingInstanceSerializer, ImagingStudySerializer
from inventory.serializers import InventoryItemSerializer
from notifications.serializers import (
    NotificationSerializer,
    NotificationTemplateSerializer,
)
from odontogram.serializers import OdontogramSerializer, ToothSerializer
from patients.serializers import PatientSerializer
from prescriptions.serializers import (
    PrescriptionSerializer,
    PrescriptionTemplateSerializer,
)
from reports.serializers import ReportDefinitionSerializer
from staff.serializers import StaffProfileSerializer
from treatment_plans.serializers import TreatmentPlanSerializer
from treatments.serializers import TreatmentSerializer


class SerializerContractTests(TestCase):
    """
    SER-001 regression tests.

    These tests verify the explicit serializer ownership contract:
    - server-controlled fields are read-only;
    - client-controlled fields remain writable.

    Business validation of complete payloads is covered by the
    resource-specific API tests.
    """

    EXPECTED_READ_ONLY_FIELDS = {
        UserSerializer: {
            "id",
        },

        AuditLogSerializer: {
            "id",
            "created_at",
            "updated_at",
            "action",
            "model_name",
            "object_id",
            "changes",
            "context",
            "ip_address",
            "user",
        },

        PatientSerializer: {
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        },

        AppointmentSerializer: {
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "confirmed_at",
            "cancelled_at",
            "created_by",
            "confirmed_by",
            "cancelled_by",
            "duration_minutes",
            "completed_at",
            "completed_by",
        },

        RoomSerializer: {
            "id",
        },

        OdontogramSerializer: {
            "id",
            "teeth",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "created_by",
        },

        ToothSerializer: {
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
        },

        TreatmentSerializer: {
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "total_price",
        },

        TreatmentPlanSerializer: {
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "total_estimated_cost",
            "total_approved_cost",
            "patient_approved_at",
            "created_by",
        },

        PrescriptionSerializer: {
            "id",
            "created_at",
            "updated_at",
            "generated_at",
        },

        PrescriptionTemplateSerializer: {
            "id",
            "created_at",
            "updated_at",
        },

        InvoiceSerializer: {
            "id",
            "created_at",
            "updated_at",
            "total_amount",
            "tax_amount",
            "paid_amount",
            "balance_due",
            "created_by",
        },

        PaymentSerializer: {
            "id",
            "created_at",
            "updated_at",
            "paid_by",
        },

        DocumentSerializer: {
            "id",
            "created_at",
            "updated_at",
            "signed_at",
            "created_by",
        },

        DocumentTemplateSerializer: {
            "id",
            "created_at",
            "updated_at",
        },

        InventoryItemSerializer: {
            "id",
            "created_at",
            "updated_at",
        },

        StaffProfileSerializer: {
            "id",
            "created_at",
            "updated_at",
        },

        ReportDefinitionSerializer: {
            "id",
            "created_at",
            "updated_at",
        },

        NotificationTemplateSerializer: {
            "id",
            "created_at",
            "updated_at",
        },

        NotificationSerializer: {
            "id",
            "created_at",
            "updated_at",
            "sent_at",
        },

        ImagingStudySerializer: {
            "id",
            "created_at",
            "updated_at",
        },

        ImagingInstanceSerializer: {
            "id",
            "thumbnail",
        },
    }

    def test_serializers_use_explicit_field_contracts(self):
        for serializer_class in self.EXPECTED_READ_ONLY_FIELDS:
            with self.subTest(serializer=serializer_class.__name__):
                meta = serializer_class.Meta

                self.assertIsInstance(
                    meta.fields,
                    (list, tuple),
                    msg=(
                        f"{serializer_class.__name__}.Meta.fields must be "
                        "an explicit list or tuple"
                    ),
                )

                self.assertNotEqual(
                    meta.fields,
                    "__all__",
                    msg=(
                        f"{serializer_class.__name__} must not use "
                        'fields = "__all__"'
                    ),
                )

    def test_read_only_field_contract(self):
        for serializer_class, expected in self.EXPECTED_READ_ONLY_FIELDS.items():
            with self.subTest(serializer=serializer_class.__name__):
                serializer = serializer_class()

                actual = {
                    name
                    for name, field in serializer.fields.items()
                    if field.read_only
                }

                self.assertEqual(actual, expected)

    def test_server_owned_attribution_and_workflow_fields_are_excluded_from_input(self):
        server_owned_fields = {
            AppointmentSerializer: {
                "created_by",
                "confirmed_by",
                "cancelled_by",
                "confirmed_at",
                "cancelled_at",
                "completed_at",
                "completed_by",
            },
            TreatmentPlanSerializer: {
                "created_by",
            },
            DocumentSerializer: {
                "created_by",
            },
            PaymentSerializer: {
                "paid_by",
            },
        }

        for serializer_class, field_names in server_owned_fields.items():
            for field_name in field_names:
                with self.subTest(
                    serializer=serializer_class.__name__,
                    field=field_name,
                ):
                    serializer = serializer_class(
                        data={field_name: "client-supplied"}
                    )
                    serializer.is_valid()

                    self.assertNotIn(
                        field_name,
                        serializer.validated_data,
                        msg=(
                            f"{serializer_class.__name__}.{field_name} must not be "
                            "accepted from client input"
                        ),
                    )

    def test_non_read_only_fields_remain_writable(self):
        for serializer_class, expected_read_only in self.EXPECTED_READ_ONLY_FIELDS.items():
            with self.subTest(serializer=serializer_class.__name__):
                serializer = serializer_class()

                for field_name, field in serializer.fields.items():
                    if field_name in expected_read_only:
                        continue

                    self.assertFalse(
                        field.read_only,
                        msg=(
                            f"{serializer_class.__name__}.{field_name} "
                            "must remain writable"
                        ),
                    )

    def test_user_password_is_required_on_create(self):
        serializer = UserSerializer()

        self.assertTrue(serializer.fields["password"].required)


    def test_user_password_is_optional_on_update(self):
        user = User.objects.create_user(
            email="serializer@example.com",
            password="StrongPassword123!",
            first_name="Serializer",
            last_name="Test",
            role=User.Role.ASSISTANT,
        )
        serializer = UserSerializer(instance=user)

        self.assertFalse(serializer.fields["password"].required)

    def test_login_serializer_requires_email_and_password(self):
        serializer = LoginSerializer()

        self.assertTrue(serializer.fields["email"].required)
        self.assertTrue(serializer.fields["password"].required)

    def test_login_serializer_normalizes_email(self):
        serializer = LoginSerializer(
            data={
                "email": "  USER@EXAMPLE.COM  ",
                "password": "StrongPassword123!",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["email"],
            "user@example.com",
        )

    def test_login_serializer_rejects_invalid_email(self):
        serializer = LoginSerializer(
            data={
                "email": "not-an-email",
                "password": "StrongPassword123!",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_login_serializer_password_is_write_only(self):
        serializer = LoginSerializer()

        self.assertTrue(serializer.fields["password"].write_only)
