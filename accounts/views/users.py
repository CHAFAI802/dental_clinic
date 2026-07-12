from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from accounts.models import User
from accounts.permissions import IsStaffMember
from accounts.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserSerializer
    permission_classes = [IsStaffMember]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if user.role == User.Role.SUPER_ADMIN:
            return User.objects.filter(is_deleted=False)
        return User.objects.filter(pk=user.pk, is_deleted=False)

    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied("Seul un superadmin peut créer des comptes.")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied("Seul un superadmin peut modifier des comptes.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied("Seul un superadmin peut modifier des comptes.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied("Seul un superadmin peut supprimer des comptes.")
        return super().destroy(request, *args, **kwargs)
