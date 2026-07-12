from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts.models import User, UserLoginHistory


class AuthEndpointsTests(APITestCase):
    def setUp(self):
        self.password = 'StrongPassword123!'
        self.user = User.objects.create_user(
            email='user@example.com',
            password=self.password,
            first_name='User',
            last_name='Example',
            role=User.Role.DENTIST,
        )

    def test_login_success_returns_token_and_logs_attempt(self):
        resp = self.client.post(
            '/api/auth/login/',
            {'email': 'user@example.com', 'password': self.password},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.data)
        self.assertTrue(resp.data['token'])

        self.assertTrue(Token.objects.filter(user=self.user).exists())

        history = UserLoginHistory.objects.order_by('-login_at').first()
        self.assertIsNotNone(history)
        self.assertEqual(history.user, self.user)
        self.assertTrue(history.successful)

    def test_login_invalid_password_logs_failed_attempt(self):
        resp = self.client.post(
            '/api/auth/login/',
            {'email': 'user@example.com', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(resp.status_code, 400)

        history = UserLoginHistory.objects.order_by('-login_at').first()
        self.assertIsNotNone(history)
        # Email exists, so we keep the FK even when successful=False.
        self.assertEqual(history.user, self.user)
        self.assertFalse(history.successful)

    def test_me_requires_authentication(self):
        resp = self.client.get('/api/auth/me/')
        # DRF returns 401 when no authentication credentials are provided.
        self.assertEqual(resp.status_code, 401)

    def test_me_denies_inactive_user_even_with_token(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        token = Token.objects.create(user=self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        resp = self.client.get('/api/auth/me/')
        # TokenAuthentication rejects inactive users at authentication stage.
        self.assertEqual(resp.status_code, 401)

    def test_me_denies_soft_deleted_user_even_with_token(self):
        self.user.is_deleted = True
        self.user.save(update_fields=['is_deleted'])
        token = Token.objects.create(user=self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 403)
