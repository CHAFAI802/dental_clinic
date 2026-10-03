from rest_framework.permissions import BasePermission
from accounts.models import User


def _is_active_authenticated_user(request) -> bool:
    """Return True only for authenticated, active and non-deleted users."""
    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        return False

    # Defensive checks (AnonymousUser doesn't have these attributes).
    if getattr(user, "is_active", True) is not True:
        return False

    if getattr(user, "is_deleted", False) is True:
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
        return _has_any_role(
            request,
            (
                User.Role.SUPER_ADMIN,
                User.Role.ADMINISTRATOR,
            ),
        )

class IsDentist(BasePermission):
    message = "Rôle dentiste requis."

    def has_permission(self, request, view):
        return _has_any_role(
            request,
            (
                User.Role.DENTIST,
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


class IsAppointmentManager(BasePermission):
    """Access for roles that can manage appointments (dentist/receptionist)."""

    message = "Rôle gestionnaire de rendez-vous requis."

    def has_permission(self, request, view):
        return _has_any_role(
            request,
            (
                User.Role.DENTIST,
                User.Role.RECEPTIONIST,
            ),
        )


class InvoiceLinePermission(BasePermission):
    """
    Permissions for InvoiceLine operations.

    Dentist:
        GET     allowed
        POST    allowed
        PATCH   allowed
        DELETE  denied

    Accountant:
        GET     allowed
        POST    denied
        PATCH   denied
        DELETE  denied

    Receptionist:
        GET     allowed
        POST    denied
        PATCH   denied
        DELETE  denied

    Administrator:
        GET     allowed
        POST    denied
        PATCH   denied
        DELETE  denied
    """

    def has_permission(self, request, view):
        action = view.action

        if action in ['list', 'retrieve']:
            return _has_any_role(
                request,
                (
                    User.Role.DENTIST,
                    User.Role.ACCOUNTANT,
                    User.Role.RECEPTIONIST,
                    User.Role.ADMINISTRATOR,
                    User.Role.SUPER_ADMIN,
                ),
            )

        if action in ['create', 'update', 'partial_update']:
            return _has_any_role(
                request,
                (User.Role.DENTIST,),
            )

        if action == 'destroy':
            return False

        return False


class InvoicePermission(BasePermission):
    """
    Invoice is a read-only resource for most clinic roles.

    Authorized clinic roles can view invoices.
    Only administrators can modify the due date.
    Creation and deletion are not exposed through this API.
    """

    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user.role in {
                request.user.Role.ACCOUNTANT,
                request.user.Role.RECEPTIONIST,
                request.user.Role.ADMINISTRATOR,
                request.user.Role.SUPER_ADMIN,
            }

        if request.method == 'PATCH':
            return request.user.role == request.user.Role.ADMINISTRATOR

        return False