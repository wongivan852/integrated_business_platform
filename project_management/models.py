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
