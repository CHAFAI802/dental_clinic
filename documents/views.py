from rest_framework import viewsets

from accounts.models import User
from appointments.models import Appointment
from documents.models import Document, DocumentTemplate, DocumentTemplateVersion, DocumentType
from treatments.models import Treatment

from accounts.permissions import IsStaffMember
from .serializers import (
    DocumentSerializer,
    DocumentTemplateSerializer,
    DocumentTemplateVersionSerializer,
    DocumentTypeSerializer,
)


class DocumentTypeViewSet(viewsets.ModelViewSet):
    queryset = DocumentType.objects.filter(is_active=True)
    serializer_class = DocumentTypeSerializer
    permission_classes = [IsStaffMember]


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsStaffMember]

    def get_queryset(self):
        user = self.request.user

        # SUPER_ADMIN and ADMINISTRATOR have full access
        if user.role in (User.Role.SUPER_ADMIN, User.Role.ADMINISTRATOR):
            return Document.objects.all()

        # Dentist: documents of patients linked via Appointment or Treatment
        if user.role == User.Role.DENTIST:
            patient_ids = set()
            patient_ids.update(
                Appointment.objects.filter(practitioner=user)
                .values_list("patient_id", flat=True)
            )
            patient_ids.update(
                Treatment.objects.filter(dentist=user)
                .values_list("patient_id", flat=True)
            )
            return Document.objects.filter(patient_id__in=patient_ids)

        # Assistant: documents of patients linked via Appointment or Treatment
        if user.role == User.Role.ASSISTANT:
            patient_ids = set()
            patient_ids.update(
                Appointment.objects.filter(assistant=user)
                .values_list("patient_id", flat=True)
            )
            patient_ids.update(
                Treatment.objects.filter(assistant=user)
                .values_list("patient_id", flat=True)
            )
            return Document.objects.filter(patient_id__in=patient_ids)

        # Fallback: restrict to empty queryset when no role-specific scope exists
        return Document.objects.none()


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    queryset = DocumentTemplate.objects.filter(is_active=True)
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsStaffMember]


class DocumentTemplateVersionViewSet(viewsets.ModelViewSet):
    queryset = DocumentTemplateVersion.objects.all()
    serializer_class = DocumentTemplateVersionSerializer
    permission_classes = [IsStaffMember]
