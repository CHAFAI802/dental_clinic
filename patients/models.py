from django.db import models
from dental_clinic.common import TimestampedModel, SoftDeleteModel


class Patient(SoftDeleteModel):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    birthdate = models.DateField()
    gender = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30)
    secondary_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=128, blank=True)
    postal_code = models.CharField(max_length=16, blank=True)
    country = models.CharField(max_length=64, blank=True)
    marital_status = models.CharField(max_length=64, blank=True)
    profession = models.CharField(max_length=128, blank=True)
    employer = models.CharField(max_length=128, blank=True)
    language = models.CharField(max_length=32, default='fr')
    preferred_contact_method = models.CharField(max_length=32, default='phone')
    document_type = models.CharField(max_length=64, blank=True)
    document_number = models.CharField(max_length=128, blank=True)
    social_security_number = models.CharField(max_length=128, blank=True)
    insurance_provider = models.CharField(max_length=128, blank=True)
    insurance_policy_number = models.CharField(max_length=128, blank=True)
    insurance_group = models.CharField(max_length=128, blank=True)
    insurance_valid_until = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=8, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    smoker = models.BooleanField(default=False)
    pregnant = models.BooleanField(default=False)
    allergies_summary = models.TextField(blank=True)
    medical_history_summary = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_relation = models.CharField(max_length=128, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)
    emergency_contact_email = models.EmailField(blank=True)

    class Meta:
        indexes = [models.Index(fields=['last_name', 'first_name', 'birthdate'])]

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class MedicalHistory(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='medical_histories', on_delete=models.CASCADE)
    condition = models.CharField(max_length=255)
    diagnosis_date = models.DateField()
    status = models.CharField(max_length=64)
    notes = models.TextField(blank=True)
    is_chronic = models.BooleanField(default=False)
    is_acute = models.BooleanField(default=False)


class Allergy(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='allergies', on_delete=models.CASCADE)
    substance = models.CharField(max_length=255)
    reaction = models.CharField(max_length=255)
    severity = models.CharField(max_length=64)
    notes = models.TextField(blank=True)


class Medication(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='medications', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=128)
    frequency = models.CharField(max_length=128)
    route = models.CharField(max_length=64)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    prescribed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)


class ClinicalNote(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='clinical_notes', on_delete=models.CASCADE)
    author = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    note_type = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    content = models.TextField()
    recorded_at = models.DateTimeField()


class PatientAttachment(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='patient_attachments', on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to='patient_attachments/')
    file_type = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    is_confidential = models.BooleanField(default=False)


class PatientConsent(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='consents', on_delete=models.CASCADE)
    consent_type = models.CharField(max_length=128)
    given_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    document = models.ForeignKey('documents.Document', null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=64)
