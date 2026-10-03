from django.db import models
from django.core.exceptions import ValidationError
from dental_clinic.common import TimestampedModel, SoftDeleteModel


class Odontogram(SoftDeleteModel):
    patient = models.ForeignKey('patients.Patient', related_name='odontograms', on_delete=models.CASCADE)
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    version = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f'Odontogram {self.patient} v{self.version}'


class Tooth(SoftDeleteModel):
    class Status(models.TextChoices):
        HEALTHY = 'healthy', 'Healthy'
        TREATED = 'treated', 'Treated'

    odontogram = models.ForeignKey('odontogram.Odontogram', related_name='teeth', on_delete=models.CASCADE)
    number = models.CharField(max_length=8)
    type = models.CharField(max_length=32)
    quadrant = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=64, choices=Status.choices)
    surface_status = models.JSONField(default=dict, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = [('odontogram', 'number')]

    def clean(self):
        super().clean()

        # STATE-003: Status vocabulary enforcement
        valid_statuses = [choice.value for choice in self.Status]
        if self.status not in valid_statuses:
            raise ValidationError(
                {
                    "status": (
                        f"'{self.status}' is not a valid status. "
                        f"Must be one of: {', '.join(valid_statuses)}."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'Tooth {self.number} ({self.status})'


class ToothHistory(TimestampedModel):
    tooth = models.ForeignKey('odontogram.Tooth', related_name='history', on_delete=models.CASCADE)
    changed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    field = models.CharField(max_length=64)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    note = models.TextField(blank=True)


class ToothDiagnostic(TimestampedModel):
    tooth = models.ForeignKey('odontogram.Tooth', related_name='diagnostics', on_delete=models.CASCADE)
    diagnosis_code = models.CharField(max_length=64)
    diagnosis_label = models.CharField(max_length=255)
    severity = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    recorded_at = models.DateTimeField()
    recorded_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)


class ToothTreatment(TimestampedModel):
    tooth = models.ForeignKey('odontogram.Tooth', related_name='treatments', on_delete=models.CASCADE)
    treatment = models.ForeignKey('treatments.Treatment', null=True, blank=True, on_delete=models.SET_NULL)
    planned = models.BooleanField(default=False)
    performed_at = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey('accounts.User', null=True, blank=True, related_name='performed_tooth_treatments', on_delete=models.SET_NULL)
    status = models.CharField(max_length=32)
    notes = models.TextField(blank=True)
