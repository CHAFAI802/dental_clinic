from rest_framework import viewsets

from accounts.models import AuditLog
from accounts.permissions import IsSuperAdmin
from accounts.serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdmin]