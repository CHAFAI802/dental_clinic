from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from appointments.models import Appointment
from appointments.services.appointmentstatus import complete_appointment_from_treatment 

from billing.models import InvoiceLine, Prestation, PrestationCategory
from treatments.models import Treatment


class TreatmentCreationService:

    @staticmethod
    @transaction.atomic
    def create(*, appointment, prestation, dentist):
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
            

            # Valeurs temporaires nécessaires au modèle actuel.
            status=Treatment.Status.PLANNED,
            category=Treatment.Category.CONSULTATION,
            code=prestation.code,
            label=prestation.label,
            start_at=appointment.start_at,
        )

        InvoiceLine.objects.create(
            treatment=treatment,
            prestation=prestation,
            description=prestation.label,
            quantity=Decimal("3.00"),# quantity doit etre accessible via dentiste interface elle releve de billing/invoiceline 
        )

        complete_appointment_from_treatment(
            treatment=treatment,
        )

        return treatment
