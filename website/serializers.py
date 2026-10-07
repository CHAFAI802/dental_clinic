from rest_framework import serializers

from .models import SiteImage, SiteSettings, WorkingHours


def _merge_json_objects(existing, updates):
    merged = existing.copy()
    for key, value in updates.items():
        if isinstance(existing.get(key), dict) and isinstance(value, dict):
            merged[key] = _merge_json_objects(existing[key], value)
        else:
            merged[key] = value
    return merged


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = ["id", "config", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if (
            self.partial
            and "config" in validated_data
            and isinstance(instance.config, dict)
            and isinstance(validated_data["config"], dict)
        ):
            validated_data["config"] = _merge_json_objects(
                instance.config,
                validated_data["config"],
            )
        return super().update(instance, validated_data)


class SiteImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SiteImage
        fields = ["id", "key", "image", "url", "alt", "created_at", "updated_at"]
        read_only_fields = ["id", "url", "created_at", "updated_at"]

    def get_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        if request is not None:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


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