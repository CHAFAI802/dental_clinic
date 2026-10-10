from rest_framework.permissions import BasePermission

from accounts.models import User
from appointments.models import Appointment
from treatments.models import Treatment


class CanAccessPrescriptionDocument(BasePermission):
    message = 'Vous ne pouvez pas accéder à cette ordonnance.'

    def has_object_permission(self, request, view, prescription):
        user = request.user
        if user.role in (User.Role.SUPER_ADMIN, User.Role.ADMINISTRATOR):
            return True

        if user.role == User.Role.DENTIST:
            return prescription.dentist_id == user.pk

        if user.role == User.Role.ASSISTANT:
            has_assigned_appointment = Appointment.objects.filter(
                patient_id=prescription.patient_id,
                assistant=user,
                is_deleted=False,
            ).exists()
            has_assigned_treatment = Treatment.objects.filter(
                patient_id=prescription.patient_id,
                assistant=user,
                is_deleted=False,
            ).exists()
            return has_assigned_appointment or has_assigned_treatment

        return False
