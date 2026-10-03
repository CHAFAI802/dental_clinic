from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OdontogramViewSet, ToothViewSet

router = DefaultRouter()
router.register('odontograms', OdontogramViewSet)
router.register('teeth', ToothViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
