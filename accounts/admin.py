from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from accounts.models import AuditLog, User, UserLoginHistory


class UserAdminCreationForm(forms.ModelForm):
    """Admin form for creating users with a properly hashed password."""

    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmation du mot de passe', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'phone',
            'role',
            'timezone',
            'language',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if not password1:
            raise forms.ValidationError('Le mot de passe est obligatoire.')
        if password1 != password2:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserAdminChangeForm(forms.ModelForm):
    """Admin form for updating users; displays password hash as read-only."""

    password = ReadOnlyPasswordHashField(label='Mot de passe')

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    model = User

    list_display = (
        'email',
        'first_name',
        'last_name',
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'is_deleted',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'is_deleted')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Préférences', {'fields': ('role', 'timezone', 'language')}),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        (
            'Audit',
            {
                'fields': (
                    'last_login',
                    'last_login_ip',
                    'created_at',
                    'updated_at',
                    'is_deleted',
                    'deleted_at',
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'phone',
                    'role',
                    'timezone',
                    'language',
                    'password1',
                    'password2',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
    )

    readonly_fields = ('created_at', 'updated_at', 'last_login', 'last_login_ip', 'deleted_at')
    filter_horizontal = ('groups', 'user_permissions')


@admin.register(UserLoginHistory)
class UserLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('login_at', 'user', 'successful', 'source_ip')
    list_filter = ('successful', 'login_at')
    search_fields = ('user__email', 'source_ip', 'user_agent')
    ordering = ('-login_at',)
    readonly_fields = ('created_at', 'updated_at', 'user', 'login_at', 'source_ip', 'user_agent', 'successful')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'model_name', 'object_id', 'user', 'ip_address', 'sensitive')
    list_filter = ('sensitive', 'action', 'model_name', 'created_at')
    search_fields = ('action', 'model_name', 'object_id', 'context', 'ip_address', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'user',
        'action',
        'model_name',
        'object_id',
        'changes',
        'context',
        'ip_address',
        'sensitive',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
