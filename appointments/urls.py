from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppointmentViewSet, RoomViewSet

router = DefaultRouter()
router.register('appointments', AppointmentViewSet)
router.register('rooms', RoomViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
