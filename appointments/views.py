from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView 
from rest_framework.decorators import action 
from datetime import datetime
from notifications.services.appointment_confirmed_notification import (
    appointment_confirmed_notification,
)

from accounts.permissions import IsAppointmentManager

from .models import Appointment, Room
from accounts.models import User
from .services.appointmentstatus import get_available_slots
from .serializers import AppointmentSerializer, RoomSerializer, AppointmentRequestSerializer, AvailableSlotSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.filter(
        is_deleted=False,
    ).select_related(
        "patient",
        "practitioner",
    )
    serializer_class = AppointmentSerializer
    permission_classes = [IsAppointmentManager]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.role == User.Role.DENTIST:
            queryset = queryset.filter(
                practitioner=self.request.user,
            )

        return queryset

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        if request.user.role != User.Role.RECEPTIONIST:
            return Response(
                {"detail": "Only receptionists can validate appointments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        appointment = self.get_object()

        if appointment.status != Appointment.Status.PENDING:
            return Response(
                {"detail": "Only pending appointments can be validated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.CONFIRMED
        appointment.save(changed_by=request.user)

        appointment_confirmed_notification(appointment)

        return Response(
            AppointmentSerializer(
                appointment,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )
    
class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.filter(is_active=True)
    serializer_class = RoomSerializer
    permission_classes = [IsAppointmentManager]

class AppointmentRequestView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = AppointmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment = serializer.save()

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )

class AppointmentSlotsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        practitioner_id = request.query_params.get("practitioner")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        practitioner = None

        if practitioner_id:
            try:
                practitioner = User.objects.get(
                    pk=practitioner_id,
                    role=User.Role.DENTIST,
                    is_active=True,
                    is_deleted=False,
                )
            except User.DoesNotExist:
                return Response(
                    {"practitioner": "Dentist not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            start_date = (
                datetime.strptime(start_date, "%Y-%m-%d").date()
                if start_date
                else None
            )
            end_date = (
                datetime.strptime(end_date, "%Y-%m-%d").date()
                if end_date
                else None
            )
        except ValueError:
            return Response(
                {"date": "Dates must use the YYYY-MM-DD format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            slots = get_available_slots(
                practitioner=practitioner,
                start_date=start_date,
                end_date=end_date,
            )
        except ValueError as exc:
            return Response(
                {"date": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        practitioner_ids = {
            slot["practitioner"]
            for slot in slots
        }

        practitioners = {
            user.id: user
            for user in User.objects.filter(
                id__in=practitioner_ids,
                role=User.Role.DENTIST,
                is_active=True,
                is_deleted=False,
            )
        }

        enriched_slots = [
            {
                **slot,
                "practitioner_name": (
                    f"{practitioners[slot['practitioner']].first_name} "
                    f"{practitioners[slot['practitioner']].last_name}"
                ),
            }
            for slot in slots
        ]

        serializer = AvailableSlotSerializer(
            enriched_slots,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
