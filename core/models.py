"""
Core models for integrated business platform.
Includes user app access control and audit logging.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class UserAppAccess(models.Model):
    """
    Control which apps users can access and their roles within each app.
    Implements role-based access control (RBAC) per application.
    """

    ROLE_CHOICES = [
        ('none', _('No Access')),
        ('employee', _('Employee')),
        ('manager', _('Manager')),
        ('admin', _('Admin')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='app_access_permissions',
        verbose_name=_('User')
    )

    app_code = models.CharField(
        _('Application Code'),
        max_length=50,
        help_text=_('Internal application identifier (e.g., expense_claims, leave_system)')
    )

    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee',
        help_text=_('User role within this application')
    )

    is_active = models.BooleanField(
        _('Is Active'),
        default=True,
        help_text=_('Whether this access grant is currently active')
    )

    # Audit fields
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_app_accesses',
        verbose_name=_('Granted By')
    )

    granted_at = models.DateTimeField(
        _('Granted At'),
        auto_now_add=True
    )

    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_app_accesses',
        verbose_name=_('Modified By')
    )

    modified_at = models.DateTimeField(
        _('Modified At'),
        auto_now=True
    )

    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Optional notes about this access grant')
    )

    class Meta:
        verbose_name = _('User App Access')
        verbose_name_plural = _('User App Accesses')
        ordering = ['user__email', 'app_code']
        unique_together = [['user', 'app_code']]
        indexes = [
            models.Index(fields=['user', 'app_code', 'is_active']),
            models.Index(fields=['app_code', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.app_code} ({self.role})"

    def save(self, *args, **kwargs):
        """Override save to track modifications."""
        if self.pk:  # Existing record
            # Track modification in audit log
            original = UserAppAccess.objects.get(pk=self.pk)
            if original.role != self.role or original.is_active != self.is_active:
                AppAccessAuditLog.log_change(
                    user=self.user,
                    app_code=self.app_code,
                    action='role_changed' if original.role != self.role else 'status_changed',
                    old_value={'role': original.role, 'is_active': original.is_active},
                    new_value={'role': self.role, 'is_active': self.is_active},
                    modified_by=self.modified_by
                )
        super().save(*args, **kwargs)


class AppAccessAuditLog(models.Model):
    """
    Audit log for tracking changes to user app access permissions.
    """

    ACTION_CHOICES = [
        ('access_granted', _('Access Granted')),
        ('access_revoked', _('Access Revoked')),
        ('role_changed', _('Role Changed')),
        ('status_changed', _('Status Changed')),
        ('access_denied', _('Access Denied')),
        ('permission_checked', _('Permission Checked')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_access_audit_logs',
        verbose_name=_('User')
    )

    app_code = models.CharField(
        _('Application Code'),
        max_length=50
    )

    action = models.CharField(
        _('Action'),
        max_length=50,
        choices=ACTION_CHOICES
    )

    old_value = models.JSONField(
        _('Old Value'),
        default=dict,
        blank=True,
        help_text=_('Previous state before change')
    )

    new_value = models.JSONField(
        _('New Value'),
        default=dict,
        blank=True,
        help_text=_('New state after change')
    )

    # Who made the change
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='app_access_modifications',
        verbose_name=_('Modified By')
    )

    # Request metadata
    ip_address = models.GenericIPAddressField(
        _('IP Address'),
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        _('User Agent'),
        blank=True
    )

    details = models.JSONField(
        _('Additional Details'),
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('App Access Audit Log')
        verbose_name_plural = _('App Access Audit Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'app_code', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "Unknown"
        return f"{self.action} - {user_str} @ {self.app_code}"

    @classmethod
    def log_change(cls, user, app_code, action, old_value=None, new_value=None,
                   modified_by=None, request=None, **details):
        """
        Helper method to create audit log entries.

        Args:
            user: User whose access was changed
            app_code: Application code
            action: Action type
            old_value: Previous state (dict)
            new_value: New state (dict)
            modified_by: User who made the change
            request: HTTP request (for IP/user agent)
            **details: Additional details to log
        """
        ip_address = None
        user_agent = ''

        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(
            user=user,
            app_code=app_code,
            action=action,
            old_value=old_value or {},
            new_value=new_value or {},
            modified_by=modified_by,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

    @staticmethod
    def get_client_ip(request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SystemConfiguration(models.Model):
    """
    System-wide configuration settings.
    """

    key = models.CharField(
        _('Configuration Key'),
        max_length=100,
        unique=True,
        db_index=True
    )

    value = models.TextField(
        _('Value'),
        help_text=_('Configuration value (can be JSON)')
    )

    value_type = models.CharField(
        _('Value Type'),
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ],
        default='string'
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Human-readable description of this setting')
    )

    is_public = models.BooleanField(
        _('Is Public'),
        default=False,
        help_text=_('Whether this setting can be viewed by non-admin users')
    )

    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Modified By')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('System Configuration')
        verbose_name_plural = _('System Configurations')
        ordering = ['key']

    def __str__(self):
        return self.key

    def get_value(self):
        """Get the configuration value in the appropriate type."""
        import json

        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            return json.loads(self.value)
        return self.value

    @classmethod
    def get_config(cls, key, default=None):
        """Get a configuration value by key."""
        try:
            config = cls.objects.get(key=key)
            return config.get_value()
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, key, value, value_type='string', description='', modified_by=None):
        """Set a configuration value."""
        import json

        # Convert value to string for storage
        if value_type == 'json':
            value_str = json.dumps(value)
        else:
            value_str = str(value)

        config, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value_str,
                'value_type': value_type,
                'description': description,
                'modified_by': modified_by,
            }
        )
        return config
"""
App Status Tracking Models
Track development lifecycle and function-level status for all business applications
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class AppStatus(models.Model):
    """
    Track the overall development status of each business application.
    """

    STATUS_CHOICES = [
        ('developing', _('Developing')),
        ('prototype', _('Prototype')),
        ('uat', _('UAT (User Acceptance Testing)')),
        ('softlaunch', _('Soft Launch')),
        ('production', _('Production')),
        ('deprecated', _('Deprecated')),
    ]

    PRIORITY_CHOICES = [
        ('critical', _('Critical')),
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]

    app_code = models.CharField(
        _('Application Code'),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Internal app identifier (e.g., expense_claims)')
    )

    app_name = models.CharField(
        _('Application Name'),
        max_length=100,
        help_text=_('User-friendly app name')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='developing',
        db_index=True
    )

    priority = models.CharField(
        _('Priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    version = models.CharField(
        _('Version'),
        max_length=20,
        default='0.1.0',
        help_text=_('Current version number')
    )

    port = models.IntegerField(
        _('Port Number'),
        null=True,
        blank=True,
        help_text=_('Port number if app runs on separate server')
    )

    repository_url = models.URLField(
        _('Repository URL'),
        blank=True,
        help_text=_('GitLab/GitHub repository URL')
    )

    # Progress tracking
    completion_percentage = models.IntegerField(
        _('Completion %'),
        default=0,
        help_text=_('Overall completion percentage (0-100)')
    )

    functions_total = models.IntegerField(
        _('Total Functions'),
        default=0,
        help_text=_('Total number of functions/features')
    )

    functions_complete = models.IntegerField(
        _('Complete Functions'),
        default=0,
        help_text=_('Number of completed functions')
    )

    # Dates
    started_at = models.DateField(
        _('Started At'),
        null=True,
        blank=True
    )

    prototype_date = models.DateField(
        _('Prototype Date'),
        null=True,
        blank=True
    )

    uat_date = models.DateField(
        _('UAT Date'),
        null=True,
        blank=True
    )

    softlaunch_date = models.DateField(
        _('Soft Launch Date'),
        null=True,
        blank=True
    )

    production_date = models.DateField(
        _('Production Date'),
        null=True,
        blank=True
    )

    target_launch_date = models.DateField(
        _('Target Launch Date'),
        null=True,
        blank=True
    )

    # Team
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_apps',
        verbose_name=_('App Owner')
    )

    developers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='developed_apps',
        blank=True,
        verbose_name=_('Developers')
    )

    # Notes and issues
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Development notes, issues, blockers')
    )

    known_issues = models.TextField(
        _('Known Issues'),
        blank=True,
        help_text=_('Known bugs and limitations')
    )

    # Meta
    is_active = models.BooleanField(
        _('Is Active'),
        default=True,
        help_text=_('Whether this app is actively maintained')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('App Status')
        verbose_name_plural = _('App Statuses')
        ordering = ['priority', 'app_name']

    def __str__(self):
        return f"{self.app_name} ({self.get_status_display()})"

    def update_completion(self):
        """Auto-calculate completion percentage based on functions."""
        if self.functions_total > 0:
            self.completion_percentage = int(
                (self.functions_complete / self.functions_total) * 100
            )
        else:
            self.completion_percentage = 0

        # Auto-calculate totals from AppFunction
        self.functions_total = self.functions.count()
        self.functions_complete = self.functions.filter(
            status__in=['completed', 'uat', 'softlaunch', 'production']
        ).count()

        self.save(update_fields=['completion_percentage', 'functions_total', 'functions_complete'])

    def get_status_color(self):
        """Get Bootstrap color class for status."""
        colors = {
            'developing': 'secondary',
            'prototype': 'info',
            'uat': 'warning',
            'softlaunch': 'primary',
            'production': 'success',
            'deprecated': 'danger',
        }
        return colors.get(self.status, 'secondary')

    def get_priority_color(self):
        """Get Bootstrap color class for priority."""
        colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary',
        }
        return colors.get(self.priority, 'secondary')


