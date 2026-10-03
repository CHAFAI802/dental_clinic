from rest_framework import serializers
from .models import Document, DocumentTemplate


class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = [
            "id", "created_at", "updated_at", "name", "description", "content",
            "variables", "default_sections", "is_active",
        ]


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
