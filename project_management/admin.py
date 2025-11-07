"""
Admin panel configuration for Project Management app
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Project, ProjectMember, Task, TaskDependency,
    ProjectBaseline, BaselineTask, KanbanColumn,
    TaskLabel, TaskLabelAssignment, TaskChecklist,
    ChecklistItem, TaskComment, TaskAttachment, TaskActivity,
    # Phase 4 models
    Skill, Resource, ResourceAssignment,
    ProjectCost, TaskCost, EVMSnapshot,
    ProjectTemplate, TemplateTask, TemplateDependency,
    # Phase 5 models
    ProjectMetrics, DashboardWidget, Notification
)


# ============================================================================
# INLINE ADMIN CLASSES
# ============================================================================

class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ['task_code', 'title', 'status', 'priority', 'progress']
    readonly_fields = ['task_code']
    show_change_link = True


class KanbanColumnInline(admin.TabularInline):
    model = KanbanColumn
    extra = 0
    fields = ['name', 'position', 'color', 'wip_limit']
    ordering = ['position']


class TaskLabelInline(admin.TabularInline):
    model = TaskLabel
    extra = 1
    fields = ['name', 'color', 'description']


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1
    fields = ['text', 'is_completed', 'position', 'assigned_to']
    ordering = ['position']


class TaskCommentInline(admin.StackedInline):
    model = TaskComment
    extra = 0
    fields = ['author', 'text', 'created_at']
    readonly_fields = ['created_at']


# ============================================================================
# MODEL ADMIN CLASSES
# ============================================================================

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        'project_code', 'name', 'status_badge', 'priority_badge',
        'owner', 'progress_bar', 'days_remaining_display',
        'budget_display', 'created_at'
    ]
    list_filter = ['status', 'priority', 'default_view', 'created_at']
    search_fields = ['name', 'project_code', 'description', 'owner__email']
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'project_code', 'description', 'owner', 'created_by']
        }),
        ('Dates', {
            'fields': [
                ('start_date', 'end_date'),
                ('actual_start_date', 'actual_end_date')
            ]
        }),
        ('Status & Progress', {
            'fields': [
                ('status', 'priority'),
                'progress_percentage',
                'default_view'
            ]
        }),
        ('Budget', {
            'fields': [('budget', 'actual_cost')],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': [('created_at', 'updated_at')],
            'classes': ['collapse']
        })
    ]

    inlines = [ProjectMemberInline, KanbanColumnInline, TaskLabelInline]

    def status_badge(self, obj):
        colors = {
            'planning': 'gray',
            'active': 'green',
            'on_hold': 'orange',
            'completed': 'blue',
            'cancelled': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def priority_badge(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def progress_bar(self, obj):
        percentage = float(obj.progress_percentage) if obj.progress_percentage else 0
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: #007bff; color: white; '
            'text-align: center; border-radius: 3px; padding: 2px;">{}%</div></div>',
            percentage, int(percentage)
        )
    progress_bar.short_description = 'Progress'

    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if obj.is_overdue:
            return format_html('<span style="color: red;">Overdue</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        return f'{days} days'
    days_remaining_display.short_description = 'Time Left'

    def budget_display(self, obj):
        if obj.budget:
            percentage = float(obj.budget_percentage_used) if obj.budget_percentage_used else 0
            actual = float(obj.actual_cost) if obj.actual_cost else 0
            budget = float(obj.budget)

            if percentage > 100:
                color = 'red'
            elif percentage > 80:
                color = 'orange'
            else:
                color = 'green'

            # Format the numbers first, then pass to format_html
            actual_formatted = f'¥{actual:,.2f}'
            budget_formatted = f'¥{budget:,.2f}'

            return format_html(
                '<span style="color: {};">{} / {}</span>',
                color, actual_formatted, budget_formatted
            )
        return '-'
    budget_display.short_description = 'Budget'


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'project__name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'task_code', 'title', 'project', 'status_badge',
        'priority_badge', 'progress_display', 'assignees_display',
        'due_date_display', 'is_milestone'
    ]
    list_filter = [
        'status', 'priority', 'is_milestone',
        'kanban_column', 'created_at'
    ]
    search_fields = ['task_code', 'title', 'description', 'project__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']

    fieldsets = [
        ('Basic Information', {
            'fields': [
                'project', 'title', 'task_code',
                'description', 'created_by'
            ]
        }),
        ('Hierarchy (Gantt)', {
            'fields': [
                'parent_task', 'indent_level', 'order'
            ],
            'classes': ['collapse']
        }),
        ('Gantt Chart Fields', {
            'fields': [
                ('start_date', 'end_date'),
                'duration', 'progress', 'is_milestone'
            ]
        }),
        ('Kanban Board Fields', {
            'fields': [
                'kanban_column', 'kanban_position'
            ]
        }),
        ('Status & Priority', {
            'fields': [
                ('status', 'priority'),
                'due_date'
            ]
        }),
        ('Time Tracking', {
            'fields': [
                ('estimated_hours', 'actual_hours')
            ],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': [('created_at', 'updated_at')],
            'classes': ['collapse']
        })
    ]

    filter_horizontal = ['assigned_to']
    inlines = [TaskCommentInline]

    def status_badge(self, obj):
        colors = {
            'todo': '#6c757d',
            'in_progress': '#007bff',
            'review': '#ffc107',
            'blocked': '#dc3545',
            'completed': '#28a745'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def priority_badge(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def progress_display(self, obj):
        progress = int(obj.progress) if obj.progress else 0
        return format_html(
            '<div style="width: 60px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: #28a745; color: white; '
            'text-align: center; border-radius: 3px; padding: 2px; font-size: 10px;">'
            '{}%</div></div>',
            progress, progress
        )
    progress_display.short_description = 'Progress'

    def assignees_display(self, obj):
        assignees = obj.assigned_to.all()
        if assignees:
            names = ', '.join([u.get_full_name() or u.email for u in assignees[:2]])
            if assignees.count() > 2:
                names += f' +{assignees.count() - 2}'
            return names
        return '-'
    assignees_display.short_description = 'Assigned To'

    def due_date_display(self, obj):
        if obj.due_date:
            if obj.is_overdue:
                return format_html('<span style="color: red;">{}</span>', obj.due_date)
            return obj.due_date
        return '-'
    due_date_display.short_description = 'Due Date'


@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display = [
        'predecessor', 'dependency_type_display',
        'successor', 'lag_days', 'created_at'
    ]
    list_filter = ['dependency_type', 'created_at']
    search_fields = [
        'predecessor__task_code', 'predecessor__title',
        'successor__task_code', 'successor__title'
    ]

    def dependency_type_display(self, obj):
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-family: monospace;">{}</span>',
            obj.dependency_type
        )
    dependency_type_display.short_description = 'Type'


@admin.register(ProjectBaseline)
class ProjectBaselineAdmin(admin.ModelAdmin):
    list_display = ['project', 'name', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['project__name', 'name', 'description']
    readonly_fields = ['created_at', 'created_by']


@admin.register(BaselineTask)
class BaselineTaskAdmin(admin.ModelAdmin):
    list_display = ['baseline', 'task_code', 'title', 'start_date', 'end_date', 'progress']
    list_filter = ['baseline']
    search_fields = ['task_code', 'title']


@admin.register(KanbanColumn)
class KanbanColumnAdmin(admin.ModelAdmin):
    list_display = ['project', 'name', 'position', 'color_display', 'task_count', 'wip_limit_display']
    list_filter = ['project']
    search_fields = ['project__name', 'name']
    ordering = ['project', 'position']

    def color_display(self, obj):
        return format_html(
            '<div style="width: 30px; height: 20px; background-color: {}; '
            'border: 1px solid #ccc; border-radius: 3px;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'

    def wip_limit_display(self, obj):
        if obj.wip_limit:
            if obj.is_over_wip_limit:
                return format_html(
                    '<span style="color: red;">{} / {} (OVER)</span>',
                    obj.task_count, obj.wip_limit
                )
            return f'{obj.task_count} / {obj.wip_limit}'
        return '-'
    wip_limit_display.short_description = 'WIP Limit'


@admin.register(TaskLabel)
class TaskLabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'color_display', 'description']
    list_filter = ['project']
    search_fields = ['name', 'description']

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 12px; '
            'border-radius: 10px;">{}</span>',
            obj.color, obj.name
        )
    color_display.short_description = 'Preview'


@admin.register(TaskLabelAssignment)
class TaskLabelAssignmentAdmin(admin.ModelAdmin):
    list_display = ['task', 'label', 'assigned_at']
    list_filter = ['label', 'assigned_at']
    search_fields = ['task__task_code', 'task__title', 'label__name']


@admin.register(TaskChecklist)
class TaskChecklistAdmin(admin.ModelAdmin):
    list_display = ['task', 'title', 'completion_display', 'position', 'created_at']
    list_filter = ['created_at']
    search_fields = ['task__task_code', 'task__title', 'title']
    inlines = [ChecklistItemInline]

    def completion_display(self, obj):
        percentage = obj.completion_percentage
        color = '#28a745' if percentage == 100 else '#007bff'
        return format_html(
            '<div style="width: 80px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; '
            'text-align: center; border-radius: 3px; padding: 2px; font-size: 10px;">'
            '{}%</div></div>',
            percentage, color, percentage
        )
    completion_display.short_description = 'Completion'


@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = [
        'checklist', 'text_preview', 'is_completed',
        'assigned_to', 'completed_by', 'position'
    ]
    list_filter = ['is_completed', 'completed_at']
    search_fields = ['text', 'checklist__title']

    def text_preview(self, obj):
        if len(obj.text) > 50:
            return obj.text[:50] + '...'
        return obj.text
    text_preview.short_description = 'Text'


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'text_preview', 'created_at', 'is_edited']
    list_filter = ['created_at', 'is_edited']
    search_fields = ['task__task_code', 'author__email', 'text']
    readonly_fields = ['created_at', 'updated_at']

    def text_preview(self, obj):
        if len(obj.text) > 100:
            return obj.text[:100] + '...'
        return obj.text
    text_preview.short_description = 'Comment'


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        'filename', 'task', 'file_size_display',
        'file_type', 'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['filename', 'task__task_code', 'description']
    readonly_fields = ['uploaded_at', 'file_size']

    def file_size_display(self, obj):
        return f'{obj.file_size_mb} MB'
    file_size_display.short_description = 'File Size'


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'action_badge', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['task__task_code', 'user__email']
    readonly_fields = ['timestamp', 'details']

    def action_badge(self, obj):
        colors = {
            'created': '#28a745',
            'updated': '#007bff',
            'moved': '#17a2b8',
            'assigned': '#6f42c1',
            'completed': '#28a745',
            'status_changed': '#ffc107',
            'priority_changed': '#fd7e14'
        }
        color = colors.get(obj.action, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_action_display()
        )
    action_badge.short_description = 'Action'


# ============================================================================
# PHASE 4: RESOURCE MANAGEMENT & EVM ADMIN CLASSES
# ============================================================================

class ResourceAssignmentInline(admin.TabularInline):
    model = ResourceAssignment
    extra = 1
    fields = ['task', 'allocation_percentage', 'assigned_hours', 'actual_hours', 'start_date', 'end_date']
    readonly_fields = ['actual_hours']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description']
    list_filter = ['category']
    search_fields = ['name', 'description']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = [
        'user_display', 'job_title', 'department',
        'hourly_rate_display', 'availability_display',
        'hours_per_day', 'is_active'
    ]
    list_filter = ['is_active', 'department', 'start_date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'job_title', 'department']
    filter_horizontal = ['skills']
    readonly_fields = ['available_hours_per_day']

    fieldsets = [
        ('Basic Information', {
            'fields': ['user', 'job_title', 'department', 'is_active']
        }),
        ('Capacity & Availability', {
            'fields': [
                'working_hours_per_day',
                'availability_percentage',
                'available_hours_per_day',
                ('start_date', 'end_date')
            ]
        }),
        ('Financial', {
            'fields': ['hourly_rate'],
            'classes': ['collapse']
        }),
        ('Skills', {
            'fields': ['skills']
        })
    ]

    inlines = [ResourceAssignmentInline]

    def user_display(self, obj):
        return obj.user.get_full_name() or obj.user.email
    user_display.short_description = 'User'

    def hourly_rate_display(self, obj):
        rate = float(obj.hourly_rate) if obj.hourly_rate else 0
        rate_formatted = f'${rate:,.2f}'
        return format_html('{}', rate_formatted)
    hourly_rate_display.short_description = 'Hourly Rate'

    def availability_display(self, obj):
        availability = int(obj.availability_percentage) if obj.availability_percentage else 0
        color = '#28a745' if availability >= 80 else '#ffc107'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, availability
        )
    availability_display.short_description = 'Availability'

    def hours_per_day(self, obj):
        return f'{obj.available_hours_per_day:.1f} hrs'
    hours_per_day.short_description = 'Available Hrs/Day'


@admin.register(ResourceAssignment)
class ResourceAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'resource', 'task', 'allocation_display',
        'assigned_hours', 'actual_hours', 'variance_display',
        'date_range'
    ]
    list_filter = ['start_date', 'end_date', 'allocation_percentage']
    search_fields = [
        'resource__user__email', 'task__task_code', 'task__title'
    ]

    def allocation_display(self, obj):
        color = '#dc3545' if obj.allocation_percentage > 100 else '#28a745'
        return format_html(
            '<span style="color: {};">{:.0f}%</span>',
            color, obj.allocation_percentage
        )
    allocation_display.short_description = 'Allocation'

    def variance_display(self, obj):
        variance = obj.actual_hours - obj.assigned_hours
        if variance > 0:
            color = '#dc3545'
            sign = '+'
        elif variance < 0:
            color = '#28a745'
            sign = ''
        else:
            color = '#6c757d'
            sign = ''
        return format_html(
            '<span style="color: {};">{}{:.1f} hrs</span>',
            color, sign, variance
        )
    variance_display.short_description = 'Variance'

    def date_range(self, obj):
        return f'{obj.start_date} to {obj.end_date}'
    date_range.short_description = 'Date Range'


@admin.register(ProjectCost)
class ProjectCostAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'date', 'category', 'amount_display',
        'vendor', 'invoice_number', 'created_by'
    ]
    list_filter = ['category', 'date', 'created_at']
    search_fields = [
        'project__name', 'description', 'vendor', 'invoice_number'
    ]
    readonly_fields = ['created_at', 'created_by']

    fieldsets = [
        ('Cost Information', {
            'fields': ['project', 'date', 'category', 'amount', 'description']
        }),
        ('Vendor Details', {
            'fields': ['vendor', 'invoice_number'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at'],
            'classes': ['collapse']
        })
    ]

    def amount_display(self, obj):
        amount = float(obj.amount) if obj.amount else 0
        amount_formatted = f'¥{amount:,.2f}'
        return format_html('{}', amount_formatted)
    amount_display.short_description = 'Amount'


@admin.register(TaskCost)
class TaskCostAdmin(admin.ModelAdmin):
    list_display = [
        'task', 'cost_type', 'planned_display',
        'actual_display', 'variance_display'
    ]
    list_filter = ['cost_type']
    search_fields = ['task__task_code', 'task__title']

    def planned_display(self, obj):
        planned = float(obj.planned_cost) if obj.planned_cost else 0
        planned_formatted = f'${planned:,.2f}'
        return format_html('{}', planned_formatted)
    planned_display.short_description = 'Planned Cost'

    def actual_display(self, obj):
        actual = float(obj.actual_cost) if obj.actual_cost else 0
        actual_formatted = f'${actual:,.2f}'
        return format_html('{}', actual_formatted)
    actual_display.short_description = 'Actual Cost'

    def variance_display(self, obj):
        planned = float(obj.planned_cost) if obj.planned_cost else 0
        actual = float(obj.actual_cost) if obj.actual_cost else 0
        variance = actual - planned

        if variance > 0:
            color = '#dc3545'
            sign = '+'
        elif variance < 0:
            color = '#28a745'
            sign = ''
        else:
            color = '#6c757d'
            sign = ''

        variance_formatted = f'${sign}{abs(variance):,.2f}'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, variance_formatted
        )
    variance_display.short_description = 'Variance'


@admin.register(EVMSnapshot)
class EVMSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'snapshot_date', 'cpi_display',
        'spi_display', 'cv_display', 'sv_display',
        'health_indicator'
    ]
    list_filter = ['snapshot_date']
    search_fields = ['project__name']
    readonly_fields = ['created_at']

    fieldsets = [
        ('Snapshot Information', {
            'fields': ['project', 'snapshot_date', 'created_at']
        }),
        ('Baseline', {
            'fields': ['budget_at_completion', 'planned_duration_days']
        }),
        ('EVM Metrics', {
            'fields': [
                ('planned_value', 'earned_value', 'actual_cost')
            ]
        }),
        ('Performance Indices', {
            'fields': [
                ('cost_performance_index', 'schedule_performance_index')
            ]
        }),
        ('Variances', {
            'fields': [
                ('cost_variance', 'schedule_variance')
            ]
        }),
        ('Forecasts', {
            'fields': [
                'estimate_at_completion',
                'estimate_to_complete',
                'variance_at_completion'
            ]
        })
    ]

    def cpi_display(self, obj):
        color = '#28a745' if obj.cost_performance_index >= 1.0 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color, obj.cost_performance_index
        )
    cpi_display.short_description = 'CPI'

    def spi_display(self, obj):
        color = '#28a745' if obj.schedule_performance_index >= 1.0 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color, obj.schedule_performance_index
        )
    spi_display.short_description = 'SPI'

    def cv_display(self, obj):
        color = '#28a745' if obj.cost_variance >= 0 else '#dc3545'
        sign = '+' if obj.cost_variance > 0 else ''
        return format_html(
            '<span style="color: {};">{}{:,.2f}</span>',
            color, sign, obj.cost_variance
        )
    cv_display.short_description = 'CV'

    def sv_display(self, obj):
        color = '#28a745' if obj.schedule_variance >= 0 else '#dc3545'
        sign = '+' if obj.schedule_variance > 0 else ''
        return format_html(
            '<span style="color: {};">{}{:,.2f}</span>',
            color, sign, obj.schedule_variance
        )
    sv_display.short_description = 'SV'

    def health_indicator(self, obj):
        if obj.is_under_budget and obj.is_ahead_of_schedule:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; '
                'border-radius: 3px;">Excellent</span>'
            )
        elif obj.is_under_budget or obj.is_ahead_of_schedule:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; '
                'border-radius: 3px;">Good</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; '
                'border-radius: 3px;">At Risk</span>'
            )
    health_indicator.short_description = 'Health'


# ============================================================================
# PHASE 4: PROJECT TEMPLATES ADMIN CLASSES
# ============================================================================

class TemplateTaskInline(admin.TabularInline):
    model = TemplateTask
    extra = 1
    fields = ['name', 'estimated_hours', 'assignee_role', 'sequence_number', 'is_milestone']
    ordering = ['sequence_number']


@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'duration_display',
        'created_by', 'is_public', 'use_count',
        'created_at'
    ]
    list_filter = ['category', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['use_count', 'created_at']

    fieldsets = [
        ('Template Information', {
            'fields': ['name', 'description', 'category']
        }),
        ('Settings', {
            'fields': [
                'default_duration_days',
                'is_public',
                'created_by'
            ]
        }),
        ('Statistics', {
            'fields': ['use_count', 'created_at'],
            'classes': ['collapse']
        })
    ]

    inlines = [TemplateTaskInline]

    def duration_display(self, obj):
        return f'{obj.default_duration_days} days'
    duration_display.short_description = 'Duration'


@admin.register(TemplateTask)
class TemplateTaskAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template', 'hours_display',
        'assignee_role', 'sequence_number', 'is_milestone'
    ]
    list_filter = ['template', 'assignee_role', 'is_milestone']
    search_fields = ['name', 'description', 'template__name']
    ordering = ['template', 'sequence_number']

    def hours_display(self, obj):
        return f'{obj.estimated_hours} hrs'
    hours_display.short_description = 'Est. Hours'


@admin.register(TemplateDependency)
class TemplateDependencyAdmin(admin.ModelAdmin):
    list_display = [
        'task', 'dependency_type_display',
        'depends_on', 'lag_display', 'template'
    ]
    list_filter = ['dependency_type', 'task__template']
    search_fields = [
        'task__name', 'depends_on__name'
    ]

    def dependency_type_display(self, obj):
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-family: monospace;">{}</span>',
            obj.dependency_type
        )
    dependency_type_display.short_description = 'Type'

    def lag_display(self, obj):
        if obj.lag_days == 0:
            return '-'
        return f'{obj.lag_days} days'
    lag_display.short_description = 'Lag'

    def template(self, obj):
        return obj.task.template
    template.short_description = 'Template'


# ============================================================================
# PHASE 5: ANALYTICS ADMIN
# ============================================================================

@admin.register(ProjectMetrics)
class ProjectMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'project', 'snapshot_date', 'progress_display',
        'health_score_display', 'tasks_summary', 'budget_variance_display'
    ]
    list_filter = ['snapshot_date', 'health_score']
    search_fields = ['project__name']
    date_hierarchy = 'snapshot_date'
    ordering = ['-snapshot_date', 'project']
    readonly_fields = ['created_at']

    def progress_display(self, obj):
        color = 'success' if obj.progress_percentage >= 75 else 'warning' if obj.progress_percentage >= 50 else 'danger'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; padding: 2px 5px; border-radius: 3px; text-align: center;">'
            '{}%</div></div>',
            obj.progress_percentage,
            '#28a745' if color == 'success' else '#ffc107' if color == 'warning' else '#dc3545',
            obj.progress_percentage
        )
    progress_display.short_description = 'Progress'

    def health_score_display(self, obj):
        color = '#28a745' if obj.health_score >= 80 else '#ffc107' if obj.health_score >= 60 else '#dc3545'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.health_score
        )
    health_score_display.short_description = 'Health'

    def tasks_summary(self, obj):
        return f'{obj.tasks_completed}/{obj.tasks_total} ({obj.tasks_overdue} overdue)'
    tasks_summary.short_description = 'Tasks'

    def budget_variance_display(self, obj):
        color = '#28a745' if obj.cost_variance >= 0 else '#dc3545'
        sign = '+' if obj.cost_variance >= 0 else ''
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{}</span>',
            color, sign, obj.cost_variance
        )
    budget_variance_display.short_description = 'Budget Variance'


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'widget_type', 'title',
        'size', 'position', 'is_visible'
    ]
    list_filter = ['widget_type', 'size', 'is_visible']
    search_fields = ['user__username', 'user__email', 'title']
    ordering = ['user', 'position']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Widget Information', {
            'fields': ('user', 'widget_type', 'title')
        }),
        ('Display Settings', {
            'fields': ('size', 'position', 'is_visible')
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'title', 'notification_type_badge',
        'is_read_badge', 'project_link', 'task_link',
        'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'read_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Related Objects', {
            'fields': ('project', 'task', 'action_url')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'created_at')
        }),
    )

    def notification_type_badge(self, obj):
        colors = {
            'task_assigned': '#6f42c1',
            'task_completed': '#28a745',
            'task_overdue': '#dc3545',
            'deadline_approaching': '#fd7e14',
            'budget_alert': '#e83e8c',
            'project_status_changed': '#17a2b8',
            'comment_added': '#20c997',
            'mention': '#ffc107',
            'milestone_completed': '#00bcd4',
            'resource_assigned': '#6c757d'
        }
        color = colors.get(obj.notification_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Type'

    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Read</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;"><i class="fas fa-circle"></i> Unread</span>'
        )
    is_read_badge.short_description = 'Status'

    def project_link(self, obj):
        if obj.project:
            return format_html(
                '<a href="/admin/project_management/project/{}/change/">{}</a>',
                obj.project.id, obj.project.name
            )
        return '-'
    project_link.short_description = 'Project'

    def task_link(self, obj):
        if obj.task:
            return format_html(
                '<a href="/admin/project_management/task/{}/change/">{}</a>',
                obj.task.id, obj.task.task_code
            )
        return '-'
    task_link.short_description = 'Task'

    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected']

    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(is_read=False).update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{count} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'{count} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'