class AppFunction(models.Model):
    """
    Track individual functions/features within each application.
    """

    STATUS_CHOICES = [
        ('planned', _('Planned')),
        ('developing', _('Developing')),
        ('completed', _('Completed')),
        ('uat', _('UAT')),
        ('softlaunch', _('Soft Launch')),
        ('production', _('Production')),
        ('blocked', _('Blocked')),
        ('deprecated', _('Deprecated')),
    ]

    PRIORITY_CHOICES = [
        ('critical', _('Critical')),
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]

    app = models.ForeignKey(
        AppStatus,
        on_delete=models.CASCADE,
        related_name='functions',
        verbose_name=_('Application')
    )

    function_name = models.CharField(
        _('Function Name'),
        max_length=200,
        help_text=_('Name of the function/feature')
    )

    function_code = models.CharField(
        _('Function Code'),
        max_length=50,
        help_text=_('Short identifier (e.g., expense_submit, leave_approve)')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Detailed description of what this function does')
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned',
        db_index=True
    )

    priority = models.CharField(
        _('Priority'),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    # Technical details
    is_api = models.BooleanField(
        _('Is API'),
        default=False,
        help_text=_('Whether this is an API endpoint')
    )

    is_ui = models.BooleanField(
        _('Is UI'),
        default=True,
        help_text=_('Whether this has UI components')
    )

    has_tests = models.BooleanField(
        _('Has Tests'),
        default=False,
        help_text=_('Whether unit/integration tests exist')
    )

    has_documentation = models.BooleanField(
        _('Has Documentation'),
        default=False,
        help_text=_('Whether user documentation exists')
    )

    # Dependencies
    depends_on = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='required_by',
        verbose_name=_('Depends On')
    )

    # Team
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_functions',
        verbose_name=_('Assigned To')
    )

    # Dates
    started_at = models.DateField(
        _('Started At'),
        null=True,
        blank=True
    )

    completed_at = models.DateField(
        _('Completed At'),
        null=True,
        blank=True
    )

    target_date = models.DateField(
        _('Target Completion Date'),
        null=True,
        blank=True
    )

    # Issues and blockers
    is_blocked = models.BooleanField(
        _('Is Blocked'),
        default=False
    )

    blocker_reason = models.TextField(
        _('Blocker Reason'),
        blank=True,
        help_text=_('Why this function is blocked')
    )

    notes = models.TextField(
        _('Notes'),
        blank=True
    )

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('App Function')
        verbose_name_plural = _('App Functions')
        ordering = ['app', 'priority', 'function_name']
        unique_together = [['app', 'function_code']]

    def __str__(self):
        return f"{self.app.app_name} - {self.function_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update parent app completion
        self.app.update_completion()

    def get_status_color(self):
        """Get Bootstrap color class for status."""
        colors = {
            'planned': 'light',
            'developing': 'info',
            'completed': 'success',
            'uat': 'warning',
            'softlaunch': 'primary',
            'production': 'success',
            'blocked': 'danger',
            'deprecated': 'secondary',
        }
        return colors.get(self.status, 'secondary')

    def get_priority_color(self):
        """Get Bootstrap color class for priority."""
        colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary',
        }
        return colors.get(self.priority, 'secondary')


class AppStatusHistory(models.Model):
    """
    Track status changes for audit trail.
    """

    app = models.ForeignKey(
        AppStatus,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('Application')
    )

    old_status = models.CharField(
        _('Old Status'),
        max_length=20
    )

    new_status = models.CharField(
        _('New Status'),
        max_length=20
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Changed By')
    )

    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Reason for status change')
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('App Status History')
        verbose_name_plural = _('App Status Histories')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.app.app_name}: {self.old_status} → {self.new_status}"
