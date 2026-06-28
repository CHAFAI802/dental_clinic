from rest_framework import viewsets
from .models import Document, DocumentTemplate
from accounts.permissions import IsStaffMember
from .serializers import DocumentSerializer, DocumentTemplateSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsStaffMember]


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    queryset = DocumentTemplate.objects.filter(is_active=True)
    serializer_class = DocumentTemplateSerializer
    permission_classes = [IsStaffMember]
