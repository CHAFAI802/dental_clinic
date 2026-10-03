from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImagingStudyViewSet, ImagingInstanceViewSet

router = DefaultRouter()
router.register('imaging-studies', ImagingStudyViewSet)
router.register('imaging-instances', ImagingInstanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
