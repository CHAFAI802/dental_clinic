from accounts.services.authentication import create_authentication_session
from rest_framework.test import APITestCase
from unittest.mock import patch
from accounts.models import AuditLog, User


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
        session, token = create_authentication_session(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        resp = self.client.get('/api/users/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['id'], self.user.id)

    def test_superadmin_list_sees_all_users(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        resp = self.client.get('/api/users/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_non_superadmin_cannot_create_user(self):
        session, token = create_authentication_session(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

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
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

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
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

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

        def test_superadmin_update_user_creates_audit_log(self):
            session, token = create_authentication_session(self.superadmin)
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

            payload = {
                'first_name': 'Updated',
                'last_name': 'User',
                'role': User.Role.RECEPTIONIST,
                'is_active': False,
            }

            resp = self.client.patch(
                f'/api/users/{self.user.pk}/',
                payload,
                format='json',
            )

            self.assertEqual(resp.status_code, 200)

            self.user.refresh_from_db()

            self.assertEqual(self.user.first_name, 'Updated')
            self.assertEqual(self.user.last_name, 'User')
            self.assertEqual(self.user.role, User.Role.RECEPTIONIST)
            self.assertFalse(self.user.is_active)

            log = AuditLog.objects.get(
                action='user.updated',
                model_name='User',
                object_id=str(self.user.pk),
            )

            self.assertEqual(log.user, self.superadmin)

            self.assertEqual(
                log.changes['first_name'],
                {
                    'old': 'User',
                    'new': 'Updated',
                },
            )

            self.assertEqual(
                log.changes['last_name'],
                {
                    'old': 'Example',
                    'new': 'User',
                },
            )

            self.assertEqual(
                log.changes['role'],
                {
                    'old': User.Role.ASSISTANT,
                    'new': User.Role.RECEPTIONIST,
                },
            )

            self.assertEqual(
                log.changes['is_active'],
                {
                    'old': True,
                    'new': False,
                },
            )

            self.assertNotIn('password', log.changes)

    def test_failed_user_update_does_not_create_audit_log(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        payload = {
            'email': 'not-an-email',
        }

        resp = self.client.patch(
            f'/api/users/{self.user.pk}/',
            payload,
            format='json',
        )

        self.assertEqual(resp.status_code, 400)

        self.assertFalse(
            AuditLog.objects.filter(
                action='user.updated',
                model_name='User',
                object_id=str(self.user.pk),
            ).exists()
        )


    def test_user_update_rolls_back_when_audit_fails(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        payload = {
            'first_name': 'Rollback',
        }

        with patch(
            'accounts.views.users.log_audit',
            side_effect=RuntimeError('Audit failure'),
        ):
            with self.assertRaises(RuntimeError):
                self.client.patch(
                    f'/api/users/{self.user.pk}/',
                    payload,
                    format='json',
                )

        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, 'User')

        self.assertFalse(
            AuditLog.objects.filter(
                action='user.updated',
                model_name='User',
                object_id=str(self.user.pk),
            ).exists()
        )


    def test_user_password_update_does_not_write_password_to_audit_log(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        new_password = 'NewUpdatedPassword123!'

        payload = {
            'password': new_password,
        }

        resp = self.client.patch(
            f'/api/users/{self.user.pk}/',
            payload,
            format='json',
        )

        self.assertEqual(resp.status_code, 200)

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password(new_password)
        )

        log = AuditLog.objects.get(
            action='user.updated',
            model_name='User',
            object_id=str(self.user.pk),
        )

        self.assertNotIn('password', log.changes)

    def test_superadmin_create_user_creates_audit_log(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        payload = {
            'email': 'audited@example.com',
            'password': 'NewStrongPassword123!',
            'first_name': 'Audited',
            'last_name': 'User',
            'role': User.Role.RECEPTIONIST,
        }

        resp = self.client.post('/api/users/', payload, format='json')

        self.assertEqual(resp.status_code, 201)

        created_user = User.objects.get(email='audited@example.com')

        from accounts.models import AuditLog

        log = AuditLog.objects.get(
            action='user.created',
            model_name='User',
            object_id=str(created_user.pk),
        )

        self.assertEqual(log.user, self.superadmin)
        self.assertEqual(log.changes['email']['new'], 'audited@example.com')
        self.assertEqual(log.changes['role']['new'], User.Role.RECEPTIONIST)
        self.assertNotIn('password', log.changes)

    def test_failed_user_creation_does_not_create_audit_log(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        payload = {
            'email': 'invalid@example.com',
            'first_name': 'Invalid',
            'last_name': 'User',
            'role': User.Role.RECEPTIONIST,
        }

        resp = self.client.post('/api/users/', payload, format='json')

        self.assertEqual(resp.status_code, 400)

        from accounts.models import AuditLog

        self.assertFalse(
            AuditLog.objects.filter(
                action='user.created',
                model_name='User',
            ).exists()
        )

    def test_user_creation_rolls_back_when_audit_fails(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        payload = {
            'email': 'rollback@example.com',
            'password': 'NewStrongPassword123!',
            'first_name': 'Rollback',
            'last_name': 'User',
            'role': User.Role.RECEPTIONIST,
        }

        with patch(
            'accounts.views.users.log_audit',
            side_effect=RuntimeError('Audit failure'),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    '/api/users/',
                    payload,
                    format='json',
                )

        self.assertFalse(
            User.objects.filter(email='rollback@example.com').exists()
        )

        self.assertFalse(
            AuditLog.objects.filter(
                action='user.created',
                model_name='User',
            ).exists()
        )


    def test_superadmin_can_soft_delete_user(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        response = self.client.delete(
            f"/api/users/{self.user.pk}/"
        )

        self.assertEqual(response.status_code, 204)

        self.user.refresh_from_db()

        self.assertTrue(self.user.is_deleted)
        self.assertIsNotNone(self.user.deleted_at)


    def test_non_superadmin_cannot_delete_user(self):
        session, token = create_authentication_session(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        response = self.client.delete(
            f"/api/users/{self.superadmin.pk}/"
        )

        self.assertEqual(response.status_code, 403)

        self.superadmin.refresh_from_db()

        self.assertFalse(self.superadmin.is_deleted)
        self.assertIsNone(self.superadmin.deleted_at)


    def test_soft_deleted_user_is_not_returned_by_user_list(self):
        session, token = create_authentication_session(self.superadmin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

        response = self.client.delete(
            f"/api/users/{self.user.pk}/"
        )

        self.assertEqual(response.status_code, 204)

        list_response = self.client.get("/api/users/")

        self.assertEqual(list_response.status_code, 200)

        returned_ids = {
            user["id"]
            for user in list_response.data
        }

        self.assertNotIn(self.user.pk, returned_ids)
