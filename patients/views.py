from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError

from accounts.permissions import IsDentist, IsReceptionOrAdmin
from .models import Allergy, Patient,MedicalHistory, Medication
from .serializers import (
    AllergySerializer,
    MedicationSerializer,
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

def get_linked_patients_for_dentist(user):
    """
    Patients accessibles au dentiste :
    au moins un rendez-vous non supprimé OU un traitement non supprimé.
    """
    return Patient.objects.filter(
        Q(
            appointments__practitioner=user,
            appointments__is_deleted=False,
        )
        | Q(
            treatments__dentist=user,
            treatments__is_deleted=False,
        )
    ).distinct()


class MedicalHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalHistorySerializer
    permission_classes = [IsDentist]

    def get_linked_patients(self):
        return get_linked_patients_for_dentist(self.request.user)

    def get_queryset(self):
        queryset = MedicalHistory.objects.filter(
            patient__in=self.get_linked_patients()
        )
        patient_id = self.request.query_params.get("patient")

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset

    def perform_create(self, serializer):
        patient_id = self.request.query_params.get("patient")
        if not patient_id:
            raise ValidationError(
                {"patient": "Le paramètre patient est requis ( ?patient=<id> )."}
            )

        patient = get_object_or_404(
            self.get_linked_patients(),
            pk=patient_id,
        )
        serializer.save(patient=patient)


class AllergyViewSet(viewsets.ModelViewSet):
    serializer_class = AllergySerializer
    permission_classes = [IsDentist]

    def get_linked_patients(self):
        return get_linked_patients_for_dentist(self.request.user)

    def get_queryset(self):
        queryset = Allergy.objects.filter(
            patient__in=self.get_linked_patients()
        )
        patient_id = self.request.query_params.get("patient")

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset

    def perform_create(self, serializer):
        patient_id = self.request.query_params.get("patient")
        if not patient_id:
            raise ValidationError(
                {"patient": "Le paramètre patient est requis ( ?patient=<id> )."}
            )

        patient = get_object_or_404(
            self.get_linked_patients(),
            pk=patient_id,
        )
        serializer.save(patient=patient)


class MedicationViewSet(viewsets.ModelViewSet):
    """Traitements médicamenteux destinés aux ordonnances (module médecin).

    Contrat : `POST|GET /api/medications/?patient=<id>` puis ces mêmes
    identifiants dans `POST /api/prescriptions/generate-from-document-template/`.

    Sécurité alignée sur celle de la génération d'ordonnance
    (prescriptions/views.py) : un dentiste ne voit et ne crée des
    médicaments que pour un patient qui lui est rattaché par un rendez-vous
    ou un traitement ; `prescribed_by` est toujours le dentiste connecté.
    """
    serializer_class = MedicationSerializer
    permission_classes = [IsDentist]

    def get_linked_patients(self):
        return get_linked_patients_for_dentist(self.request.user)

    def get_queryset(self):
        queryset = Medication.objects.all()
        patient_id = self.request.query_params.get("patient")

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)

        return queryset.filter(patient__in=self.get_linked_patients())

    def perform_create(self, serializer):
        patient_id = self.request.query_params.get("patient")
        if not patient_id:
            raise ValidationError(
                {"patient": "Le paramètre patient est requis ( ?patient=<id> )."}
            )
        # Patient hors rattachement => 404 : aucune existence divulguée.
        patient = get_object_or_404(self.get_linked_patients(), pk=patient_id)
        serializer.save(patient=patient, prescribed_by=self.request.user)