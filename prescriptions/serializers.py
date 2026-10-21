from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.models import User
from documents.models import DocumentTemplate
from documents.services.docx import inspect_docx_template
from patients.models import Medication, Patient
from .models import Prescription, PrescriptionTemplate


class PrescriptionGenerationSerializer(serializers.Serializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    document_template = serializers.PrimaryKeyRelatedField(
        queryset=DocumentTemplate.objects.filter(
            is_active=True,
            is_approved=True,
        )
    )
    medications = serializers.PrimaryKeyRelatedField(
        queryset=Medication.objects.all(),
        many=True,
        required=False,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        patient = attrs["patient"]
        user = self.context["request"].user
        for medication in attrs.get("medications", []):
            if (
                medication.patient_id != patient.pk
                or medication.prescribed_by_id != user.pk
            ):
                raise serializers.ValidationError(
                    "Chaque médicament doit appartenir au patient et avoir été "
                    "prescrit par le dentiste connecté."
                )
        return attrs


class PrescriptionTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionTemplate
        fields = [
            "id", "created_at", "updated_at", "name", "description", "content",
            "variables", "is_active",
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = [
            "id", "created_at", "updated_at", "filled_data", "generated_at",
            "status", "pdf_file", "generated_file", "notes", "patient", "dentist",
            "template", "document_template",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at", "generated_at",
            "document_template",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        if (
            self.instance is None
            and request is not None
            and request.user.role == User.Role.DENTIST
        ):
            raise serializers.ValidationError(
                "Les dentistes doivent générer leurs ordonnances à partir "
                "d’un modèle DOCX approuvé."
            )

        template = attrs.get(
            "template",
            getattr(self.instance, "template", None),
        )
        document_template = attrs.get(
            "document_template",
            getattr(self.instance, "document_template", None),
        )
        if bool(template) == bool(document_template):
            raise serializers.ValidationError(
                "Une ordonnance doit utiliser un seul type de modèle."
            )
        return attrs

    def validate_generated_file(self, value):
        if value:
            if not value.name.lower().endswith(".docx"):
                raise serializers.ValidationError(
                    "Seuls les fichiers DOCX sont autorisés."
                )
            try:
                inspect_docx_template(value.read())
            except DjangoValidationError as error:
                raise serializers.ValidationError(error.messages) from error
            finally:
                value.seek(0)
        return value
