from rest_framework import viewsets
from .models import Appointment, Room
from accounts.permissions import IsStaffMember
from .serializers import AppointmentSerializer, RoomSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.filter(is_deleted=False)
    serializer_class = AppointmentSerializer
    permission_classes = [IsStaffMember]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.filter(is_active=True)
    serializer_class = RoomSerializer
    permission_classes = [IsStaffMember]
