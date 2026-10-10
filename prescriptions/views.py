from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from .models import Prescription, PrescriptionTemplate
from accounts.permissions import IsStaffMember
from .serializers import PrescriptionSerializer, PrescriptionTemplateSerializer
from documents.docx import DocxTemplateError
from .permissions import CanAccessPrescriptionDocument
from .services import generate_prescription_docx, open_generated_docx


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [IsStaffMember]

    @action(
        detail=True,
        methods=['post'],
        url_path='generate-docx',
        permission_classes=[IsStaffMember, CanAccessPrescriptionDocument],
    )
    def generate_docx(self, request, pk=None):
        prescription = self.get_object()
        try:
            generate_prescription_docx(prescription)
        except (DocxTemplateError, ValueError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            self.get_serializer(prescription).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='docx',
        url_name='download-docx',
        permission_classes=[IsStaffMember, CanAccessPrescriptionDocument],
    )
    def download_docx(self, request, pk=None):
        prescription = self.get_object()
        docx_file = open_generated_docx(prescription)
        if docx_file is None:
            raise NotFound('Aucun document DOCX généré pour cette ordonnance.')

        return FileResponse(
            docx_file,
            as_attachment=True,
            filename=f'ordonnance-{prescription.pk}.docx',
            content_type=(
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ),
        )


class PrescriptionTemplateViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionTemplate.objects.filter(is_active=True)
    serializer_class = PrescriptionTemplateSerializer
    permission_classes = [IsStaffMember]
