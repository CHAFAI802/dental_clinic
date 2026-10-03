from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, PaymentViewSet, EstimateViewSet, CreditNoteViewSet, PaymentMethodViewSet, PrestationViewSet, PrestationCategoryViewSet, PrestationTarifViewSet, InvoiceLineViewSet

router = DefaultRouter()
router.register('invoices', InvoiceViewSet)
router.register('payments', PaymentViewSet)
router.register('estimates', EstimateViewSet)
router.register('credit-notes', CreditNoteViewSet)
router.register('payment-methods', PaymentMethodViewSet)
router.register('prestations', PrestationViewSet)
router.register('prestation-categories', PrestationCategoryViewSet)
router.register('prestation-tarifs', PrestationTarifViewSet)
router.register('invoice-lines', InvoiceLineViewSet)
urlpatterns = [
    path('', include(router.urls)),
]
