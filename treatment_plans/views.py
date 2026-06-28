from rest_framework import viewsets
from .models import TreatmentPlan
from accounts.permissions import IsClinicalStaff
from .serializers import TreatmentPlanSerializer


class TreatmentPlanViewSet(viewsets.ModelViewSet):
    queryset = TreatmentPlan.objects.filter(is_deleted=False)
    serializer_class = TreatmentPlanSerializer
    permission_classes = [IsClinicalStaff]
