from django.db import models, transaction
from django.utils import timezone
from dental_clinic.common import ProtectedDeleteManager, TimestampedModel, SoftDeleteModel
from django.core.exceptions import ValidationError
from accounts.models import User


class Room(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=256, blank=True)
    location = models.CharField(max_length=128, blank=True)
    capacity = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    objects = ProtectedDeleteManager()

    def clean(self):
        super().clean()
        # ROOM-004: room capacity must be at least one
        if self.capacity is not None and self.capacity < 1:
            raise ValidationError(
                {
                    "capacity": "Room capacity must be greater than or equal to 1."
                }
            )

    def delete(self, using=None, keep_parents=False):
        raise ValidationError(
            "Rooms cannot be deleted. Set is_active=False instead."
        )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1),
                name="room_capacity_gte_one",
            ),
        ]

    def __str__(self):
        return self.name

class Appointment(SoftDeleteModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No show'

    class Source(models.TextChoices):
        RECEPTION = "reception", "Reception"
        PATIENT = "patient", "Patient"
        PHONE = "phone", "Phone"
        ONLINE = "online", "Online"

    patient = models.ForeignKey('patients.Patient', related_name='appointments', on_delete=models.CASCADE)
    practitioner = models.ForeignKey('accounts.User', related_name='appointments', on_delete=models.PROTECT)
    assistant = models.ForeignKey('accounts.User', related_name='assisted_appointments', null=True, blank=True, on_delete=models.SET_NULL)
    room = models.ForeignKey('appointments.Room', null=True, blank=True, on_delete=models.SET_NULL)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    reason = models.CharField(max_length=256, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', related_name='created_appointments', null=True, blank=True, on_delete=models.SET_NULL)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey('accounts.User', related_name='confirmed_appointments', null=True, blank=True, on_delete=models.SET_NULL)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey('accounts.User', related_name='completed_appointments', null=True, blank=True, on_delete=models.SET_NULL)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey('accounts.User', related_name='cancelled_appointments', null=True, blank=True, on_delete=models.SET_NULL)
    cancel_reason = models.TextField(blank=True)
    source = models.CharField(max_length=64, choices=Source.choices, blank=True)

    def _get_old_status(self):
        """Return the current persisted status, or None for new appointments."""
        if self.pk is None:
            return None
        try:
            return Appointment.objects.get(pk=self.pk).status
        except Appointment.DoesNotExist:
            return None

    @staticmethod
    def _get_allowed_transitions(current_status):
        """Return list of allowed next statuses from the given current status."""

        transitions = {
            Appointment.Status.PENDING: [
                Appointment.Status.CONFIRMED,
            ],

            Appointment.Status.CONFIRMED: [
                Appointment.Status.COMPLETED,
                Appointment.Status.CANCELLED,
                Appointment.Status.NO_SHOW,
            ],

            Appointment.Status.COMPLETED: [],
            Appointment.Status.CANCELLED: [],
            Appointment.Status.NO_SHOW: [],
        }
        return transitions.get(current_status, [])

    def clean(self):
        super().clean()
        # ROOM-002: an appointment cannot use an inactive room
        if self.room_id is not None and not self.room.is_active:
            raise ValidationError(
                {
                    "room": (
                        "The appointment cannot be assigned "
                        "to an inactive room."
                    )
                }
            )

        # RULE-001: end_at must be strictly after start_at
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValidationError(
                {
                    "end_at": (
                        "The appointment end time must be "
                        "strictly greater than the start time."
                    )
                }
            )

        # RULE-002: practitioner overlap detection
        if (
            self.practitioner_id is not None
            and self.start_at is not None
            and self.end_at is not None
        ):
            overlapping = Appointment.objects.filter(
                practitioner=self.practitioner,
                start_at__lt=self.end_at,
                end_at__gt=self.start_at,
                is_deleted=False,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(
                    {
                        "practitioner": (
                            "The practitioner already has an overlapping "
                            "appointment during this time interval."
                        )
                    }
                )

        # ROOM-003: room overlap detection
        if (
            self.room_id is not None
            and self.start_at is not None
            and self.end_at is not None
        ):
            overlapping = Appointment.objects.filter(
                room=self.room,
                start_at__lt=self.end_at,
                end_at__gt=self.start_at,
                is_deleted=False,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(
                    {
                        "room": (
                            "The room already has an overlapping "
                            "appointment during this time interval."
                        )
                    }
                )

        # STATE-001: Status transition validation
        if self.pk is not None:
            old_status = self._get_old_status()
            if old_status is not None and old_status != self.status:
                allowed = self._get_allowed_transitions(old_status)
                if self.status not in allowed:
                    raise ValidationError(
                        {
                            "status": (
                                f"Cannot transition from '{old_status}' "
                                f"to '{self.status}'."
                            )
                        }
                    )
        if (
            self.practitioner_id is not None
            and self.practitioner.role != User.Role.DENTIST
            ):
            raise ValidationError(
                {
                    "practitioner": (
                        "The practitioner must have the DENTIST role."
                    )
                }
            )
        if (
            self.assistant_id is not None
            and self.assistant.role != User.Role.ASSISTANT
            ):
            raise ValidationError(
                {
                    "assistant": (
                        "The assistant must have the ASSISTANT role."
                    )
                }
            )

    def save(self, *args, changed_by=None, **kwargs):
        # Detect status change before full_clean()
        old_status = self._get_old_status()

        if self.start_at is not None:
            self.start_at = self._meta.get_field("start_at").to_python(
                self.start_at
            )

        if self.end_at is not None:
            self.end_at = self._meta.get_field("end_at").to_python(
                self.end_at
            )

        if self.start_at is not None and self.end_at is not None:
            self.duration_minutes = int(
                (self.end_at - self.start_at).total_seconds() / 60
            )

        self.full_clean()

        status_changed = (
            old_status is not None and old_status != self.status
        )

        if status_changed and changed_by is None:
            raise ValidationError(
                {
                    "status": (
                        "An actor is required when changing "
                        "appointment status."
                    )
                }
            )

        if status_changed:
            if self.status == self.Status.CONFIRMED:
                if not self.confirmed_at:
                    self.confirmed_at = timezone.now()
                self.confirmed_by = changed_by

            if self.status == self.Status.COMPLETED:
                if not self.completed_at:
                    self.completed_at = timezone.now()
                self.completed_by = changed_by

            if self.status == self.Status.CANCELLED:
                if not self.cancelled_at:
                    self.cancelled_at = timezone.now()
                self.cancelled_by = changed_by

        with transaction.atomic():
            result = super().save(*args, **kwargs)

            if status_changed:
                AppointmentStatusLog.objects.create(
                    appointment=self,
                    previous_status=old_status,
                    new_status=self.status,
                    changed_by=changed_by,
                    changed_at=timezone.now(),
                )

            return result

    class Meta:
        ordering = ['start_at']
        indexes = [models.Index(fields=['status', 'start_at']), models.Index(fields=['practitioner', 'start_at'])]
        constraints = [
        models.CheckConstraint(
            condition=models.Q(end_at__gt=models.F("start_at")),
            name="appointment_end_after_start",
        ),
    ]

    def __str__(self):
        return f'{self.patient} - {self.start_at}'

class AppointmentStatusLog(TimestampedModel):
    appointment = models.ForeignKey('appointments.Appointment', related_name='status_logs', on_delete=models.CASCADE)
    previous_status = models.CharField(max_length=32)
    new_status = models.CharField(max_length=32)
    changed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField()
    note = models.TextField(blank=True)
