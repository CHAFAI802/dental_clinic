from rest_framework import serializers
from .models import ImagingStudy, ImagingInstance


class ImagingStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingStudy
        fields = [
            "id", "created_at", "updated_at", "study_type", "study_date",
            "description", "status", "source_system", "patient", "practitioner",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ImagingInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingInstance
        fields = [
            "id", "instance_number", "file", "file_type", "study_date",
            "notes", "thumbnail", "series",
        ]
        read_only_fields = ["id", "thumbnail"]
