from django.core.mail import send_mail

from accounts.models import User
from appointments.models import Appointment


def request_appointment_notification(appointment):
    if appointment.status != Appointment.Status.PENDING:
        return

    receptionists = User.objects.filter(
        role=User.Role.RECEPTIONIST,
        is_active=True,
    )

    subject = "Nouvelle demande de rendez-vous"

    message = (
        f"Une nouvelle demande de rendez-vous a été reçue.\n\n"
        f"Patient : {appointment.patient.first_name} "
        f"{appointment.patient.last_name}\n"
        f"Date : {appointment.start_at:%d/%m/%Y}\n"
        f"Heure : {appointment.start_at:%H:%M}\n"
    )

    for receptionist in receptionists:
        if receptionist.email:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[receptionist.email],
                fail_silently=False,
            )

def appointment_request_received_notification(appointment):
    if appointment.status != Appointment.Status.PENDING:
        return

    patient = appointment.patient

    if not patient.email:
        return

    subject = "Votre demande de rendez-vous a bien été enregistrée"

    message = (
        f"Bonjour {patient.first_name},\n\n"
        f"Votre demande de rendez-vous a bien été enregistrée.\n\n"
        f"Date demandée : {appointment.start_at:%d/%m/%Y}\n"
        f"Heure demandée : {appointment.start_at:%H:%M}\n\n"
        f"Votre demande est actuellement en attente de validation "
        f"par notre équipe.\n"
        f"Votre rendez-vous n'est donc pas encore confirmé.\n\n"
        f"Votre code patient est : {patient.patient_code}\n\n"
        f"Veuillez conserver ce code. Il vous sera demandé lors "
        f"de vos prochaines demandes de rendez-vous.\n\n"
        f"Vous recevrez un nouveau message lorsque votre demande "
        f"sera validée.\n\n"
        f"Cordialement,\n"
        f"L'équipe de la clinique"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=[patient.email],
        fail_silently=False,
    )

