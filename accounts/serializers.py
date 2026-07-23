from django.db import transaction
from rest_framework import serializers

from .models import AuditLog, User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate_email(self, value):
        return value.strip().lower()


class UserSerializer(serializers.ModelSerializer):
    # Password is mandatory on creation, optional on update.
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone",
            "role",
            "timezone",
            "language",
            "is_active",
        ]
        read_only_fields = ["id"]

    def get_fields(self):
        fields = super().get_fields()

        # Password is required when creating a user,
        # optional when updating an existing one.
        fields["password"].required = self.instance is None

        return fields

    def validate_email(self, value):
        return value.strip().lower()

    def validate_password(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "Le mot de passe est obligatoire."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(
            password=password,
            **validated_data,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "user",
            "action",
            "model_name",
            "object_id",
            "changes",
            "context",
            "ip_address",
            "sensitive",
        ]