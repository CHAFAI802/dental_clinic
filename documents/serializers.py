from rest_framework import serializers
from .models import Document, DocumentTemplate, DocumentTemplateVersion, DocumentType


class DocumentTypeSerializer(serializers.ModelSerializer):
    code = serializers.SlugField(max_length=80, required=False)

    class Meta:
        model = DocumentType
        fields = [
            'id', 'code', 'name', 'description',
            'is_active', 'created_at', 'updated_at',
        ]


class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = [
            "id", "created_at", "updated_at", "code", "document_type", "name",
            "description", "content", "variables", "default_sections", "is_active",
            "created_by",
        ]


class DocumentTemplateVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplateVersion
        fields = [
            'id', 'template', 'version_number', 'status', 'schema_version',
            'definition', 'published_at', 'created_by', 'created_at', 'updated_at',
        ]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id", "created_at", "updated_at", "document_type", "title", "content",
            "signed_at", "status", "pdf_file", "patient", "created_by", "template",
            "template_version",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "signed_at", "created_by",
        ]
