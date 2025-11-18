"""
QR Code Attendance System Models
Integrated with business platform SSO.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from authentication.models import CompanyUser
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image


class Participant(models.Model):
    """
    Participant model for QR-based attendance tracking.
    Linked to CompanyUser for SSO integration.
    """
    CLASS_CHOICES = [
        ('regular', _('Regular')),
        ('vip', _('VIP')),
        ('student', _('Student')),
        ('staff', _('Staff')),
        ('guest', _('Guest')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unique_id = models.CharField(
        _('Unique ID'),
        max_length=50,
        unique=True,
        default=uuid.uuid4,
        help_text=_('Unique identifier for QR code')
    )

    # Link to SSO user (optional - allows external guests)
    user = models.OneToOneField(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qr_participant',
        help_text=_('Linked SSO account (optional for external participants)')
    )

    # Basic information (used when not linked to SSO user)
    name = models.CharField(_('Full Name'), max_length=100)
    email = models.EmailField(_('Email'), blank=True, null=True)
    phone = models.CharField(_('Phone'), max_length=20, blank=True)

    participant_class = models.CharField(
        _('Participant Class'),
        max_length=20,
        choices=CLASS_CHOICES,
        default='regular'
    )

    qr_code = models.ImageField(
        _('QR Code'),
        upload_to='qr_codes/',
        blank=True,
        help_text=_('Generated QR code image')
    )

    is_active = models.BooleanField(_('Is Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('QR Participant')
        verbose_name_plural = _('QR Participants')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.unique_id})"

    def get_display_name(self):
        """Get display name from SSO user or participant name"""
        if self.user:
            return self.user.get_full_name() or self.user.email
        return self.name

    def get_email(self):
        """Get email from SSO user or participant email"""
        if self.user:
            return self.user.email
        return self.email

    def generate_qr_code(self):
        """Generate QR code for this participant"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.unique_id))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Save to model
        filename = f'qr_{self.unique_id}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        # Generate QR code if it doesn't exist
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)


class QRAttendanceRecord(models.Model):
    """
    QR-based attendance check-in/check-out records with venue tracking.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='qr_records'
    )

    venue = models.ForeignKey(
        'Venue',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_records',
        help_text=_('Venue/Location where check-in occurred')
    )

    time_in = models.DateTimeField(_('Check-In Time'))
    time_out = models.DateTimeField(_('Check-Out Time'), null=True, blank=True)

    duration_minutes = models.IntegerField(
        _('Duration (Minutes)'),
        null=True,
        blank=True,
        help_text=_('Calculated when checked out')
    )

    checked_in = models.BooleanField(
        _('Currently Checked In'),
        default=True,
        help_text=_('True if participant is currently inside venue')
    )

    override_reason = models.TextField(
        _('Override Reason'),
        blank=True,
        help_text=_('Reason for duplicate entry override')
    )

    scanned_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scanned_qr_attendances',
        help_text=_('Operator who scanned this record')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('QR Attendance Record')
        verbose_name_plural = _('QR Attendance Records')
        ordering = ['-time_in']
        indexes = [
            models.Index(fields=['participant', '-time_in']),
            models.Index(fields=['venue', 'checked_in']),
            models.Index(fields=['checked_in']),
        ]

    def __str__(self):
        status = "Checked In" if self.checked_in else "Checked Out"
        return f"{self.participant.name} - {status} at {self.time_in.strftime('%Y-%m-%d %H:%M')}"

    def calculate_duration(self):
        """Calculate duration between check-in and check-out"""
        if self.time_out and self.time_in:
            delta = self.time_out - self.time_in
            self.duration_minutes = int(delta.total_seconds() / 60)
            return self.duration_minutes
        return None

    def checkout(self, time_out=None):
        """Process checkout for this record"""
        from django.utils import timezone
        self.time_out = time_out or timezone.now()
        self.checked_in = False
        self.calculate_duration()
        self.save()


class Venue(models.Model):
    """
    Venue/Location model for multi-venue event management.
    Each venue can have its own capacity settings.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        _('Venue Name'),
        max_length=100,
        help_text=_('Name of the venue/location')
    )

    code = models.CharField(
        _('Venue Code'),
        max_length=50,
        unique=True,
        help_text=_('Short code for the venue (e.g., HALL_A, ROOM_101)')
    )

    location = models.CharField(
        _('Location/Address'),
        max_length=255,
        blank=True,
        help_text=_('Physical address or location description')
    )

    max_capacity = models.IntegerField(
        _('Maximum Capacity'),
        default=100,
        help_text=_('Maximum number of people allowed in this venue')
    )

    warning_threshold = models.IntegerField(
        _('Warning Threshold (%)'),
        default=90,
        help_text=_('Show warning when capacity reaches this percentage')
    )

    enable_capacity_limit = models.BooleanField(
        _('Enable Capacity Limit'),
        default=True,
        help_text=_('Block check-ins when venue is at maximum capacity')
    )

    is_active = models.BooleanField(
        _('Is Active'),
        default=True,
        help_text=_('Whether this venue is currently active')
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Additional venue information')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_venues'
    )
    updated_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_venues'
    )

    class Meta:
        verbose_name = _('Venue')
        verbose_name_plural = _('Venues')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @classmethod
    def get_default_venue(cls):
        """Get or create a default venue for backward compatibility"""
        venue, created = cls.objects.get_or_create(
            code='DEFAULT',
            defaults={
                'name': 'Main Venue',
                'max_capacity': 100,
                'warning_threshold': 90,
                'enable_capacity_limit': True,
                'is_active': True
            }
        )
        return venue

    def get_current_occupancy(self):
        """Get current number of people checked in at this venue"""
        return QRAttendanceRecord.objects.filter(
            venue=self,
            checked_in=True
        ).count()

    def get_available_capacity(self):
        """Get number of available seats in this venue"""
        return self.max_capacity - self.get_current_occupancy()

    def get_occupancy_percentage(self):
        """Get occupancy as percentage for this venue"""
        if self.max_capacity == 0:
            return 0
        return int((self.get_current_occupancy() / self.max_capacity) * 100)

    def is_at_capacity(self):
        """Check if this venue is at maximum capacity"""
        if not self.enable_capacity_limit:
            return False
        return self.get_current_occupancy() >= self.max_capacity

    def is_at_warning_level(self):
        """Check if this venue is at warning threshold"""
        return self.get_occupancy_percentage() >= self.warning_threshold

    def get_checked_in_participants(self):
        """Get list of participants currently checked in at this venue"""
        return Participant.objects.filter(
            qr_records__venue=self,
            qr_records__checked_in=True
        ).distinct()


class AuditLog(models.Model):
    """
    Audit trail for QR attendance system activities.
    """
    ACTION_CHOICES = [
        ('scan_in', _('Scan Check-In')),
        ('scan_out', _('Scan Check-Out')),
        ('override', _('Duplicate Override')),
        ('participant_add', _('Participant Added')),
        ('participant_edit', _('Participant Edited')),
        ('participant_delete', _('Participant Deleted')),
        ('settings_change', _('Settings Changed')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(_('Action'), max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='qr_audit_logs'
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    details = models.TextField(_('Details'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('QR Audit Log')
        verbose_name_plural = _('QR Audit Logs')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
