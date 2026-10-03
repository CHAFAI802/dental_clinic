from django.contrib import admin

from notifications.models import (
    Notification,
    NotificationEvent,
    NotificationLog,
    NotificationSetting,
    NotificationTemplate,
)


admin.site.register(Notification)
admin.site.register(NotificationEvent)
admin.site.register(NotificationLog)
admin.site.register(NotificationSetting)
admin.site.register(NotificationTemplate)
