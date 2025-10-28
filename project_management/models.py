"""
Project Management Application Models
Supports both Gantt Chart and Kanban Board views with unified data model
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


# ============================================================================
# CORE MODELS
# ============================================================================

class Project(models.Model):
    """
    Main project container - supports both Gantt and Kanban views
    """
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    VIEW_CHOICES = [
        ('gantt', 'Gantt Chart'),
        ('kanban', 'Kanban Board'),
    ]

    # Basic Information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project_code = models.CharField(max_length=50, unique=True, db_index=True)

    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)

    # Status & Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    # Ownership & Team
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_projects'
    )
    team_members = models.ManyToManyField(
        User,
        through='ProjectMember',
        related_name='projects'
    )

    # View Preferences
    default_view = models.CharField(
        max_length=10,
        choices=VIEW_CHOICES,
        default='kanban'
    )

    # Budget Tracking
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Total project budget"
    )
    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Actual costs incurred"
    )

    # Progress
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_projects'
    )

    # Template tracking
    created_from_template = models.ForeignKey(
        'ProjectTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_projects',
        help_text="Template used to create this project"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['owner', 'status']),
        ]

    def __str__(self):
        return f"{self.project_code} - {self.name}"

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


class ProjectMember(models.Model):
    """
    Through model for project team membership with roles
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'user']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.project.name} ({self.role})"


class Task(models.Model):
    """
    Universal task model - works for both Gantt and Kanban
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('blocked', 'Blocked'),
        ('completed', 'Completed'),
    ]

    # Basic Information
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    task_code = models.CharField(max_length=50, db_index=True)

    # Hierarchy (for WBS in Gantt)
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtasks'
    )
    order = models.IntegerField(default=0, help_text="Sort order within parent")
    indent_level = models.IntegerField(default=0, help_text="WBS hierarchy level")

    # Gantt-specific fields
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    duration = models.IntegerField(
        default=1,
        help_text="Duration in days",
        validators=[MinValueValidator(0)]
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress percentage (0-100)"
    )
    is_milestone = models.BooleanField(default=False)

    # Kanban-specific fields
    kanban_column = models.ForeignKey(
        'KanbanColumn',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )
    kanban_position = models.IntegerField(default=0)

    # Universal fields
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    assigned_to = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)

    # Time Tracking
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated hours to complete"
    )
    actual_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Actual hours spent"
    )

    # Due Date (for both views)
    due_date = models.DateField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tasks'
    )

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'kanban_column']),
            models.Index(fields=['status', 'due_date']),
        ]

    def __str__(self):
        return f"{self.task_code} - {self.title}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('project_management:task_detail', kwargs={'pk': self.pk})

    @property
    def is_overdue(self):
        """Check if task is past its due date"""
        if self.due_date and self.status != 'completed':
            return timezone.now().date() > self.due_date
        return False

    @property
    def calculated_duration(self):
        """Calculate duration from start and end dates"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return self.duration


# ============================================================================
# GANTT CHART SPECIFIC MODELS
# ============================================================================

