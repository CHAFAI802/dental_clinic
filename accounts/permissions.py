from rest_framework.permissions import BasePermission

from accounts.models import User


def _is_active_authenticated_user(request) -> bool:
    """Return True only for authenticated, active and non-deleted users."""

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return False

    # Defensive checks (AnonymousUser doesn't have these attributes).
    if getattr(user, 'is_active', True) is not True:
        return False
    if getattr(user, 'is_deleted', False) is True:
        return False

    return True


def _has_any_role(request, roles) -> bool:
    if not _is_active_authenticated_user(request):
        return False
    return request.user.role in roles


class IsSuperAdmin(BasePermission):
    message = "Rôle super admin requis."

    def has_permission(self, request, view):
        return _has_any_role(request, (User.Role.SUPER_ADMIN,))


class IsAdministrator(BasePermission):
    message = "Rôle administrateur requis."

    def has_permission(self, request, view):
        return _has_any_role(request, (User.Role.SUPER_ADMIN, User.Role.ADMINISTRATOR))


class IsClinicalStaff(BasePermission):
    """Access for clinical staff (dentist/assistant) and admins."""

    message = "Rôle clinique requis."

    def has_permission(self, request, view):
        return _has_any_role(
            request,
            (
                User.Role.SUPER_ADMIN,
                User.Role.ADMINISTRATOR,
                User.Role.DENTIST,
                User.Role.ASSISTANT,
            ),
        )


class IsReceptionOrAdmin(BasePermission):
    message = "Rôle réceptionniste ou administrateur requis."

    def has_permission(self, request, view):
        return _has_any_role(
            request,
            (
                User.Role.SUPER_ADMIN,
                User.Role.ADMINISTRATOR,
                User.Role.RECEPTIONIST,
            ),
        )


class IsAccountantOrAdmin(BasePermission):
    message = "Rôle comptable ou administrateur requis."

    def has_permission(self, request, view):
        return _has_any_role(
            request,
            (
                User.Role.SUPER_ADMIN,
                User.Role.ADMINISTRATOR,
                User.Role.ACCOUNTANT,
            ),
        )


class IsStaffMember(BasePermission):
    """Access for any staff role defined in the User model."""

    message = "Rôle membre du personnel requis."

    def has_permission(self, request, view):
        return _has_any_role(request, tuple(User.Role.values))
