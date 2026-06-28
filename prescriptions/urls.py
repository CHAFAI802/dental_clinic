from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrescriptionViewSet, PrescriptionTemplateViewSet

router = DefaultRouter()
router.register('prescriptions', PrescriptionViewSet)
router.register('prescription-templates', PrescriptionTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
