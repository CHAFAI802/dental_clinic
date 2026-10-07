import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from website.models import SiteImage, SiteSettings, WorkingHours


def build_test_image(file_name='test-image.jpg', size=(40, 40), color=(255, 0, 0)):
    image = Image.new('RGB', size, color=color)
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(file_name, buffer.read(), content_type='image/jpeg')


class SiteSettingsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='StrongPass123!',
            first_name='Admin',
            last_name='Test',
            role=User.Role.ADMINISTRATOR,
        )
        self.super_admin = User.objects.create_user(
            email='super@example.com',
            password='StrongPass123!',
            first_name='Super',
            last_name='Admin',
            role=User.Role.SUPER_ADMIN,
        )
        self.other = User.objects.create_user(
            email='user@example.com',
            password='StrongPass123!',
            first_name='User',
            last_name='Test',
            role=User.Role.RECEPTIONIST,
        )
        self.site_settings = SiteSettings.get_solo()

    def test_public_get_site_settings_works(self):
        response = self.client.get('/api/site-settings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('branding', response.data['config'])
        self.assertIn('hero', response.data['config'])

    def test_non_authenticated_user_can_read(self):
        response = self.client.get('/api/site-settings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_administrator_can_update(self):
        self.client.force_authenticate(user=self.admin)
        payload = {'config': {'branding': {'cabinetName': 'Cabinet Test'}}}
        response = self.client.patch('/api/site-settings/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.site_settings.refresh_from_db()
        self.assertEqual(self.site_settings.config['branding']['cabinetName'], 'Cabinet Test')

    def test_partial_config_patch_preserves_existing_sections(self):
        config = self.site_settings.config
        config['branding']['logo'] = '/images/logo.png'
        original_theme = config['branding']['theme'].copy()
        sections = {
            'branding', 'nav', 'hero', 'home', 'about', 'services', 'team',
            'technology', 'steps', 'testimonials', 'info', 'cta', 'contact', 'footer',
        }
        self.site_settings.config = config
        self.site_settings.save(update_fields=['config'])
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            '/api/site-settings/',
            {'config': {'branding': {'cabinetName': 'Cabinet B'}}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.site_settings.refresh_from_db()
        self.assertEqual(self.site_settings.config['branding']['cabinetName'], 'Cabinet B')
        self.assertEqual(self.site_settings.config['branding']['logo'], '/images/logo.png')
        self.assertEqual(self.site_settings.config['branding']['theme'], original_theme)
        self.assertTrue(sections.issubset(self.site_settings.config))

    def test_patch_replaces_lists(self):
        self.client.force_authenticate(user=self.admin)
        updated_links = [
            {'label': 'Accueil personnalisé', 'to': '/'},
            {'label': 'Contact', 'to': '/contact'},
        ]

        response = self.client.patch(
            '/api/site-settings/',
            {'config': {'nav': {'links': updated_links}}},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.site_settings.refresh_from_db()
        self.assertEqual(self.site_settings.config['nav']['links'], updated_links)

    def test_super_admin_can_update(self):
        self.client.force_authenticate(user=self.super_admin)
        payload = {'config': {'hero': {'title': 'Nouveau titre'}}}
        response = self.client.patch('/api/site-settings/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.site_settings.refresh_from_db()
        self.assertEqual(self.site_settings.config['hero']['title'], 'Nouveau titre')

    def test_other_roles_cannot_update(self):
        other_roles = [User.Role.DENTIST, User.Role.ASSISTANT, User.Role.RECEPTIONIST, User.Role.ACCOUNTANT]
        for role in other_roles:
            with self.subTest(role=role):
                user = self.other
                if role != User.Role.RECEPTIONIST:
                    user = User.objects.create_user(
                        email=f'{role}@example.com',
                        password='StrongPass123!',
                        first_name='Other',
                        last_name='Role',
                        role=role,
                    )
                self.client.force_authenticate(user=user)
                response = self.client.patch(
                    '/api/site-settings/',
                    {'config': {'branding': {'cabinetName': 'Interdit'}}},
                    format='json',
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_update(self):
        response = self.client.patch(
            '/api/site-settings/',
            {'config': {'branding': {'cabinetName': 'Interdit'}}},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_multiple_site_settings_are_not_created_accidentally(self):
        with self.assertRaises(ValueError):
            SiteSettings.objects.create(config={'branding': {'cabinetName': 'Second'}})


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='dental-site-images-'))
class SiteImageAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='admin-img@example.com',
            password='StrongPass123!',
            first_name='Admin',
            last_name='Image',
            role=User.Role.ADMINISTRATOR,
        )
        self.super_admin = User.objects.create_user(
            email='super-img@example.com',
            password='StrongPass123!',
            first_name='Super',
            last_name='Image',
            role=User.Role.SUPER_ADMIN,
        )
        self.other = User.objects.create_user(
            email='user-img@example.com',
            password='StrongPass123!',
            first_name='User',
            last_name='Image',
            role=User.Role.RECEPTIONIST,
        )

    def test_public_read_if_needed(self):
        image = SiteImage.objects.create(key='logo', image=build_test_image('logo.jpg'))
        response = self.client.get('/api/site-images/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['key'] == image.key for item in response.data))

    def test_administrator_can_upload(self):
        self.client.force_authenticate(user=self.admin)
        payload = {'key': 'hero', 'alt': 'Hero alt', 'image': build_test_image('hero.jpg')}
        response = self.client.post('/api/site-images/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['key'], 'hero')

    def test_super_admin_can_upload(self):
        self.client.force_authenticate(user=self.super_admin)
        payload = {'key': 'favicon', 'alt': 'Favicon alt', 'image': build_test_image('favicon.jpg')}
        response = self.client.post('/api/site-images/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['key'], 'favicon')

    def test_other_roles_cannot_upload(self):
        self.client.force_authenticate(user=self.other)
        payload = {'key': 'not-allowed', 'alt': 'Nope', 'image': build_test_image('nope.jpg')}
        response = self.client.post('/api/site-images/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_image_url_is_generated(self):
        image = SiteImage.objects.create(key='logo', image=build_test_image('logo.jpg'))
        self.assertIn('/media/', image.get_absolute_url())
        response = self.client.get('/api/site-images/')
        self.assertIn('/media/', response.data[0]['url'])

    def test_deletion_is_protected(self):
        image = SiteImage.objects.create(key='logo', image=build_test_image('logo.jpg'))
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f'/api/site-images/{image.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_replacement_is_protected(self):
        image = SiteImage.objects.create(key='logo', image=build_test_image('logo.jpg'))
        self.client.force_authenticate(user=self.other)
        payload = {'alt': 'Updated alt'}
        response = self.client.patch(f'/api/site-images/{image.pk}/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class WorkingHoursModelTests(TestCase):
    def test_working_hours_stays_independent_from_appointments(self):
        fields = WorkingHours._meta.get_fields()
        related_models = [
            field.related_model.__name__
            for field in fields
            if hasattr(field, 'related_model') and field.related_model is not None
        ]
        self.assertNotIn('Appointment', related_models)
