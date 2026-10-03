from rest_framework import serializers

from .models import WorkingHours


class WorkingHoursSerializer(serializers.ModelSerializer):
    practitioner_name = serializers.CharField(
        source="practitioner.get_full_name",
        read_only=True,
    )
    weekday_display = serializers.CharField(
        source="get_weekday_display",
        read_only=True,
    )

    class Meta:
        model = WorkingHours
        fields = [
            "id",
            "practitioner",
            "practitioner_name",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "practitioner_name",
            "weekday_display",
        ]