from rest_framework import viewsets
from .models import Treatment
from accounts.permissions import IsClinicalStaff
from .serializers import TreatmentSerializer


class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.filter(is_deleted=False)
    serializer_class = TreatmentSerializer
    permission_classes = [IsClinicalStaff]
