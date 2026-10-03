from rest_framework import serializers
from .models import TreatmentPlan


class TreatmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentPlan
        fields = [
            "id", "created_at", "updated_at", "is_deleted", "deleted_at",
            "status", "total_estimated_cost", "total_approved_cost",
            "patient_approved_at", "notes", "version", "patient", "created_by",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "is_deleted", "deleted_at",
            "total_estimated_cost", "total_approved_cost",
            "patient_approved_at", "created_by",
        ]
