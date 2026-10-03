from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import InventoryItem


class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = [
            "id", "created_at", "updated_at", "sku", "name", "description",
            "unit", "reorder_point", "reorder_quantity", "stock_quantity",
            "cost_price", "sale_price", "is_active", "category",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
