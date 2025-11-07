"""
Admin interface for authentication models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CompanyUser, UserSession, ApplicationConfig


@admin.register(CompanyUser)
class CompanyUserAdmin(UserAdmin):
    """Admin interface for CompanyUser model."""

    # Fields to display in list view
    list_display = [
        'email', 'get_full_name', 'employee_id', 'region',
        'department', 'is_active', 'is_staff', 'date_joined'
    ]

    # Fields to filter by
    list_filter = [
        'region', 'department', 'is_active', 'is_staff',
        'is_superuser', 'date_joined', 'last_login'
    ]

    # Fields to search
    search_fields = ['email', 'first_name', 'last_name', 'employee_id']

    # Default ordering
    ordering = ['department', 'last_name', 'first_name']

    # Fields to display in detail view
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'employee_id', 'phone')
        }),
        (_('Company info'), {
            'fields': ('region', 'department', 'apps_access')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('SSO info'), {
            'fields': ('sso_token', 'last_sso_login'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )

    # Fields for add user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'employee_id', 'phone')
        }),
        (_('Company info'), {
            'fields': ('region', 'department', 'apps_access')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )

    # Read-only fields
    readonly_fields = [
        'sso_token', 'last_sso_login', 'date_joined',
        'created_at', 'updated_at', 'last_login'
    ]

    # Actions
    actions = ['refresh_sso_tokens', 'grant_all_apps_access']

    def refresh_sso_tokens(self, request, queryset):
        """Refresh SSO tokens for selected users."""
        count = 0
        for user in queryset:
            user.refresh_sso_token()
            count += 1
        self.message_user(request, f'Refreshed SSO tokens for {count} users.')
    refresh_sso_tokens.short_description = _('Refresh SSO tokens')

    def grant_all_apps_access(self, request, queryset):
        """Grant access to all apps for selected users."""
        apps = ApplicationConfig.objects.filter(is_active=True).values_list('name', flat=True)
        count = 0
        for user in queryset:
            user.apps_access = list(apps)
            user.save(update_fields=['apps_access'])
            count += 1
        self.message_user(request, f'Granted all apps access to {count} users.')
    grant_all_apps_access.short_description = _('Grant access to all apps')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserSession model."""

    list_display = [
        'user', 'app_name', 'ip_address', 'created_at',
        'last_activity', 'expires_at', 'is_expired'
    ]

    list_filter = [
        'app_name', 'created_at', 'expires_at',
        'user__region', 'user__department'
    ]

    search_fields = ['user__email', 'app_name', 'ip_address']

    readonly_fields = [
        'session_key', 'created_at', 'last_activity'
    ]

    ordering = ['-created_at']

    # Custom method to show if session is expired
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = _('Expired')

    # Actions
    actions = ['cleanup_expired_sessions']

    def cleanup_expired_sessions(self, request, queryset):
        """Remove expired sessions."""
        from django.utils import timezone
        expired_sessions = queryset.filter(expires_at__lt=timezone.now())
        count = expired_sessions.count()
        expired_sessions.delete()
        self.message_user(request, f'Cleaned up {count} expired sessions.')
    cleanup_expired_sessions.short_description = _('Clean up expired sessions')


@admin.register(ApplicationConfig)
class ApplicationConfigAdmin(admin.ModelAdmin):
    """Admin interface for ApplicationConfig model."""

    list_display = [
        'display_name', 'name', 'url', 'is_active',
        'requires_sso', 'order', 'updated_at'
    ]

    list_filter = ['is_active', 'requires_sso', 'created_at']

    search_fields = ['name', 'display_name', 'description']

    readonly_fields = ['created_at', 'updated_at']

    ordering = ['display_name']

    fieldsets = (
        (_('Basic Info'), {
            'fields': ('name', 'display_name', 'description')
        }),
        (_('Configuration'), {
            'fields': ('url', 'icon', 'color', 'order')
        }),
        (_('Security'), {
            'fields': ('is_active', 'requires_sso', 'sso_secret')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Actions
    actions = ['activate_apps', 'deactivate_apps', 'enable_sso', 'disable_sso']

    def activate_apps(self, request, queryset):
        """Activate selected applications."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'Activated {count} applications.')
    activate_apps.short_description = _('Activate applications')

    def deactivate_apps(self, request, queryset):
        """Deactivate selected applications."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {count} applications.')
    deactivate_apps.short_description = _('Deactivate applications')

    def enable_sso(self, request, queryset):
        """Enable SSO for selected applications."""
        count = queryset.update(requires_sso=True)
        self.message_user(request, f'Enabled SSO for {count} applications.')
    enable_sso.short_description = _('Enable SSO')

    def disable_sso(self, request, queryset):
        """Disable SSO for selected applications."""
        count = queryset.update(requires_sso=False)
        self.message_user(request, f'Disabled SSO for {count} applications.')
    disable_sso.short_description = _('Disable SSO')


# Customize admin site
admin.site.site_header = _('Company Business Platform Administration')
admin.site.site_title = _('Company Platform Admin')
admin.site.index_title = _('Welcome to Company Platform Administration')
