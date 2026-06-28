from django.db import models
from dental_clinic.common import TimestampedModel


class DocumentTemplate(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    default_sections = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DocumentSection(models.Model):
    template = models.ForeignKey('documents.DocumentTemplate', related_name='sections', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    content = models.TextField()

    class Meta:
        ordering = ['order']


class DocumentVariable(models.Model):
    template = models.ForeignKey('documents.DocumentTemplate', related_name='variable_definitions', on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    label = models.CharField(max_length=255)
    data_type = models.CharField(max_length=32)
    is_required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True)


class Document(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='documents', on_delete=models.CASCADE)
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    document_type = models.CharField(max_length=64)
    template = models.ForeignKey('documents.DocumentTemplate', null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=255)
    content = models.TextField()
    signed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32)
    pdf_file = models.FileField(upload_to='documents/', null=True, blank=True)


class DocumentAttachment(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='document_attachments', on_delete=models.CASCADE)
    document = models.ForeignKey('documents.Document', null=True, blank=True, related_name='attachments', on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to='document_attachments/')
    file_type = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    is_confidential = models.BooleanField(default=False)


class ConsentForm(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='consent_forms', on_delete=models.CASCADE)
    document = models.ForeignKey('documents.Document', related_name='consents', on_delete=models.CASCADE)
    consent_type = models.CharField(max_length=128)
    given_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    given_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32)


class DocumentHistory(TimestampedModel):
    document = models.ForeignKey('documents.Document', related_name='history', on_delete=models.CASCADE)
    changed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    changes = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)
