from django.db import models
from dental_clinic.common import TimestampedModel


class PrescriptionTemplate(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PrescriptionSection(models.Model):
    template = models.ForeignKey('prescriptions.PrescriptionTemplate', related_name='sections', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    content = models.TextField()

    class Meta:
        ordering = ['order']


class PrescriptionVariable(models.Model):
    template = models.ForeignKey('prescriptions.PrescriptionTemplate', related_name='variable_definitions', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    label = models.CharField(max_length=255)
    default_value = models.CharField(max_length=255, blank=True)
    data_type = models.CharField(max_length=32)
    is_required = models.BooleanField(default=False)


class Prescription(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='prescriptions', on_delete=models.CASCADE)
    dentist = models.ForeignKey('accounts.User', related_name='prescriptions', on_delete=models.PROTECT)
    template = models.ForeignKey('prescriptions.PrescriptionTemplate', related_name='prescriptions', on_delete=models.PROTECT)
    filled_data = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32)
    pdf_file = models.FileField(upload_to='prescriptions/', null=True, blank=True)
    notes = models.TextField(blank=True)


class PrescriptionHistory(TimestampedModel):
    prescription = models.ForeignKey('prescriptions.Prescription', related_name='history', on_delete=models.CASCADE)
    changed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    changes = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)
