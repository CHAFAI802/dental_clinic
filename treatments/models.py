from django.db import models
from dental_clinic.common import TimestampedModel, SoftDeleteModel


class Treatment(SoftDeleteModel):
    class Category(models.TextChoices):
        CONSULTATION = 'consultation', 'Consultation'
        DETARTRAGE = 'detartrage', 'Détartrage'
        EXTRACTION = 'extraction', 'Extraction'
        IMPLANT = 'implant', 'Implant'
        ENDODONTIE = 'endodontie', 'Endodontie'
        ORTHODONTIE = 'orthodontie', 'Orthodontie'
        CHIRURGIE = 'chirurgie', 'Chirurgie'
        AUTRE = 'autre', 'Autre'

    patient = models.ForeignKey('patients.Patient', related_name='treatments', on_delete=models.CASCADE)
    dentist = models.ForeignKey('accounts.User', related_name='treatments', on_delete=models.PROTECT)
    assistant = models.ForeignKey('accounts.User', null=True, blank=True, related_name='assisted_treatments', on_delete=models.SET_NULL)
    appointment = models.ForeignKey('appointments.Appointment', null=True, blank=True, on_delete=models.SET_NULL)
    treatment_plan = models.ForeignKey('treatment_plans.TreatmentPlan', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=32)
    category = models.CharField(max_length=32, choices=Category.choices)
    code = models.CharField(max_length=64)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['status', 'category']), models.Index(fields=['dentist', 'start_at'])]

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


class TreatmentTemplate(TimestampedModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=64)
    default_code = models.CharField(max_length=64)
    default_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
