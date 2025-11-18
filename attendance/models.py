"""
Attendance system models integrated with business platform SSO.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from authentication.models import CompanyUser
import uuid


class Department(models.Model):
    """Department model for organizing employees"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Department Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')

    def __str__(self):
        return self.name


class AttendanceProfile(models.Model):
    """
    Extended attendance profile for CompanyUser.
    Links SSO users with attendance system.
    """
    ROLE_CHOICES = [
        ('employee', _('Employee')),
        ('manager', _('Manager')),
        ('admin', _('Administrator')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CompanyUser,
        on_delete=models.CASCADE,
        related_name='attendance_profile'
    )
    employee_code = models.CharField(
        _('Employee Code'),
        max_length=50,
        unique=True,
        help_text=_('Unique employee identification code')
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    attendance_role = models.CharField(
        _('Attendance Role'),
        max_length=50,
        choices=ROLE_CHOICES,
        default='employee'
    )
    work_schedule_start = models.TimeField(
        _('Work Start Time'),
        null=True,
        blank=True,
        help_text=_('e.g., 09:00')
    )
    work_schedule_end = models.TimeField(
        _('Work End Time'),
        null=True,
        blank=True,
        help_text=_('e.g., 18:00')
    )
    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_code']
        verbose_name = _('Attendance Profile')
        verbose_name_plural = _('Attendance Profiles')

    def __str__(self):
        return f"{self.employee_code} - {self.user.get_full_name()}"


class AttendanceRecord(models.Model):
    """Employee attendance clock in/out records"""

    CLOCK_METHOD_CHOICES = [
        ('auto_wifi', _('Auto WiFi')),
        ('manual', _('Manual')),
        ('admin_adjusted', _('Admin Adjusted')),
        ('auto_eod', _('Auto End of Day')),
        ('qr_code', _('QR Code')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        AttendanceProfile,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    clock_in = models.DateTimeField(_('Clock In Time'))
    clock_out = models.DateTimeField(_('Clock Out Time'), null=True, blank=True)
    clock_in_method = models.CharField(
        _('Clock In Method'),
        max_length=20,
        choices=CLOCK_METHOD_CHOICES,
        default='auto_wifi'
    )
    clock_out_method = models.CharField(
        _('Clock Out Method'),
        max_length=20,
        choices=CLOCK_METHOD_CHOICES,
        null=True,
        blank=True
    )
    total_hours = models.DecimalField(
        _('Total Hours'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    notes = models.TextField(_('Notes'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    device_hostname = models.CharField(_('Device Hostname'), max_length=255, blank=True)
    is_adjusted = models.BooleanField(_('Is Adjusted'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-clock_in']
        verbose_name = _('Attendance Record')
        verbose_name_plural = _('Attendance Records')
        indexes = [
            models.Index(fields=['profile', '-clock_in']),
            models.Index(fields=['clock_in']),
        ]

    def __str__(self):
        return f"{self.profile.employee_code} - {self.clock_in.date()}"

    def calculate_total_hours(self):
        """Calculate total hours between clock_in and clock_out"""
        if self.clock_in and self.clock_out:
            duration = self.clock_out - self.clock_in
            self.total_hours = round(duration.total_seconds() / 3600, 2)
            return self.total_hours
        return None

    def save(self, *args, **kwargs):
        # Auto-calculate total hours before saving
        if self.clock_out:
            self.calculate_total_hours()
        super().save(*args, **kwargs)


class AttendanceAdjustment(models.Model):
    """Audit trail for attendance record adjustments"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attendance_record = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name='adjustments'
    )
    adjusted_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.CASCADE,
        related_name='attendance_adjustments_made'
    )
    original_clock_in = models.DateTimeField(_('Original Clock In'), null=True, blank=True)
    new_clock_in = models.DateTimeField(_('New Clock In'), null=True, blank=True)
    original_clock_out = models.DateTimeField(_('Original Clock Out'), null=True, blank=True)
    new_clock_out = models.DateTimeField(_('New Clock Out'), null=True, blank=True)
    reason = models.TextField(_('Adjustment Reason'))
    approved = models.BooleanField(_('Approved'), default=False)
    approved_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_approvals_made'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Attendance Adjustment')
        verbose_name_plural = _('Attendance Adjustments')

    def __str__(self):
        return f"Adjustment for {self.attendance_record} by {self.adjusted_by}"


class ClientDevice(models.Model):
    """Registered devices for WiFi/QR-based attendance"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(
        AttendanceProfile,
        on_delete=models.CASCADE,
        related_name='devices'
    )
    device_hostname = models.CharField(_('Device Hostname'), max_length=255)
    mac_address = models.CharField(_('MAC Address'), max_length=17, blank=True)
    device_type = models.CharField(
        _('Device Type'),
        max_length=50,
        default='desktop',
        help_text=_('desktop, laptop, mobile')
    )
    is_active = models.BooleanField(_('Is Active'), default=True)
    last_seen = models.DateTimeField(_('Last Seen'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_seen']
        verbose_name = _('Client Device')
        verbose_name_plural = _('Client Devices')
        unique_together = ['profile', 'device_hostname']

    def __str__(self):
        return f"{self.device_hostname} ({self.profile.employee_code})"


class AttendanceSystemConfig(models.Model):
    """System-wide configuration for attendance system"""

    auto_clock_out_enabled = models.BooleanField(
        _('Auto Clock Out Enabled'),
        default=True,
        help_text=_('Automatically clock out employees at end of day')
    )
    auto_clock_out_time = models.TimeField(
        _('Auto Clock Out Time'),
        default='23:59',
        help_text=_('Time to auto clock out (if not clocked out manually)')
    )
    grace_period_minutes = models.IntegerField(
        _('Grace Period (Minutes)'),
        default=15,
        help_text=_('Grace period for late clock-in')
    )
    max_work_hours_per_day = models.DecimalField(
        _('Max Work Hours Per Day'),
        max_digits=4,
        decimal_places=2,
        default=12.0
    )
    require_approval_for_adjustments = models.BooleanField(
        _('Require Approval for Adjustments'),
        default=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Attendance System Configuration')
        verbose_name_plural = _('Attendance System Configuration')

    def __str__(self):
        return "Attendance System Configuration"

    def save(self, *args, **kwargs):
        # Singleton pattern - only one config record
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Get or create the single configuration instance"""
        config, created = cls.objects.get_or_create(pk=1)
        return config
