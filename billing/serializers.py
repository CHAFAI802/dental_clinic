from rest_framework import fields, serializers
from .models import Invoice, Payment, Estimate, CreditNote,InvoiceLine, PaymentMethod,Prestation,PrestationCategory,PrestationTarif

from django.core.exceptions import ValidationError as DjangoValidationError


class EstimateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estimate
        fields = [
            "id",
            "patient",
            "created_by",
            "validated_by",
            "valid_until",
            "total_amount",
            "tax_amount",
            "notes",
            "reference_number",
            "related_treatment_plan",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "validated_by",
        ]

    def update(self, instance, validated_data):
        validated_data.pop("patient", None)
        validated_data.pop("reference_number", None)

        return super().update(instance, validated_data)

class PrestationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrestationCategory
        fields = [
            'id',
            'created_at',
            'updated_at',
            'name',
            'code',
            'is_active',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


class PrestationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prestation
        fields = [
            'id',
            'created_at',
            'updated_at',
            'category',
            'code',
            'label',
            'description',
            'is_active',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


class PrestationTarifSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrestationTarif
        fields = [
            'id',
            'created_at',
            'updated_at',
            'prestation',
            'amount',
            'tax_rate',
            'effective_from',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


class InvoiceLineSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    tax_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = InvoiceLine
        fields = [
            'id',
            'invoice',
            'treatment',
            'prestation',
            'subtotal',
            'unit_price',
            'tax_rate',
            'tax_amount',
            'total',
            'description',
            'quantity',
            'updated_at',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'subtotal',
            'unit_price',
            'tax_rate',
            'tax_amount',
            'total',
            'created_at',
        ]

    def validate(self, attrs):
        if self.instance is not None:
            invoice = attrs.get('invoice', self.instance.invoice)
            treatment = attrs.get('treatment', self.instance.treatment)
            prestation = attrs.get('prestation', self.instance.prestation)
        else:
            # L'invoice est optionnelle à la création : si elle est
            # omise, InvoiceLine.save() la déduit du rendez-vous du
            # traitement (regroupement par Appointment).
            invoice = attrs.get('invoice')
            treatment = attrs['treatment']
            prestation = attrs['prestation']

        errors = {}

        if treatment.prestation_id != prestation.id:
            errors['prestation'] = (
                "La prestation de la ligne doit correspondre "
                "à la prestation du traitement."
            )

        if (
            invoice is not None
            and treatment.patient_id != invoice.patient_id
        ):
            errors['treatment'] = (
                "Le patient du traitement doit correspondre "
                "au patient de la facture."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as error:
            detail = (
                error.message_dict
                if hasattr(error, "message_dict")
                else error.messages
            )
            raise serializers.ValidationError(detail) from error

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as error:
            detail = (
                error.message_dict
                if hasattr(error, "message_dict")
                else error.messages
            )
            raise serializers.ValidationError(detail) from error


class InvoiceSerializer(serializers.ModelSerializer):
    created_by_last_name = serializers.CharField(
        source='created_by.last_name',
        read_only=True,
    )

    created_by_first_name = serializers.CharField(
        source='created_by.first_name',
        read_only=True,
    )

    class Meta:
        model = Invoice
        fields = [
            'id',
            'patient',
            'created_by',
            'created_by_last_name',
            'created_by_first_name',
            'issued_at',
            'due_date',
            'status',
            'subtotal',
            'tax_amount',
            'total_amount',
            'credit_amount',
            'paid_amount',
            'balance_due',
            'reference_number',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'patient',
            'issued_at',
            'reference_number',
            'created_by',
            'created_by_last_name',
            'created_by_first_name',
            'status',
            'subtotal',
            'tax_amount',
            'total_amount',
            'credit_amount',
            'paid_amount',
            'balance_due',
            'created_at',
            'updated_at',
        ]


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = [
            'id',
            'invoice',
            'patient',
            'paid_by',
            'payment_at',
            'amount',
            'method',
            'reference',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'updated_at',
        ]


class CreditNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNote
        fields = [
            'id',
            'invoice',
            'created_by',
            'issued_at',
            'amount',
            'reason',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'status',
            'created_at',
            'updated_at',
        ]


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            'id',
            'name',
            'provider',
            'details',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]