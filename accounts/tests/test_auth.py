from accounts.models import AuthenticationSession
from rest_framework.test import APITestCase
from accounts.services.authentication import (
    AUTHENTICATION_SESSION_LIFETIME,
    create_authentication_session,
    hash_authentication_credential,
)
from accounts.models import User, UserLoginHistory
from datetime import timedelta

from django.utils import timezone

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
        session = AuthenticationSession.objects.get(user=self.user)
        duration = session.expires_at - session.created_at
        self.assertAlmostEqual(
        duration.total_seconds(),
        AUTHENTICATION_SESSION_LIFETIME.total_seconds(),
        delta=1,
        msg="Authentication session lifetime is not as expected.",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.data)
        self.assertTrue(resp.data['token'])

        self.assertTrue(AuthenticationSession.objects.filter(user=self.user).exists())

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
        session, token = create_authentication_session(self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.get('/api/auth/me/')
        # AuthenticationSessionAuthentication rejects inactive users at authentication stage.
        self.assertEqual(resp.status_code, 401)

    def test_me_denies_soft_deleted_user_even_with_token(self):
        self.user.is_deleted = True
        self.user.save(update_fields=['is_deleted'])
        session, token = create_authentication_session(self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 401)

    def test_login_logout_relogin_rotates_and_revokes_credentials(self):
        login_1 = self.client.post(
            '/api/auth/login/',
            {'email': 'user@example.com', 'password': self.password},
            format='json',
        )
        self.assertEqual(login_1.status_code, 200)
        token_a = login_1.data['token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_a}')
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)

        logout = self.client.post('/api/auth/logout/')
        self.assertEqual(logout.status_code, 200)

        session_a = AuthenticationSession.objects.get(
            token_hash=hash_authentication_credential(token_a)
        )
        self.assertIsNotNone(session_a.revoked_at)
        self.assertEqual(
            session_a.revocation_reason,
            AuthenticationSession.RevocationReason.LOGOUT,
        )

        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

        login_2 = self.client.post(
            '/api/auth/login/',
            {'email': 'user@example.com', 'password': self.password},
            format='json',
        )
        self.assertEqual(login_2.status_code, 200)
        token_b = login_2.data['token']

        self.assertNotEqual(token_a, token_b)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_b}')
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)

    def test_expired_authentication_session_is_rejected(self):
        session, token = create_authentication_session(self.user)

        session.expires_at = timezone.now() - timedelta(seconds=1)
        session.save(update_fields=["expires_at"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        resp = self.client.get("/api/auth/me/")

        self.assertEqual(resp.status_code, 401)

    def test_revoking_one_session_does_not_revoke_another(self):
        session_a, token_a = create_authentication_session(self.user)
        session_b, token_b = create_authentication_session(self.user)

        self.assertNotEqual(token_a, token_b)
        self.assertNotEqual(session_a.pk, session_b.pk)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_a}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_b}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

        session_a.revoked_at = timezone.now()
        session_a.revocation_reason = (
            AuthenticationSession.RevocationReason.LOGOUT
        )
        session_a.save(update_fields=["revoked_at", "revocation_reason"])

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_a}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token_b}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

    def test_login_is_locked_after_five_failed_attempts(self):
        login_url = "/api/auth/login/"

        # Successful login first: verifies the account/password work
        # and that AXES_RESET_ON_SUCCESS starts from a clean state.
        response = self.client.post(
            login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        self.client.post("/api/auth/logout/", format="json")

        # Five invalid attempts are allowed but recorded as failures.
        for attempt in range(5):
            response = self.client.post(
                login_url,
                {
                    "email": self.user.email,
                    "password": "WrongPassword123!",
                },
                format="json",
            )

            if attempt < 4:
                self.assertEqual(response.status_code, 400)
            else:
                self.assertEqual(response.status_code, 429)

        # Once locked, even the correct password is rejected.
        response = self.client.post(
            login_url,
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 429)

    def test_login_unknown_email_logs_failed_attempt_without_user(self):
        resp = self.client.post(
            "/api/auth/login/",
            {
                "email": "unknown@example.com",
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

        history = UserLoginHistory.objects.order_by("-login_at").first()
        self.assertIsNotNone(history)
        self.assertIsNone(history.user)
        self.assertFalse(history.successful)

    def test_login_inactive_user_logs_failed_attempt(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        resp = self.client.post(
            "/api/auth/login/",
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(resp.status_code, 400)

        history = UserLoginHistory.objects.order_by("-login_at").first()
        self.assertIsNotNone(history)
        self.assertEqual(history.user, self.user)
        self.assertFalse(history.successful)

    def test_login_history_keeps_user_after_soft_delete(self):
        history = UserLoginHistory.objects.create(
            user=self.user,
            login_at=timezone.now(),
            successful=True,
        )

        self.user.is_deleted = True
        self.user.save(update_fields=["is_deleted"])

        history.refresh_from_db()

        self.assertEqual(history.user, self.user)
        self.assertTrue(history.user.is_deleted)

    def test_login_history_records_client_ip_and_user_agent(self):
        self.client.post(
            "/api/auth/login/",
            {
                "email": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_FORWARDED_FOR="203.0.113.10, 10.0.0.5",
            HTTP_USER_AGENT="DentalClinicTestBrowser/1.0",
        )

        history = UserLoginHistory.objects.order_by("-login_at").first()

        self.assertIsNotNone(history)
        self.assertEqual(history.source_ip, "203.0.113.10")
        self.assertEqual(
            history.user_agent,
            "DentalClinicTestBrowser/1.0",
        )
        self.assertTrue(history.successful)
