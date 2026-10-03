from django.db import transaction
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from accounts.models import User
from accounts.permissions import IsStaffMember
from accounts.serializers import UserSerializer
from accounts.services.audit import log_audit


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

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied("Seul un superadmin peut créer des comptes.")

        response = super().create(request, *args, **kwargs)

        log_audit(
            action="user.created",
            model_name="User",
            object_id=response.data["id"],
            user=request.user,
            changes={
                "email": {
                    "old": None,
                    "new": response.data["email"],
                },
                "first_name": {
                    "old": None,
                    "new": response.data["first_name"],
                },
                "last_name": {
                    "old": None,
                    "new": response.data["last_name"],
                },
                "role": {
                    "old": None,
                    "new": response.data["role"],
                },
                "is_active": {
                    "old": None,
                    "new": response.data["is_active"],
                },
            },
            context={
                "source": "api",
                "endpoint": request.path,
                "method": request.method,
            },
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return response

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied(
                "Seul un superadmin peut modifier des comptes."
            )

        instance = self.get_object()

        old_values = {
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "role": instance.role,
            "is_active": instance.is_active,
        }

        response = super().update(request, *args, **kwargs)

        instance.refresh_from_db()

        changes = {}

        for field, old_value in old_values.items():
            new_value = getattr(instance, field)

            if old_value != new_value:
                changes[field] = {
                    "old": old_value,
                    "new": new_value,
                }

        password_changed = "password" in request.data
        if changes or password_changed:
            log_audit(
                action="user.updated",
                model_name="User",
                object_id=instance.pk,
                user=request.user,
                changes=changes,
                context={
                    "source": "api",
                    "endpoint": request.path,
                    "method": request.method,
                },
                ip_address=request.META.get("REMOTE_ADDR"),
            )

        return response

    def partial_update(self, request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied("Seul un superadmin peut modifier des comptes.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.role != User.Role.SUPER_ADMIN:
            raise PermissionDenied("Seul un superadmin peut supprimer des comptes.")
        return super().destroy(request, *args, **kwargs)
