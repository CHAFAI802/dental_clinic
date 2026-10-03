from rest_framework import serializers
from .models import NotificationTemplate, Notification


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = [
            "id", "created_at", "updated_at", "name", "description", "channel",
            "subject", "body", "variables", "is_active",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "created_at", "updated_at", "channel", "payload", "sent_at",
            "status", "error_message", "recipient_user", "recipient_patient",
            "template",
        ]
        read_only_fields = [
        "id",
        "created_at",
        "updated_at",
        "sent_at",
        ]
