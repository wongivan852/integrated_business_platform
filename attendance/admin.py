"""
Django admin configuration for attendance system.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    Department,
    AttendanceProfile,
    AttendanceRecord,
    AttendanceAdjustment,
    ClientDevice,
    AttendanceSystemConfig
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin interface for Department model"""
    list_display = ['name', 'employee_count', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

    def employee_count(self, obj):
        """Display number of employees in department"""
        return obj.employees.count()
    employee_count.short_description = _('Employees')


@admin.register(AttendanceProfile)
class AttendanceProfileAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceProfile model"""
    list_display = [
        'employee_code',
        'user_full_name',
        'user_email',
        'department',
        'attendance_role',
        'work_schedule',
        'is_active_badge',
        'created_at'
    ]
    list_filter = ['attendance_role', 'is_active', 'department', 'created_at']
    search_fields = [
        'employee_code',
        'user__email',
        'user__first_name',
        'user__last_name',
        'department__name'
    ]
    raw_id_fields = ['user', 'department']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['employee_code']

    fieldsets = (
        (_('User Information'), {
            'fields': ('user', 'employee_code')
        }),
        (_('Attendance Settings'), {
            'fields': ('department', 'attendance_role', 'work_schedule_start', 'work_schedule_end')
        }),
        (_('Status'), {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )

    def user_full_name(self, obj):
        """Display user's full name"""
        return obj.user.get_full_name() or obj.user.email
    user_full_name.short_description = _('Full Name')
    user_full_name.admin_order_field = 'user__first_name'

    def user_email(self, obj):
        """Display user's email"""
        return obj.user.email
    user_email.short_description = _('Email')
    user_email.admin_order_field = 'user__email'

    def work_schedule(self, obj):
        """Display work schedule range"""
        if obj.work_schedule_start and obj.work_schedule_end:
            return f"{obj.work_schedule_start.strftime('%H:%M')} - {obj.work_schedule_end.strftime('%H:%M')}"
        return _('Not set')
    work_schedule.short_description = _('Work Schedule')

    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> Active')
        return format_html('<span style="color: red;">●</span> Inactive')
    is_active_badge.short_description = _('Status')
    is_active_badge.admin_order_field = 'is_active'


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceRecord model"""
    list_display = [
        'employee_code',
        'clock_in_display',
        'clock_out_display',
        'total_hours_display',
        'clock_in_method',
        'is_adjusted_badge',
        'created_at'
    ]
    list_filter = [
        'clock_in_method',
        'clock_out_method',
        'is_adjusted',
        'clock_in',
        'profile__department'
    ]
    search_fields = [
        'profile__employee_code',
        'profile__user__email',
        'profile__user__first_name',
        'profile__user__last_name',
        'notes',
        'device_hostname'
    ]
    raw_id_fields = ['profile']
    readonly_fields = ['total_hours', 'created_at', 'updated_at']
    date_hierarchy = 'clock_in'
    ordering = ['-clock_in']

    fieldsets = (
        (_('Employee'), {
            'fields': ('profile',)
        }),
        (_('Time Tracking'), {
            'fields': ('clock_in', 'clock_out', 'total_hours')
        }),
        (_('Method & Device'), {
            'fields': ('clock_in_method', 'clock_out_method', 'ip_address', 'device_hostname')
        }),
        (_('Adjustment'), {
            'fields': ('is_adjusted', 'notes')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def employee_code(self, obj):
        """Display employee code"""
        return obj.profile.employee_code
    employee_code.short_description = _('Employee Code')
    employee_code.admin_order_field = 'profile__employee_code'

    def clock_in_display(self, obj):
        """Display clock in time"""
        return obj.clock_in.strftime('%Y-%m-%d %H:%M:%S')
    clock_in_display.short_description = _('Clock In')
    clock_in_display.admin_order_field = 'clock_in'

    def clock_out_display(self, obj):
        """Display clock out time"""
        if obj.clock_out:
            return obj.clock_out.strftime('%Y-%m-%d %H:%M:%S')
        return format_html('<span style="color: orange;">●</span> Active')
    clock_out_display.short_description = _('Clock Out')
    clock_out_display.admin_order_field = 'clock_out'

    def total_hours_display(self, obj):
        """Display total hours worked"""
        if obj.total_hours:
            hours = float(obj.total_hours)
            return f"{hours:.2f}h"
        return _('N/A')
    total_hours_display.short_description = _('Total Hours')
    total_hours_display.admin_order_field = 'total_hours'

    def is_adjusted_badge(self, obj):
        """Display adjusted status as badge"""
        if obj.is_adjusted:
            return format_html('<span style="color: orange;">⚠</span> Adjusted')
        return '✓'
    is_adjusted_badge.short_description = _('Adjusted')
    is_adjusted_badge.admin_order_field = 'is_adjusted'


@admin.register(AttendanceAdjustment)
class AttendanceAdjustmentAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceAdjustment model"""
    list_display = [
        'attendance_record_display',
        'adjusted_by_display',
        'adjustment_summary',
        'approved_badge',
        'approved_by_display',
        'created_at'
    ]
    list_filter = ['approved', 'created_at']
    search_fields = [
        'attendance_record__profile__employee_code',
        'adjusted_by__email',
        'approved_by__email',
        'reason'
    ]
    raw_id_fields = ['attendance_record', 'adjusted_by', 'approved_by']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        (_('Record Information'), {
            'fields': ('attendance_record',)
        }),
        (_('Adjustment Details'), {
            'fields': (
                'original_clock_in',
                'new_clock_in',
                'original_clock_out',
                'new_clock_out',
                'reason'
            )
        }),
        (_('Approval'), {
            'fields': ('adjusted_by', 'approved', 'approved_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def attendance_record_display(self, obj):
        """Display attendance record info"""
        return f"{obj.attendance_record.profile.employee_code} - {obj.attendance_record.clock_in.date()}"
    attendance_record_display.short_description = _('Attendance Record')

    def adjusted_by_display(self, obj):
        """Display who made the adjustment"""
        return obj.adjusted_by.get_full_name() or obj.adjusted_by.email
    adjusted_by_display.short_description = _('Adjusted By')
    adjusted_by_display.admin_order_field = 'adjusted_by__email'

    def approved_by_display(self, obj):
        """Display who approved the adjustment"""
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.email
        return _('N/A')
    approved_by_display.short_description = _('Approved By')

    def adjustment_summary(self, obj):
        """Display summary of changes"""
        changes = []
        if obj.new_clock_in and obj.original_clock_in:
            changes.append('Clock In')
        if obj.new_clock_out and obj.original_clock_out:
            changes.append('Clock Out')
        return ', '.join(changes) if changes else _('No changes')
    adjustment_summary.short_description = _('Changes')

    def approved_badge(self, obj):
        """Display approval status as badge"""
        if obj.approved:
            return format_html('<span style="color: green;">✓</span> Approved')
        return format_html('<span style="color: orange;">⏳</span> Pending')
    approved_badge.short_description = _('Status')
    approved_badge.admin_order_field = 'approved'


@admin.register(ClientDevice)
class ClientDeviceAdmin(admin.ModelAdmin):
    """Admin interface for ClientDevice model"""
    list_display = [
        'device_hostname',
        'employee_code',
        'device_type',
        'mac_address',
        'is_active_badge',
        'last_seen_display',
        'created_at'
    ]
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = [
        'device_hostname',
        'mac_address',
        'profile__employee_code',
        'profile__user__email'
    ]
    raw_id_fields = ['profile']
    readonly_fields = ['last_seen', 'created_at']
    ordering = ['-last_seen']

    fieldsets = (
        (_('Device Information'), {
            'fields': ('profile', 'device_hostname', 'mac_address', 'device_type')
        }),
        (_('Status'), {
            'fields': ('is_active', 'last_seen', 'created_at')
        }),
    )

    def employee_code(self, obj):
        """Display employee code"""
        return obj.profile.employee_code
    employee_code.short_description = _('Employee Code')
    employee_code.admin_order_field = 'profile__employee_code'

    def is_active_badge(self, obj):
        """Display active status as badge"""
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> Active')
        return format_html('<span style="color: gray;">●</span> Inactive')
    is_active_badge.short_description = _('Status')
    is_active_badge.admin_order_field = 'is_active'

    def last_seen_display(self, obj):
        """Display last seen time"""
        if obj.last_seen:
            return obj.last_seen.strftime('%Y-%m-%d %H:%M:%S')
        return _('Never')
    last_seen_display.short_description = _('Last Seen')
    last_seen_display.admin_order_field = 'last_seen'


@admin.register(AttendanceSystemConfig)
class AttendanceSystemConfigAdmin(admin.ModelAdmin):
    """Admin interface for AttendanceSystemConfig model (Singleton)"""
    list_display = [
        'auto_clock_out_status',
        'auto_clock_out_time',
        'grace_period_minutes',
        'max_work_hours_per_day',
        'require_approval_status',
        'updated_at'
    ]
    readonly_fields = ['updated_at']

    fieldsets = (
        (_('Auto Clock Out Settings'), {
            'fields': ('auto_clock_out_enabled', 'auto_clock_out_time')
        }),
        (_('Work Rules'), {
            'fields': ('grace_period_minutes', 'max_work_hours_per_day')
        }),
        (_('Approval Settings'), {
            'fields': ('require_approval_for_adjustments',)
        }),
        (_('Metadata'), {
            'fields': ('updated_by', 'updated_at')
        }),
    )

    def has_add_permission(self, request):
        """Prevent adding multiple config records (singleton)"""
        return not AttendanceSystemConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the config record"""
        return False

    def auto_clock_out_status(self, obj):
        """Display auto clock out status"""
        if obj.auto_clock_out_enabled:
            return format_html('<span style="color: green;">✓</span> Enabled')
        return format_html('<span style="color: gray;">✗</span> Disabled')
    auto_clock_out_status.short_description = _('Auto Clock Out')

    def require_approval_status(self, obj):
        """Display approval requirement status"""
        if obj.require_approval_for_adjustments:
            return format_html('<span style="color: green;">✓</span> Required')
        return format_html('<span style="color: gray;">✗</span> Not Required')
    require_approval_status.short_description = _('Approval Required')
