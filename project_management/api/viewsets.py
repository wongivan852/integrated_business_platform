"""
REST API ViewSets for Project Management
Provides RESTful API endpoints for all resources
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta

from ..models import (
    Project, Task, Resource, Notification,
    UserPresence, ProjectTemplate
)
from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer, ProjectCreateSerializer,
    TaskListSerializer, TaskDetailSerializer, TaskCreateSerializer,
    ResourceSerializer, NotificationSerializer,
    UserPresenceSerializer, ProjectTemplateSerializer, ProjectStatisticsSerializer
)
from .permissions import IsProjectMemberOrReadOnly, IsOwnerOrReadOnly


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for projects
    Supports list, retrieve, create, update, and delete operations
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'owner']
    search_fields = ['name', 'description', 'project_code']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'progress_percentage']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get projects accessible by current user"""
        user = self.request.user
        if user.is_superuser:
            return Project.objects.all()
        return Project.objects.filter(
            Q(owner=user) | Q(team_members=user)
        ).distinct()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        return ProjectDetailSerializer

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get all tasks for a project"""
        project = self.get_object()
        tasks = project.tasks.all()

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            tasks = tasks.filter(status=status_filter)

        priority_filter = request.query_params.get('priority')
        if priority_filter:
            tasks = tasks.filter(priority=priority_filter)

        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get project statistics"""
        project = self.get_object()
        tasks = project.tasks.all()

        stats = {
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status='completed').count(),
            'in_progress_tasks': tasks.filter(status='in_progress').count(),
            'pending_tasks': tasks.filter(status='pending').count(),
            'overdue_tasks': tasks.filter(
                status__in=['pending', 'in_progress'],
                due_date__lt=datetime.now().date()
            ).count(),
            'team_members': project.team_members.count(),
            'progress': project.progress_percentage,
            'budget': float(project.budget) if project.budget else 0,
            'actual_cost': float(project.actual_cost),
            'budget_variance': float(project.budget - project.actual_cost) if project.budget else 0
        }
        return Response(stats)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a team member to the project"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'member')

        try:
            from django.contrib.auth import get_user_model
            from ..models import ProjectMember
            User = get_user_model()

            user = User.objects.get(id=user_id)
            member, created = ProjectMember.objects.get_or_create(
                project=project,
                user=user,
                defaults={'role': role}
            )

            if created:
                return Response({
                    'message': f'{user.username} added to project',
                    'user_id': user.id,
                    'username': user.username
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'message': 'User is already a member of this project'
                }, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a team member from the project"""
        project = self.get_object()
        user_id = request.data.get('user_id')

        try:
            from ..models import ProjectMember
            member = ProjectMember.objects.get(project=project, user_id=user_id)
            username = member.user.username
            member.delete()

            return Response({
                'message': f'{username} removed from project'
            })
        except ProjectMember.DoesNotExist:
            return Response({
                'error': 'Member not found'
            }, status=status.HTTP_404_NOT_FOUND)


class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for tasks
    Supports full CRUD operations and custom actions
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'project', 'assignee']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get tasks accessible by current user"""
        user = self.request.user
        if user.is_superuser:
            return Task.objects.all()
        return Task.objects.filter(
            Q(project__owner=user) |
            Q(project__team_members=user) |
            Q(assignee=user)
        ).distinct()

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        return TaskDetailSerializer

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign task to a user"""
        task = self.get_object()
        user_id = request.data.get('user_id')

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)

            # Check if user is a project member
            if not task.project.team_members.filter(id=user_id).exists():
                return Response({
                    'error': 'User is not a member of this project'
                }, status=status.HTTP_400_BAD_REQUEST)

            task.assignee = user
            task.save()

            return Response({
                'message': f'Task assigned to {user.username}',
                'assignee': {
                    'id': user.id,
                    'username': user.username
                }
            })
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task status"""
        task = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(Task.STATUS_CHOICES):
            return Response({
                'error': 'Invalid status'
            }, status=status.HTTP_400_BAD_REQUEST)

        task.status = new_status
        task.save()

        return Response({
            'message': f'Task status updated to {new_status}',
            'status': new_status
        })

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks assigned to current user"""
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks"""
        tasks = self.get_queryset().filter(
            status__in=['pending', 'in_progress'],
            due_date__lt=datetime.now().date()
        )
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class ResourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for resources
    """
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'role']
    search_fields = ['user__username', 'role', 'skills']
    ordering_fields = ['hourly_rate', 'availability_hours']
    ordering = ['user__username']

    def get_queryset(self):
        """Get resources (admin only sees all)"""
        if self.request.user.is_superuser:
            return Resource.objects.all()
        return Resource.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available resources"""
        resources = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read', 'notification_type']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get notifications for current user"""
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'message': 'Notification marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=datetime.now()
        )
        return Response({'message': f'{count} notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notification count"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})


class UserPresenceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user presence (read-only)
    """
    serializer_class = UserPresenceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'is_online']

    def get_queryset(self):
        """Get presence records for accessible projects"""
        user = self.request.user
        if user.is_superuser:
            return UserPresence.objects.all()
        return UserPresence.objects.filter(
            Q(project__owner=user) | Q(project__team_members=user)
        ).distinct()

    @action(detail=False, methods=['get'])
    def online(self, request):
        """Get currently online users"""
        presence = self.get_queryset().filter(is_online=True)
        serializer = self.get_serializer(presence, many=True)
        return Response(serializer.data)


class ProjectTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for project templates
    """
    serializer_class = ProjectTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_public']
    search_fields = ['name', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        """Get templates accessible by current user"""
        user = self.request.user
        return ProjectTemplate.objects.filter(
            Q(is_public=True) | Q(created_by=user)
        ).distinct()

    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Create a project from this template"""
        template = self.get_object()
        project_name = request.data.get('name', f"{template.name} - New Project")
        project_data = request.data.copy()
        project_data['name'] = project_name

        # Create project from template logic here
        # (Implementation depends on your specific requirements)

        return Response({
            'message': 'Project created from template',
            'template_id': template.id,
            'template_name': template.name
        }, status=status.HTTP_201_CREATED)


class DashboardViewSet(viewsets.ViewSet):
    """
    API endpoint for dashboard statistics
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall dashboard statistics"""
        user = request.user

        # Get user's projects
        if user.is_superuser:
            projects = Project.objects.all()
            tasks = Task.objects.all()
        else:
            projects = Project.objects.filter(
                Q(owner=user) | Q(team_members=user)
            ).distinct()
            tasks = Task.objects.filter(
                Q(project__owner=user) |
                Q(project__team_members=user) |
                Q(assignee=user)
            ).distinct()

        stats = {
            'total_projects': projects.count(),
            'active_projects': projects.filter(status='active').count(),
            'completed_projects': projects.filter(status='completed').count(),
            'on_hold_projects': projects.filter(status='on_hold').count(),
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status='completed').count(),
            'in_progress_tasks': tasks.filter(status='in_progress').count(),
            'overdue_tasks': tasks.filter(
                status__in=['pending', 'in_progress'],
                due_date__lt=datetime.now().date()
            ).count(),
            'my_tasks': tasks.filter(assignee=user).count(),
            'total_budget': sum([float(p.budget) for p in projects if p.budget]),
            'total_cost': sum([float(p.actual_cost) for p in projects]),
            'team_size': projects.aggregate(
                total_members=Count('team_members', distinct=True)
            )['total_members'] or 0,
            'avg_completion_rate': projects.aggregate(
                avg_progress=Avg('progress_percentage')
            )['avg_progress'] or 0
        }

        serializer = ProjectStatisticsSerializer(stats)
        return Response(serializer.data)
