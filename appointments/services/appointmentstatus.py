from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

from appointments.models import Appointment 
from patients.models import Patient
from website.models import WorkingHours


def get_available_slots(
    practitioner=None,
    start_date=None,
    end_date=None,
    slot_duration_minutes=30,
):
    """
    Return available appointment slots for the requested practitioners
    and date range.
    """

    if start_date is None:
        start_date = timezone.localdate()

    if end_date is None:
        end_date = start_date + timedelta(days=6)

    if end_date < start_date:
        raise ValueError("end_date must be greater than or equal to start_date.")

    working_hours = WorkingHours.objects.filter(
        is_active=True,
        weekday__in=[
            current_date.weekday()
            for current_date in (
                start_date + timedelta(days=offset)
                for offset in range((end_date - start_date).days + 1)
            )
        ],
    ).select_related("practitioner")

    if practitioner is not None:
        working_hours = working_hours.filter(
            practitioner=practitioner,
        )

    slots = []

    for working_hour in working_hours:
        current_date = start_date + timedelta(
            days=(
                working_hour.weekday
                - start_date.weekday()
            ) % 7
        )

        while current_date <= end_date:
            if current_date.weekday() != working_hour.weekday:
                current_date += timedelta(days=6)
                continue

            slot_start = datetime.combine(
                current_date,
                working_hour.start_time,
            )
            slot_end = datetime.combine(
                current_date,
                working_hour.end_time,
            )

            if timezone.is_aware(timezone.now()):
                slot_start = timezone.make_aware(
                    slot_start,
                    timezone.get_current_timezone(),
                )
                slot_end = timezone.make_aware(
                    slot_end,
                    timezone.get_current_timezone(),
                )

            while (
                slot_start + timedelta(minutes=slot_duration_minutes)
                <= slot_end
            ):
                candidate_end = slot_start + timedelta(
                    minutes=slot_duration_minutes
                )

                has_conflict = Appointment.objects.filter(
                    practitioner=working_hour.practitioner,
                    start_at__lt=candidate_end,
                    end_at__gt=slot_start,
                    is_deleted=False,
                ).exclude(
                    status=Appointment.Status.CANCELLED,
                ).exists()

                if not has_conflict:
                    slots.append(
                        {
                            "practitioner": working_hour.practitioner_id,
                            "date": current_date,
                            "start_at": slot_start,
                            "end_at": candidate_end,
                        }
                    )

                slot_start = candidate_end

            current_date += timedelta(days=6)

    return slots

class AppointmentRequestService:

    @staticmethod
    @transaction.atomic
    def submit(
        *,
        first_request,
        practitioner,
        start_at,
        end_at,
        patient_code=None,
        first_name=None,
        last_name=None,
        email=None,
        phone=None,
        birthdate=None,
        gender=None,
        reason="",
    ):
        if first_request:
            patient = Patient.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email or "",
                phone=phone,
            )
        else:
            patient = AppointmentRequestService._find_existing_patient(
                patient_code=patient_code,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                birthdate=birthdate,
                gender=gender,
            )

        appointment = Appointment.objects.create(
            patient=patient,
            practitioner=practitioner,
            start_at=start_at,
            end_at=end_at,
            status=Appointment.Status.PENDING,
            source=Appointment.Source.ONLINE,
            reason=reason or "",
        )

        return appointment

    @staticmethod
    def _find_existing_patient(
        *,
        patient_code=None,
        first_name=None,
        last_name=None,
        email=None,
        phone=None,
        birthdate=None,
        gender=None,
    ):
        if patient_code:
            return Patient.objects.get(
                patient_code=patient_code,
            )

        patients = Patient.objects.filter(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
        )

        if patients.count() == 1:
            return patients.get()

        if patients.count() > 1:
            if birthdate is not None:
                patients = patients.filter(
                    birthdate=birthdate,
                )

            if gender:
                patients = patients.filter(
                    gender=gender,
                )

        if patients.count() == 1:
            return patients.get()

        if patients.count() > 1:
            raise ValueError(
                "Please call the clinic to identify your patient record."
            )

        raise Patient.DoesNotExist(
            "No patient matches the provided information."
        )

def complete_appointment_from_treatment(*, treatment):
    appointment = treatment.appointment

    if appointment is None:
        return None

    if appointment.status != Appointment.Status.CONFIRMED:
        return appointment

    appointment.status = Appointment.Status.COMPLETED
    appointment.save(changed_by=treatment.dentist)

    treatment.end_at = appointment.completed_at
    treatment.save(update_fields=["end_at", "updated_at"])

    return appointment
