from rest_framework import serializers

from patients.models import Patient
from .models import Appointment, Room
from django.core.exceptions import ValidationError as DjangoValidationError 
from appointments.services.appointmentstatus import AppointmentRequestService

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            "id",
            "name",
            "description",
            "location",
            "capacity",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_capacity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Room capacity must be greater than or equal to 1."
            )
        return value

class AppointmentSerializer(serializers.ModelSerializer):
    patient_code = serializers.CharField(
        source="patient.patient_code",
        read_only=True,
    )
    patient_name = serializers.SerializerMethodField()
    practitioner_name = serializers.SerializerMethodField()

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}".strip()

    def get_practitioner_name(self, obj):
        return f"{obj.practitioner.first_name} {obj.practitioner.last_name}".strip()
    class Meta:
        model = Appointment
        fields = [
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "start_at",
            "end_at",
            "duration_minutes",
            "status",
            "reason",
            "notes",
            "confirmed_at",
            "cancelled_at",
            "cancel_reason",
            "source",
            "patient",
            "practitioner",
            "patient_code",
            "patient_name",
            "practitioner_name",
            "assistant",
            "room",
            "created_by",
            "confirmed_by",
            "cancelled_by",
            "completed_at",
            "completed_by",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "confirmed_at",
            "cancelled_at",
            "completed_at",
            "created_by",
            "confirmed_by",
            "cancelled_by",
            "completed_by",
            "duration_minutes",
            "status",
        ]

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

    def update(self, instance, validated_data):
        try:
            request = self.context.get("request")
            changed_by = request.user if request and request.user.is_authenticated else None
            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save(changed_by=changed_by)
            return instance
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

class AppointmentRequestSerializer(serializers.Serializer):
    first_request = serializers.BooleanField()
    patient_code = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    birthdate = serializers.DateField(required=False)
    gender = serializers.CharField(required=False, allow_blank=True)
    practitioner = serializers.PrimaryKeyRelatedField(
        queryset=Appointment._meta.get_field(
            "practitioner"
        ).remote_field.model.objects.all()
    )
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get("first_request"):
            patient_code = attrs.get("patient_code", "").strip()

            if not patient_code:
                raise serializers.ValidationError(
                    {"patient_code": "Veuillez fournir votre code patient."}
                )

            try:
                patient = Patient.objects.get(patient_code=patient_code)
            except Patient.DoesNotExist:
                raise serializers.ValidationError(
                    {"patient_code": "Code patient invalide."}
                )

            attrs["first_name"] = patient.first_name
            attrs["last_name"] = patient.last_name
            attrs["email"] = patient.email
            attrs["phone"] = patient.phone
            attrs["birthdate"] = patient.birthdate
            attrs["gender"] = patient.gender

        return attrs

    def create(self, validated_data):
        try:
            return AppointmentRequestService.submit(**validated_data)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError({"patient": str(exc)})
        except ValueError as exc:
            raise serializers.ValidationError({"patient": str(exc)})

class AvailableSlotSerializer(serializers.Serializer):
    practitioner = serializers.IntegerField()
    practitioner_name = serializers.CharField()
    date = serializers.DateField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
