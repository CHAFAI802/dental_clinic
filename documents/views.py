from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError as APIValidationError,
)
from rest_framework.response import Response
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from accounts.models import User
from appointments.models import Appointment
from billing.models import Invoice, Payment
from documents.models import Document, DocumentTemplate
from documents.services.dynamic_document import (
    generate_document,
    get_builtin_catalog,
    get_builtin_catalogs,
    get_builtin_exposures,
    parse_definition,
    queryset_hints,
)
from documents.services.dynamic_document.validator import validate_template
from inventory.models import InventoryFamily
from treatments.models import Treatment

from accounts.permissions import IsAdministrator, IsDentist, IsStaffMember
from .serializers import DocumentSerializer, DocumentTemplateSerializer
from .services.docx import file_sha256, inspect_docx_template

_DOCUMENT_GENERATION_ROLES = {
    "invoice": {
        User.Role.ACCOUNTANT,
        User.Role.RECEPTIONIST,
        User.Role.ADMINISTRATOR,
        User.Role.SUPER_ADMIN,
    },
    "payment": {
        User.Role.ACCOUNTANT,
        User.Role.ADMINISTRATOR,
        User.Role.SUPER_ADMIN,
    },
    "inventory": {
        User.Role.ACCOUNTANT,
        User.Role.RECEPTIONIST,
        User.Role.ADMINISTRATOR,
        User.Role.SUPER_ADMIN,
    },
}

_DOCUMENT_ROOT_MODELS = {
    "invoice": ("billing.Invoice", Invoice),
    "payment": ("billing.Payment", Payment),
    "inventory": ("inventory.InventoryFamily", InventoryFamily),
}


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
        if self.action in ("available", "generate"):
            return [IsStaffMember()]
        if self.action in ("list", "retrieve"):
            return [(IsAdministrator | IsDentist)()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = DocumentTemplate.objects.all()
        if getattr(self.request.user, "role", None) == User.Role.DENTIST:
            queryset = queryset.filter(is_active=True, is_approved=True)
        return queryset

    @staticmethod
    def _validate_template_content(template, content):
        if template.structure_config:
            definition = parse_definition(template.structure_config)
            catalog = get_builtin_catalog(definition.root_model, definition.root_name)
            validated = validate_template(content, definition, catalog)
            return {
                "variables": list(
                    dict.fromkeys(item.name for item in validated.scan.variables)
                ),
                "marker_pairs": [
                    {
                        "index": pair.index,
                        "zone": next(
                            (
                                zone.name
                                for zone in definition.zones
                                if zone.marker_pair == pair.index
                            ),
                            None,
                        ),
                    }
                    for pair in validated.scan.marker_pairs
                ],
                "document_type": definition.document_type,
                "valid": True,
            }

        inspected = inspect_docx_template(content)
        return {
            "variables": list(inspected.variables),
            "marker_pairs": [],
            "document_type": None,
            "valid": True,
        }

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAdministrator],
    )
    def catalog(self, request, *args, **kwargs):
        return Response({"catalogs": get_builtin_catalogs()})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdministrator],
    )
    def validate(self, request, *args, **kwargs):
        template = self.get_object()
        if not template.file:
            raise APIValidationError({"file": "Un fichier Word DOCX est requis."})
        try:
            with template.file.open("rb") as source:
                result = self._validate_template_content(template, source.read())
        except DjangoValidationError as error:
            raise APIValidationError({"file": error.messages}) from error
        except FileNotFoundError as error:
            raise APIValidationError(
                {"file": "Le fichier DOCX associé au modèle est indisponible."}
            ) from error
        result["zones"] = [
            {
                "name": zone["name"],
                "type": zone["type"],
                "collection": zone["collection"],
                "marker_pair": zone["marker_pair"],
            }
            for zone in template.structure_config.get("zones", [])
        ]
        return Response(result)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsStaffMember],
    )
    def available(self, request, *args, **kwargs):
        document_type = request.query_params.get("document_type")
        role = request.user.role
        if document_type not in _DOCUMENT_GENERATION_ROLES:
            raise APIValidationError(
                {"document_type": "Type documentaire non pris en charge."}
            )
        if role not in _DOCUMENT_GENERATION_ROLES[document_type]:
            raise PermissionDenied(
                "Vous ne pouvez pas utiliser ce type de document."
            )

        templates = DocumentTemplate.objects.filter(
            is_active=True,
            is_approved=True,
            structure_config__document_type=document_type,
        )
        return Response(self.get_serializer(templates, many=True).data)

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
                self._validate_template_content(template, source.read())
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

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsStaffMember],
    )
    def generate(self, request, *args, **kwargs):
        template = self.get_object()
        if not template.is_active or not template.is_approved:
            raise APIValidationError(
                "Seuls les modèles actifs et approuvés peuvent être utilisés."
            )

        try:
            definition = parse_definition(template.structure_config)
        except DjangoValidationError as error:
            raise APIValidationError({"structure_config": error.messages}) from error

        if (
            definition.document_type not in _DOCUMENT_GENERATION_ROLES
            or request.user.role
            not in _DOCUMENT_GENERATION_ROLES[definition.document_type]
        ):
            raise PermissionDenied(
                "Vous ne pouvez pas générer ce type de document."
            )

        expected = _DOCUMENT_ROOT_MODELS.get(definition.document_type)
        if expected is None or definition.root_model != expected[0]:
            raise APIValidationError(
                {"structure_config": "Le type et le modèle racine ne correspondent pas."}
            )

        object_id = serializers.IntegerField(min_value=1).run_validation(
            request.data.get("object_id")
        )
        exposure = get_builtin_exposures()[definition.root_model]
        select_related, prefetch_related = queryset_hints(exposure)
        queryset = expected[1].objects.all()
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        try:
            instance = queryset.get(pk=object_id)
        except expected[1].DoesNotExist as error:
            raise NotFound("L’objet demandé est introuvable.") from error

        if template.file:
            try:
                current_file_hash = file_sha256(template.file)
            except FileNotFoundError as error:
                raise APIValidationError(
                    {"file": "Le fichier DOCX associé au modèle est indisponible."}
                ) from error
            if current_file_hash != template.approved_file_sha256:
                raise APIValidationError(
                    {"file": "Le fichier DOCX a changé depuis son approbation."}
                )
        else:
            raise APIValidationError({"file": "Le modèle ne possède pas de fichier DOCX."})

        try:
            content = generate_document(template, instance)
        except DjangoValidationError as error:
            raise APIValidationError(error.messages) from error

        reference = getattr(
            instance,
            "reference_number",
            getattr(instance, "code", instance.pk),
        )
        filename = slugify(f"{template.name}-{reference}") or "document"
        response = HttpResponse(
            content,
            content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}.docx"'
        return response
