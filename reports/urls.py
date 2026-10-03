from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportDefinitionViewSet

router = DefaultRouter()
router.register('reports', ReportDefinitionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