class TaskDependency(models.Model):
    """
    Task dependencies for Gantt chart
    """
    DEPENDENCY_TYPES = [
        ('FS', 'Finish-to-Start'),
        ('SS', 'Start-to-Start'),
        ('FF', 'Finish-to-Finish'),
        ('SF', 'Start-to-Finish'),
    ]

    predecessor = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='successors'
    )
    successor = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='predecessors'
    )
    dependency_type = models.CharField(
        max_length=2,
        choices=DEPENDENCY_TYPES,
        default='FS'
    )
    lag_days = models.IntegerField(
        default=0,
        help_text="Delay in days (positive) or overlap (negative)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['predecessor', 'successor']
        verbose_name_plural = 'Task dependencies'

    def __str__(self):
        return f"{self.predecessor.task_code} → {self.successor.task_code} ({self.dependency_type})"


class ProjectBaseline(models.Model):
    """
    Saved baseline for schedule comparison
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='baselines')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class BaselineTask(models.Model):
    """
    Snapshot of task data at baseline time
    """
    baseline = models.ForeignKey(
        ProjectBaseline,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    task_code = models.CharField(max_length=50)
    title = models.CharField(max_length=300)
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.IntegerField()
    progress = models.IntegerField()

    def __str__(self):
        return f"Baseline: {self.task_code}"


# ============================================================================
# KANBAN BOARD SPECIFIC MODELS
# ============================================================================

class KanbanColumn(models.Model):
    """
    Columns in Kanban board (e.g., To Do, In Progress, Done)
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='kanban_columns'
    )
    name = models.CharField(max_length=100)
    position = models.IntegerField()
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text="Hex color code"
    )
    wip_limit = models.IntegerField(
        null=True,
        blank=True,
        help_text="Work-in-progress limit (optional)"
    )

    class Meta:
        ordering = ['position']
        unique_together = ['project', 'position']
        indexes = [
            models.Index(fields=['project', 'position']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    @property
    def task_count(self):
        """Count tasks in this column"""
        return self.tasks.count()

    @property
    def is_over_wip_limit(self):
        """Check if column exceeds WIP limit"""
        if self.wip_limit:
            return self.task_count > self.wip_limit
        return False


class TaskLabel(models.Model):
    """
    Color-coded labels for Kanban cards
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#007bff')
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['project', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


class TaskLabelAssignment(models.Model):
    """
    Many-to-many relationship between tasks and labels
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='label_assignments')
    label = models.ForeignKey(TaskLabel, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['task', 'label']

    def __str__(self):
        return f"{self.task.task_code} - {self.label.name}"


# ============================================================================
# TASK DETAILS & COLLABORATION
# ============================================================================

class TaskChecklist(models.Model):
    """
    Checklist within a task
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklists')
    title = models.CharField(max_length=200)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return self.title

    @property
    def completion_percentage(self):
        """Calculate percentage of completed items"""
        total = self.items.count()
        if total == 0:
            return 0
        completed = self.items.filter(is_completed=True).count()
        return int((completed / total) * 100)


class ChecklistItem(models.Model):
    """
    Individual checklist item
    """
    checklist = models.ForeignKey(
        TaskChecklist,
        on_delete=models.CASCADE,
        related_name='items'
    )
    text = models.CharField(max_length=300)
    is_completed = models.BooleanField(default=False)
    position = models.IntegerField(default=0)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_checklist_items'
    )

    class Meta:
        ordering = ['position']

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.text}"


class TaskComment(models.Model):
    """
    Comments/discussion on tasks
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    # For threading (optional)
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.task.task_code}"


class TaskAttachment(models.Model):
    """
    File attachments on tasks
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='project_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename

    @property
    def file_size_mb(self):
        """Return file size in megabytes"""
        return round(self.file_size / (1024 * 1024), 2)


class TaskActivity(models.Model):
    """
    Activity log for audit trail
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('moved', 'Moved'),
        ('assigned', 'Assigned'),
        ('unassigned', 'Unassigned'),
        ('status_changed', 'Status Changed'),
        ('priority_changed', 'Priority Changed'),
        ('completed', 'Completed'),
        ('reopened', 'Reopened'),
        ('commented', 'Commented'),
        ('attached_file', 'Attached File'),
        ('dependency_added', 'Dependency Added'),
        ('dependency_removed', 'Dependency Removed'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict, help_text="Additional details about the change")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Task activities'
        indexes = [
            models.Index(fields=['task', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() if self.user else 'System'} {self.action} {self.task.task_code}"


# ============================================================================
# RESOURCE MANAGEMENT (PHASE 4)
# ============================================================================

class Skill(models.Model):
    """
    Skills and competencies for resource matching
    """
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('technical', 'Technical'),
            ('management', 'Management'),
            ('design', 'Design'),
            ('communication', 'Communication'),
            ('analysis', 'Analysis'),
            ('other', 'Other'),
        ],
        default='technical'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Resource(models.Model):
    """
    Team member resource with capacity and availability
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resource_profile')
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Hourly rate for cost calculations"
    )
    availability_percentage = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of time available for project work"
    )
    working_hours_per_day = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=8.0,
        help_text="Standard working hours per day"
    )
    start_date = models.DateField(help_text="When they joined the team")
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="When they leave (if applicable)"
    )
    skills = models.ManyToManyField(Skill, related_name='resources', blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - {self.job_title}"

    @property
    def available_hours_per_day(self):
        """Calculate available hours per day based on availability percentage"""
        return (self.working_hours_per_day * self.availability_percentage) / 100

    @property
    def is_currently_active(self):
        """Check if resource is active and within date range"""
        if not self.is_active:
            return False
        today = timezone.now().date()
        if self.end_date and today > self.end_date:
            return False
        return today >= self.start_date

    def get_workload(self, start_date, end_date):
        """Get total assigned hours for date range"""
        assignments = self.assignments.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        return sum(a.assigned_hours for a in assignments)

    def get_utilization(self, start_date, end_date):
        """Calculate utilization percentage for date range"""
        days = (end_date - start_date).days + 1
        total_available = self.available_hours_per_day * days
        if total_available == 0:
            return 0
        workload = self.get_workload(start_date, end_date)
        return (workload / total_available) * 100


class ResourceAssignment(models.Model):
    """
    Assignment of a resource to a task with allocation details
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='resource_assignments')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='assignments')
    allocation_percentage = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of resource's time allocated to this task"
    )
    assigned_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Total hours assigned"
    )
    actual_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        help_text="Actual hours spent"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_assignments')

    class Meta:
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['resource', 'start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.resource.user.get_full_name()} on {self.task.task_code} ({self.assigned_hours}h)"

    @property
    def hours_remaining(self):
        """Calculate remaining hours"""
        return self.assigned_hours - self.actual_hours

    @property
    def is_over_allocated(self):
        """Check if actual hours exceed assigned hours"""
        return self.actual_hours > self.assigned_hours


# ============================================================================
# COST TRACKING & EARNED VALUE MANAGEMENT (PHASE 4)
# ============================================================================

class ProjectCost(models.Model):
    """
    Actual costs incurred on a project
    """
    CATEGORY_CHOICES = [
        ('labor', 'Labor'),
        ('materials', 'Materials'),
        ('equipment', 'Equipment'),
        ('subcontractor', 'Subcontractor'),
        ('travel', 'Travel'),
        ('software', 'Software/Licenses'),
        ('overhead', 'Overhead'),
        ('other', 'Other'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='costs')
    date = models.DateField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    invoice_number = models.CharField(max_length=50, blank=True)
    vendor = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['project', 'date']),
            models.Index(fields=['project', 'category']),
        ]

    def __str__(self):
        return f"{self.project.project_code} - ${self.amount} ({self.get_category_display()})"


class TaskCost(models.Model):
    """
    Cost breakdown at task level
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='costs')
    cost_type = models.CharField(
        max_length=50,
        choices=[
            ('labor', 'Labor'),
            ('material', 'Material'),
            ('equipment', 'Equipment'),
            ('other', 'Other'),
        ],
        default='labor'
    )
    planned_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Planned/budgeted cost"
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Actual cost incurred"
    )

    class Meta:
        ordering = ['task', 'cost_type']

    def __str__(self):
        return f"{self.task.task_code} - {self.get_cost_type_display()}: ${self.planned_cost}"

    @property
    def cost_variance(self):
        """Calculate cost variance (negative = over budget)"""
        return self.planned_cost - self.actual_cost


class EVMSnapshot(models.Model):
    """
    Earned Value Management snapshot for a specific date
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='evm_snapshots')
    snapshot_date = models.DateField()

    # Baseline values
    budget_at_completion = models.DecimalField(max_digits=12, decimal_places=2)
    planned_duration_days = models.IntegerField()

    # Calculated EVM values
    planned_value = models.DecimalField(max_digits=12, decimal_places=2, help_text="PV (BCWS)")
    earned_value = models.DecimalField(max_digits=12, decimal_places=2, help_text="EV (BCWP)")
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, help_text="AC (ACWP)")

    # Performance indices
    cost_performance_index = models.DecimalField(max_digits=5, decimal_places=2, help_text="CPI = EV/AC")
    schedule_performance_index = models.DecimalField(max_digits=5, decimal_places=2, help_text="SPI = EV/PV")

    # Variances
    cost_variance = models.DecimalField(max_digits=12, decimal_places=2, help_text="CV = EV - AC")
    schedule_variance = models.DecimalField(max_digits=12, decimal_places=2, help_text="SV = EV - PV")

    # Forecasts
    estimate_at_completion = models.DecimalField(max_digits=12, decimal_places=2, help_text="EAC")
    estimate_to_complete = models.DecimalField(max_digits=12, decimal_places=2, help_text="ETC = EAC - AC")
    variance_at_completion = models.DecimalField(max_digits=12, decimal_places=2, help_text="VAC = BAC - EAC")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-snapshot_date']
        unique_together = ['project', 'snapshot_date']
        indexes = [
            models.Index(fields=['project', '-snapshot_date']),
        ]

    def __str__(self):
        return f"{self.project.project_code} EVM - {self.snapshot_date}"

    @property
    def is_under_budget(self):
        """Check if project is under budget (CPI > 1.0)"""
        return self.cost_performance_index > 1.0

    @property
    def is_ahead_of_schedule(self):
        """Check if project is ahead of schedule (SPI > 1.0)"""
        return self.schedule_performance_index > 1.0


