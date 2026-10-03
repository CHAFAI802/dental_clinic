from rest_framework import mixins, viewsets

from accounts.permissions import IsDentist, IsReceptionOrAdmin
from .models import Patient,MedicalHistory
from .serializers import (
    PractitionerPatientSerializer,
    ReceptionistPatientSerializer,
    MedicalHistorySerializer,
)


class ReceptionistPatientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Patient.objects.filter(is_deleted=False)
    serializer_class = ReceptionistPatientSerializer
    permission_classes = [IsReceptionOrAdmin]


class PractitionerPatientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Patient.objects.filter(is_deleted=False)
    serializer_class = PractitionerPatientSerializer
    permission_classes = [IsDentist]

class MedicalHistoryViewSet(viewsets.ModelViewSet):
    queryset=MedicalHistory.objects.filter()
    serializer_class = MedicalHistorySerializer
    permission_classes =[IsDentist]
