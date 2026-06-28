from rest_framework import viewsets
from .models import Patient
from accounts.permissions import IsClinicalStaff
from .serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.filter(is_deleted=False)
    serializer_class = PatientSerializer
    permission_classes = [IsClinicalStaff]
