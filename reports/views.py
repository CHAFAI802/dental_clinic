from rest_framework import viewsets
from .models import ReportDefinition
from accounts.permissions import IsAdministrator
from .serializers import ReportDefinitionSerializer


class ReportDefinitionViewSet(viewsets.ModelViewSet):
    queryset = ReportDefinition.objects.all()
    serializer_class = ReportDefinitionSerializer
    permission_classes = [IsAdministrator]
