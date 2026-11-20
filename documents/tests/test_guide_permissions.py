from rest_framework.test import APITestCase

from accounts.models import User


class AdminGuidePermissionTests(APITestCase):
    def setUp(self):
        self.roles = [
            User.Role.SUPER_ADMIN,
            User.Role.ADMINISTRATOR,
            User.Role.DENTIST,
            User.Role.ASSISTANT,
            User.Role.RECEPTIONIST,
            User.Role.ACCOUNTANT,
        ]

        self.users = {
            role: User.objects.create_user(
                email=f"{role}@guide-test.example",
                password="test-password",
                first_name="Guide",
                last_name="Test",
                role=role,
            )
            for role in self.roles
        }

        self.admin_guide_url = "/api/admin-guide/"
        self.user_guide_url = "/api/user-guide/pdf/"

    def test_only_administrator_roles_can_read_admin_guide(self):
        allowed_roles = {
            User.Role.SUPER_ADMIN,
            User.Role.ADMINISTRATOR,
        }

        for role, user in self.users.items():
            with self.subTest(role=role):
                self.client.force_authenticate(user=user)

                response = self.client.get(self.admin_guide_url)

                expected_status = 200 if role in allowed_roles else 403
                self.assertEqual(response.status_code, expected_status)

    def test_admin_guide_returns_expected_structure(self):
        self.client.force_authenticate(
            user=self.users[User.Role.ADMINISTRATOR]
        )

        response = self.client.get(self.admin_guide_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["title"],
            "Guide administrateur Dental Clinic",
        )
        self.assertEqual(response.data["version"], "1.0")
        self.assertIsInstance(response.data["sections"], list)
        self.assertTrue(response.data["sections"])

        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_anonymous_user_cannot_read_admin_guide(self):
        response = self.client.get(self.admin_guide_url)

        self.assertIn(response.status_code, (401, 403))

    def test_user_guide_remains_available_to_all_authenticated_roles(self):
        for role, user in self.users.items():
            with self.subTest(role=role):
                self.client.force_authenticate(user=user)

                response = self.client.get(self.user_guide_url)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "application/pdf")
