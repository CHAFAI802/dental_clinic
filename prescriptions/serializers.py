from rest_framework import serializers
from .models import Prescription, PrescriptionTemplate


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
            "status", "pdf_file", "notes", "patient", "dentist", "template",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at", "generated_at",
        ]
