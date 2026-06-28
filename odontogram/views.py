from rest_framework import viewsets
from .models import Odontogram, Tooth
from accounts.permissions import IsClinicalStaff
from .serializers import OdontogramSerializer, ToothSerializer


class OdontogramViewSet(viewsets.ModelViewSet):
    queryset = Odontogram.objects.filter(is_deleted=False)
    serializer_class = OdontogramSerializer
    permission_classes = [IsClinicalStaff]


class ToothViewSet(viewsets.ModelViewSet):
    queryset = Tooth.objects.filter(is_deleted=False)
    serializer_class = ToothSerializer
    permission_classes = [IsClinicalStaff]
