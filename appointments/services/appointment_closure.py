import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment
from billing.services.prescription_billing import apply_prescription_billing

logger = logging.getLogger(__name__)


def close_appointment(*, appointment):
    """
    Clôture un rendez-vous arrivé à la fin de son créneau.

    - transactionnel et verrouillé : deux exécutions concurrentes ne
      provoquent pas de transition en double ;
    - seuls les rendez-vous CONFIRMED, non supprimés et dont `end_at` est
      atteint sont clôturés (annulés, déjà clôturés et futurs sont
      ignorés) ;
    - la transition est journalisée dans AppointmentStatusLog avec la
      note explicite de transition automatique (aucun dentiste imité) ;
    - la facturation de la prescription est décidée à ce moment-là
      (règle PRESC).

    Retourne l'appointment clôturé, ou None si rien ne devait être fait.
    """
    now = timezone.now()

    with transaction.atomic():
        locked = (
            Appointment.objects
            .select_for_update()
            .filter(pk=appointment.pk, is_deleted=False)
            .first()
        )

        if locked is None:
            return None

        if locked.status != Appointment.Status.CONFIRMED:
            # Déjà clôturé, annulé ou jamais confirmé : aucune double
            # transition.
            return None

        if locked.end_at > now:
            # Le créneau n'est pas terminé.
            return None

        locked.status = Appointment.Status.COMPLETED
        locked.save(auto=True)

        try:
            with transaction.atomic():
                apply_prescription_billing(appointment=locked)
        except ValidationError as error:
            # La clôture reste acquise : une anomalie de tarif PRESC ne
            # doit pas empêcher le rendez-vous d'être clos à l'heure.
            # L'erreur est journalisée pour correction côté catalogue.
            logger.error(
                "Facturation PRESC impossible pour le rendez-vous %s : %s",
                locked.pk,
                error.messages if hasattr(error, "messages") else error,
            )

    return locked


def close_expired_appointments(*, now=None):
    """
    Clôture tous les rendez-vous confirmés dont l'heure de fin est
    passée. Idempotent : une exécution répétée ne reclôture rien.

    Retourne la liste des identifiants clôturés.
    """
    if now is None:
        now = timezone.now()

    candidate_ids = list(
        Appointment.objects
        .filter(
            status=Appointment.Status.CONFIRMED,
            end_at__lte=now,
            is_deleted=False,
        )
        .order_by("end_at")
        .values_list("pk", flat=True)
    )

    closed_ids = []

    for appointment_id in candidate_ids:
        appointment = Appointment.objects.filter(pk=appointment_id).first()

        if appointment is None:
            continue

        if close_appointment(appointment=appointment) is not None:
            closed_ids.append(appointment_id)

    return closed_ids
