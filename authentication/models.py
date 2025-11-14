"""
Authentication models for integrated business platform.
Supports email-based authentication for HK and China staff.
"""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class CompanyUserManager(UserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Set username to email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CompanyUser(AbstractUser):
    """
    Custom user model for company staff in HK and China.
    Uses email as the primary authentication field.
    """

    REGION_CHOICES = [
        ('HK', _('Hong Kong')),
        ('CN', _('China')),
        ('GLOBAL', _('Global')),
    ]

    DEPARTMENT_CHOICES = [
        ('HR', _('Human Resources')),
        ('FINANCE', _('Finance')),
        ('IT', _('Information Technology')),
        ('OPERATIONS', _('Operations')),
        ('SALES', _('Sales & Marketing')),
        ('MANAGEMENT', _('Management')),
        ('ADMIN', _('Administration')),
    ]

    # Override email field to be unique and required
    email = models.EmailField(
        _('Email Address'),
        unique=True,
        help_text=_('Company email address used for login')
    )

    # Company-specific fields
    employee_id = models.CharField(
        _('Employee ID'),
        max_length=20,
        unique=True,
        help_text=_('Unique employee identification number')
    )

    region = models.CharField(
        _('Region'),
        max_length=10,
        choices=REGION_CHOICES,
        default='HK',
        help_text=_('Primary work region')
    )

    department = models.CharField(
        _('Department'),
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        help_text=_('Department/Division')
    )

    phone = models.CharField(
        _('Phone Number'),
        max_length=20,
        blank=True,
        help_text=_('Contact phone number')
    )

    # App access control
    apps_access = models.JSONField(
        _('Allowed Applications'),
        default=list,
        help_text=_('List of applications this user can access'),
        blank=True
    )

    # SSO and session management
    sso_token = models.UUIDField(
        _('SSO Token'),
        default=uuid.uuid4,
        unique=True,
        help_text=_('Single Sign-On token for cross-app authentication')
    )

    last_sso_login = models.DateTimeField(
        _('Last SSO Login'),
        null=True,
        blank=True,
        help_text=_('Last time user logged in via SSO')
    )

    # Password management
    password_change_required = models.BooleanField(
        _('Password Change Required'),
        default=False,
        help_text=_('User must change password on next login')
    )

    # Approval workflow
    is_approved = models.BooleanField(
        _('Is Approved'),
        default=False,
        help_text=_('Whether user registration has been approved by superadmin')
    )

    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users',
        verbose_name=_('Approved By')
    )

    approved_at = models.DateTimeField(
        _('Approved At'),
        null=True,
        blank=True,
        help_text=_('When user was approved')
    )

    # Audit fields
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name=_('Created By')
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['employee_id', 'first_name', 'last_name']

    # Use custom manager
    objects = CompanyUserManager()

    class Meta:
        verbose_name = _('Company User')
        verbose_name_plural = _('Company Users')
        ordering = ['department', 'last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_display_name(self):
        """Get display name for UI."""
        full_name = self.get_full_name()
        return full_name if full_name else self.email

    def has_app_access(self, app_name):
        """Check if user has access to a specific application."""
        return app_name in self.apps_access or self.is_superuser

    def add_app_access(self, app_name):
        """Grant access to an application."""
        if app_name not in self.apps_access:
            self.apps_access.append(app_name)
            self.save(update_fields=['apps_access'])

    def remove_app_access(self, app_name):
        """Revoke access to an application."""
        if app_name in self.apps_access:
            self.apps_access.remove(app_name)
            self.save(update_fields=['apps_access'])

    def refresh_sso_token(self):
        """Generate new SSO token."""
        self.sso_token = uuid.uuid4()
        self.save(update_fields=['sso_token'])
        return self.sso_token


class UserSession(models.Model):
    """
    Track user sessions across applications for SSO.
    """
    user = models.ForeignKey(
        CompanyUser,
        on_delete=models.CASCADE,
        related_name='sso_sessions'
    )

    session_key = models.CharField(
        _('Session Key'),
        max_length=40,
        unique=True
    )

    app_name = models.CharField(
        _('Application'),
        max_length=50,
        help_text=_('Name of the application for this session')
    )

    ip_address = models.GenericIPAddressField(
        _('IP Address'),
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        _('User Agent'),
        blank=True
    )

    expires_at = models.DateTimeField(
        _('Expires At'),
        help_text=_('When this session expires')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.app_name}"

    def is_expired(self):
        """Check if session is expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at


class ApplicationConfig(models.Model):
    """
    Configuration for integrated applications.
    """
    name = models.CharField(
        _('Application Name'),
        max_length=50,
        unique=True,
        help_text=_('Internal name of the application')
    )

    display_name = models.CharField(
        _('Display Name'),
        max_length=100,
        help_text=_('User-friendly name shown in interface')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Brief description of the application')
    )

    url = models.URLField(
        _('Application URL'),
        help_text=_('Base URL for the application')
    )

    icon = models.CharField(
        _('Icon Class'),
        max_length=50,
        default='fas fa-app',
        help_text=_('CSS class for application icon')
    )

    color = models.CharField(
        _('Theme Color'),
        max_length=7,
        default='#007bff',
        help_text=_('Hex color code for application theme')
    )

    is_active = models.BooleanField(
        _('Is Active'),
        default=True,
        help_text=_('Whether this application is available for use')
    )

    requires_sso = models.BooleanField(
        _('Requires SSO'),
        default=True,
        help_text=_('Whether this application uses SSO authentication')
    )

    sso_secret = models.CharField(
        _('SSO Secret'),
        max_length=255,
        help_text=_('Secret key for SSO token validation'),
        blank=True
    )

    order = models.PositiveIntegerField(
        _('Display Order'),
        default=0,
        help_text=_('Order in which to display in the app grid')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Application Configuration')
        verbose_name_plural = _('Application Configurations')
        ordering = ['display_name']

    def __str__(self):
        return self.display_name
