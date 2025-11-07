"""
Permission Utility Functions and Decorators for Phase 6.3
Provides helpers for checking permissions, decorators for views, and utility functions
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils import timezone

from .models import (
    CustomRole, CustomPermission, UserRoleAssignment,
    PermissionAuditLog, Project, Task, Resource
)


# ============================================================================
# PERMISSION CHECKING FUNCTIONS
# ============================================================================

def user_has_permission(user, permission_code, context=None):
    """
    Check if a user has a specific permission.

    Args:
        user: User object
        permission_code: Permission code string (e.g., 'project.edit')
        context: Optional dict with 'project', 'resource', or 'task' keys

    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user.is_authenticated:
        return False

    # Superusers have all permissions
    if user.is_superuser:
        return True

    # Get user's role assignments
    assignments = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True
    )

    # Filter by context if provided
    if context:
        if 'project' in context:
            assignments = assignments.filter(
                models.Q(project=context['project']) | models.Q(is_global=True)
            )
        elif 'resource' in context:
            assignments = assignments.filter(
                models.Q(resource=context['resource']) | models.Q(is_global=True)
            )
        else:
            # No specific context, check global assignments
            assignments = assignments.filter(is_global=True)

    # Check each assignment for the permission
    for assignment in assignments:
        if not assignment.is_valid():
            continue

        # Check if role has the permission
        if assignment.role.has_permission(permission_code):
            return True

    return False


def user_has_any_permission(user, permission_codes, context=None):
    """
    Check if user has any of the specified permissions.

    Args:
        user: User object
        permission_codes: List of permission code strings
        context: Optional context dict

    Returns:
        bool: True if user has at least one permission
    """
    for code in permission_codes:
        if user_has_permission(user, code, context):
            return True
    return False


def user_has_all_permissions(user, permission_codes, context=None):
    """
    Check if user has all of the specified permissions.

    Args:
        user: User object
        permission_codes: List of permission code strings
        context: Optional context dict

    Returns:
        bool: True if user has all permissions
    """
    for code in permission_codes:
        if not user_has_permission(user, code, context):
            return False
    return True


def get_user_permissions(user, context=None):
    """
    Get all permissions for a user in a given context.

    Args:
        user: User object
        context: Optional context dict

    Returns:
        set: Set of CustomPermission objects
    """
    if not user.is_authenticated:
        return set()

    # Superusers have all permissions
    if user.is_superuser:
        return set(CustomPermission.objects.filter(is_active=True))

    # Get user's role assignments
    assignments = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True
    )

    # Filter by context if provided
    if context:
        if 'project' in context:
            assignments = assignments.filter(
                models.Q(project=context['project']) | models.Q(is_global=True)
            )
        elif 'resource' in context:
            assignments = assignments.filter(
                models.Q(resource=context['resource']) | models.Q(is_global=True)
            )

    # Collect all permissions from valid assignments
    permissions = set()
    for assignment in assignments:
        if assignment.is_valid():
            permissions.update(assignment.get_permissions())

    return permissions


def get_user_roles(user, context=None):
    """
    Get all active roles for a user in a given context.

    Args:
        user: User object
        context: Optional context dict

    Returns:
        QuerySet: UserRoleAssignment queryset
    """
    assignments = UserRoleAssignment.objects.filter(
        user=user,
        is_active=True
    )

    # Filter by context
    if context:
        if 'project' in context:
            assignments = assignments.filter(
                models.Q(project=context['project']) | models.Q(is_global=True)
            )
        elif 'resource' in context:
            assignments = assignments.filter(
                models.Q(resource=context['resource']) | models.Q(is_global=True)
            )

    # Only return valid assignments
    valid_assignments = []
    for assignment in assignments:
        if assignment.is_valid():
            valid_assignments.append(assignment)

    return valid_assignments


# ============================================================================
# PERMISSION DECORATORS FOR VIEWS
# ============================================================================

