from django.db import models
from dental_clinic.common import TimestampedModel, SoftDeleteModel


class Room(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=256, blank=True)
    location = models.CharField(max_length=128, blank=True)
    capacity = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Appointment(SoftDeleteModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No show'

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
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey('accounts.User', related_name='cancelled_appointments', null=True, blank=True, on_delete=models.SET_NULL)
    cancel_reason = models.TextField(blank=True)
    source = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['start_at']
        indexes = [models.Index(fields=['status', 'start_at']), models.Index(fields=['practitioner', 'start_at'])]

    def __str__(self):
        return f'{self.patient} - {self.start_at}'


class AppointmentStatusLog(TimestampedModel):
    appointment = models.ForeignKey('appointments.Appointment', related_name='status_logs', on_delete=models.CASCADE)
    previous_status = models.CharField(max_length=32)
    new_status = models.CharField(max_length=32)
    changed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField()
    note = models.TextField(blank=True)
