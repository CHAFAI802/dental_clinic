from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import InventoryCategory, Supplier, InventoryFamily, Unit, InventoryItem, StockEntry, StockExit, StockExitAllocation, StockAlert, StockDestruction,StockDestructionLine


class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = [
            "id",
            "code",
            "name",
            "description",
            "parent",
        ]
        read_only_fields = ["id"]

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "contact_name",
            "phone",
            "email",
            "address",
            "notes",
        ]
        read_only_fields = ["id"]

class InventoryFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryFamily
        fields = [
            "id",
            "category",
            "name",
            "code",
            "is_active",
            "next_sku_number",
        ]
        read_only_fields = [
            "id",
            "next_sku_number",
            ]

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "name",
            "symbol",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

class InventoryItemSerializer(serializers.ModelSerializer):
    family = serializers.PrimaryKeyRelatedField(
        queryset=InventoryFamily.objects.all(),
        required=True,
    )

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "sku",
            "name",
            "family",
            "description",
            "unit",
            "reorder_point",
            "reorder_quantity",
            "expiration_alert_days",
            "stock_quantity",
            "is_perishable",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "sku",
            "stock_quantity",
        ]

class StockEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockEntry
        fields = [
            "id",
            "item",
            "supplier",
            "quantity",
            "remaining_quantity",
            "unit_cost",
            "total_cost",
            "received_at",
            "batch_number",
            "expiration_date",
            "received_by",
            "comments",
        ]
        read_only_fields = [
            "id",
            "remaining_quantity",
            "received_by",
            "total_cost",
        ]

    def validate(self, data):
        quantity = data.get(
            "quantity",
            getattr(self.instance, "quantity", None),
        )
        unit_cost = data.get(
            "unit_cost",
            getattr(self.instance, "unit_cost", None),
        )

        errors = {}

        if quantity is not None and quantity <= 0:
            errors["quantity"] = (
                "La quantité reçue doit être strictement positive."
            )

        if unit_cost is not None and unit_cost < 0:
            errors["unit_cost"] = (
                "Le coût unitaire ne peut pas être négatif."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        stock_entry = StockEntry(**validated_data)
        stock_entry.apply()
        return stock_entry

    def update(self, instance, validated_data):
        raise serializers.ValidationError(
            "Une entrée de stock enregistrée ne peut pas être modifiée."
        )


class StockExitSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockExit
        fields = [
            "id",
            "item",
            "treatment",
            "quantity",
            "exited_at",
            "used_by",
            "usage_type",
            "comments",
            "selection_mode",
            "manual_allocations",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        allocations = validated_data.pop("manual_allocations", None)
        stock_exit = StockExit(**validated_data)
        stock_exit.manual_allocations = allocations
        stock_exit.apply()
        return stock_exit

    def update(self, instance, validated_data):
        raise serializers.ValidationError(
            "Une sortie de stock enregistrée ne peut pas être modifiée."
        )

class StockExitAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockExitAllocation
        fields = [
            "id",
            "stock_exit",
            "stock_entry",
            "quantity",
        ]
        read_only_fields = fields

class StockAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAlert
        fields = [
            "id",
            "item",
            "alert_type",
            "current_quantity",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "current_quantity",
            "created_at",
        ]

class StockDestructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockDestruction
        fields = [
            "id",
            "destroyed_by",
            "destroyed_at",
            "reason",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "destroyed_by",
            "created_at",
            "updated_at",
            "status",
        ]

class StockDestructionLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockDestructionLine
        fields = [
            "id",
            "destruction",
            "item",
            "stock_entry",
            "quantity",
            "stock_alert",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]
