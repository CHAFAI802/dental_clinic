from django.db import models
from dental_clinic.common import TimestampedModel


class ImagingStudy(TimestampedModel):
    patient = models.ForeignKey('patients.Patient', related_name='imaging_studies', on_delete=models.CASCADE)
    practitioner = models.ForeignKey('accounts.User', related_name='imaging_studies', on_delete=models.PROTECT)
    study_type = models.CharField(max_length=64)
    study_date = models.DateTimeField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32)
    source_system = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return f'{self.study_type} for {self.patient}'


class ImagingSeries(models.Model):
    study = models.ForeignKey('imaging.ImagingStudy', related_name='series', on_delete=models.CASCADE)
    series_number = models.PositiveIntegerField()
    modality = models.CharField(max_length=64)
    body_part = models.CharField(max_length=64, blank=True)
    laterality = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)


class ImagingInstance(models.Model):
    series = models.ForeignKey('imaging.ImagingSeries', related_name='instances', on_delete=models.CASCADE)
    instance_number = models.PositiveIntegerField()
    file = models.FileField(upload_to='imaging/')
    file_type = models.CharField(max_length=64)
    study_date = models.DateTimeField()
    notes = models.TextField(blank=True)
    thumbnail = models.FileField(upload_to='imaging/thumbnails/', null=True, blank=True)


class ImagingReport(TimestampedModel):
    study = models.ForeignKey('imaging.ImagingStudy', related_name='reports', on_delete=models.CASCADE)
    author = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    report_text = models.TextField()
    status = models.CharField(max_length=32)


class DICOMConfiguration(models.Model):
    ae_title = models.CharField(max_length=64)
    host = models.CharField(max_length=128)
    port = models.PositiveIntegerField()
    transfer_syntax = models.CharField(max_length=128)
    enabled = models.BooleanField(default=False)


class ImagingMetadata(models.Model):
    instance = models.ForeignKey('imaging.ImagingInstance', related_name='metadata', on_delete=models.CASCADE)
    tag = models.CharField(max_length=128)
    value = models.TextField()
