from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import WorkingHoursViewSet

router = DefaultRouter()
router.register('working-hours', WorkingHoursViewSet)

urlpatterns = [
    path('', include(router.urls)),
]