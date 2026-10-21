from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InventoryCategoryViewset,
    StockDestructionLineViewset,
    SupplierViewset,
    InventoryFamilyViewset,
    UnitViewset,
    InventoryItemViewset,
    StockEntryViewset,
    StockExitViewset,
    StockExitAllocationViewset,
    StockAlertViewset,
    StockDestructionViewset,
)

router = DefaultRouter()
router.register('inventory-categories', InventoryCategoryViewset, basename='inventory-category')
router.register('suppliers', SupplierViewset, basename='supplier')
router.register('inventory-families', InventoryFamilyViewset, basename='inventory-family')
router.register('units', UnitViewset, basename='unit')
router.register('inventory-items', InventoryItemViewset, basename='inventory-item')
router.register('stock-entries', StockEntryViewset, basename='stock-entry')
router.register('stock-exits', StockExitViewset, basename='stock-exit')
router.register('stock-exit-allocations', StockExitAllocationViewset, basename='stock-exit-allocation')
router.register('stock-alerts', StockAlertViewset, basename='stock-alert')
router.register('stock-destructions', StockDestructionViewset, basename='stock-destruction')
router.register('stock-destruction-lines', StockDestructionLineViewset, basename='stock-destruction-line')

urlpatterns = [
    path('', include(router.urls)),
    path('stock-destructions/<int:pk>/apply/', StockDestructionViewset.as_view({'post': 'apply'}), name='stock-destruction-apply'),
]
