from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from accounts.models import User
from accounts.permissions import IsStaffMember, IsSuperAdmin


class PermissionsUnitTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_is_staff_member_denies_anonymous(self):
        request = self.factory.get('/api/users/')
        request.user = AnonymousUser()
        self.assertFalse(IsStaffMember().has_permission(request, None))

    def test_is_staff_member_denies_deleted_user(self):
        user = User.objects.create_user(
            email='user@example.com',
            password='StrongPassword123!',
            first_name='User',
            last_name='Example',
            role=User.Role.DENTIST,
        )
        user.is_deleted = True
        user.save(update_fields=['is_deleted'])

        request = self.factory.get('/api/users/')
        request.user = user
        self.assertFalse(IsStaffMember().has_permission(request, None))

    def test_is_super_admin_allows_super_admin(self):
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='StrongPassword123!',
            first_name='Super',
            last_name='Admin',
            role=User.Role.DENTIST,
        )

        request = self.factory.get('/api/audit-logs/')
        request.user = user
        self.assertTrue(IsSuperAdmin().has_permission(request, None))
