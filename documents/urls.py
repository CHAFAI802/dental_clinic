from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentTemplateViewSet

router = DefaultRouter()
router.register('documents', DocumentViewSet)
router.register('document-templates', DocumentTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
