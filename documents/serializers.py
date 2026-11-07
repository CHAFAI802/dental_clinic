import json

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Document, DocumentTemplate
from .services.dynamic_document import (
    get_builtin_catalog,
    parse_definition,
    validate_template,
)
from .services.docx import inspect_docx_template


class DocumentStructureConfigField(serializers.JSONField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as error:
                raise serializers.ValidationError(
                    "La configuration doit être un JSON valide."
                ) from error
        return super().to_internal_value(data)


class DocumentTemplateSerializer(serializers.ModelSerializer):
    structure_config = DocumentStructureConfigField(required=False)

    class Meta:
        model = DocumentTemplate
        fields = [
            "id",
            "name",
            "description",
            "file",
            "structure_config",
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
            config = self._effective_structure_config()
            content = value.read()
            if config:
                self._validate_dynamic_template(content, config)
            else:
                inspect_docx_template(content)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        finally:
            value.seek(0)

        return value

    def _effective_structure_config(self):
        raw_config = self.initial_data.get("structure_config")
        if raw_config is None:
            return getattr(self.instance, "structure_config", {})
        if isinstance(raw_config, str):
            try:
                return json.loads(raw_config)
            except json.JSONDecodeError as error:
                raise serializers.ValidationError(
                    {"structure_config": "La configuration doit être un JSON valide."}
                ) from error
        return raw_config

    @staticmethod
    def _validate_dynamic_template(content, config):
        definition = parse_definition(config)
        catalog = get_builtin_catalog(definition.root_model, definition.root_name)
        validate_template(content, definition, catalog)

    def validate(self, attrs):
        config = attrs.get(
            "structure_config",
            getattr(self.instance, "structure_config", {}),
        )
        if config:
            try:
                definition = parse_definition(config)
                catalog = get_builtin_catalog(
                    definition.root_model,
                    definition.root_name,
                )
                uploaded_file = attrs.get("file")
                if uploaded_file is not None:
                    uploaded_file.seek(0)
                    validate_template(uploaded_file.read(), definition, catalog)
                    uploaded_file.seek(0)
                elif self.instance is not None and self.instance.file:
                    with self.instance.file.open("rb") as template_file:
                        validate_template(
                            template_file.read(),
                            definition,
                            catalog,
                        )
            except DjangoValidationError as error:
                raise serializers.ValidationError(
                    {"structure_config": error.messages}
                ) from error
            except FileNotFoundError as error:
                raise serializers.ValidationError(
                    {"file": "Le fichier DOCX associé au modèle est indisponible."}
                ) from error
        return attrs



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
