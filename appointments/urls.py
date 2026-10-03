from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentViewSet,
    RoomViewSet,
    AppointmentRequestView,
    AppointmentSlotsView,
)

router = DefaultRouter()

router.register('appointments', AppointmentViewSet)
router.register('rooms', RoomViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path(
        'appointment-request/',
        AppointmentRequestView.as_view(),
        name='appointment-request',
    ),
    path(
        'appointment-slots/',
        AppointmentSlotsView.as_view(),
        name='appointment-slots',
    ),
]
