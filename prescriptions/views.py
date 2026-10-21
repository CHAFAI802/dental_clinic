from pathlib import Path

from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Prescription, PrescriptionTemplate
from accounts.permissions import IsDentist, IsStaffMember
from appointments.models import Appointment
from documents.models import DocumentTemplate
from documents.services.docx import (
    file_sha256,
    inspect_docx_template,
    render_prescription_docx,
)
from treatments.models import Treatment
from .serializers import (
    PrescriptionGenerationSerializer,
    PrescriptionSerializer,
    PrescriptionTemplateSerializer,
)


class PrescriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PrescriptionSerializer
    permission_classes = [IsDentist]
    def get_queryset(self):
        return Prescription.objects.filter(dentist=self.request.user)

    @action(
        detail=False,
        methods=["post"],
        url_path="generate-from-document-template",
        permission_classes=[IsDentist],
    )
    def generate_from_document_template(self, request):
        input_serializer = PrescriptionGenerationSerializer(
            data=request.data,
            context={"request": request},
        )
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        patient = data["patient"]
        has_appointment = Appointment.objects.filter(
            practitioner=request.user,
            patient=patient,
        ).exists()
        has_treatment = Treatment.objects.filter(
            dentist=request.user,
            patient=patient,
        ).exists()
        if not (has_appointment or has_treatment):
            raise PermissionDenied(
                "Vous ne pouvez générer une ordonnance que pour un patient "
                "qui vous est rattaché."
            )

        with transaction.atomic():
            template = DocumentTemplate.objects.select_for_update().filter(
                pk=data["document_template"].pk,
                is_active=True,
                is_approved=True,
            ).first()
            if template is None:
                raise ValidationError(
                    {"document_template": "Le modèle n’est plus approuvé ou actif."}
                )
            if not template.file:
                raise ValidationError(
                    {"document_template": "Le modèle approuvé ne contient pas de fichier."}
                )
            try:
                with template.file.open("rb") as source:
                    source_content = source.read()
                source_hash = file_sha256(template.file)
            except (FileNotFoundError, OSError) as error:
                raise ValidationError(
                    {"document_template": "Le fichier source du modèle est indisponible."}
                ) from error
            if not source_content:
                raise ValidationError(
                    {"document_template": "Le fichier source du modèle est vide."}
                )
            if source_hash != template.approved_file_sha256:
                raise ValidationError(
                    {"document_template": "Le fichier source a changé depuis son approbation."}
                )
            try:
                template_info = inspect_docx_template(source_content)
            except DjangoValidationError as error:
                # Fichier illisible ou variables inconnues : erreur de
                # validation métier, jamais une erreur serveur 500.
                raise ValidationError(
                    {"document_template": error.messages}
                ) from error

            medications = list(data.get("medications", []))
            if template_info.expects_medications and not medications:
                raise ValidationError(
                    {"medications": "Sélectionnez au moins un médicament pour ce modèle."}
                )
            if medications and not template_info.supports_medications:
                raise ValidationError(
                    {"document_template": "Ce modèle ne contient aucune zone de prescription."}
                )
            generated_at = timezone.now()
            prescription = Prescription.objects.create(
                patient=patient,
                dentist=request.user,
                document_template=template,
                filled_data={
                    "medications": [
                        _medication_snapshot(medication)
                        for medication in medications
                    ]
                },
                generated_at=generated_at,
                status=Prescription.Status.GENERATED,
                notes=data.get("notes", ""),
            )
            try:
                generated_content = render_prescription_docx(
                    source_content,
                    patient=patient,
                    dentist=request.user,
                    generated_at=generated_at,
                    notes=prescription.notes,
                    medications=medications,
                )
            except DjangoValidationError as error:
                raise ValidationError({"document_template": error.messages}) from error
            suffix = Path(template.file.name).suffix.lower()
            prescription.generated_file.save(
                f"prescription-{prescription.pk}{suffix}",
                ContentFile(generated_content),
                save=False,
            )
            prescription.save(update_fields=("generated_file", "updated_at"))

        response_serializer = PrescriptionSerializer(
            prescription,
            context=self.get_serializer_context(),
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


def _medication_snapshot(medication):
    return {
        "id": medication.pk,
        "name": medication.name,
        "dosage": medication.dosage,
        "frequency": medication.frequency,
        "route": medication.route,
        "start_date": medication.start_date.isoformat(),
        "end_date": (
            medication.end_date.isoformat()
            if medication.end_date is not None
            else None
        ),
        "notes": medication.notes,
    }


class PrescriptionTemplateViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionTemplate.objects.filter(is_active=True)
    serializer_class = PrescriptionTemplateSerializer
    permission_classes = [IsDentist]
