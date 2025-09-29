"""
Unified User Model for Krystal Company Applications
Replaces authentication.models.CompanyUser
"""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class KrystalUserManager(UserManager):
    """Unified user manager for email-based authentication across all Krystal apps."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Use email as username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class KrystalUser(AbstractUser):
    """
    Unified User model for all Krystal Company applications.
    Replaces multiple user models across the system.
    """

    # Core identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Email as primary authentication field
    email = models.EmailField(
        _('Email Address'),
        unique=True,
        help_text=_('Company email address used for login across all systems')
    )

    # Employee identification
    employee_id = models.CharField(
        _('Employee ID'),
        max_length=20,
        unique=True,
        help_text=_('Unique employee identification number')
    )

    # Geographic/Regional information
    REGION_CHOICES = [
        ('HK', _('Hong Kong')),
        ('CN', _('China')),
        ('GLOBAL', _('Global')),
        ('OTHER', _('Other')),
    ]

    region = models.CharField(
        _('Region'),
        max_length=10,
        choices=REGION_CHOICES,
        default='HK',
        help_text=_('Primary work region')
    )

    # Organizational structure
    DEPARTMENT_CHOICES = [
        ('HR', _('Human Resources')),
        ('FINANCE', _('Finance')),
        ('IT', _('Information Technology')),
        ('OPERATIONS', _('Operations')),
        ('SALES', _('Sales & Marketing')),
        ('MANAGEMENT', _('Management')),
        ('ADMIN', _('Administration')),
        ('OTHER', _('Other')),
    ]

    department = models.CharField(
        _('Department'),
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        help_text=_('Department/Division')
    )

    position = models.CharField(
        _('Position'),
        max_length=100,
        blank=True,
        help_text=_('Job title/position')
    )

    # Management hierarchy
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_employees',
        verbose_name=_('Manager'),
        help_text=_('Direct manager for approval workflows')
    )

    # Role-based access control (unified across all apps)
    ROLE_CHOICES = [
        ('STAFF', _('Staff')),
        ('MANAGER', _('Manager')),
        ('ADMIN', _('Administrator')),
        ('FINANCE', _('Finance Officer')),
        ('HR', _('HR Officer')),
        ('SUPER_ADMIN', _('Super Administrator')),
    ]

    role = models.CharField(
        _('Role'),
        max_length=15,
        choices=ROLE_CHOICES,
        default='STAFF',
        help_text=_('System role determining permissions across all applications')
    )

    # Application-specific permissions
    can_approve_expenses = models.BooleanField(
        _('Can Approve Expenses'),
        default=False,
        help_text=_('Can approve expense claims in expense system')
    )

    expense_approval_limit = models.DecimalField(
        _('Expense Approval Limit (HKD)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Maximum amount user can approve in HKD')
    )

    can_approve_leave = models.BooleanField(
        _('Can Approve Leave'),
        default=False,
        help_text=_('Can approve leave applications in leave system')
    )

    can_manage_customers = models.BooleanField(
        _('Can Manage Customers'),
        default=False,
        help_text=_('Can create/edit customers in CRM system')
    )

    # Additional metadata
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=20,
        blank=True,
        help_text=_('Contact phone number')
    )

    hire_date = models.DateField(
        _('Hire Date'),
        null=True,
        blank=True,
        help_text=_('Employee hire date')
    )

    is_active_employee = models.BooleanField(
        _('Active Employee'),
        default=True,
        help_text=_('Whether user is currently an active employee')
    )

    # Language preference for multi-language support
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('zh-hk', _('Traditional Chinese')),
        ('zh-cn', _('Simplified Chinese')),
    ]

    preferred_language = models.CharField(
        _('Preferred Language'),
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text=_('Preferred language for user interface')
    )

    # SSO and integration fields
    sso_token = models.CharField(
        _('SSO Token'),
        max_length=255,
        blank=True,
        help_text=_('Current SSO session token')
    )

    last_sso_login = models.DateTimeField(
        _('Last SSO Login'),
        null=True,
        blank=True,
        help_text=_('Last successful SSO login time')
    )

    # Use custom manager
    objects = KrystalUserManager()

    # Email as the unique identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['employee_id', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('Krystal User')
        verbose_name_plural = _('Krystal Users')
        db_table = 'krystal_users'  # Use existing table

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Return the full name for the user."""
        return f"{self.first_name} {self.last_name}".strip()

    def get_display_name(self):
        """Return display name with employee ID."""
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.employee_id})"
        return self.email

    def can_approve_expense_amount(self, amount):
        """Check if user can approve a specific expense amount."""
        if not self.can_approve_expenses:
            return False
        if self.expense_approval_limit is None:
            return True  # Unlimited approval
        return amount <= self.expense_approval_limit

    def get_managed_employees(self):
        """Get all employees managed by this user (including indirect reports)."""
        managed = []
        direct_reports = self.managed_employees.all()
        managed.extend(direct_reports)

        # Get indirect reports recursively
        for report in direct_reports:
            managed.extend(report.get_managed_employees())

        return managed

    def has_application_access(self, app_name):
        """Check if user has access to specific application."""
        if not self.is_active or not self.is_active_employee:
            return False

        # Application-specific access logic
        access_map = {
            'expense_system': True,  # All active employees can use expense system
            'leave_system': True,    # All active employees can use leave system
            'crm_system': self.can_manage_customers or self.role in ['ADMIN', 'SUPER_ADMIN', 'SALES'],
            'integrated_platform': True,  # All users need access to central platform
            'stripe_dashboard': self.role in ['FINANCE', 'ADMIN', 'SUPER_ADMIN'],
        }

        return access_map.get(app_name, False)


# Backward compatibility alias
CompanyUser = KrystalUser