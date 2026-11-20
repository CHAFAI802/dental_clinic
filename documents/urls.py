from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, DocumentTemplateViewSet
from .guide_views import AdminGuideContentView, UserGuideDocumentView


router = DefaultRouter()
router.register("documents", DocumentViewSet)
router.register("document-templates", DocumentTemplateViewSet)

urlpatterns = [
    path(
        "user-guide/<str:document_format>/",
        UserGuideDocumentView.as_view(),
        name="user-guide-document",
    ),
    path(
        "admin-guide/",
        AdminGuideContentView.as_view(),
        name="admin-guide-content",
    ),
    path("", include(router.urls)),
]
