from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationTemplateViewSet, NotificationViewSet

router = DefaultRouter()
router.register('notification-templates', NotificationTemplateViewSet)
router.register('notifications', NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
