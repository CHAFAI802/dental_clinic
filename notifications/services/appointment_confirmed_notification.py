from django.core.mail import send_mail

from appointments.models import Appointment


def appointment_confirmed_notification(appointment):
    patient = appointment.patient
    practitioner = appointment.practitioner

    appointment_date = appointment.start_at.strftime("%d/%m/%Y")
    appointment_time = appointment.start_at.strftime("%H:%M")

    if patient.email:
        send_mail(
            subject="Votre rendez-vous est confirmé",
            message=(
                f"Bonjour {patient.first_name},\n\n"
                f"Votre rendez-vous a été confirmé.\n\n"
                f"Date : {appointment_date}\n"
                f"Heure : {appointment_time}\n"
                f"Praticien : {practitioner.first_name} "
                f"{practitioner.last_name}\n"
            ),
            from_email=None,
            recipient_list=[patient.email],
            fail_silently=False,
        )

    if practitioner.email:
        send_mail(
            subject="Nouveau rendez-vous confirmé",
            message=(
                f"Bonjour Dr {practitioner.last_name},\n\n"
                f"Un rendez-vous a été confirmé.\n\n"
                f"Patient : {patient.first_name} "
                f"{patient.last_name}\n"
                f"Date : {appointment_date}\n"
                f"Heure : {appointment_time}\n"
            ),
            from_email=None,
            recipient_list=[practitioner.email],
            fail_silently=False,
        )


def appointment_cancelled_notification(appointment):
    patient = appointment.patient
    practitioner = appointment.practitioner

    appointment_date = appointment.start_at.strftime("%d/%m/%Y")
    appointment_time = appointment.start_at.strftime("%H:%M")

    if patient.email:
        send_mail(
            subject="Votre rendez-vous a été annulé",
            message=(
                f"Bonjour {patient.first_name},\n\n"
                f"Votre rendez-vous a été annulé.\n\n"
                f"Date : {appointment_date}\n"
                f"Heure : {appointment_time}\n"
                f"Praticien : {practitioner.first_name} "
                f"{practitioner.last_name}\n"
            ),
            from_email=None,
            recipient_list=[patient.email],
            fail_silently=False,
        )

    if practitioner.email:
        send_mail(
            subject="Rendez-vous annulé",
            message=(
                f"Bonjour Dr {practitioner.last_name},\n\n"
                f"Le rendez-vous suivant a été annulé.\n\n"
                f"Patient : {patient.first_name} "
                f"{patient.last_name}\n"
                f"Date : {appointment_date}\n"
                f"Heure : {appointment_time}\n"
            ),
            from_email=None,
            recipient_list=[practitioner.email],
            fail_silently=False,
        )

