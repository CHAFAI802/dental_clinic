from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register('invoices', InvoiceViewSet)
router.register('payments', PaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
