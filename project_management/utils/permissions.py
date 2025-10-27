"""
Permission checking utilities for project management
"""
from django.shortcuts import get_object_or_404
from ..models import Project, ProjectMember


def check_project_access(user, project):
    """
    Check if user has access to a project and return their role

    Args:
        user: Django User object
        project: Project instance

    Returns:
        tuple: (has_access: bool, role: str or None)
    """
    if not user.is_authenticated:
        return False, None

    # Superusers have full access
    if user.is_superuser:
        return True, 'owner'

    # Check project membership
    try:
        membership = ProjectMember.objects.get(project=project, user=user)
        return True, membership.role
    except ProjectMember.DoesNotExist:
        return False, None


def user_can_edit_project(user, project):
    """
    Check if user can edit project (owner or manager)

    Args:
        user: Django User object
        project: Project instance

    Returns:
        bool: True if user can edit
    """
    has_access, role = check_project_access(user, project)
    return has_access and role in ['owner', 'manager']


def user_can_delete_project(user, project):
    """
    Check if user can delete project (owner only)

    Args:
        user: Django User object
        project: Project instance

    Returns:
        bool: True if user can delete
    """
    has_access, role = check_project_access(user, project)
    return has_access and role == 'owner'


def user_can_manage_members(user, project):
    """
    Check if user can manage project members (owner or manager)

    Args:
        user: Django User object
        project: Project instance

    Returns:
        bool: True if user can manage members
    """
    has_access, role = check_project_access(user, project)
    return has_access and role in ['owner', 'manager']


def user_can_create_task(user, project):
    """
    Check if user can create tasks (owner, manager, or member)

    Args:
        user: Django User object
        project: Project instance

    Returns:
        bool: True if user can create tasks
    """
    has_access, role = check_project_access(user, project)
    return has_access and role in ['owner', 'manager', 'member']


def user_can_edit_task(user, task):
    """
    Check if user can edit a task (owner, manager, or assigned member)

    Args:
        user: Django User object
        task: Task instance

    Returns:
        bool: True if user can edit task
    """
    has_access, role = check_project_access(user, task.project)

    # Owner and managers can always edit
    if has_access and role in ['owner', 'manager']:
        return True

    # Members can edit if assigned or if they created it
    if has_access and role == 'member':
        if task.created_by == user or user in task.assigned_to.all():
            return True

    return False


def user_can_delete_task(user, task):
    """
    Check if user can delete a task (owner, manager, or task creator)

    Args:
        user: Django User object
        task: Task instance

    Returns:
        bool: True if user can delete task
    """
    has_access, role = check_project_access(user, task.project)

    # Owner and managers can always delete
    if has_access and role in ['owner', 'manager']:
        return True

    # Task creator can delete their own task
    if has_access and role == 'member' and task.created_by == user:
        return True

    return False


def get_user_projects(user, role=None):
    """
    Get all projects accessible to a user

    Args:
        user: Django User object
        role: Optional role filter ('owner', 'manager', 'member')

    Returns:
        QuerySet: Projects the user can access
    """
    if not user.is_authenticated:
        return Project.objects.none()

    # Superusers see all projects
    if user.is_superuser:
        return Project.objects.all()

    # Filter by membership
    memberships = ProjectMember.objects.filter(user=user)

    if role:
        memberships = memberships.filter(role=role)

    project_ids = memberships.values_list('project_id', flat=True)
    return Project.objects.filter(id__in=project_ids)
