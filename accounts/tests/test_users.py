from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User


class UsersEndpointsTests(APITestCase):
    def setUp(self):
        self.superadmin_password = 'StrongPassword123!'
        self.superadmin = User.objects.create_superuser(
            email='admin@example.com',
            password=self.superadmin_password,
            first_name='Super',
            last_name='Admin',
            role=User.Role.DENTIST,  # must be forced to SUPER_ADMIN by manager
        )

        self.user_password = 'AnotherStrongPassword123!'
        self.user = User.objects.create_user(
            email='user@example.com',
            password=self.user_password,
            first_name='User',
            last_name='Example',
            role=User.Role.ASSISTANT,
        )

    def test_create_superuser_forces_role_super_admin(self):
        self.superadmin.refresh_from_db()
        self.assertEqual(self.superadmin.role, User.Role.SUPER_ADMIN)

    def test_non_superadmin_list_sees_only_self(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        resp = self.client.get('/api/users/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], self.user.id)

    def test_superadmin_list_sees_all_users(self):
        token = Token.objects.create(user=self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        resp = self.client.get('/api/users/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_non_superadmin_cannot_create_user(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            'email': 'new@example.com',
            'password': 'NewStrongPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': User.Role.RECEPTIONIST,
        }
        resp = self.client.post('/api/users/', payload, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_superadmin_create_requires_password(self):
        token = Token.objects.create(user=self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            'email': 'nopassword@example.com',
            'first_name': 'No',
            'last_name': 'Password',
            'role': User.Role.RECEPTIONIST,
        }
        resp = self.client.post('/api/users/', payload, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(User.objects.filter(email='nopassword@example.com').exists())

    def test_superadmin_create_user_success(self):
        token = Token.objects.create(user=self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        payload = {
            'email': 'created@example.com',
            'password': 'NewStrongPassword123!',
            'first_name': 'Created',
            'last_name': 'User',
            'role': User.Role.RECEPTIONIST,
        }
        resp = self.client.post('/api/users/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(User.objects.filter(email='created@example.com').exists())
