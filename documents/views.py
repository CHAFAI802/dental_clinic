from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as APIValidationError
from rest_framework.response import Response
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

from accounts.models import User
from appointments.models import Appointment
from documents.models import Document, DocumentTemplate
from treatments.models import Treatment

from accounts.permissions import IsAdministrator, IsDentist, IsStaffMember
from .serializers import DocumentSerializer, DocumentTemplateSerializer
from .services.docx import file_sha256, inspect_docx_template


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
    queryset = DocumentTemplate.objects.all()
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsAdministrator]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [(IsAdministrator | IsDentist)()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = DocumentTemplate.objects.all()
        if getattr(self.request.user, "role", None) == User.Role.DENTIST:
            queryset = queryset.filter(is_active=True, is_approved=True)
        return queryset

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdministrator],
    )
    def approve(self, request, *args, **kwargs):
        template = self.get_object()
        if (
            not template.file
            or not template.file.name.lower().endswith(".docx")
        ):
            raise APIValidationError(
                {"file": "Un fichier Word DOCX est requis avant approbation."}
            )

        try:
            with template.file.open("rb") as source:
                inspect_docx_template(source.read())
            approved_file_sha256 = file_sha256(template.file)
        except DjangoValidationError as error:
            raise APIValidationError({"file": error.messages}) from error
        except FileNotFoundError as error:
            raise APIValidationError(
                {"file": "Le fichier DOCX associé au modèle est indisponible."}
            ) from error

        template.is_approved = True
        template.approved_by = request.user
        template.approved_at = timezone.now()
        template.approved_file_sha256 = approved_file_sha256
        template.save(
            update_fields=(
                "is_approved",
                "approved_by",
                "approved_at",
                "approved_file_sha256",
                "updated_at",
            )
        )
        return Response(self.get_serializer(template).data)
