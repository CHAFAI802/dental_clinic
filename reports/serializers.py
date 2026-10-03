from rest_framework import serializers
from .models import ReportDefinition


class ReportDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportDefinition
        fields = [
            "id", "created_at", "updated_at", "name", "description",
            "query_type", "parameters", "is_public", "template",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
