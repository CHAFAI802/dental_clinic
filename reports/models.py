from django.db import models
from dental_clinic.common import TimestampedModel


class ReportDefinition(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    query_type = models.CharField(max_length=64)
    parameters = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=False)
    template = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name


class ReportSchedule(TimestampedModel):
    report = models.ForeignKey('reports.ReportDefinition', related_name='schedules', on_delete=models.CASCADE)
    frequency = models.CharField(max_length=64)
    next_run_at = models.DateTimeField()
    recipients = models.JSONField(default=list, blank=True)
    last_run_at = models.DateTimeField(null=True, blank=True)


class ReportExecution(TimestampedModel):
    report = models.ForeignKey('reports.ReportDefinition', related_name='executions', on_delete=models.CASCADE)
    executed_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    executed_at = models.DateTimeField()
    status = models.CharField(max_length=32)
    result_location = models.CharField(max_length=255, blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
