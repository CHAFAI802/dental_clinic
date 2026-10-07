from django.db import models
from dental_clinic.common import TimestampedModel, SoftDeleteModel
from django.core.exceptions import ValidationError


class Treatment(SoftDeleteModel):
    
    patient = models.ForeignKey('patients.Patient', related_name='treatments', on_delete=models.CASCADE)
    dentist = models.ForeignKey('accounts.User', related_name='treatments', on_delete=models.PROTECT)
    assistant = models.ForeignKey('accounts.User', null=True, blank=True, related_name='assisted_treatments', on_delete=models.SET_NULL)
    appointment = models.ForeignKey('appointments.Appointment', related_name='treatments', null=True, blank=True, on_delete=models.SET_NULL)
    treatment_plan = models.ForeignKey('treatment_plans.TreatmentPlan', null=True, blank=True, on_delete=models.SET_NULL)
    prestation = models.ForeignKey('billing.Prestation', on_delete=models.PROTECT, related_name='treatments')
    code = models.CharField(max_length=64)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def clean(self):
        super().clean()

        if (
            self.appointment_id is not None
            and self.patient_id != self.appointment.patient_id
        ):
            raise ValidationError(
                {
                    "appointment": (
                        "The appointment must belong "
                        "to the same patient as the treatment."
                    )
                }
            )
        if (
            self.treatment_plan_id is not None
            and self.patient_id != self.treatment_plan.patient_id
        ):
            raise ValidationError(
                {
                    "treatment_plan": (
                        "The treatment plan must belong "
                        "to the same patient as the treatment."
                    )
                }
            )


    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        indexes = [models.Index(fields=['dentist', 'start_at'])]

    def __str__(self):
        return f'{self.label} for {self.patient}'


class TreatmentTooth(models.Model):
    treatment = models.ForeignKey('treatments.Treatment', related_name='treatment_teeth', on_delete=models.CASCADE)
    tooth = models.ForeignKey('odontogram.Tooth', related_name='treatment_links', on_delete=models.CASCADE)
    surface = models.CharField(max_length=32, blank=True)
    role = models.CharField(max_length=64, blank=True)


class TreatmentMaterial(TimestampedModel):
    treatment = models.ForeignKey('treatments.Treatment', related_name='materials', on_delete=models.CASCADE)
    inventory_item = models.ForeignKey('inventory.InventoryItem', null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)


class TreatmentProtocol(TimestampedModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=64)
    steps = models.JSONField(default=list, blank=True)
    default_duration = models.PositiveIntegerField(null=True, blank=True)
    default_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # default_price will be deleted once we will audit the model and remove the default_price field from the model

class TreatmentTemplate(TimestampedModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=64)
    default_code = models.CharField(max_length=64)
    default_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    # default_price will be deleted once we will audit the model and remove the default_price field from the model