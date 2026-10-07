from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SiteImageViewSet, SiteSettingsAPIView, WorkingHoursViewSet

router = DefaultRouter()
router.register('site-images', SiteImageViewSet)
router.register('working-hours', WorkingHoursViewSet)

urlpatterns = [
    path('site-settings/', SiteSettingsAPIView.as_view(), name='site-settings'),
    path('', include(router.urls)),
]