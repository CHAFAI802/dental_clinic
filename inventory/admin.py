from django.contrib import admin
from .models import InventoryCategory, InventoryItem, StockEntry

admin.site.register(InventoryCategory)
admin.site.register(InventoryItem)
admin.site.register(StockEntry)
