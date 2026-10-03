from rest_framework import viewsets
from .models import StaffProfile
from accounts.permissions import IsAdministrator
from .serializers import StaffProfileSerializer


class StaffProfileViewSet(viewsets.ModelViewSet):
    queryset = StaffProfile.objects.all()
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAdministrator]
