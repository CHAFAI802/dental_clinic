from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from dental_clinic.common import TimestampedModel
from django.core.exceptions import ValidationError


class DocumentType(TimestampedModel):
    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = slugify(self.name) or 'document-type'
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DocumentTemplate(TimestampedModel):
    code = models.SlugField(max_length=128, unique=True, blank=True, db_index=True)
    document_type = models.ForeignKey(
        'documents.DocumentType',
        related_name='templates',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    default_sections = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='document_templates',
    )

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.code:
            base_name = self.name.strip() if self.name else 'template'
            self.code = slugify(base_name) or 'template'
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DocumentTemplateVersion(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    template = models.ForeignKey(
        'documents.DocumentTemplate',
        related_name='versions',
        on_delete=models.CASCADE,
    )
    version_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    schema_version = models.CharField(max_length=32, default='1.0')
    definition = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'accounts.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='document_template_versions',
    )

    class Meta:
        ordering = ['-version_number']
        constraints = [
            models.UniqueConstraint(
                fields=['template', 'version_number'],
                name='unique_document_template_version_number',
            )
        ]

    def clean(self):
        super().clean()
        valid_statuses = [choice.value for choice in self.Status]
        if self.status not in valid_statuses:
            raise ValidationError(
                {
                    'status': (
                        f"'{self.status}' is not a valid status. "
                        f"Must be one of: {', '.join(valid_statuses)}."
                    )
                }
            )

        if self.definition is None:
            raise ValidationError({'definition': 'Definition cannot be null.'})

        if not isinstance(self.definition, dict):
            raise ValidationError({'definition': 'Definition must be a JSON object.'})

        pages = self.definition.get('pages')
        if not isinstance(pages, list):
            raise ValidationError({'definition': 'Definition must contain a "pages" list.'})

        for index, page in enumerate(pages):
            if not isinstance(page, dict):
                raise ValidationError({'definition': f'Page {index} must be an object.'})
            elements = page.get('elements', [])
            if not isinstance(elements, list):
                raise ValidationError({'definition': f'Page {index} must expose an "elements" list.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        return super().save(*args, **kwargs)

    def publish(self, commit=True):
        self.status = self.Status.PUBLISHED
        self.published_at = timezone.now()
        if commit:
            self.save()
        return self

    def next_version_number(self):
        latest_version = self.template.versions.order_by('-version_number').first()
        if latest_version is None:
            return 1
        return latest_version.version_number + 1

    def __str__(self):
        return f"{self.template.name} v{self.version_number}"


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
    template_version = models.ForeignKey(
        'documents.DocumentTemplateVersion',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='documents',
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    signed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices)
    pdf_file = models.FileField(upload_to='documents/', null=True, blank=True)

    def clean(self):
        super().clean()

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

        if self.template_version and self.template and self.template_version.template_id != self.template_id:
            raise ValidationError(
                {
                    'template_version': (
                        'DocumentTemplateVersion must belong to the same template '
                        'as the current template.'
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
