from django.db import models
from django.core.exceptions import ValidationError
from dental_clinic.common import TimestampedModel
from documents.storage import private_document_storage


class PrescriptionTemplate(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    docx_file = models.FileField(
        upload_to='prescription_templates/',
        storage=private_document_storage,
        blank=True,
    )
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
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        GENERATED = 'generated', 'Generated'

    patient = models.ForeignKey('patients.Patient', related_name='prescriptions', on_delete=models.CASCADE)
    dentist = models.ForeignKey('accounts.User', related_name='prescriptions', on_delete=models.PROTECT)
    template = models.ForeignKey('prescriptions.PrescriptionTemplate', related_name='prescriptions', on_delete=models.PROTECT)
    filled_data = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices)
    pdf_file = models.FileField(upload_to='prescriptions/', null=True, blank=True)
    generated_docx = models.FileField(
        upload_to='generated_prescriptions/',
        storage=private_document_storage,
        blank=True,
    )
    notes = models.TextField(blank=True)


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


class PrescriptionHistory(TimestampedModel):
    prescription = models.ForeignKey('prescriptions.Prescription', related_name='history', on_delete=models.CASCADE)
    changed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    changes = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)
