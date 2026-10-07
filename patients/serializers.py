from rest_framework import serializers

from .models import Patient,MedicalHistory, Allergy


class ReceptionistPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "first_name",
            "last_name",
            "middle_name",
            "birthdate",
            "gender",
            "email",
            "phone",
            "secondary_phone",
            "address",
            "city",
            "postal_code",
            "country",
            "marital_status",
            "profession",
            "employer",
            "language",
            "preferred_contact_method",
            "document_type",
            "document_number",
            "social_security_number",
            "insurance_provider",
            "insurance_policy_number",
            "insurance_group",
            "insurance_valid_until",
            "emergency_contact_name",
            "emergency_contact_relation",
            "emergency_contact_phone",
            "emergency_contact_email",
            "patient_code",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
            "deleted_at",
            "patient_code",
        ]


class PractitionerPatientSerializer(serializers.ModelSerializer):
    allergies_summary = serializers.SerializerMethodField()

    def get_allergies_summary(self, obj):
        return obj.allergies.exists()

    class Meta:
        model = Patient
        fields = [
            "id",
            "created_at",
            "updated_at",
            "patient_code",
            "first_name",
            "last_name",
            "middle_name",
            "birthdate",
            "gender",
            "email",
            "phone",
            "blood_type",
            "weight_kg",
            "height_cm",
            "smoker",
            "pregnant",
            "allergies_summary",
            "medical_history_summary",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "patient_code",
            "first_name",
            "last_name",
            "middle_name",
            "birthdate",
            "gender",
            "email",
            "phone",
            "allergies_summary",
        ]

class MedicalHistorySerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MedicalHistory
        fields = [
            'id',
            'patient',
            'condition',
            'diagnosis_date',
            'status',
            'notes',
            'is_chronic',
            'is_acute',
        ]
        read_only_fields = ['patient']

class AllergySerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Allergy
        fields = [
            'id',
            'patient',
            'substance',
            'reaction',
            'severity',
            'notes',
        ]
        read_only_fields = ['patient']
