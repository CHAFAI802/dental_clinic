from rest_framework import viewsets
from .models import NotificationTemplate, Notification
from accounts.permissions import IsAdministrator
from .serializers import NotificationTemplateSerializer, NotificationSerializer


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    queryset = NotificationTemplate.objects.filter(is_active=True)
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAdministrator]


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAdministrator]
