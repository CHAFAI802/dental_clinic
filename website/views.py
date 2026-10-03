from django.shortcuts import render

from rest_framework import viewsets

from accounts.permissions import IsAdministrator

from .models import WorkingHours
from .serializers import WorkingHoursSerializer


class WorkingHoursViewSet(viewsets.ModelViewSet):
    queryset = WorkingHours.objects.select_related("practitioner").all()
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAdministrator]
