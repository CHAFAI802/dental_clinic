from rest_framework import serializers
from .models import Odontogram, Tooth


class ToothSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tooth
        fields = [
            "id", "created_at", "updated_at", "is_deleted", "deleted_at",
            "number", "type", "quadrant", "status", "surface_status",
            "remarks", "odontogram",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "is_deleted", "deleted_at",
        ]


class OdontogramSerializer(serializers.ModelSerializer):
    teeth = ToothSerializer(many=True, read_only=True)

    class Meta:
        model = Odontogram
        fields = [
            "id", "teeth", "created_at", "updated_at", "is_deleted", "deleted_at",
            "version", "notes", "patient", "created_by",
        ]
        read_only_fields = [
        "id",
        "teeth",
        "created_at",
        "updated_at",
        "is_deleted",
        "deleted_at",
        "created_by",
        ]
