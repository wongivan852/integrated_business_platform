"""
Admin configuration for App Registry.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ApplicationConfig, Department, DepartmentAppAccess, UserAppAccess, AppAccessLog


@admin.register(ApplicationConfig)
class ApplicationConfigAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'category', 'status_badge', 'is_active',
        'maintenance_mode', 'display_order', 'version'
    ]
    list_filter = ['status', 'category', 'is_active', 'maintenance_mode', 'requires_permission']
    search_fields = ['name', 'code', 'description']
    ordering = ['display_order', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'category')
        }),
        ('Display', {
            'fields': ('icon', 'color', 'display_order')
        }),
        ('URL Configuration', {
            'fields': ('url_path', 'external_url', 'internal_port')
        }),
        ('Status & Control', {
            'fields': ('status', 'is_active', 'requires_permission', 'permission_key', 'version')
        }),
        ('Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def status_badge(self, obj):
        colors = {
            'developing': '#6c757d',
            'prototype': '#17a2b8',
            'uat': '#ffc107',
            'softlaunch': '#007bff',
            'production': '#28a745',
            'maintenance': '#fd7e14',
            'deprecated': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'manager', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']


@admin.register(DepartmentAppAccess)
class DepartmentAppAccessAdmin(admin.ModelAdmin):
    list_display = ['department', 'app', 'is_enabled', 'granted_by', 'granted_at']
    list_filter = ['is_enabled', 'department', 'app']
    search_fields = ['department__name', 'app__name']
    ordering = ['department__name', 'app__name']
    autocomplete_fields = ['department', 'app', 'granted_by']


@admin.register(UserAppAccess)
class UserAppAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'app', 'access_level', 'is_enabled', 'granted_by', 'granted_at']
    list_filter = ['access_level', 'is_enabled', 'app']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'app__name']
    ordering = ['user__email', 'app__name']
    autocomplete_fields = ['user', 'app', 'granted_by']


@admin.register(AppAccessLog)
class AppAccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'app', 'action', 'ip_address', 'created_at']
    list_filter = ['action', 'app', 'created_at']
    search_fields = ['user__email', 'app__name', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = ['user', 'app', 'action', 'details', 'ip_address', 'user_agent', 'performed_by', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
