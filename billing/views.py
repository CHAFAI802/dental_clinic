from rest_framework import status, viewsets
from .models import Invoice, Payment, Estimate, CreditNote, InvoiceLine, PaymentMethod, Prestation, PrestationCategory, PrestationTarif
from accounts.permissions import IsAccountantOrAdmin,IsAdministrator,InvoiceLinePermission,InvoicePermission
from .serializers import InvoiceSerializer, PaymentSerializer, EstimateSerializer, CreditNoteSerializer, InvoiceLineSerializer, PaymentMethodSerializer, PrestationSerializer, PrestationCategorySerializer, PrestationTarifSerializer
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError


class PrestationCategoryViewSet(viewsets.ModelViewSet):
    queryset = PrestationCategory.objects.all()
    serializer_class = PrestationCategorySerializer
    permission_classes = [IsAdministrator]

class PrestationViewSet(viewsets.ModelViewSet):
    queryset = Prestation.objects.all()
    serializer_class = PrestationSerializer
    permission_classes = [IsAdministrator]

class PrestationTarifViewSet(viewsets.ModelViewSet):
    queryset = PrestationTarif.objects.all()
    serializer_class = PrestationTarifSerializer
    permission_classes = [IsAdministrator]

class EstimateViewSet(viewsets.ModelViewSet):
    queryset = Estimate.objects.all()
    serializer_class = EstimateSerializer

class InvoiceLineViewSet(viewsets.ModelViewSet):
    queryset = InvoiceLine.objects.all()
    serializer_class = InvoiceLineSerializer
    permission_classes = [InvoiceLinePermission]


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [InvoicePermission]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAccountantOrAdmin]

class CreditNoteViewSet(viewsets.ModelViewSet):
    queryset = CreditNote.objects.all()
    serializer_class = CreditNoteSerializer
    permission_classes = [IsAccountantOrAdmin]

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAccountantOrAdmin]
