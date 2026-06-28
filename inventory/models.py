from django.db import models
from dental_clinic.common import TimestampedModel


class InventoryCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('inventory.InventoryCategory', null=True, blank=True, related_name='children', on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class InventoryItem(TimestampedModel):
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey('inventory.InventoryCategory', null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=64)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StockEntry(TimestampedModel):
    item = models.ForeignKey('inventory.InventoryItem', related_name='entries', on_delete=models.CASCADE)
    supplier = models.ForeignKey('inventory.Supplier', null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2)
    received_at = models.DateTimeField()
    batch_number = models.CharField(max_length=128, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    received_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    comments = models.TextField(blank=True)


class StockExit(TimestampedModel):
    item = models.ForeignKey('inventory.InventoryItem', related_name='exits', on_delete=models.CASCADE)
    treatment = models.ForeignKey('treatments.Treatment', null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2)
    exited_at = models.DateTimeField()
    used_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    usage_type = models.CharField(max_length=64)
    comments = models.TextField(blank=True)


class StockAdjustment(TimestampedModel):
    item = models.ForeignKey('inventory.InventoryItem', related_name='adjustments', on_delete=models.CASCADE)
    adjusted_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    adjusted_at = models.DateTimeField()
    quantity_before = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_after = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()


class StockAlert(TimestampedModel):
    item = models.ForeignKey('inventory.InventoryItem', related_name='alerts', on_delete=models.CASCADE)
    triggered_at = models.DateTimeField()
    threshold = models.DecimalField(max_digits=12, decimal_places=2)
    current_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)


class InventoryTransaction(TimestampedModel):
    item = models.ForeignKey('inventory.InventoryItem', related_name='transactions', on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=64)
    reference_id = models.UUIDField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