def permission_required(permission_code, context_param=None, raise_exception=True):
    """
    Decorator to check if user has a specific permission.

    Usage:
        @permission_required('project.edit', context_param='project_id')
        def edit_project(request, project_id):
            ...

    Args:
        permission_code: Permission code string
        context_param: Name of view parameter that contains context object ID
        raise_exception: If True, raise PermissionDenied; if False, return 403
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Build context if context_param is provided
            context = None
            if context_param and context_param in kwargs:
                obj_id = kwargs[context_param]

                # Determine context type from parameter name
                if 'project' in context_param:
                    project = get_object_or_404(Project, id=obj_id)
                    context = {'project': project}
                elif 'resource' in context_param:
                    resource = get_object_or_404(Resource, id=obj_id)
                    context = {'resource': resource}
                elif 'task' in context_param:
                    task = get_object_or_404(Task, id=obj_id)
                    context = {'project': task.project}

            # Check permission
            has_perm = user_has_permission(user, permission_code, context)

            # Log access attempt
            PermissionAuditLog.log_action(
                action_type='access_allowed' if has_perm else 'access_denied',
                user=user,
                description=f"User {'granted' if has_perm else 'denied'} {permission_code}",
                resource_type=view_func.__name__,
                status='success' if has_perm else 'failure',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )

            if not has_perm:
                if raise_exception:
                    raise PermissionDenied(
                        f"You do not have permission: {permission_code}"
                    )
                else:
                    return HttpResponseForbidden(
                        f"You do not have permission: {permission_code}"
                    )

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def any_permission_required(permission_codes, context_param=None, raise_exception=True):
    """
    Decorator to check if user has any of the specified permissions.

    Usage:
        @any_permission_required(['project.edit', 'project.view'], context_param='project_id')
        def view_or_edit_project(request, project_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Build context
            context = None
            if context_param and context_param in kwargs:
                obj_id = kwargs[context_param]
                if 'project' in context_param:
                    project = get_object_or_404(Project, id=obj_id)
                    context = {'project': project}

            # Check permissions
            has_perm = user_has_any_permission(user, permission_codes, context)

            if not has_perm:
                # Log denial
                PermissionAuditLog.log_action(
                    'access_denied',
                    user,
                    f"User denied any of: {', '.join(permission_codes)}",
                    resource_type=view_func.__name__,
                    status='failure'
                )

                if raise_exception:
                    raise PermissionDenied(
                        f"You need one of these permissions: {', '.join(permission_codes)}"
                    )
                else:
                    return HttpResponseForbidden()

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


def all_permissions_required(permission_codes, context_param=None, raise_exception=True):
    """
    Decorator to check if user has all of the specified permissions.

    Usage:
        @all_permissions_required(['project.edit', 'project.manage'], context_param='project_id')
        def advanced_edit_project(request, project_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            # Build context
            context = None
            if context_param and context_param in kwargs:
                obj_id = kwargs[context_param]
                if 'project' in context_param:
                    project = get_object_or_404(Project, id=obj_id)
                    context = {'project': project}

            # Check permissions
            has_perm = user_has_all_permissions(user, permission_codes, context)

            if not has_perm:
                # Log denial
                PermissionAuditLog.log_action(
                    'access_denied',
                    user,
                    f"User missing required permissions: {', '.join(permission_codes)}",
                    resource_type=view_func.__name__,
                    status='failure'
                )

                if raise_exception:
                    raise PermissionDenied(
                        f"You need all of these permissions: {', '.join(permission_codes)}"
                    )
                else:
                    return HttpResponseForbidden()

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# ROLE MANAGEMENT FUNCTIONS
# ============================================================================

def assign_role_to_user(user, role, assigned_by, project=None, resource=None,
                        is_global=False, valid_until=None, notes=''):
    """
    Assign a role to a user with full audit logging.

    Args:
        user: User to assign role to
        role: CustomRole object
        assigned_by: User performing the assignment
        project: Optional Project object
        resource: Optional Resource object
        is_global: Boolean for global role
        valid_until: Optional expiration datetime
        notes: Optional notes

    Returns:
        UserRoleAssignment object
    """
    # Create assignment
    assignment = UserRoleAssignment.objects.create(
        user=user,
        role=role,
        project=project,
        resource=resource,
        is_global=is_global,
        valid_until=valid_until,
        assigned_by=assigned_by,
        notes=notes
    )

    # Log action
    context_desc = "globally"
    if project:
        context_desc = f"for project '{project.name}'"
    elif resource:
        context_desc = f"for resource '{resource.user.username}'"

    PermissionAuditLog.log_action(
        action_type='role_assigned',
        user=assigned_by,
        description=f"Assigned role '{role.display_name}' to {user.username} {context_desc}",
        target_user=user,
        target_role=role,
        project=project,
        status='success'
    )

    return assignment


def revoke_role_from_user(assignment, revoked_by, reason=''):
    """
    Revoke a role assignment from a user.

    Args:
        assignment: UserRoleAssignment object
        revoked_by: User performing the revocation
        reason: Optional reason for revocation

    Returns:
        bool: True if successful
    """
    user = assignment.user
    role = assignment.role
    project = assignment.project

    # Deactivate assignment
    assignment.is_active = False
    assignment.save()

    # Log action
    PermissionAuditLog.log_action(
        action_type='role_revoked',
        user=revoked_by,
        description=f"Revoked role '{role.display_name}' from {user.username}. Reason: {reason}",
        target_user=user,
        target_role=role,
        project=project,
        status='success'
    )

    return True


def create_custom_role(name, display_name, description, role_type, created_by,
                       parent_role=None, level=50):
    """
    Create a new custom role.

    Args:
        name: Unique role name
        display_name: Display name
        description: Role description
        role_type: Type (project, task, resource, global)
        created_by: User creating the role
        parent_role: Optional parent CustomRole
        level: Hierarchy level (0-100)

    Returns:
        CustomRole object
    """
    role = CustomRole.objects.create(
        name=name,
        display_name=display_name,
        description=description,
        role_type=role_type,
        parent_role=parent_role,
        level=level,
        created_by=created_by
    )

    # Log action
    PermissionAuditLog.log_action(
        action_type='role_created',
        user=created_by,
        description=f"Created custom role '{display_name}' ({name})",
        target_role=role,
        changes={
            'name': name,
            'display_name': display_name,
            'role_type': role_type,
            'level': level
        },
        status='success'
    )

    return role


def assign_permission_to_role(role, permission, assigned_by):
    """
    Assign a permission to a role.

    Args:
        role: CustomRole object
        permission: CustomPermission object
        assigned_by: User performing the assignment

    Returns:
        bool: True if successful
    """
    # Add permission to role
    role.permissions.add(permission)

    # Log action
    PermissionAuditLog.log_action(
        action_type='permission_granted',
        user=assigned_by,
        description=f"Granted permission '{permission.code}' to role '{role.display_name}'",
        target_role=role,
        target_permission=permission,
        status='success'
    )

    return True


def remove_permission_from_role(role, permission, removed_by):
    """
    Remove a permission from a role.

    Args:
        role: CustomRole object
        permission: CustomPermission object
        removed_by: User performing the removal

    Returns:
        bool: True if successful
    """
    # Remove permission from role
    role.permissions.remove(permission)

    # Log action
    PermissionAuditLog.log_action(
        action_type='permission_denied',
        user=removed_by,
        description=f"Removed permission '{permission.code}' from role '{role.display_name}'",
        target_role=role,
        target_permission=permission,
        status='success'
    )

    return True


# ============================================================================
# INITIALIZATION FUNCTIONS
# ============================================================================

def initialize_default_roles_and_permissions():
    """
    Initialize default roles and permissions for the system.
    Should be run once during setup or via management command.

    Returns:
        dict: Summary of created roles and permissions
    """
    from django.db import transaction

    summary = {
        'roles_created': 0,
        'permissions_created': 0
    }

    with transaction.atomic():
        # Create default permissions
        default_permissions = [
            # Project permissions
            ('project.view', 'View Project', 'project', 'view', 'low'),
            ('project.create', 'Create Project', 'project', 'create', 'medium'),
            ('project.edit', 'Edit Project', 'project', 'edit', 'medium'),
            ('project.delete', 'Delete Project', 'project', 'delete', 'high'),
            ('project.manage', 'Manage Project', 'project', 'manage', 'high'),
            ('project.export', 'Export Project', 'project', 'export', 'medium'),

            # Task permissions
            ('task.view', 'View Task', 'task', 'view', 'low'),
            ('task.create', 'Create Task', 'task', 'create', 'low'),
            ('task.edit', 'Edit Task', 'task', 'edit', 'medium'),
            ('task.delete', 'Delete Task', 'task', 'delete', 'medium'),
            ('task.assign', 'Assign Task', 'task', 'assign', 'medium'),
            ('task.comment', 'Comment on Task', 'task', 'comment', 'low'),

            # Resource permissions
            ('resource.view', 'View Resource', 'resource', 'view', 'low'),
            ('resource.create', 'Create Resource', 'resource', 'create', 'medium'),
            ('resource.edit', 'Edit Resource', 'resource', 'edit', 'medium'),
            ('resource.delete', 'Delete Resource', 'resource', 'delete', 'high'),

            # Report permissions
            ('report.view', 'View Reports', 'report', 'view', 'low'),
            ('report.create', 'Create Reports', 'report', 'create', 'medium'),
            ('report.export', 'Export Reports', 'report', 'export', 'medium'),

            # User management
            ('user.manage', 'Manage Users', 'user', 'manage', 'critical'),
            ('role.manage', 'Manage Roles', 'role', 'manage', 'critical'),
        ]

        for code, name, resource_type, action_type, risk_level in default_permissions:
            permission, created = CustomPermission.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'resource_type': resource_type,
                    'action_type': action_type,
                    'risk_level': risk_level,
                    'is_system_permission': True
                }
            )
            if created:
                summary['permissions_created'] += 1

        # Create default roles
        # Admin role
        admin_role, created = CustomRole.objects.get_or_create(
            name='admin',
            defaults={
                'display_name': 'Administrator',
                'description': 'Full system access with all permissions',
                'role_type': 'global',
                'level': 0,
                'is_system_role': True
            }
        )
        if created:
            summary['roles_created'] += 1
            # Grant all permissions to admin
            admin_role.permissions.set(CustomPermission.objects.filter(is_system_permission=True))

        # Project Manager role
        pm_role, created = CustomRole.objects.get_or_create(
            name='project_manager',
            defaults={
                'display_name': 'Project Manager',
                'description': 'Manage projects and teams',
                'role_type': 'project',
                'level': 10,
                'is_system_role': True
            }
        )
        if created:
            summary['roles_created'] += 1
            pm_permissions = CustomPermission.objects.filter(
                code__in=['project.view', 'project.edit', 'project.manage',
                          'task.view', 'task.create', 'task.edit', 'task.assign',
                          'resource.view', 'report.view', 'report.create']
            )
            pm_role.permissions.set(pm_permissions)

        # Developer role
        dev_role, created = CustomRole.objects.get_or_create(
            name='developer',
            defaults={
                'display_name': 'Developer',
                'description': 'Work on tasks and projects',
                'role_type': 'project',
                'level': 30,
                'is_system_role': True
            }
        )
        if created:
            summary['roles_created'] += 1
            dev_permissions = CustomPermission.objects.filter(
                code__in=['project.view', 'task.view', 'task.edit', 'task.comment',
                          'resource.view']
            )
            dev_role.permissions.set(dev_permissions)

        # Viewer role
        viewer_role, created = CustomRole.objects.get_or_create(
            name='viewer',
            defaults={
                'display_name': 'Viewer',
                'description': 'Read-only access',
                'role_type': 'project',
                'level': 50,
                'is_system_role': True
            }
        )
        if created:
            summary['roles_created'] += 1
            viewer_permissions = CustomPermission.objects.filter(
                code__in=['project.view', 'task.view', 'resource.view', 'report.view']
            )
            viewer_role.permissions.set(viewer_permissions)

    return summary


# Import models at the bottom to avoid circular imports
from django.db import models
