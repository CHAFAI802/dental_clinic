from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from accounts.permissions import CanManageStock, IsAdministrator
from .models import InventoryCategory, Supplier, InventoryFamily, Unit, InventoryItem, StockEntry, StockExit, StockExitAllocation, StockAlert, StockDestruction,StockDestructionLine
from .serializers import InventoryCategorySerializer, SupplierSerializer, InventoryFamilySerializer, UnitSerializer, InventoryItemSerializer, StockEntrySerializer, StockExitSerializer, StockExitAllocationSerializer, StockAlertSerializer, StockDestructionSerializer, StockDestructionLineSerializer
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status

class InventoryCategoryViewset(viewsets.ModelViewSet):
    serializer_class = InventoryCategorySerializer
    permission_classes = [IsAdministrator]
    def get_queryset(self):
        return InventoryCategory.objects.all()

class SupplierViewset(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    permission_classes = [IsAdministrator]
    def get_queryset(self):
        return Supplier.objects.all()

class InventoryFamilyViewset(viewsets.ModelViewSet):
    serializer_class = InventoryFamilySerializer
    permission_classes = [IsAdministrator]
    def get_queryset(self):
        return InventoryFamily.objects.all()

class UnitViewset(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [IsAdministrator]
    def get_queryset(self):
        return Unit.objects.all()

class InventoryItemViewset(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    permission_classes = [CanManageStock]
    def get_queryset(self):
        return InventoryItem.objects.all()

class StockEntryViewset(viewsets.ModelViewSet):
    serializer_class = StockEntrySerializer
    permission_classes = [CanManageStock]

    def get_queryset(self):
        return StockEntry.objects.all()

    def perform_create(self, serializer):
        serializer.save(received_by=self.request.user)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages)

class StockExitViewset(viewsets.ModelViewSet):
    serializer_class = StockExitSerializer
    permission_classes = [CanManageStock]

    def get_queryset(self):
        return StockExit.objects.all()

    def perform_create(self, serializer):
        try:
            serializer.save()
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages)

class StockExitAllocationViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockExitAllocationSerializer
    permission_classes = [CanManageStock]
    def get_queryset(self):
        return StockExitAllocation.objects.all()

class StockAlertViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockAlertSerializer
    permission_classes = [CanManageStock]
    def get_queryset(self):
        return StockAlert.objects.all()

class StockDestructionViewset(viewsets.ModelViewSet):
    serializer_class = StockDestructionSerializer
    permission_classes = [CanManageStock]

    def get_queryset(self):
        return StockDestruction.objects.all()

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ValidationError as exc:
            raise serializers.ValidationError(
                exc.messages
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="apply",
        permission_classes=[CanManageStock],
    )
    def apply(self, request, pk=None):
        """Exécute une destruction enregistrée.

        Appelle la méthode métier `StockDestruction.apply()` qui :
          - vérifie les lots et quantités en provenance de la base ;
          - déduit les quantités des lots et du stock physique ;
          - passe le document à COMPLETED ;
          - synchronise les alertes.

        La méthode est propre à l'action : le serializer et la vue ne
        reproduisent pas la logique métier, qui reste dans le modèle.
        """
        try:
            instance = self.get_object()

            # Les droits d'écriture sont déjà vérifiés par le
            # permission_classes de la vue, mais l'action apply est
            # déclarée avec la même classe pour la sécurité défense.
            result = instance.apply()

            return Response(
                {
                    "id": result["destruction_id"],
                    "status": result["status"],
                    "destroyed_quantities": result["destroyed_quantities"],
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(
                exc.messages if isinstance(exc.messages, list) else [exc.messages],
                status=status.HTTP_400_BAD_REQUEST,
            )

class StockDestructionLineViewset(viewsets.ModelViewSet):
    serializer_class = StockDestructionLineSerializer
    permission_classes = [CanManageStock]
    def get_queryset(self):
        return StockDestructionLine.objects.all()
