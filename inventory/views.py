from rest_framework import viewsets
from .models import InventoryItem
from accounts.permissions import IsAccountantOrAdmin
from .serializers import InventoryItemSerializer


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.filter(is_active=True)
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAccountantOrAdmin]
