from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TreatmentPlanViewSet

router = DefaultRouter()
router.register('treatment-plans', TreatmentPlanViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
