from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'super_admin')


class IsAdministrator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['super_admin', 'administrator'])


class IsClinicalStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['super_admin', 'administrator', 'dentist', 'assistant'])


class IsReceptionOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['super_admin', 'administrator', 'receptionist'])


class IsAccountantOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['super_admin', 'administrator', 'accountant'])


class IsStaffMember(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in [
                'super_admin',
                'administrator',
                'dentist',
                'assistant',
                'receptionist',
                'accountant',
            ]
        )
