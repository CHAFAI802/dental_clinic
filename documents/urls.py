from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentTemplateVersionViewSet,
    DocumentTemplateViewSet,
    DocumentTypeViewSet,
    DocumentViewSet,
)

router = DefaultRouter()
router.register('document-types', DocumentTypeViewSet)
router.register('documents', DocumentViewSet)
router.register('document-templates', DocumentTemplateViewSet)
router.register('document-template-versions', DocumentTemplateVersionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
