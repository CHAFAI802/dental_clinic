from django.db.models.signals import post_save
from django.dispatch import receiver

from appointments.models import Appointment
from notifications.services.AppointmentPending import (
    request_appointment_notification,
)


@receiver(post_save, sender=Appointment)
def appointment_pending_notification(
    sender,
    instance,
    created,
    **kwargs,
):
    if created and instance.status == Appointment.Status.PENDING:
        request_appointment_notification(instance)
