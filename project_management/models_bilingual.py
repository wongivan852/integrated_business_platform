"""
Updated Project Management Models with Bilingual Support
This file shows the updated models - actual integration will be done via migration
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

# Import our bilingual mixins
from .mixins import BilingualModel, TimestampMixin, UserTrackingMixin
from .validators import normalize_phone_number

User = get_user_model()


class Project(BilingualModel):
    """
    Main project container with bilingual support
    Supports both Gantt Chart and Kanban Board views
    """
    STATUS_CHOICES = [
        ('planning', _('Planning')),
        ('active', _('Active')),
        ('on_hold', _('On Hold')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]

    VIEW_CHOICES = [
        ('gantt', _('Gantt Chart')),
        ('kanban', _('Kanban Board')),
    ]

    # BILINGUAL FIELDS - Separate storage for each language
    name_en = models.CharField(
        max_length=200,
        verbose_name=_('Project Name (English)'),
        help_text=_('Project name in English'),
        blank=True  # At least one language required
    )
    name_zh = models.CharField(
        max_length=200,
        verbose_name=_('项目名称(中文)'),
        help_text=_('Project name in Chinese'),
        blank=True  # At least one language required
    )
    description_en = models.TextField(
        blank=True,
        verbose_name=_('Description (English)'),
        help_text=_('Project description in English')
    )
    description_zh = models.TextField(
        blank=True,
        verbose_name=_('描述(中文)'),
        help_text=_('Project description in Chinese')
    )

    # LANGUAGE-NEUTRAL FIELDS - Same in all languages
    project_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_('Project Code'),
        help_text=_('Unique project identifier (e.g., PROJ-2024-001)')
    )

    # Dates - stored as date objects, formatted based on language
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))
    actual_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Actual Start Date')
    )
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Actual End Date')
    )

    # Status & Priority - choices are translated via gettext_lazy
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning',
        verbose_name=_('Status')
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('Priority')
    )

    # Ownership & Team
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_projects',
        verbose_name=_('Project Owner')
    )
    team_members = models.ManyToManyField(
        User,
        through='ProjectMember',
        related_name='projects',
        verbose_name=_('Team Members')
    )

    # View Preferences
    default_view = models.CharField(
        max_length=10,
        choices=VIEW_CHOICES,
        default='kanban',
        verbose_name=_('Default View')
    )

    # Budget Tracking - decimal numbers are language-neutral
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Budget'),
        help_text=_('Total project budget')
    )
    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Actual Cost'),
        help_text=_('Actual costs incurred')
    )

    # Progress
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Progress %')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_projects',
        verbose_name=_('Created By')
    )

    # Template tracking
    created_from_template = models.ForeignKey(
        'ProjectTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_projects',
        verbose_name=_('Created From Template'),
        help_text=_('Template used to create this project')
    )

    # Language preference for this project
    primary_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('zh-hans', '简体中文')],
        default='en',
        verbose_name=_('Primary Language'),
        help_text=_('Primary language for this project')
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['project_code']),
        ]
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')

    def __str__(self):
        """Return project code and name in current language"""
        return f"{self.project_code} - {self.name}"

    def clean(self):
        """Validate that at least one language version is provided"""
        from django.core.exceptions import ValidationError
        if not self.name_en and not self.name_zh:
            raise ValidationError({
                'name_en': _('At least one language version of name is required'),
                'name_zh': _('At least one language version of name is required'),
            })

    def save(self, *args, **kwargs):
        """Auto-fill missing language versions if only one is provided"""
        # If only one language is provided, copy to the other as placeholder
        # In production, you might want to use a translation API
        if self.name_en and not self.name_zh:
            self.name_zh = self.name_en  # Placeholder
        elif self.name_zh and not self.name_en:
            self.name_en = self.name_zh  # Placeholder

        if self.description_en and not self.description_zh:
            self.description_zh = self.description_en  # Placeholder
        elif self.description_zh and not self.description_en:
            self.description_en = self.description_zh  # Placeholder

        super().save(*args, **kwargs)

    # BilingualModel provides these automatically:
    # @property
    # def name(self):
    #     return self.get_bilingual_field('name')
    #
    # @property
    # def description(self):
    #     return self.get_bilingual_field('description')

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('project_management:project_detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self):
        """Check if project is past its end date"""
        if self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.end_date
        return False

    @property
    def days_remaining(self):
        """Calculate days until end date"""
        if self.status in ['completed', 'cancelled']:
            return 0
        delta = self.end_date - timezone.now().date()
        return max(0, delta.days)

    @property
    def budget_remaining(self):
        """Calculate remaining budget"""
        if self.budget:
            return self.budget - self.actual_cost
        return None

    @property
    def budget_percentage_used(self):
        """Calculate percentage of budget used"""
        if self.budget and self.budget > 0:
            return (self.actual_cost / self.budget) * 100
        return 0


class Task(BilingualModel):
    """
    Task model with bilingual support
    Universal task model - works for both Gantt and Kanban
    """
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ]

    STATUS_CHOICES = [
        ('todo', _('To Do')),
        ('in_progress', _('In Progress')),
        ('review', _('In Review')),
        ('blocked', _('Blocked')),
        ('completed', _('Completed')),
    ]

    # BILINGUAL FIELDS
    title_en = models.CharField(
        max_length=300,
        verbose_name=_('Task Title (English)'),
        blank=True
    )
    title_zh = models.CharField(
        max_length=300,
        verbose_name=_('任务标题(中文)'),
        blank=True
    )
    description_en = models.TextField(
        blank=True,
        verbose_name=_('Description (English)')
    )
    description_zh = models.TextField(
        blank=True,
        verbose_name=_('描述(中文)')
    )

    # LANGUAGE-NEUTRAL FIELDS
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('Project')
    )
    task_code = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name=_('Task Code')
    )

    # Hierarchy (for WBS in Gantt)
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks',
        verbose_name=_('Parent Task')
    )
    order = models.IntegerField(
        default=0,
        help_text=_('Sort order within parent')
    )
    indent_level = models.IntegerField(
        default=0,
        help_text=_('WBS hierarchy level')
    )

    # Gantt-specific fields
    start_date = models.DateField(null=True, blank=True, verbose_name=_('Start Date'))
    end_date = models.DateField(null=True, blank=True, verbose_name=_('End Date'))
    duration = models.IntegerField(
        default=1,
        help_text=_('Duration in days'),
        validators=[MinValueValidator(0)]
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Progress percentage (0-100)')
    )
    is_milestone = models.BooleanField(default=False, verbose_name=_('Is Milestone'))

    # Kanban-specific fields
    kanban_column = models.ForeignKey(
        'KanbanColumn',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        verbose_name=_('Kanban Column')
    )
    kanban_position = models.IntegerField(default=0)

    # Universal fields
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('Priority')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo',
        verbose_name=_('Status')
    )
    assigned_to = models.ManyToManyField(
        User,
        related_name='assigned_tasks',
        blank=True,
        verbose_name=_('Assigned To')
    )

    # Time Tracking
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Estimated hours to complete')
    )
    actual_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text=_('Actual hours spent')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Language preference
    primary_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('zh-hans', '简体中文')],
        default='en',
        verbose_name=_('Primary Language')
    )

    class Meta:
        ordering = ['project', 'order', 'created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'priority']),
        ]
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')

    def __str__(self):
        return f"{self.task_code} - {self.title}"

    # BilingualModel provides:
    # @property
    # def title(self):
    #     return self.get_bilingual_field('title')
    #
    # @property
    # def description(self):
    #     return self.get_bilingual_field('description')

    def clean(self):
        """Validate that at least one language version is provided"""
        from django.core.exceptions import ValidationError
        if not self.title_en and not self.title_zh:
            raise ValidationError({
                'title_en': _('At least one language version of title is required'),
                'title_zh': _('At least one language version of title is required'),
            })

    def save(self, *args, **kwargs):
        """Auto-fill missing language versions"""
        if self.title_en and not self.title_zh:
            self.title_zh = self.title_en
        elif self.title_zh and not self.title_en:
            self.title_en = self.title_zh

        if self.description_en and not self.description_zh:
            self.description_zh = self.description_en
        elif self.description_zh and not self.description_en:
            self.description_en = self.description_zh

        super().save(*args, **kwargs)


# Example of a contact model with phone validation
class ProjectContact(models.Model):
    """
    Project contact with cultural-aware phone validation
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='contacts'
    )

    # Bilingual name
    name_en = models.CharField(max_length=100, blank=True)
    name_zh = models.CharField(max_length=100, blank=True)

    # Phone - stored in E.164 format
    phone = models.CharField(
        max_length=20,
        verbose_name=_('Phone Number'),
        help_text=_('Phone number in local format')
    )

    email = models.EmailField(verbose_name=_('Email'))

    # Address with bilingual support
    address_en = models.TextField(blank=True, verbose_name=_('Address (English)'))
    address_zh = models.TextField(blank=True, verbose_name=_('地址(中文)'))

    role = models.CharField(
        max_length=100,
        verbose_name=_('Role'),
        help_text=_('Contact role in project')
    )

    primary_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('zh-hans', '简体中文')],
        default='en'
    )

    def save(self, *args, **kwargs):
        """Normalize phone number on save"""
        if self.phone:
            country_code = '86' if self.primary_language.startswith('zh') else None
            self.phone = normalize_phone_number(self.phone, country_code)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Project Contact')
        verbose_name_plural = _('Project Contacts')

    def __str__(self):
        name = self.name_zh if self.primary_language.startswith('zh') else self.name_en
        return f"{name} - {self.role}"
