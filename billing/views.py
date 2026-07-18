from rest_framework import status, viewsets
from .models import Invoice, Payment
from accounts.permissions import IsAccountantOrAdmin
from .serializers import InvoiceSerializer, PaymentSerializer
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAccountantOrAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            instance.delete()
        except DjangoValidationError as exc:
            return Response(
                exc.message_dict,
                status=status.HTTP_400_BAD_REQUEST,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAccountantOrAdmin]
