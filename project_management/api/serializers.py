"""
REST API Serializers for Project Management
Handles serialization/deserialization of models for API endpoints
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import (
    Project, Task, Resource, ProjectMember,
    KanbanColumn, TaskDependency,
    ProjectTemplate, TemplateTask, Notification, UserPresence
)

User = get_user_model()


# ============================================================================
# USER SERIALIZERS
# ============================================================================

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user information"""
    project_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'date_joined', 'is_active', 'project_count', 'task_count']
        read_only_fields = ['id', 'date_joined', 'project_count', 'task_count']

    def get_project_count(self, obj):
        return obj.projects.count()

    def get_task_count(self, obj):
        return obj.assigned_tasks.count()


# ============================================================================
# PROJECT SERIALIZERS
# ============================================================================

class ProjectListSerializer(serializers.ModelSerializer):
    """List view serializer for projects"""
    owner = UserBasicSerializer(read_only=True)
    team_member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'project_code', 'status', 'priority', 'start_date',
                  'end_date', 'owner', 'team_member_count', 'task_count',
                  'completion_rate', 'progress_percentage', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_team_member_count(self, obj):
        return obj.team_members.count()

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_completion_rate(self, obj):
        total = obj.tasks.count()
        if total == 0:
            return 0
        completed = obj.tasks.filter(status='completed').count()
        return round((completed / total) * 100, 2)


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Detailed view serializer for projects"""
    owner = UserBasicSerializer(read_only=True)
    team_members = UserBasicSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()
    milestones = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'project_code', 'status', 'priority',
                  'start_date', 'end_date', 'actual_start_date', 'actual_end_date',
                  'owner', 'team_members', 'budget', 'actual_cost',
                  'progress_percentage', 'default_view', 'tasks', 'milestones',
                  'stats', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tasks(self, obj):
        tasks = obj.tasks.all()[:10]  # Limit to 10 most recent
        return TaskListSerializer(tasks, many=True).data

    def get_milestones(self, obj):
        milestones = obj.milestones.all()[:5]
        return MilestoneSerializer(milestones, many=True).data

    def get_stats(self, obj):
        total_tasks = obj.tasks.count()
        return {
            'total_tasks': total_tasks,
            'completed_tasks': obj.tasks.filter(status='completed').count(),
            'in_progress_tasks': obj.tasks.filter(status='in_progress').count(),
            'pending_tasks': obj.tasks.filter(status='pending').count(),
            'overdue_tasks': obj.tasks.filter(status__in=['pending', 'in_progress'],
                                              due_date__lt=serializers.DateField().to_representation(obj)).count() if hasattr(obj, 'tasks') else 0,
            'team_member_count': obj.team_members.count(),
            'milestone_count': obj.milestones.count(),
            'budget_spent_percentage': round((float(obj.actual_cost) / float(obj.budget) * 100), 2) if obj.budget and obj.budget > 0 else 0
        }


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects"""
    team_member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'project_code', 'status', 'priority',
                  'start_date', 'end_date', 'budget', 'default_view', 'team_member_ids']

    def create(self, validated_data):
        team_member_ids = validated_data.pop('team_member_ids', [])
        request = self.context.get('request')
        validated_data['owner'] = request.user
        project = Project.objects.create(**validated_data)

        # Add team members
        if team_member_ids:
            for user_id in team_member_ids:
                try:
                    user = User.objects.get(id=user_id)
                    ProjectMember.objects.create(project=project, user=user, role='member')
                except User.DoesNotExist:
                    pass

        return project


# ============================================================================
# TASK SERIALIZERS
# ============================================================================

class TaskListSerializer(serializers.ModelSerializer):
    """List view serializer for tasks"""
    assignee = UserBasicSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'status', 'priority', 'project', 'project_name',
                  'assignee', 'due_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskDetailSerializer(serializers.ModelSerializer):
    """Detailed view serializer for tasks"""
    assignee = UserBasicSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    dependencies = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'project',
                  'assignee', 'due_date', 'start_date', 'end_date', 'actual_start_date',
                  'actual_end_date', 'estimated_hours', 'actual_hours', 'progress_percentage',
                  'dependencies', 'comments_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_dependencies(self, obj):
        deps = obj.dependents.all()
        return [{'id': d.predecessor.id, 'title': d.predecessor.title,
                 'dependency_type': d.dependency_type} for d in deps]

    def get_comments_count(self, obj):
        return getattr(obj, 'comments', []).count() if hasattr(obj, 'comments') else 0


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks"""
    assignee_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'project',
                  'assignee_id', 'due_date', 'start_date', 'estimated_hours']

    def create(self, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        task = Task.objects.create(**validated_data)

        if assignee_id:
            try:
                task.assignee = User.objects.get(id=assignee_id)
                task.save()
            except User.DoesNotExist:
                pass

        return task


# ============================================================================
# RESOURCE SERIALIZERS
# ============================================================================

class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for resources"""
    user = UserBasicSerializer(read_only=True)
    allocation_count = serializers.SerializerMethodField()
    utilization_rate = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = ['id', 'user', 'role', 'hourly_rate', 'availability_hours',
                  'skills', 'is_active', 'allocation_count', 'utilization_rate',
                  'created_at']
        read_only_fields = ['id', 'created_at']

    def get_allocation_count(self, obj):
        return obj.allocations.filter(is_active=True).count()

    def get_utilization_rate(self, obj):
        total_allocated = sum([a.allocated_hours for a in obj.allocations.filter(is_active=True)])
        if obj.availability_hours == 0:
            return 0
        return round((total_allocated / obj.availability_hours) * 100, 2)


# ============================================================================
# NOTIFICATION SERIALIZERS
# ============================================================================

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications"""
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'project',
                  'task', 'action_url', 'is_read', 'read_at', 'created_at']
        read_only_fields = ['id', 'created_at', 'read_at']


# ============================================================================
# PRESENCE SERIALIZERS
# ============================================================================

class UserPresenceSerializer(serializers.ModelSerializer):
    """Serializer for user presence"""
    user = UserBasicSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserPresence
        fields = ['id', 'user', 'project', 'project_name', 'is_online',
                  'current_page', 'last_seen', 'is_active']
        read_only_fields = ['id', 'last_seen', 'is_active']


# ============================================================================
# TEMPLATE SERIALIZERS
# ============================================================================

class TemplateTaskSerializer(serializers.ModelSerializer):
    """Serializer for template tasks"""
    class Meta:
        model = TemplateTask
        fields = ['id', 'title', 'description', 'estimated_hours', 'priority',
                  'order', 'default_status']
        read_only_fields = ['id']


class ProjectTemplateSerializer(serializers.ModelSerializer):
    """Serializer for project templates"""
    created_by = UserBasicSerializer(read_only=True)
    tasks = TemplateTaskSerializer(source='tasks.all', many=True, read_only=True)
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectTemplate
        fields = ['id', 'name', 'description', 'category', 'is_public',
                  'created_by', 'tasks', 'usage_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_usage_count(self, obj):
        return obj.usage_count


# ============================================================================
# STATISTICS SERIALIZERS
# ============================================================================

class ProjectStatisticsSerializer(serializers.Serializer):
    """Serializer for project statistics"""
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    on_hold_projects = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    total_budget = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    team_size = serializers.IntegerField()
    avg_completion_rate = serializers.FloatField()
