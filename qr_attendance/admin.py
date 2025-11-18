"""
QR Attendance Admin Interface
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Participant, QRAttendanceRecord, Venue, AuditLog


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    """Admin interface for Venues"""
    list_display = [
        'name',
        'code',
        'location',
        'max_capacity',
        'current_occupancy_display',
        'occupancy_status',
        'is_active'
    ]
    list_filter = ['is_active', 'enable_capacity_limit']
    search_fields = ['name', 'code', 'location']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    fieldsets = (
        ('Venue Information', {
            'fields': ('name', 'code', 'location', 'description')
        }),
        ('Capacity Settings', {
            'fields': ('max_capacity', 'warning_threshold', 'enable_capacity_limit')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def current_occupancy_display(self, obj):
        """Display current occupancy"""
        return f"{obj.get_current_occupancy()} / {obj.max_capacity}"
    current_occupancy_display.short_description = 'Current Occupancy'

    def occupancy_status(self, obj):
        """Display occupancy status with color"""
        percentage = obj.get_occupancy_percentage()
        if obj.is_at_capacity():
            color = 'red'
            status = 'AT CAPACITY'
        elif obj.is_at_warning_level():
            color = 'orange'
            status = 'WARNING'
        else:
            color = 'green'
            status = 'NORMAL'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({}%)</span>',
            color, status, percentage
        )
    occupancy_status.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Save model with user tracking"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    """Admin interface for Participants"""
    list_display = [
        'name',
        'participant_class',
        'email',
        'phone',
        'sso_user_link',
        'qr_code_display',
        'is_active',
        'created_at'
    ]
    list_filter = ['participant_class', 'is_active', 'created_at']
    search_fields = ['name', 'email', 'phone', 'unique_id']
    readonly_fields = ['unique_id', 'qr_code_preview', 'created_at', 'updated_at']

    fieldsets = (
        ('Participant Information', {
            'fields': ('name', 'email', 'phone', 'participant_class')
        }),
        ('SSO Integration', {
            'fields': ('user',),
            'description': 'Link to company SSO user (optional for external guests)'
        }),
        ('QR Code', {
            'fields': ('unique_id', 'qr_code', 'qr_code_preview')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )

    def sso_user_link(self, obj):
        """Display SSO user link"""
        if obj.user:
            return format_html(
                '<span style="color: green;">✓ {}</span>',
                obj.user.username
            )
        return format_html('<span style="color: gray;">External Guest</span>')
    sso_user_link.short_description = 'SSO User'

    def qr_code_display(self, obj):
        """Display small QR code thumbnail"""
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                obj.qr_code.url
            )
        return '-'
    qr_code_display.short_description = 'QR Code'

    def qr_code_preview(self, obj):
        """Display larger QR code preview in detail view"""
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-width: 300px; border: 2px solid #ddd; padding: 10px;" />',
                obj.qr_code.url
            )
        return 'QR code will be generated upon save'
    qr_code_preview.short_description = 'QR Code Preview'


@admin.register(QRAttendanceRecord)
class QRAttendanceRecordAdmin(admin.ModelAdmin):
    """Admin interface for QR Attendance Records"""
    list_display = [
        'participant',
        'venue',
        'time_in',
        'time_out',
        'duration_display',
        'checked_in_status',
        'scanned_by',
    ]
    list_filter = ['checked_in', 'venue', 'time_in', 'participant__participant_class']
    search_fields = ['participant__name', 'venue__name', 'scanned_by__username']
    readonly_fields = ['id', 'duration_display']
    date_hierarchy = 'time_in'

    fieldsets = (
        ('Participant & Venue', {
            'fields': ('participant', 'venue')
        }),
        ('Check-In/Out Times', {
            'fields': ('time_in', 'time_out', 'duration_display', 'checked_in')
        }),
        ('System Information', {
            'fields': ('scanned_by', 'id')
        }),
    )

    def checked_in_status(self, obj):
        """Display check-in status with color"""
        if obj.checked_in:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Checked In</span>'
            )
        return format_html(
            '<span style="color: gray;">Checked Out</span>'
        )
    checked_in_status.short_description = 'Status'

    def duration_display(self, obj):
        """Display duration"""
        duration = obj.get_duration()
        if duration:
            return duration
        return '-'
    duration_display.short_description = 'Duration'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('participant', 'scanned_by')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for Audit Logs"""
    list_display = [
        'created_at',
        'action',
        'user',
        'participant',
        'ip_address',
        'details_short'
    ]
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'participant__name', 'details', 'ip_address']
    readonly_fields = ['id', 'created_at', 'action', 'user', 'participant', 'details', 'ip_address']
    date_hierarchy = 'created_at'

    def details_short(self, obj):
        """Display shortened details"""
        if obj.details and len(obj.details) > 50:
            return obj.details[:50] + '...'
        return obj.details or '-'
    details_short.short_description = 'Details'

    def has_add_permission(self, request):
        """Prevent manual creation of audit logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Prevent editing of audit logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs (for compliance)"""
        return request.user.is_superuser
