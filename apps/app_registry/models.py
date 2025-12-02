"""
App Registry Models

Centralized configuration for all business applications in the integrated platform.
Provides single source of truth for app definitions, access control, and status tracking.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class ApplicationConfig(models.Model):
    """
    Central configuration for each business application.

    This replaces:
    - settings.py BUSINESS_APPS
    - apps/app_integrations/registry.py INTEGRATED_APPS
    - authentication.models.ApplicationConfig (merge/migrate)
    """

    STATUS_CHOICES = [
        ('developing', _('Developing')),
        ('prototype', _('Prototype')),
        ('uat', _('UAT')),
        ('softlaunch', _('Soft Launch')),
        ('production', _('Production')),
        ('maintenance', _('Maintenance')),
        ('deprecated', _('Deprecated')),
    ]

    CATEGORY_CHOICES = [
        ('finance', _('Finance')),
        ('hr', _('Human Resources')),
        ('operations', _('Operations')),
        ('sales', _('Sales & CRM')),
        ('admin', _('Administration')),
        ('system', _('System')),
    ]

    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        _('App Code'),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Internal identifier (e.g., expense_claims, leave_management)')
    )
    name = models.CharField(
        _('Display Name'),
        max_length=100,
        help_text=_('User-friendly name shown in dashboard')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Brief description of the application')
    )

    # Display
    icon = models.CharField(
        _('Icon Class'),
        max_length=50,
        default='fas fa-cube',
        help_text=_('Font Awesome icon class (e.g., fas fa-receipt)')
    )
    color = models.CharField(
        _('Color'),
        max_length=20,
        default='#007bff',
        help_text=_('Hex color for app card/button')
    )
    category = models.CharField(
        _('Category'),
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='operations'
    )
    display_order = models.IntegerField(
        _('Display Order'),
        default=100,
        help_text=_('Order in dashboard (lower = first)')
    )

    # URL Configuration
    url_path = models.CharField(
        _('URL Path'),
        max_length=200,
        help_text=_('Internal URL path (e.g., /expense-claims/)')
    )
    external_url = models.URLField(
        _('External URL'),
        blank=True,
        help_text=_('External URL if app runs on separate server')
    )
    internal_port = models.IntegerField(
        _('Internal Port'),
        null=True,
        blank=True,
        help_text=_('Port number if app runs separately')
    )

    # Status & Control
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='developing',
        db_index=True
    )
    is_active = models.BooleanField(
        _('Is Active'),
        default=True,
        help_text=_('Global enable/disable for all users')
    )
    requires_permission = models.BooleanField(
        _('Requires Permission'),
        default=True,
        help_text=_('Whether users need explicit access to use this app')
    )
    permission_key = models.CharField(
        _('Permission Key'),
        max_length=50,
        blank=True,
        help_text=_('Key used in SSO token permissions (e.g., expense_system)')
    )

    # Maintenance
    maintenance_mode = models.BooleanField(
        _('Maintenance Mode'),
        default=False,
        help_text=_('Show maintenance message instead of app')
    )
    maintenance_message = models.TextField(
        _('Maintenance Message'),
        blank=True,
        default='This application is currently under maintenance.'
    )

    # Metadata
    version = models.CharField(
        _('Version'),
        max_length=20,
        default='1.0.0'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_apps'
    )

    class Meta:
        verbose_name = _('Application Configuration')
        verbose_name_plural = _('Application Configurations')
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['category', 'display_order']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_url(self):
        """Get the URL for this app (external or internal)."""
        if self.external_url:
            return self.external_url
        return self.url_path

    def is_available(self):
        """Check if app is available (active and not in maintenance)."""
        return self.is_active and not self.maintenance_mode


class Department(models.Model):
    """
    Department model for organizational grouping.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        _('Department Name'),
        max_length=100,
        unique=True
    )
    code = models.CharField(
        _('Department Code'),
        max_length=20,
        unique=True,
        db_index=True
    )
    description = models.TextField(
        _('Description'),
        blank=True
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        ordering = ['name']

    def __str__(self):
        return self.name


class DepartmentAppAccess(models.Model):
    """
    Control which apps are available to each department.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='app_access'
    )
    app = models.ForeignKey(
        ApplicationConfig,
        on_delete=models.CASCADE,
        related_name='department_access'
    )
    is_enabled = models.BooleanField(
        _('Is Enabled'),
        default=True,
        help_text=_('Whether this department can access this app')
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_department_access'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Department App Access')
        verbose_name_plural = _('Department App Accesses')
        unique_together = [['department', 'app']]
        ordering = ['department__name', 'app__name']

    def __str__(self):
        status = 'enabled' if self.is_enabled else 'disabled'
        return f"{self.department.name} - {self.app.name} ({status})"


class UserAppAccess(models.Model):
    """
    Individual user access control for applications.
    Provides granular permission levels per app.
    """

    ACCESS_LEVEL_CHOICES = [
        ('none', _('No Access')),
        ('view', _('View Only')),
        ('edit', _('View & Edit')),
        ('admin', _('Full Admin')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='app_registry_access'
    )
    app = models.ForeignKey(
        ApplicationConfig,
        on_delete=models.CASCADE,
        related_name='user_access'
    )
    access_level = models.CharField(
        _('Access Level'),
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='view'
    )
    is_enabled = models.BooleanField(
        _('Is Enabled'),
        default=True
    )

    # Audit fields
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_user_app_access'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _('User App Access')
        verbose_name_plural = _('User App Accesses')
        unique_together = [['user', 'app']]
        ordering = ['user__email', 'app__name']
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
            models.Index(fields=['app', 'access_level']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.app.name} ({self.access_level})"

    def can_view(self):
        """Check if user can view the app."""
        return self.is_enabled and self.access_level in ['view', 'edit', 'admin']

    def can_edit(self):
        """Check if user can edit in the app."""
        return self.is_enabled and self.access_level in ['edit', 'admin']

    def can_admin(self):
        """Check if user has admin access."""
        return self.is_enabled and self.access_level == 'admin'


class AppAccessLog(models.Model):
    """
    Audit log for app access events.
    """

    ACTION_CHOICES = [
        ('access_granted', _('Access Granted')),
        ('access_revoked', _('Access Revoked')),
        ('access_modified', _('Access Modified')),
        ('app_accessed', _('App Accessed')),
        ('access_denied', _('Access Denied')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='app_access_logs'
    )
    app = models.ForeignKey(
        ApplicationConfig,
        on_delete=models.SET_NULL,
        null=True,
        related_name='access_logs'
    )
    action = models.CharField(
        _('Action'),
        max_length=30,
        choices=ACTION_CHOICES
    )
    details = models.JSONField(
        _('Details'),
        default=dict,
        blank=True
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
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_app_access_actions'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _('App Access Log')
        verbose_name_plural = _('App Access Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['app', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else 'Unknown'
        app_str = self.app.name if self.app else 'Unknown'
        return f"{user_str} - {self.action} - {app_str}"

    @classmethod
    def log(cls, user, app, action, request=None, performed_by=None, **details):
        """Helper method to create audit log entries."""
        ip_address = None
        user_agent = ''

        if request:
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(
            user=user,
            app=app,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            performed_by=performed_by
        )
