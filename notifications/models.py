from django.db import models
from dental_clinic.common import TimestampedModel


class NotificationTemplate(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    channel = models.CharField(max_length=32)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    variables = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Notification(TimestampedModel):
    recipient_user = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    recipient_patient = models.ForeignKey('patients.Patient', null=True, blank=True, on_delete=models.SET_NULL)
    template = models.ForeignKey('notifications.NotificationTemplate', null=True, blank=True, on_delete=models.SET_NULL)
    channel = models.CharField(max_length=32)
    payload = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32)
    error_message = models.TextField(blank=True)


class NotificationLog(TimestampedModel):
    notification = models.ForeignKey('notifications.Notification', related_name='logs', on_delete=models.CASCADE)
    sent_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    attempted_at = models.DateTimeField()
    status = models.CharField(max_length=32)
    response = models.TextField(blank=True)


class NotificationSetting(TimestampedModel):
    user = models.ForeignKey('accounts.User', related_name='notification_settings', on_delete=models.CASCADE)
    channel = models.CharField(max_length=32)
    enabled = models.BooleanField(default=True)
    preferences = models.JSONField(default=dict, blank=True)


class NotificationEvent(TimestampedModel):
    event_type = models.CharField(max_length=64)
    related_object = models.JSONField(default=dict, blank=True)
    triggered_at = models.DateTimeField()
    status = models.CharField(max_length=32)
    triggered_by = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
