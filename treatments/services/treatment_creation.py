from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from appointments.services.appointmentstatus import (
    validate_session_appointment,
)
from billing.models import InvoiceLine, Prestation
from treatments.models import Treatment

# Identifiant métier de la prestation « Acte de prescrire ».
# L'identifiant technique est le code, jamais la pk (variable selon les
# environnements) ni le libellé.
PRESC_CODE = "PRESC"

# La quantité de l'acte PRESC est toujours 1, imposée côté backend.
PRESC_QUANTITY = Decimal("1")


class TreatmentCreationService:
    """
    Création d'une prestation pendant une séance.

    Plusieurs prestations peuvent être enregistrées pour un même
    rendez-vous : la création ne clôture plus le rendez-vous, qui est
    clôturé automatiquement à la fin du créneau
    (cf. appointments.services.appointment_closure).
    """

    @staticmethod
    @transaction.atomic
    def create(*, appointment, prestation, dentist, quantity):
        # Praticien, statut CONFIRMED, intervalle horaire :
        # mêmes contrôles que pour la génération d'une ordonnance.
        validate_session_appointment(
            appointment=appointment,
            dentist=dentist,
            action="le traitement",
        )

        if not prestation.is_active:
            raise ValidationError({
                "prestation": "Cette prestation n'est pas active."
            })

        is_prescription = prestation.code == PRESC_CODE

        if is_prescription:
            # Quantité fixe de l'acte PRESC, quelle que soit la requête.
            quantity = PRESC_QUANTITY

        now = timezone.now()

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
            # Horodatage de l'enregistrement de l'acte : la durée totale
            # de la séance n'est jamais recopiée sur chaque traitement.
            end_at=now,
        )

        # L'acte PRESC n'est facturé qu'à la clôture du rendez-vous :
        # il n'est facturable que si aucune prestation dentaire n'a été
        # réalisée pendant la même séance (cf.
        # billing.services.prescription_billing). Les autres prestations
        # restent facturées immédiatement, comme auparavant.
        if not is_prescription:
            InvoiceLine.objects.create(
                treatment=treatment,
                prestation=prestation,
                description=prestation.label,
                quantity=quantity,
            )

        return treatment


def ensure_prescription_treatment(*, appointment, dentist):
    """
    Rattache automatiquement l'acte PRESC à la séance lors de la
    génération d'une ordonnance, sans sélection manuelle.

    - Si une ou plusieurs prestations dentaires existent déjà pour le
      rendez-vous, elles sont conservées : aucun traitement PRESC n'est
      ajouté.
    - Sinon l'acte PRESC est utilisé (aucune facturation ici).
    - Idempotent : réutilise le traitement PRESC déjà rattaché au
      rendez-vous au lieu d'en créer un doublon.

    Retourne le traitement PRESC concerné, ou None si la séance comporte
    déjà des prestations dentaires.
    """
    existing_presc = (
        Treatment.objects
        .filter(
            appointment=appointment,
            prestation__code=PRESC_CODE,
        )
        .first()
    )

    if existing_presc is not None:
        return existing_presc

    has_dental_treatment = (
        Treatment.objects
        .filter(appointment=appointment)
        .exclude(prestation__code=PRESC_CODE)
        .exists()
    )

    if has_dental_treatment:
        # Les prestations dentaires déjà enregistrées sont conservées :
        # on ne les remplace pas par PRESC.
        return None

    prestation = (
        Prestation.objects
        .filter(code=PRESC_CODE, is_active=True)
        .first()
    )

    if prestation is None:
        raise ValidationError({
            "appointment": (
                "La prestation PRESC (« Acte de prescrire ») est "
                "introuvable ou inactive dans le catalogue."
            )
        })

    return Treatment.objects.create(
        patient=appointment.patient,
        dentist=dentist,
        appointment=appointment,
        prestation=prestation,
        treatment_plan=None,
        notes="",
        code=prestation.code,
        label=prestation.label,
        start_at=appointment.start_at,
        end_at=timezone.now(),
    )
