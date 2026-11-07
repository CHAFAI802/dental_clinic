from django.db import models
from dental_clinic.common import TimestampedModel
from django.core.exceptions import ValidationError
from django.conf import settings
from documents.services.docx import file_sha256


class DocumentTemplate(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="document_templates/", blank=True, null=True)
    structure_config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Configuration documentaire JSON version 1 : type et modèle racine. "
            "Les variables et collections sont détectées dans le fichier DOCX. "
            "Les anciennes configurations avec zones répétitives restent prises "
            "en charge."
        ),
    )
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_document_templates",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_file_sha256 = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if self.pk:
            previous = (
                type(self).objects.filter(pk=self.pk)
                .values("approved_file_sha256", "structure_config")
                .first()
            )
            file_may_have_changed = update_fields is None or "file" in update_fields
            config_may_have_changed = (
                update_fields is None or "structure_config" in update_fields
            )
            config_changed = (
                config_may_have_changed
                and previous is not None
                and self.structure_config != previous["structure_config"]
            )
            file_changed = False
            if self.is_approved and file_may_have_changed:
                current_hash = file_sha256(self.file) if self.file else ""
                file_changed = current_hash != (
                    previous["approved_file_sha256"] if previous else ""
                )
            if self.is_approved and (config_changed or file_changed):
                self.is_approved = False
                self.approved_by = None
                self.approved_at = None
                self.approved_file_sha256 = ""
                if update_fields is not None:
                    kwargs["update_fields"] = set(update_fields) | {
                        "is_approved",
                        "approved_by",
                        "approved_at",
                        "approved_file_sha256",
                    }
        return super().save(*args, **kwargs)

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
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SIGNED = 'signed', 'Signed'

    patient = models.ForeignKey('patients.Patient', related_name='documents', on_delete=models.CASCADE)
    created_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    document_type = models.CharField(max_length=64)
    template = models.ForeignKey('documents.DocumentTemplate', null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=255)
    content = models.TextField()
    signed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices)
    pdf_file = models.FileField(upload_to='documents/', null=True, blank=True)


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


class DocumentAttachment(TimestampedModel):
    patient = models.ForeignKey(
        'patients.Patient',
        related_name='document_attachments',
        on_delete=models.CASCADE,
    )
    document = models.ForeignKey(
        'documents.Document',
        null=True,
        blank=True,
        related_name='attachments',
        on_delete=models.CASCADE,
    )
    uploaded_by = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    file = models.FileField(upload_to='document_attachments/')
    file_type = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    is_confidential = models.BooleanField(default=False)

    def clean(self):
        super().clean()

        if (
            self.document is not None
            and self.patient_id != self.document.patient_id
        ):
            raise ValidationError(
                {
                    'patient': (
                        "Attachment patient must match the related document patient."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class ConsentForm(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='consent_forms', on_delete=models.CASCADE)
    document = models.ForeignKey('documents.Document', related_name='consents', on_delete=models.CASCADE)
    consent_type = models.CharField(max_length=128)
    given_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    given_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32)

    def clean(self):
        super().clean()

        if self.patient_id != self.document.patient_id:
            raise ValidationError(
                {
                    "patient": (
                        "Consent patient must match the related document patient."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class DocumentHistory(TimestampedModel):
    document = models.ForeignKey('documents.Document', related_name='history', on_delete=models.CASCADE)
    changed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    changes = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)