# ============================================================================
# PROJECT TEMPLATES (PHASE 4)
# ============================================================================

class ProjectTemplate(models.Model):
    """
    Reusable project structure template
    """
    CATEGORY_CHOICES = [
        ('software', 'Software Development'),
        ('construction', 'Construction'),
        ('marketing', 'Marketing Campaign'),
        ('research', 'Research Project'),
        ('event', 'Event Planning'),
        ('consulting', 'Consulting Project'),
        ('design', 'Design Project'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    default_duration_days = models.IntegerField(help_text="Typical project duration")
    estimated_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated budget for projects created from this template"
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(
        default=False,
        help_text="Public templates visible to all users"
    )
    use_count = models.IntegerField(default=0, help_text="Times this template was used")

    class Meta:
        ordering = ['-use_count', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class TemplateTask(models.Model):
    """
    Task blueprint within a project template
    """
    ROLE_CHOICES = [
        ('owner', 'Project Owner'),
        ('manager', 'Project Manager'),
        ('member', 'Team Member'),
        ('lead', 'Team Lead'),
    ]

    template = models.ForeignKey(ProjectTemplate, on_delete=models.CASCADE, related_name='template_tasks')
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    estimated_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=8.0,
        help_text="Estimated hours to complete"
    )
    assignee_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        help_text="Role that should be assigned this task"
    )
    sequence_number = models.IntegerField(
        default=0,
        help_text="Order in which tasks should be executed"
    )
    is_milestone = models.BooleanField(default=False)

    class Meta:
        ordering = ['sequence_number']

    def __str__(self):
        return f"{self.template.name} - {self.name}"


class TemplateDependency(models.Model):
    """
    Dependency blueprint between template tasks
    """
    DEPENDENCY_TYPE_CHOICES = [
        ('FS', 'Finish-to-Start'),
        ('SS', 'Start-to-Start'),
        ('FF', 'Finish-to-Finish'),
        ('SF', 'Start-to-Finish'),
    ]

    task = models.ForeignKey(
        TemplateTask,
        on_delete=models.CASCADE,
        related_name='template_dependencies'
    )
    depends_on = models.ForeignKey(
        TemplateTask,
        on_delete=models.CASCADE,
        related_name='dependent_template_tasks'
    )
    dependency_type = models.CharField(
        max_length=2,
        choices=DEPENDENCY_TYPE_CHOICES,
        default='FS'
    )
    lag_days = models.IntegerField(default=0)

    class Meta:
        unique_together = ['task', 'depends_on']
        verbose_name_plural = 'Template dependencies'

    def __str__(self):
        return f"{self.depends_on.name} → {self.task.name} ({self.dependency_type})"


# ============================================================================
# PHASE 5: ANALYTICS & METRICS MODELS
# ============================================================================

class ProjectMetrics(models.Model):
    """
    Daily snapshot of project metrics for analytics and trend analysis
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='metrics_snapshots'
    )
    snapshot_date = models.DateField(default=timezone.now)

    # Progress Metrics
    tasks_total = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    tasks_in_progress = models.IntegerField(default=0)
    tasks_overdue = models.IntegerField(default=0)
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    # Schedule Metrics
    days_remaining = models.IntegerField(default=0)
    schedule_variance_days = models.IntegerField(
        default=0,
        help_text="Positive = ahead of schedule, Negative = behind"
    )

    # Cost Metrics
    budget_allocated = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    cost_variance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Positive = under budget, Negative = over budget"
    )

    # Team Metrics
    team_size = models.IntegerField(default=0)
    resource_utilization = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage of team capacity used"
    )

    # Quality Metrics
    issues_open = models.IntegerField(default=0)
    issues_resolved = models.IntegerField(default=0)

    # Velocity (tasks per week)
    velocity = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Tasks completed per week"
    )

    # Health Score (0-100)
    health_score = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall project health score"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-snapshot_date']
        unique_together = ['project', 'snapshot_date']
        verbose_name_plural = 'Project metrics'
        indexes = [
            models.Index(fields=['project', '-snapshot_date']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.snapshot_date}"


class DashboardWidget(models.Model):
    """
    Customizable dashboard widgets for personalized user experience
    """
    WIDGET_TYPE_CHOICES = [
        ('project_status', 'Project Status Overview'),
        ('task_summary', 'Task Summary'),
        ('budget_tracker', 'Budget Tracker'),
        ('schedule_timeline', 'Schedule Timeline'),
        ('team_workload', 'Team Workload'),
        ('recent_activity', 'Recent Activity'),
        ('upcoming_deadlines', 'Upcoming Deadlines'),
        ('performance_metrics', 'Performance Metrics'),
        ('cost_breakdown', 'Cost Breakdown'),
        ('velocity_chart', 'Velocity Chart'),
        ('burndown_chart', 'Burndown Chart'),
        ('risk_alerts', 'Risk Alerts'),
    ]

    SIZE_CHOICES = [
        ('small', 'Small (1/4 width)'),
        ('medium', 'Medium (1/2 width)'),
        ('large', 'Large (Full width)'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_widgets'
    )
    widget_type = models.CharField(max_length=50, choices=WIDGET_TYPE_CHOICES)
    title = models.CharField(max_length=100)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES, default='medium')
    position = models.IntegerField(
        default=0,
        help_text="Display order on dashboard"
    )
    is_visible = models.BooleanField(default=True)

    # Widget Configuration (JSON)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Widget-specific configuration"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user', 'position']
        unique_together = ['user', 'widget_type']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Notification(models.Model):
    """
    User notifications for project events and updates
    """
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('task_overdue', 'Task Overdue'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('budget_alert', 'Budget Alert'),
        ('project_status_changed', 'Project Status Changed'),
        ('comment_added', 'Comment Added'),
        ('mention', 'Mentioned'),
        ('milestone_completed', 'Milestone Completed'),
        ('resource_assigned', 'Resource Assigned'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Link to related objects
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # URL to navigate to when clicked
    action_url = models.CharField(max_length=500, blank=True)

    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


# ============================================================================
# PHASE 6: REAL-TIME COLLABORATION MODELS
# ============================================================================

class UserPresence(models.Model):
    """
    Track user presence for real-time collaboration features.
    Shows which users are online and what they're currently viewing.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='presence_records'
    )
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Project the user is currently viewing"
    )
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Task the user is currently viewing"
    )

    # Status
    is_online = models.BooleanField(default=False)
    current_page = models.CharField(
        max_length=200,
        blank=True,
        help_text="Current page URL or identifier"
    )

    # Timestamps
    last_seen = models.DateTimeField(auto_now=True)
    session_start = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_seen']
        indexes = [
            models.Index(fields=['user', 'is_online']),
            models.Index(fields=['project', 'is_online']),
            models.Index(fields=['last_seen']),
        ]
        unique_together = ['user', 'project']

    def __str__(self):
        status = "online" if self.is_online else "offline"
        project_str = f" in {self.project.name}" if self.project else ""
        return f"{self.user.username} ({status}){project_str}"

    @property
    def is_active(self):
        """Check if user has been active in the last 5 minutes"""
        from datetime import timedelta
        if not self.is_online:
            return False
        threshold = timezone.now() - timedelta(minutes=5)
        return self.last_seen >= threshold


