from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Document, DocumentTemplate
from .services.docx import inspect_docx_template

class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = [
            "id",
            "name",
            "description",
            "file",
            "is_active",
            "is_approved",
            "approved_by",
            "approved_at",
            "approved_file_sha256",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_approved",
            "approved_by",
            "approved_at",
            "approved_file_sha256",
            "created_at",
            "updated_at",
        ]

    def to_internal_value(self, data):
        if not self.partial and "is_active" not in data:
            data = data.copy()
            data["is_active"] = True
        return super().to_internal_value(data)

    def validate_file(self, value):
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


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id", "created_at", "updated_at", "document_type", "title", "content",
            "signed_at", "status", "pdf_file", "patient", "created_by", "template",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "signed_at", "created_by",
        ]
