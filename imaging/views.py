from rest_framework import viewsets
from .models import ImagingStudy, ImagingInstance
from accounts.permissions import IsClinicalStaff
from .serializers import ImagingStudySerializer, ImagingInstanceSerializer


class ImagingStudyViewSet(viewsets.ModelViewSet):
    queryset = ImagingStudy.objects.all()
    serializer_class = ImagingStudySerializer
    permission_classes = [IsClinicalStaff]


class ImagingInstanceViewSet(viewsets.ModelViewSet):
    queryset = ImagingInstance.objects.all()
    serializer_class = ImagingInstanceSerializer
    permission_classes = [IsClinicalStaff]