# ============================================================================
# PHASE 6.3: ADVANCED PERMISSIONS SYSTEM
# ============================================================================

class CustomRole(models.Model):
    """
    Custom role definitions for fine-grained access control.
    Extends beyond the basic owner/manager/editor/viewer roles.
    """
    ROLE_TYPES = [
        ('project', 'Project Level'),
        ('task', 'Task Level'),
        ('resource', 'Resource Level'),
        ('global', 'Global Level'),
    ]

    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES, default='project')

    # Hierarchy and inheritance
    parent_role = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_roles',
        help_text='Parent role from which this role inherits permissions'
    )
    level = models.IntegerField(
        default=0,
        help_text='Role hierarchy level (0=highest, 100=lowest)'
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_system_role = models.BooleanField(
        default=False,
        help_text='System roles cannot be deleted or modified'
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_roles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'name']
        indexes = [
            models.Index(fields=['role_type', 'is_active']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.role_type})"

    def get_all_permissions(self):
        """Get all permissions assigned to this role including inherited"""
        permissions = set(self.permissions.filter(is_active=True))

        # Add inherited permissions from parent
        if self.parent_role:
            permissions.update(self.parent_role.get_all_permissions())

        return permissions

    def has_permission(self, permission_code):
        """Check if this role has a specific permission"""
        all_permissions = self.get_all_permissions()
        return any(p.code == permission_code for p in all_permissions)


class CustomPermission(models.Model):
    """
    Individual permission definitions for granular access control.
    Maps to specific actions users can perform.
    """
    RESOURCE_TYPES = [
        ('project', 'Project'),
        ('task', 'Task'),
        ('resource', 'Resource'),
        ('template', 'Template'),
        ('report', 'Report'),
        ('settings', 'Settings'),
        ('user', 'User'),
        ('role', 'Role'),
    ]

    ACTION_TYPES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('assign', 'Assign'),
        ('approve', 'Approve'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('share', 'Share'),
        ('comment', 'Comment'),
        ('manage', 'Manage'),
    ]

    # Permission identification
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique permission code (e.g., project.edit, task.delete)'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    # Permission categorization
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)

    # Role assignments
    roles = models.ManyToManyField(
        CustomRole,
        related_name='permissions',
        blank=True
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_system_permission = models.BooleanField(
        default=False,
        help_text='System permissions cannot be deleted'
    )

    # Risk level for audit purposes
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVELS,
        default='low',
        help_text='Risk level for audit logging'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['resource_type', 'action_type', 'code']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['resource_type', 'action_type']),
            models.Index(fields=['risk_level']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class RoleTemplate(models.Model):
    """
    Predefined role templates for quick role assignment.
    Contains sets of permissions for common use cases.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    # Template configuration
    base_role = models.ForeignKey(
        CustomRole,
        on_delete=models.CASCADE,
        related_name='templates',
        help_text='The role this template is based on'
    )

    additional_permissions = models.ManyToManyField(
        CustomPermission,
        related_name='templates',
        blank=True,
        help_text='Additional permissions beyond the base role'
    )

    # Template metadata
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text='Template category (e.g., Development, Management, QA)'
    )

    is_public = models.BooleanField(
        default=False,
        help_text='Public templates are available to all users'
    )

    usage_count = models.IntegerField(
        default=0,
        help_text='Number of times this template has been used'
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='role_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['category', 'is_public']),
            models.Index(fields=['-usage_count']),
        ]

    def __str__(self):
        return f"{self.name} ({self.base_role.display_name})"

    def apply_to_user(self, user, project=None):
        """Apply this template to a user, optionally for a specific project"""
        # Create or update ProjectMember with the base role
        if project:
            member, created = ProjectMember.objects.get_or_create(
                project=project,
                user=user
            )
            # Store custom role reference (would need additional field in ProjectMember)
            # For now, map to existing roles
            member.save()

        # Increment usage count
        self.usage_count += 1
        self.save(update_fields=['usage_count'])

        return True


class UserRoleAssignment(models.Model):
    """
    Assigns custom roles to users for specific contexts.
    Supports project-level, global, and resource-specific assignments.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_assignments'
    )

    role = models.ForeignKey(
        CustomRole,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )

    # Context (one of these should be set)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='role_assignments',
        help_text='Project-specific role assignment'
    )

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='role_assignments',
        help_text='Resource-specific role assignment'
    )

    # Global assignment (no project or resource specified)
    is_global = models.BooleanField(
        default=False,
        help_text='Global role applies across all projects'
    )

    # Time-based constraints
    valid_from = models.DateTimeField(
        default=timezone.now,
        help_text='Role becomes active from this date'
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Role expires after this date (null = no expiration)'
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='role_assignments_made'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        help_text='Notes about this role assignment'
    )

    class Meta:
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(project__isnull=False) |
                    models.Q(resource__isnull=False) |
                    models.Q(is_global=True)
                ),
                name='role_assignment_has_context'
            )
        ]

    def __str__(self):
        context = "Global"
        if self.project:
            context = f"Project: {self.project.name}"
        elif self.resource:
            context = f"Resource: {self.resource.user.username}"

        return f"{self.user.username} → {self.role.display_name} ({context})"

    def is_valid(self):
        """Check if this role assignment is currently valid"""
        if not self.is_active:
            return False

        now = timezone.now()

        # Check if role has started
        if self.valid_from and self.valid_from > now:
            return False

        # Check if role has expired
        if self.valid_until and self.valid_until < now:
            return False

        return True

    def get_permissions(self):
        """Get all permissions granted by this role assignment"""
        if not self.is_valid():
            return set()

        return self.role.get_all_permissions()


