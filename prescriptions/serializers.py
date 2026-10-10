from rest_framework import serializers
from django.urls import reverse

from documents.docx import DocxTemplateError, validate_docx_template
from .models import Prescription, PrescriptionTemplate
from .permissions import CanAccessPrescriptionDocument


class PrescriptionTemplateSerializer(serializers.ModelSerializer):
    docx_file = serializers.FileField(
        required=False,
        allow_empty_file=False,
        use_url=False,
        write_only=True,
    )

    class Meta:
        model = PrescriptionTemplate
        fields = [
            "id", "created_at", "updated_at", "name", "description", "content",
            "variables", "docx_file", "is_active",
        ]

    def validate(self, attrs):
        template_file = attrs.get('docx_file')
        if template_file is None and self.instance:
            template_file = self.instance.docx_file
        variables = attrs.get(
            'variables',
            self.instance.variables if self.instance else [],
        )

        if template_file:
            is_stored_field = hasattr(template_file, 'field')
            if is_stored_field:
                template_file.open('rb')
            try:
                template_file.seek(0)
                template_bytes = template_file.read()
                template_file.seek(0)
            finally:
                if is_stored_field:
                    template_file.close()
            try:
                validate_docx_template(template_bytes, variables)
            except DocxTemplateError as exc:
                raise serializers.ValidationError({'docx_file': str(exc)}) from exc

        return attrs


class PrescriptionSerializer(serializers.ModelSerializer):
    docx_download_url = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            "id", "created_at", "updated_at", "filled_data", "generated_at",
            "status", "pdf_file", "docx_download_url", "notes", "patient", "dentist", "template",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at", "generated_at",
        ]

    def get_docx_download_url(self, obj):
        if not obj.generated_docx:
            return None
        request = self.context.get('request')
        if request is None or not CanAccessPrescriptionDocument().has_object_permission(
            request,
            self.context.get('view'),
            obj,
        ):
            return None
        url = reverse('prescription-download-docx', kwargs={'pk': obj.pk})
        return request.build_absolute_uri(url)
