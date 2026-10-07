from rest_framework import mixins, viewsets

from accounts.permissions import IsDentist, IsReceptionOrAdmin
from .models import Allergy, Patient,MedicalHistory
from .serializers import (
    AllergySerializer,
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

    def get_queryset(self):
        return self.queryset.filter(
            appointments__practitioner=self.request.user,
            appointments__is_deleted=False,
        ).distinct()

class MedicalHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalHistorySerializer
    permission_classes = [IsDentist]

    def get_queryset(self):
        queryset = MedicalHistory.objects.all()
        patient_id = self.request.query_params.get("patient")

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset

    def perform_create(self, serializer):
        patient_id = self.request.query_params.get("patient")
        patient = Patient.objects.get(id=patient_id)
        serializer.save(patient=patient)


class AllergyViewSet(viewsets.ModelViewSet):
    serializer_class = AllergySerializer
    permission_classes = [IsDentist]

    def get_queryset(self):
        queryset = Allergy.objects.all()
        patient_id = self.request.query_params.get("patient")

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset

    def perform_create(self, serializer):
        patient_id = self.request.query_params.get("patient")
        patient = Patient.objects.get(id=patient_id)
        serializer.save(patient=patient)