class PermissionAuditLog(models.Model):
    """
    Audit log for permission-related changes and access attempts.
    Tracks who did what, when, and why for security and compliance.
    """
    ACTION_TYPES = [
        ('role_created', 'Role Created'),
        ('role_updated', 'Role Updated'),
        ('role_deleted', 'Role Deleted'),
        ('permission_created', 'Permission Created'),
        ('permission_updated', 'Permission Updated'),
        ('permission_deleted', 'Permission Deleted'),
        ('role_assigned', 'Role Assigned to User'),
        ('role_revoked', 'Role Revoked from User'),
        ('permission_granted', 'Permission Granted'),
        ('permission_denied', 'Permission Denied'),
        ('access_allowed', 'Access Allowed'),
        ('access_denied', 'Access Denied'),
        ('template_applied', 'Template Applied'),
    ]

    # Who and what
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='permission_audit_logs',
        help_text='User who performed the action'
    )

    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)

    # Targets
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_audit_targets',
        help_text='User affected by the action'
    )

    target_role = models.ForeignKey(
        CustomRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    target_permission = models.ForeignKey(
        CustomPermission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    # Context
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_audit_logs'
    )

    resource_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='Type of resource being accessed'
    )

    resource_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='ID of the resource being accessed'
    )

    # Details
    description = models.TextField(
        help_text='Human-readable description of what happened'
    )

    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text='JSON object containing before/after values'
    )

    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    # Status
    SUCCESS_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('error', 'Error'),
    ]
    status = models.CharField(
        max_length=20,
        choices=SUCCESS_CHOICES,
        default='success'
    )

    error_message = models.TextField(
        blank=True,
        help_text='Error message if action failed'
    )

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['target_user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['project', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action_type} - {self.timestamp}"

    @classmethod
    def log_action(cls, action_type, user, description, **kwargs):
        """
        Convenience method to create audit log entries.

        Usage:
            PermissionAuditLog.log_action(
                'role_assigned',
                request.user,
                f'Assigned {role.name} to {target_user.username}',
                target_user=target_user,
                target_role=role,
                project=project
            )
        """
        return cls.objects.create(
            action_type=action_type,
            user=user,
            description=description,
            **kwargs
        )


# ============================================================================
# PHASE 6.4: THIRD-PARTY INTEGRATIONS
# ============================================================================

class IntegrationProvider(models.Model):
    """
    Third-party service integration provider configuration.
    Supports GitHub, Slack, Jira, Calendar services, etc.
    """
    PROVIDER_TYPES = [
        ('github', 'GitHub'),
        ('slack', 'Slack'),
        ('jira', 'Jira'),
        ('google_calendar', 'Google Calendar'),
        ('outlook_calendar', 'Outlook Calendar'),
        ('trello', 'Trello'),
        ('asana', 'Asana'),
        ('webhook', 'Custom Webhook'),
    ]

    name = models.CharField(max_length=100, unique=True)
    provider_type = models.CharField(max_length=50, choices=PROVIDER_TYPES)
    description = models.TextField(blank=True)

    # OAuth/API Configuration
    client_id = models.CharField(
        max_length=500,
        blank=True,
        help_text='OAuth Client ID or API Key'
    )
    client_secret = models.CharField(
        max_length=500,
        blank=True,
        help_text='OAuth Client Secret or API Secret (encrypted)'
    )

    # Webhook configuration
    webhook_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Webhook URL for receiving events'
    )
    webhook_secret = models.CharField(
        max_length=200,
        blank=True,
        help_text='Secret for webhook signature validation'
    )

    # API endpoints
    api_base_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Base URL for API requests'
    )
    oauth_authorize_url = models.URLField(max_length=500, blank=True)
    oauth_token_url = models.URLField(max_length=500, blank=True)

    # Configuration
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional provider-specific configuration'
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(
        default=False,
        help_text='Global integration available to all projects'
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='integration_providers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider_type', 'name']
        indexes = [
            models.Index(fields=['provider_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_provider_type_display()} - {self.name}"


class ProjectIntegration(models.Model):
    """
    Links a project to a third-party service integration.
    Stores project-specific credentials and mappings.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='integrations'
    )

    provider = models.ForeignKey(
        IntegrationProvider,
        on_delete=models.CASCADE,
        related_name='project_integrations'
    )

    # OAuth tokens (encrypted in production)
    access_token = models.TextField(
        blank=True,
        help_text='OAuth access token or API token'
    )
    refresh_token = models.TextField(
        blank=True,
        help_text='OAuth refresh token'
    )
    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Token expiration time'
    )

    # Service-specific identifiers
    external_id = models.CharField(
        max_length=500,
        blank=True,
        help_text='External service ID (e.g., GitHub repo ID, Jira project key)'
    )
    external_url = models.URLField(
        max_length=500,
        blank=True,
        help_text='External service URL'
    )

    # Sync configuration
    sync_enabled = models.BooleanField(
        default=True,
        help_text='Enable automatic synchronization'
    )
    sync_interval = models.IntegerField(
        default=300,
        help_text='Sync interval in seconds (default: 5 minutes)'
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful sync timestamp'
    )
    sync_status = models.CharField(
        max_length=50,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('syncing', 'Syncing'),
            ('success', 'Success'),
            ('error', 'Error'),
        ]
    )
    sync_error = models.TextField(blank=True)

    # Mapping configuration
    field_mappings = models.JSONField(
        default=dict,
        blank=True,
        help_text='Field mappings between local and external service'
    )

    # Settings
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text='Integration-specific settings'
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    configured_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='configured_integrations'
    )
    configured_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-configured_at']
        unique_together = ['project', 'provider']
        indexes = [
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['sync_status']),
        ]

    def __str__(self):
        return f"{self.project.name} → {self.provider.name}"

    def is_token_valid(self):
        """Check if OAuth token is still valid"""
        if not self.access_token:
            return False
        if self.token_expires_at:
            return timezone.now() < self.token_expires_at
        return True

    def needs_sync(self):
        """Check if sync is needed based on interval"""
        if not self.sync_enabled or not self.is_active:
            return False
        if not self.last_sync:
            return True

        from datetime import timedelta
        next_sync = self.last_sync + timedelta(seconds=self.sync_interval)
        return timezone.now() >= next_sync


class IntegrationWebhook(models.Model):
    """
    Incoming webhook events from third-party services.
    Stores webhook payloads for processing.
    """
    integration = models.ForeignKey(
        ProjectIntegration,
        on_delete=models.CASCADE,
        related_name='webhooks',
        null=True,
        blank=True
    )

    provider = models.ForeignKey(
        IntegrationProvider,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )

    # Webhook details
    event_type = models.CharField(
        max_length=100,
        help_text='Type of webhook event (e.g., push, pull_request, issue)'
    )
    event_action = models.CharField(
        max_length=100,
        blank=True,
        help_text='Specific action (e.g., opened, closed, commented)'
    )

    # Payload
    payload = models.JSONField(
        help_text='Complete webhook payload'
    )
    headers = models.JSONField(
        default=dict,
        blank=True,
        help_text='HTTP headers from webhook request'
    )

    # Processing status
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)

    # Result
    result = models.JSONField(
        default=dict,
        blank=True,
        help_text='Processing result (created/updated objects)'
    )

    # Metadata
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['provider', '-received_at']),
            models.Index(fields=['integration', '-received_at']),
            models.Index(fields=['event_type', '-received_at']),
            models.Index(fields=['processed', '-received_at']),
        ]

    def __str__(self):
        return f"{self.provider.name} - {self.event_type} ({self.received_at})"


class ExternalTaskMapping(models.Model):
    """
    Maps internal tasks to external service tasks/issues.
    Enables bi-directional sync.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='external_mappings'
    )

    integration = models.ForeignKey(
        ProjectIntegration,
        on_delete=models.CASCADE,
        related_name='task_mappings'
    )

    # External identifiers
    external_id = models.CharField(
        max_length=500,
        help_text='External task/issue ID'
    )
    external_key = models.CharField(
        max_length=200,
        blank=True,
        help_text='External task key (e.g., PROJ-123)'
    )
    external_url = models.URLField(max_length=500)

    # Sync metadata
    last_synced_at = models.DateTimeField(auto_now=True)
    external_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last modified time on external service'
    )

    # Sync status
    sync_enabled = models.BooleanField(default=True)
    sync_direction = models.CharField(
        max_length=20,
        default='both',
        choices=[
            ('both', 'Bi-directional'),
            ('import', 'Import Only'),
            ('export', 'Export Only'),
        ]
    )

    # Field mapping overrides
    field_overrides = models.JSONField(
        default=dict,
        blank=True,
        help_text='Custom field mappings for this task'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='external_task_mappings'
    )

    class Meta:
        ordering = ['-last_synced_at']
        unique_together = ['integration', 'external_id']
        indexes = [
            models.Index(fields=['task', 'integration']),
            models.Index(fields=['integration', 'sync_enabled']),
            models.Index(fields=['external_id']),
        ]

    def __str__(self):
        return f"{self.task.title} → {self.external_key or self.external_id}"


class IntegrationLog(models.Model):
    """
    Logs all integration activities for debugging and audit.
    """
    ACTION_TYPES = [
        ('auth', 'Authentication'),
        ('sync', 'Synchronization'),
        ('webhook', 'Webhook Received'),
        ('export', 'Data Export'),
        ('import', 'Data Import'),
        ('api_call', 'API Call'),
        ('error', 'Error'),
    ]

    integration = models.ForeignKey(
        ProjectIntegration,
        on_delete=models.CASCADE,
        related_name='logs',
        null=True,
        blank=True
    )

    provider = models.ForeignKey(
        IntegrationProvider,
        on_delete=models.CASCADE,
        related_name='logs'
    )

    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)

    # Details
    description = models.TextField()
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional action details'
    )

    # Request/Response
    request_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='API request data'
    )
    response_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='API response data'
    )

    # Status
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success'
    )
    error_message = models.TextField(blank=True)

    # Performance
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text='Operation duration in milliseconds'
    )

    # Metadata
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='integration_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['integration', '-timestamp']),
            models.Index(fields=['provider', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['status', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.provider.name} - {self.action_type} - {self.status}"

    @classmethod
    def log_action(cls, action_type, provider, description, **kwargs):
        """
        Convenience method to create integration log entries.

        Usage:
            IntegrationLog.log_action(
                'sync',
                provider,
                'Synced 5 tasks from GitHub',
                integration=integration,
                status='success',
                details={'tasks_synced': 5}
            )
        """
        return cls.objects.create(
            action_type=action_type,
            provider=provider,
            description=description,
            **kwargs
        )


# ============================================================================
# Phase 6.5: Mobile PWA Models
# ============================================================================

class PWAInstallation(models.Model):
    """
    Tracks PWA installations across user devices.
    Records when users install the app and on which platforms.
    """
    PLATFORM_TYPES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('windows', 'Windows'),
        ('macos', 'macOS'),
        ('linux', 'Linux'),
        ('unknown', 'Unknown'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pwa_installations')

    # Device information
    platform = models.CharField(max_length=20, choices=PLATFORM_TYPES, default='unknown')
    device_name = models.CharField(max_length=200, blank=True)
    user_agent = models.TextField(blank=True)

    # Installation details
    installed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_active = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # App version
    app_version = models.CharField(max_length=50, blank=True)

    # Device token for push notifications
    push_token = models.TextField(blank=True, help_text='Device push notification token')

    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'project_pwa_installation'
        ordering = ['-installed_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['platform', 'is_active']),
            models.Index(fields=['-last_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_platform_display()} - {self.installed_at.date()}"

    def mark_active(self):
        """Update last active timestamp"""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])


class OfflineSyncQueue(models.Model):
    """
    Stores operations performed offline to be synchronized when online.
    Implements eventual consistency for offline-first architecture.
    """
    OPERATION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    SYNC_STATUS = [
        ('pending', 'Pending'),
        ('syncing', 'Syncing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('conflict', 'Conflict'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offline_sync_queue')
    installation = models.ForeignKey(
        PWAInstallation,
        on_delete=models.CASCADE,
        related_name='sync_queue',
        null=True,
        blank=True
    )

    # Operation details
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField(null=True, blank=True, help_text='ID of affected object')

    # Data payload
    data = models.JSONField(help_text='Operation data to be synchronized')
    original_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Original data before change (for conflict resolution)'
    )

    # Sync status
    status = models.CharField(max_length=20, choices=SYNC_STATUS, default='pending', db_index=True)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_attempt = models.DateTimeField(null=True, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True)
    conflict_resolution = models.CharField(
        max_length=50,
        blank=True,
        help_text='Strategy used for conflict resolution'
    )

    # Priority for sync order
    priority = models.IntegerField(default=0, help_text='Higher priority syncs first')

    class Meta:
        db_table = 'project_offline_sync_queue'
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-priority', 'created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.operation_type} {self.model_name}({self.object_id}) - {self.status}"

    def mark_syncing(self):
        """Mark as currently syncing"""
        self.status = 'syncing'
        self.last_attempt = timezone.now()
        self.attempts += 1
        self.save(update_fields=['status', 'last_attempt', 'attempts'])

    def mark_completed(self):
        """Mark as successfully synced"""
        self.status = 'completed'
        self.synced_at = timezone.now()
        self.save(update_fields=['status', 'synced_at'])

    def mark_failed(self, error_message):
        """Mark as failed with error message"""
        self.status = 'failed' if self.attempts >= self.max_attempts else 'pending'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def mark_conflict(self, conflict_data):
        """Mark as conflicted and store conflict data"""
        self.status = 'conflict'
        self.error_message = 'Data conflict detected'
        if isinstance(conflict_data, dict):
            self.data['conflict_data'] = conflict_data
        self.save(update_fields=['status', 'error_message', 'data'])


class PushSubscription(models.Model):
    """
    Stores web push notification subscriptions for PWA.
    Uses Web Push Protocol for push notifications.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    installation = models.ForeignKey(
        PWAInstallation,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        null=True,
        blank=True
    )

    # Push subscription details (from PushManager API)
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh_key = models.CharField(max_length=200, help_text='Public key for encryption')
    auth_key = models.CharField(max_length=200, help_text='Authentication secret')

    # Subscription metadata
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Notification preferences
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text='User notification preferences (types, frequency, etc.)'
    )

    # Browser/device info
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'project_push_subscription'
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_active', '-subscribed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."

    def mark_used(self):
        """Update last used timestamp"""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])

    def deactivate(self):
        """Deactivate subscription"""
        self.is_active = False
        self.save(update_fields=['is_active'])


class OfflineCache(models.Model):
    """
    Stores cached data for offline access.
    Enables offline-first functionality with smart caching.
    """
    CACHE_TYPES = [
        ('project', 'Project Data'),
        ('task', 'Task Data'),
        ('user', 'User Data'),
        ('resource', 'Resource Data'),
        ('static', 'Static Assets'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offline_cache')
    installation = models.ForeignKey(
        PWAInstallation,
        on_delete=models.CASCADE,
        related_name='cache_entries',
        null=True,
        blank=True
    )

    # Cache identification
    cache_type = models.CharField(max_length=50, choices=CACHE_TYPES)
    cache_key = models.CharField(max_length=500, db_index=True)

    # Cached data
    data = models.JSONField(help_text='Cached data payload')

    # Cache metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Size tracking
    size_bytes = models.IntegerField(default=0, help_text='Approximate size of cached data')

    # Access tracking
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'project_offline_cache'
        ordering = ['-updated_at']
        unique_together = [['user', 'cache_type', 'cache_key']]
        indexes = [
            models.Index(fields=['user', 'cache_type']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        return f"{self.cache_type} - {self.cache_key}"

    def is_expired(self):
        """Check if cache entry has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def mark_accessed(self):
        """Update access tracking"""
        self.access_count += 1
        self.last_accessed = timezone.now()
        self.save(update_fields=['access_count', 'last_accessed'])

    @classmethod
    def cleanup_expired(cls):
        """Remove expired cache entries"""
        expired = cls.objects.filter(
            expires_at__isnull=False,
            expires_at__lt=timezone.now()
        )
        count = expired.count()
        expired.delete()
        return count


class PWAAnalytics(models.Model):
    """
    Tracks PWA usage analytics for insights and optimization.
    Helps understand mobile app usage patterns.
    """
    EVENT_TYPES = [
        ('install', 'App Installed'),
        ('launch', 'App Launched'),
        ('page_view', 'Page Viewed'),
        ('offline', 'Went Offline'),
        ('online', 'Came Online'),
        ('sync', 'Data Synchronized'),
        ('notification', 'Notification Received'),
        ('action', 'User Action'),
        ('error', 'Error Occurred'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pwa_analytics',
        null=True,
        blank=True
    )
    installation = models.ForeignKey(
        PWAInstallation,
        on_delete=models.CASCADE,
        related_name='analytics',
        null=True,
        blank=True
    )

    # Event details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)
    event_name = models.CharField(max_length=200)

    # Event data
    data = models.JSONField(default=dict, blank=True)

    # Context
    url = models.URLField(max_length=500, blank=True)
    referrer = models.URLField(max_length=500, blank=True)

    # Technical details
    connection_type = models.CharField(max_length=50, blank=True, help_text='wifi, 4g, offline, etc.')
    performance_metrics = models.JSONField(default=dict, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Session tracking
    session_id = models.CharField(max_length=100, blank=True, db_index=True)

    class Meta:
        db_table = 'project_pwa_analytics'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['session_id', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.event_name} - {self.timestamp}"

    @classmethod
    def log_event(cls, event_type, event_name, user=None, installation=None, **kwargs):
        """Create analytics event"""
        return cls.objects.create(
            event_type=event_type,
            event_name=event_name,
            user=user,
            installation=installation,
            **kwargs
        )


# ============================================================================
# Phase 6.6: Workflow Automation Models
# ============================================================================

class Workflow(models.Model):
    """
    Defines automated workflows with triggers and actions.
    Workflows automate repetitive tasks and enforce business rules.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('draft', 'Draft'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Ownership
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='workflows',
        null=True,
        blank=True,
        help_text='Project-specific workflow (null for global)'
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_workflows')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    is_template = models.BooleanField(default=False, help_text='Is this a reusable template?')

    # Configuration
    trigger_type = models.CharField(max_length=100, help_text='Type of trigger that starts workflow')
    trigger_config = models.JSONField(default=dict, help_text='Trigger configuration')

    # Execution settings
    priority = models.IntegerField(default=0, help_text='Higher priority workflows execute first')
    max_retries = models.IntegerField(default=3)
    retry_delay = models.IntegerField(default=60, help_text='Retry delay in seconds')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_executed = models.DateTimeField(null=True, blank=True)

    # Statistics
    execution_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'project_workflow'
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['status', '-priority']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['trigger_type']),
            models.Index(fields=['-last_executed']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def can_execute(self):
        """Check if workflow can be executed"""
        return self.status == 'active'

    def increment_execution_count(self):
        """Increment execution counter"""
        self.execution_count += 1
        self.last_executed = timezone.now()
        self.save(update_fields=['execution_count', 'last_executed'])


class WorkflowTrigger(models.Model):
    """
    Defines when a workflow should be triggered.
    Supports event-based, schedule-based, and manual triggers.
    """
    TRIGGER_TYPES = [
        ('task_created', 'Task Created'),
        ('task_updated', 'Task Updated'),
        ('task_status_changed', 'Task Status Changed'),
        ('task_assigned', 'Task Assigned'),
        ('task_due_soon', 'Task Due Soon'),
        ('task_overdue', 'Task Overdue'),
        ('project_created', 'Project Created'),
        ('project_updated', 'Project Updated'),
        ('schedule', 'Scheduled Time'),
        ('manual', 'Manual Trigger'),
        ('webhook', 'Webhook Trigger'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='triggers')

    # Trigger configuration
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)

    # Conditions (JSON)
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text='Conditions that must be met for trigger to fire'
    )

    # Schedule configuration (for scheduled triggers)
    schedule_cron = models.CharField(
        max_length=100,
        blank=True,
        help_text='Cron expression for scheduled triggers'
    )
    schedule_timezone = models.CharField(max_length=50, default='UTC')

    # Status
    is_active = models.BooleanField(default=True)

    # Statistics
    trigger_count = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'project_workflow_trigger'
        ordering = ['workflow', 'trigger_type']
        indexes = [
            models.Index(fields=['workflow', 'is_active']),
            models.Index(fields=['trigger_type']),
        ]

    def __str__(self):
        return f"{self.workflow.name} - {self.get_trigger_type_display()}"

    def check_conditions(self, context):
        """Check if trigger conditions are met"""
        if not self.conditions:
            return True

        for key, expected_value in self.conditions.items():
            actual_value = context.get(key)
            if actual_value != expected_value:
                return False

        return True

    def increment_trigger_count(self):
        """Increment trigger counter"""
        self.trigger_count += 1
        self.last_triggered = timezone.now()
        self.save(update_fields=['trigger_count', 'last_triggered'])


class WorkflowAction(models.Model):
    """
    Defines actions to be performed when a workflow is triggered.
    Actions are executed in sequence (by order field).
    """
    ACTION_TYPES = [
        ('send_email', 'Send Email'),
        ('send_notification', 'Send Notification'),
        ('update_task', 'Update Task'),
        ('create_task', 'Create Task'),
        ('assign_task', 'Assign Task'),
        ('change_status', 'Change Status'),
        ('add_comment', 'Add Comment'),
        ('webhook', 'Call Webhook'),
        ('delay', 'Delay'),
        ('conditional', 'Conditional Branch'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='actions')

    # Action configuration
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    order = models.IntegerField(default=0, help_text='Execution order (lower executes first)')

    # Action parameters (JSON)
    parameters = models.JSONField(
        default=dict,
        help_text='Action-specific parameters'
    )

    # Conditional execution
    condition = models.JSONField(
        default=dict,
        blank=True,
        help_text='Condition for executing this action'
    )

    # Error handling
    continue_on_error = models.BooleanField(
        default=False,
        help_text='Continue workflow if this action fails'
    )

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'project_workflow_action'
        ordering = ['workflow', 'order']
        indexes = [
            models.Index(fields=['workflow', 'order']),
            models.Index(fields=['action_type']),
        ]

    def __str__(self):
        return f"{self.workflow.name} - {self.get_action_type_display()} (#{self.order})"


class WorkflowExecution(models.Model):
    """
    Records workflow execution history.
    Tracks success, failure, and execution details.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')

    # Trigger information
    trigger = models.ForeignKey(
        WorkflowTrigger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executions'
    )
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_workflows'
    )

    # Execution context
    context = models.JSONField(
        default=dict,
        help_text='Execution context data (task, project, etc.)'
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Results
    result = models.JSONField(
        default=dict,
        blank=True,
        help_text='Execution results and output'
    )
    error_message = models.TextField(blank=True)

    # Retry tracking
    attempt = models.IntegerField(default=1)
    max_attempts = models.IntegerField(default=3)

    class Meta:
        db_table = 'project_workflow_execution'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['triggered_by', '-created_at']),
        ]

    def __str__(self):
        return f"{self.workflow.name} - {self.get_status_display()} - {self.created_at}"

    def mark_running(self):
        """Mark execution as running"""
        self.status = 'running'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def mark_completed(self, result=None):
        """Mark execution as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if result:
            self.result = result
        self.save(update_fields=['status', 'completed_at', 'result'])

        # Update workflow statistics
        self.workflow.success_count += 1
        self.workflow.save(update_fields=['success_count'])

    def mark_failed(self, error_message):
        """Mark execution as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])

        # Update workflow statistics
        self.workflow.failure_count += 1
        self.workflow.save(update_fields=['failure_count'])

    def can_retry(self):
        """Check if execution can be retried"""
        return self.status == 'failed' and self.attempt < self.max_attempts

    def duration(self):
        """Calculate execution duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AutomationRule(models.Model):
    """
    Simplified automation rules for common scenarios.
    Alternative to complex workflows for simple automations.
    """
    RULE_TYPES = [
        ('auto_assign', 'Auto-assign tasks'),
        ('status_transition', 'Auto-transition status'),
        ('send_reminder', 'Send reminders'),
        ('escalate', 'Escalate overdue tasks'),
        ('archive', 'Auto-archive completed'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='automation_rules',
        null=True,
        blank=True
    )

    # Rule configuration
    rule_type = models.CharField(max_length=50, choices=RULE_TYPES)
    conditions = models.JSONField(default=dict, help_text='When to apply rule')
    actions = models.JSONField(default=dict, help_text='What to do')

    # Status
    is_active = models.BooleanField(default=True, db_index=True)

    # Schedule
    run_schedule = models.CharField(
        max_length=100,
        blank=True,
        help_text='Cron expression for scheduled rules'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run = models.DateTimeField(null=True, blank=True)

    # Statistics
    run_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'project_automation_rule'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['rule_type']),
            models.Index(fields=['-last_run']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
