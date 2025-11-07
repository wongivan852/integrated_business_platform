"""
Custom Permission Classes for Project Management API
Defines fine-grained access control for API endpoints
"""

from rest_framework import permissions
from django.db.models import Q


class IsProjectMemberOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow members of a project to edit it.
    Non-members can only read public projects.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            # For GET, HEAD, OPTIONS - allow if user is member or owner
            if hasattr(obj, 'owner'):
                return obj.owner == request.user or request.user in obj.team_members.all()
            return True

        # Write permissions only for project owner or team members with appropriate role
        if hasattr(obj, 'owner'):
            # Project object
            if obj.owner == request.user:
                return True

            # Check if user is team member with edit permissions
            from ..models import ProjectMember
            try:
                member = ProjectMember.objects.get(project=obj, user=request.user)
                return member.role in ['manager', 'editor']
            except ProjectMember.DoesNotExist:
                return False

        # For task objects, check project access
        if hasattr(obj, 'project'):
            project = obj.project
            if project.owner == request.user:
                return True

            from ..models import ProjectMember
            try:
                member = ProjectMember.objects.get(project=project, user=request.user)
                return member.role in ['manager', 'editor']
            except ProjectMember.DoesNotExist:
                return False

        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        if hasattr(obj, 'user'):
            return obj.user == request.user

        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False


class IsTaskAssigneeOrProjectMember(permissions.BasePermission):
    """
    Permission for tasks: allows access to assignee or project members
    """

    def has_object_permission(self, request, view, obj):
        # Allow if user is the assignee
        if obj.assignee == request.user:
            return True

        # Allow if user is project owner
        if obj.project.owner == request.user:
            return True

        # Allow if user is project member
        if request.user in obj.project.team_members.all():
            # Read-only for viewers
            if request.method in permissions.SAFE_METHODS:
                return True

            # Edit for managers/editors
            from ..models import ProjectMember
            try:
                member = ProjectMember.objects.get(project=obj.project, user=request.user)
                return member.role in ['manager', 'editor']
            except ProjectMember.DoesNotExist:
                return False

        return False


class HasAPIAccess(permissions.BasePermission):
    """
    Permission to check if user has API access enabled
    Can be extended to check for API keys, rate limits, etc.
    """

    message = 'You do not have API access permissions.'

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers always have access
        if request.user.is_superuser:
            return True

        # Check if user account is active
        if not request.user.is_active:
            return False

        # Check if user has API access permission
        # This could be a custom user field or group membership
        if hasattr(request.user, 'has_api_access'):
            return request.user.has_api_access

        # By default, all authenticated active users have API access
        # You can make this more restrictive based on your requirements
        return True


class IsProjectOwner(permissions.BasePermission):
    """
    Permission that only allows project owners to perform actions
    """

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        if hasattr(obj, 'project'):
            return obj.project.owner == request.user

        return False


class CanManageTeam(permissions.BasePermission):
    """
    Permission for managing team members (add/remove)
    Only project owners and managers can manage team
    """

    def has_object_permission(self, request, view, obj):
        # Project owners can always manage team
        if hasattr(obj, 'owner'):
            if obj.owner == request.user:
                return True

        # Check if user is a manager
        if hasattr(obj, 'team_members'):
            from ..models import ProjectMember
            try:
                member = ProjectMember.objects.get(project=obj, user=request.user)
                return member.role == 'manager'
            except ProjectMember.DoesNotExist:
                return False

        return False


class CanCreateProject(permissions.BasePermission):
    """
    Permission to check if user can create new projects
    Can be extended to implement project creation limits
    """

    message = 'You do not have permission to create projects.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers can always create
        if request.user.is_superuser:
            return True

        # Check if account is active
        if not request.user.is_active:
            return False

        # Add custom logic here for project creation limits
        # For example, check user's plan, project count, etc.

        # By default, all authenticated users can create projects
        return True


class CanDeleteProject(permissions.BasePermission):
    """
    Permission to check if user can delete a project
    Only project owners can delete their projects
    """

    message = 'Only project owners can delete projects.'

    def has_object_permission(self, request, view, obj):
        # Only owners can delete
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        return False


class CanManageNotifications(permissions.BasePermission):
    """
    Permission for managing notifications
    Users can only manage their own notifications
    """

    def has_object_permission(self, request, view, obj):
        # Users can only access their own notifications
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False


class IsResourceAvailable(permissions.BasePermission):
    """
    Permission to check if resource is available for assignment
    """

    def has_object_permission(self, request, view, obj):
        # Read access for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations, check if resource is active
        if hasattr(obj, 'is_active'):
            if not obj.is_active:
                self.message = 'This resource is not currently available.'
                return False

        return True


class CanAccessProjectStatistics(permissions.BasePermission):
    """
    Permission to access project statistics
    Project members and owners can access statistics
    """

    def has_object_permission(self, request, view, obj):
        # Project owner
        if hasattr(obj, 'owner'):
            if obj.owner == request.user:
                return True

        # Project team member
        if hasattr(obj, 'team_members'):
            if request.user in obj.team_members.all():
                return True

        # Superuser
        if request.user.is_superuser:
            return True

        return False


class CanExportData(permissions.BasePermission):
    """
    Permission to export project data
    Only owners and managers can export data
    """

    message = 'You do not have permission to export data.'

    def has_object_permission(self, request, view, obj):
        # Project owner
        if hasattr(obj, 'owner'):
            if obj.owner == request.user:
                return True

        # Check if user is a manager
        if hasattr(obj, 'team_members'):
            from ..models import ProjectMember
            try:
                member = ProjectMember.objects.get(project=obj, user=request.user)
                return member.role in ['manager', 'owner']
            except ProjectMember.DoesNotExist:
                return False

        return False


class RateLimitPermission(permissions.BasePermission):
    """
    Permission class for API rate limiting
    This is a placeholder - actual rate limiting should be implemented
    using django-ratelimit or similar package
    """

    message = 'Rate limit exceeded. Please try again later.'

    def has_permission(self, request, view):
        # This is a basic implementation
        # In production, use django-ratelimit or DRF throttling

        # Superusers are exempt from rate limiting
        if request.user.is_superuser:
            return True

        # Implement your rate limiting logic here
        # For example, check Redis cache for request count

        return True


class IsAuthenticatedAndActive(permissions.BasePermission):
    """
    Combined permission: user must be authenticated and active
    """

    message = 'Authentication required and account must be active.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )
