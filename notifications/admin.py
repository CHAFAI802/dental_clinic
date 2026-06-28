from django.contrib import admin
from .models import NotificationTemplate, Notification

admin.site.register(NotificationTemplate)
admin.site.register(Notification)
