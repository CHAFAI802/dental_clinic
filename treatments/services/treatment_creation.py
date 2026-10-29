from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from appointments.models import Appointment
from appointments.services.appointmentstatus import complete_appointment_from_treatment
from billing.models import InvoiceLine
from treatments.models import Treatment


class TreatmentCreationService:

    @staticmethod
    @transaction.atomic
    def create(*, appointment, prestation, dentist, quantity):
        if appointment.practitioner_id != dentist.id:
            raise ValidationError({
                "appointment": (
                    "Ce rendez-vous n'appartient pas au dentiste connecté."
                )
            })

        if appointment.status != Appointment.Status.CONFIRMED:
            raise ValidationError({
                "appointment": (
                    "Le rendez-vous doit être confirmé avant "
                    "d'enregistrer le traitement."
                )
            })

        now = timezone.now()

        if now < appointment.start_at or now >= appointment.end_at:
            raise ValidationError({
                "appointment": (
                    "Impossible d'enregistrer cette prestation : "
                    "le traitement doit être enregistré pendant "
                    "l'intervalle du rendez-vous."
                )
            })

        if not prestation.is_active:
            raise ValidationError({
                "prestation": "Cette prestation n'est pas active."
            })

        treatment = Treatment.objects.create(
            patient=appointment.patient,
            dentist=dentist,
            appointment=appointment,
            prestation=prestation,
            treatment_plan=None,
            notes="",
            code=prestation.code,
            label=prestation.label,
            start_at=appointment.start_at,
        )

        InvoiceLine.objects.create(
            treatment=treatment,
            prestation=prestation,
            description=prestation.label,
            quantity=quantity,
        )

        complete_appointment_from_treatment(
            treatment=treatment,
        )

        return treatment