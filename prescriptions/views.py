from rest_framework import viewsets
from .models import Prescription, PrescriptionTemplate
from accounts.permissions import IsStaffMember
from .serializers import PrescriptionSerializer, PrescriptionTemplateSerializer


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsStaffMember]


class PrescriptionTemplateViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionTemplate.objects.filter(is_active=True)
    serializer_class = PrescriptionTemplateSerializer
    permission_classes = [IsStaffMember]
