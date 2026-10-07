from decimal import Decimal

from rest_framework import serializers
from .models import Treatment
from django.core.exceptions import ValidationError as DjangoValidationError
from treatments.services.treatment_creation import TreatmentCreationService


class TreatmentSerializer(serializers.ModelSerializer):
    quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        write_only=True,
    )

    class Meta:
        model = Treatment
        fields = [
            "id", "created_at", "updated_at", "is_deleted", "deleted_at",
            "code", "label", "description", "start_at",
            "end_at", "duration_minutes",
            "notes", "patient", "dentist", "assistant", "appointment",
            "treatment_plan", "prestation", "quantity",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "code",
            "label",
            "patient",
            "dentist",
        ]

    def create(self, validated_data):
        try:
            return TreatmentCreationService.create(
                appointment=validated_data["appointment"],
                prestation=validated_data["prestation"],
                dentist=self.context["request"].user,
                quantity=validated_data["quantity"],
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

    def update(self, instance, validated_data):
        validated_data.pop("quantity", None)

        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)