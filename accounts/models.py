from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from dental_clinic.common import SoftDeleteModel, TimestampedModel


class UserManager(BaseUserManager):
    """User manager enforcing required fields at creation time."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""

        if not email:
            raise ValueError('Email is required')

        email = self.normalize_email(email.strip())

        required_fields = ['first_name', 'last_name', 'role']
        missing = [field for field in required_fields if not extra_fields.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        role = extra_fields.get('role')
        if role not in self.model.Role.values:
            raise ValueError('Invalid role')

        if not password:
            raise ValueError('Password is required')

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser (always SUPER_ADMIN)."""

        if not password:
            raise ValueError('Superuser must have a password.')

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields['role'] = self.model.Role.SUPER_ADMIN

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, SoftDeleteModel):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        ADMINISTRATOR = 'administrator', 'Administrateur'
        DENTIST = 'dentist', 'Dentiste'
        ASSISTANT = 'assistant', 'Assistant dentaire'
        RECEPTIONIST = 'receptionist', 'Réceptionniste'
        ACCOUNTANT = 'accountant', 'Comptable'

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=32, choices=Role.choices)
    timezone = models.CharField(max_length=64, default='Europe/Paris')
    language = models.CharField(max_length=32, default='fr')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        ordering = ['last_name', 'first_name', 'email']
        indexes = [models.Index(fields=['email']), models.Index(fields=['role'])]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"


class UserLoginHistory(TimestampedModel):
    """Track login attempts (successful and failed)."""

    user = models.ForeignKey(
        'accounts.User',
        related_name='login_history',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    login_at = models.DateTimeField()
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    successful = models.BooleanField(default=True)

    class Meta:
        ordering = ['-login_at']
        indexes = [
            models.Index(fields=['user', 'login_at'], name='acc_login_user_login_idx'),
            models.Index(fields=['login_at'], name='acc_login_login_at_idx'),
        ]

    def __str__(self):
        status = 'SUCCESS' if self.successful else 'FAILED'
        return f"{status} login at {self.login_at}"


class AuditLog(TimestampedModel):
    """Store an auditable trace of important actions performed in the app."""

    user = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=128)
    model_name = models.CharField(max_length=128)
    object_id = models.UUIDField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    context = models.CharField(max_length=256, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    sensitive = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at'], name='acc_audit_created_at_idx'),
            models.Index(fields=['user', 'created_at'], name='acc_audit_user_created_idx'),
            models.Index(fields=['model_name', 'object_id'], name='acc_audit_model_object_idx'),
            models.Index(fields=['action', 'created_at'], name='acc_audit_action_created_idx'),
        ]

    def __str__(self):
        obj = f"{self.model_name}:{self.object_id}" if self.object_id else self.model_name
        return f"{self.action} ({obj})"
