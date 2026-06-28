from rest_framework import viewsets
from .models import User, AuditLog
from .permissions import IsAdministrator, IsSuperAdmin
from .serializers import UserSerializer, AuditLogSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserSerializer
    permission_classes = [IsAdministrator]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdmin]
