"""SSO admin configuration."""
from django.contrib import admin
from django.utils.html import format_html
from .models import SSOToken, SSOSession, SSOAuditLog


@admin.register(SSOToken)
class SSOTokenAdmin(admin.ModelAdmin):
    """Admin interface for SSO tokens."""

    list_display = [
        'jti_short',
        'user',
        'issued_at',
        'expires_at',
        'status_badge',
        'last_used',
        'ip_address'
    ]
    list_filter = ['is_active', 'is_revoked', 'issued_at']
    search_fields = ['jti', 'user__username', 'user__email', 'ip_address']
    readonly_fields = [
        'jti',
        'token',
        'refresh_token',
        'issued_at',
        'expires_at',
        'last_used',
        'ip_address',
        'user_agent',
        'revoked_at'
    ]
    date_hierarchy = 'issued_at'
    ordering = ['-issued_at']

    fieldsets = (
        ('Token Information', {
            'fields': ('user', 'jti', 'token', 'refresh_token')
        }),
        ('Timestamps', {
            'fields': ('issued_at', 'expires_at', 'last_used')
        }),
        ('Request Metadata', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Status', {
            'fields': ('is_active', 'is_revoked', 'revoked_at', 'revocation_reason')
        }),
    )

    def jti_short(self, obj):
        """Display shortened JTI."""
        return f"{obj.jti[:16]}..."
    jti_short.short_description = 'Token ID'

    def status_badge(self, obj):
        """Display token status as colored badge."""
        if obj.is_revoked:
            color = 'red'
            text = 'Revoked'
        elif not obj.is_active:
            color = 'gray'
            text = 'Inactive'
        elif not obj.is_valid():
            color = 'orange'
            text = 'Expired'
        else:
            color = 'green'
            text = 'Active'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            text
        )
    status_badge.short_description = 'Status'

    actions = ['revoke_tokens']

    def revoke_tokens(self, request, queryset):
        """Admin action to revoke selected tokens."""
        count = 0
        for token in queryset.filter(is_active=True):
            token.revoke("Admin revocation")
            count += 1
        self.message_user(request, f"{count} token(s) revoked successfully.")
    revoke_tokens.short_description = "Revoke selected tokens"


@admin.register(SSOSession)
class SSOSessionAdmin(admin.ModelAdmin):
    """Admin interface for SSO sessions."""

    list_display = [
        'user',
        'app_name',
        'started_at',
        'last_activity',
        'status_badge',
        'ip_address'
    ]
    list_filter = ['is_active', 'app_name', 'started_at']
    search_fields = ['user__username', 'user__email', 'app_name', 'ip_address']
    readonly_fields = ['user', 'token', 'app_name', 'app_url', 'started_at', 'last_activity', 'ip_address', 'user_agent', 'ended_at']
    date_hierarchy = 'started_at'
    ordering = ['-started_at']

    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'token', 'app_name', 'app_url')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'last_activity', 'ended_at')
        }),
        ('Request Metadata', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    def status_badge(self, obj):
        """Display session status as colored badge."""
        if obj.is_active:
            color = 'green'
            text = 'Active'
        else:
            color = 'gray'
            text = 'Ended'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            text
        )
    status_badge.short_description = 'Status'

    actions = ['end_sessions']

    def end_sessions(self, request, queryset):
        """Admin action to end selected sessions."""
        count = 0
        for session in queryset.filter(is_active=True):
            session.end_session()
            count += 1
        self.message_user(request, f"{count} session(s) ended successfully.")
    end_sessions.short_description = "End selected sessions"


@admin.register(SSOAuditLog)
class SSOAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for SSO audit logs."""

    list_display = [
        'created_at',
        'event_type_badge',
        'user',
        'app_name',
        'ip_address'
    ]
    list_filter = ['event_type', 'created_at', 'app_name']
    search_fields = ['user__username', 'user__email', 'ip_address', 'details']
    readonly_fields = [
        'user',
        'event_type',
        'app_name',
        'ip_address',
        'user_agent',
        'details',
        'created_at'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'user', 'app_name')
        }),
        ('Request Metadata', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Details', {
            'fields': ('details', 'created_at')
        }),
    )

    def event_type_badge(self, obj):
        """Display event type as colored badge."""
        color_map = {
            'token_issued': 'green',
            'token_validated': 'blue',
            'token_refreshed': 'cyan',
            'token_revoked': 'orange',
            'login_success': 'green',
            'login_failed': 'red',
            'logout': 'gray',
            'permission_denied': 'red',
        }

        color = color_map.get(obj.event_type, 'blue')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_event_type_display()
        )
    event_type_badge.short_description = 'Event Type'

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False
