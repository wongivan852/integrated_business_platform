"""
Project CRUD views for Project Management app
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import HttpResponseForbidden

from ..models import Project, ProjectMember, Task, KanbanColumn


# ============================================================================
# Permission Helper Functions
# ============================================================================

def get_user_projects(user):
    """
    Get all projects the user has access to
    """
    if user.is_superuser:
        return Project.objects.all()

    # Get projects where user is a member
    return Project.objects.filter(
        Q(owner=user) | Q(team_members=user)
    ).distinct()


def check_project_access(user, project, required_role=None):
    """
    Check if user has access to a project with optional role requirement

    Args:
        user: User object
        project: Project object
        required_role: Optional role requirement ('owner', 'admin', 'member', 'viewer')

    Returns:
        tuple: (has_access: bool, user_role: str)
    """
    if user.is_superuser:
        return True, 'owner'

    if project.owner == user:
        return True, 'owner'

    try:
        membership = ProjectMember.objects.get(project=project, user=user)

        if required_role:
            role_hierarchy = {'owner': 4, 'admin': 3, 'member': 2, 'viewer': 1}
            user_level = role_hierarchy.get(membership.role, 0)
            required_level = role_hierarchy.get(required_role, 0)

            if user_level >= required_level:
                return True, membership.role
            else:
                return False, membership.role

        return True, membership.role
    except ProjectMember.DoesNotExist:
        return False, None


# ============================================================================
# Project List View
# ============================================================================

@login_required
def project_list(request):
    """
    Display all projects the user has access to
    """
    projects = get_user_projects(request.user)

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        projects = projects.filter(status=status_filter)

    # Filter by priority if requested
    priority_filter = request.GET.get('priority')
    if priority_filter:
        projects = projects.filter(priority=priority_filter)

    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(project_code__icontains=search_query)
        )

    # Annotate with statistics
    projects = projects.annotate(
        task_count=Count('tasks'),
        completed_tasks=Count('tasks', filter=Q(tasks__status='done')),
        member_count=Count('team_members', distinct=True)
    ).select_related('owner').order_by('-created_at')

    # Get statistics for dashboard
    total_projects = projects.count()
    active_projects = projects.filter(status='active').count()
    completed_projects = projects.filter(status='completed').count()

    context = {
        'projects': projects,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'status_choices': Project.STATUS_CHOICES,
        'priority_choices': Project.PRIORITY_CHOICES,
    }

    return render(request, 'project_management/project_list.html', context)


# ============================================================================
# Project Detail View
# ============================================================================

@login_required
def project_detail(request, pk):
    """
    Display detailed view of a single project
    """
    project = get_object_or_404(Project, pk=pk)

    # Check access
    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have permission to view this project."))
        return redirect('project_management:project_list')

    # Get project statistics
    tasks = project.tasks.all()
    task_stats = tasks.aggregate(
        total_tasks=Count('id'),
        completed_tasks=Count('id', filter=Q(status='done')),
        in_progress_tasks=Count('id', filter=Q(status='in_progress')),
        todo_tasks=Count('id', filter=Q(status='todo')),
        overdue_tasks=Count('id', filter=Q(due_date__lt=timezone.now().date(), status__in=['todo', 'in_progress'])),
        total_estimated_hours=Sum('estimated_hours'),
        total_actual_hours=Sum('actual_hours'),
    )

    # Get team members
    team_members = ProjectMember.objects.filter(project=project).select_related('user')

    # Get recent activities (last 10)
    from ..models import TaskActivity
    recent_activities = TaskActivity.objects.filter(
        task__project=project
    ).select_related('user', 'task').order_by('-timestamp')[:10]

    # Get milestones
    milestones = tasks.filter(is_milestone=True).order_by('due_date')

    # Calculate task completion rate
    completion_rate = 0
    if task_stats['total_tasks'] > 0:
        completion_rate = (task_stats['completed_tasks'] / task_stats['total_tasks']) * 100

    context = {
        'project': project,
        'user_role': user_role,
        'task_stats': task_stats,
        'completion_rate': completion_rate,
        'team_members': team_members,
        'recent_activities': recent_activities,
        'milestones': milestones,
        'can_edit': user_role in ['owner', 'admin'],
        'can_delete': user_role == 'owner',
    }

    return render(request, 'project_management/project_detail.html', context)


# ============================================================================
# Project Create View
# ============================================================================

@login_required
def project_create(request):
    """
    Create a new project
    """
    from ..forms import ProjectForm

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.created_by = request.user
            project.save()

            # Create default Kanban columns
            default_columns = [
                {'name': 'To Do', 'position': 1, 'color': '#6c757d'},
                {'name': 'In Progress', 'position': 2, 'color': '#0dcaf0'},
                {'name': 'Review', 'position': 3, 'color': '#ffc107'},
                {'name': 'Done', 'position': 4, 'color': '#198754'},
            ]

            for col_data in default_columns:
                KanbanColumn.objects.create(
                    project=project,
                    **col_data
                )

            messages.success(request, _('Project "{}" created successfully!').format(project.name))
            return redirect('project_management:project_detail', pk=project.pk)
    else:
        form = ProjectForm()

    context = {
        'form': form,
        'action': 'Create',
    }

    return render(request, 'project_management/project_form.html', context)


# ============================================================================
# Project Edit View
# ============================================================================

@login_required
def project_edit(request, pk):
    """
    Edit an existing project
    """
    from ..forms import ProjectForm

    project = get_object_or_404(Project, pk=pk)

    # Check access - requires admin or owner role
    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        messages.error(request, _("You don't have permission to edit this project."))
        return redirect('project_management:project_detail', pk=project.pk)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, _('Project "{}" updated successfully!').format(project.name))
            return redirect('project_management:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    context = {
        'form': form,
        'project': project,
        'action': 'Edit',
    }

    return render(request, 'project_management/project_form.html', context)


# ============================================================================
# Project Delete View
# ============================================================================

@login_required
def project_delete(request, pk):
    """
    Delete a project (only owner can delete)
    """
    project = get_object_or_404(Project, pk=pk)

    # Check access - only owner can delete
    has_access, user_role = check_project_access(request.user, project, required_role='owner')
    if not has_access:
        messages.error(request, _("Only the project owner can delete this project."))
        return redirect('project_management:project_detail', pk=project.pk)

    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, _('Project "{}" deleted successfully.').format(project_name))
        return redirect('project_management:project_list')

    context = {
        'project': project,
    }

    return render(request, 'project_management/project_confirm_delete.html', context)


# ============================================================================
# Gantt Chart View (Stub for Phase 3)
# ============================================================================

@login_required
def project_gantt_view(request, pk):
    """
    Display project in Gantt chart view
    TO BE IMPLEMENTED IN PHASE 3
    """
    project = get_object_or_404(Project, pk=pk)

    # Check access
    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have permission to view this project."))
        return redirect('project_management:project_list')

    # Update project's default view preference
    project.default_view = 'gantt'
    project.save(update_fields=['default_view'])

    # Get all tasks with dependencies
    tasks = project.tasks.select_related('parent_task').prefetch_related(
        'assigned_to',
        'predecessors',
        'successors'
    ).order_by('order', 'start_date')

    context = {
        'project': project,
        'tasks': tasks,
        'user_role': user_role,
        'view_mode': 'gantt',
        'can_edit': user_role in ['owner', 'admin', 'member'],
    }

    # TODO: Phase 3 - Implement Gantt chart rendering
    messages.info(request, _('Gantt Chart view will be implemented in Phase 3'))

    return render(request, 'project_management/project_gantt.html', context)


# ============================================================================
# Kanban Board View (Stub for Phase 2)
# ============================================================================

@login_required
def project_kanban_view(request, pk):
    """
    Display project in Kanban board view
    TO BE IMPLEMENTED IN PHASE 2
    """
    project = get_object_or_404(Project, pk=pk)

    # Check access
    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have permission to view this project."))
        return redirect('project_management:project_list')

    # Update project's default view preference
    project.default_view = 'kanban'
    project.save(update_fields=['default_view'])

    # Get Kanban columns with tasks
    columns = project.kanban_columns.prefetch_related(
        'tasks__assigned_to'
    ).order_by('position')

    # Get unassigned tasks (not in any column)
    unassigned_tasks = project.tasks.filter(kanban_column__isnull=True).select_related()

    # Get all labels for the project
    from ..models import TaskLabel
    labels = TaskLabel.objects.filter(project=project).order_by('name')

    context = {
        'project': project,
        'columns': columns,
        'unassigned_tasks': unassigned_tasks,
        'labels': labels,
        'user_role': user_role,
        'view_mode': 'kanban',
        'can_edit': user_role in ['owner', 'admin', 'member'],
        'can_manage_columns': user_role in ['owner', 'admin'],
    }

    return render(request, 'project_management/project_kanban.html', context)


# ============================================================================
# Team Member Management Views
# ============================================================================

@login_required
def project_add_member(request, pk):
    """
    Add a team member to a project
    """
    project = get_object_or_404(Project, pk=pk)

    # Check access - requires owner or admin
    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        messages.error(request, _("You don't have permission to add members to this project."))
        return redirect('project_management:project_detail', pk=project.pk)

    if request.method == 'POST':
        from ..forms import ProjectMemberForm
        form = ProjectMemberForm(request.POST, project=project)
        if form.is_valid():
            member = form.save(commit=False)
            member.project = project
            member.save()
            messages.success(request, _('Team member "{}" added successfully!').format(
                member.user.get_full_name() or member.user.email
            ))
            return redirect('project_management:project_detail', pk=project.pk)
    else:
        from ..forms import ProjectMemberForm
        form = ProjectMemberForm(project=project)

    context = {
        'form': form,
        'project': project,
    }

    return render(request, 'project_management/project_add_member.html', context)


@login_required
def project_remove_member(request, pk, member_id):
    """
    Remove a team member from a project
    """
    project = get_object_or_404(Project, pk=pk)
    member = get_object_or_404(ProjectMember, pk=member_id, project=project)

    # Check access - requires owner or admin
    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        messages.error(request, _("You don't have permission to remove members from this project."))
        return redirect('project_management:project_detail', pk=project.pk)

    # Prevent removing the project owner
    if member.user == project.owner:
        messages.error(request, _("Cannot remove the project owner."))
        return redirect('project_management:project_detail', pk=project.pk)

    if request.method == 'POST':
        member_name = member.user.get_full_name() or member.user.email
        member.delete()
        messages.success(request, _('Team member "{}" removed from project.').format(member_name))
        return redirect('project_management:project_detail', pk=project.pk)

    context = {
        'project': project,
        'member': member,
    }

    return render(request, 'project_management/project_remove_member.html', context)


@login_required
def project_file_pool(request, project_pk):
    """
    Display all files uploaded to a project
    """
    from ..models import TaskAttachment
    
    project = get_object_or_404(Project, pk=project_pk)
    
    # Check access
    has_access, user_role = check_project_access(request.user, project, required_role='viewer')
    if not has_access:
        messages.error(request, _('You do not have permission to view this project.'))
        return redirect('project_management:project_list')
    
    # Get all attachments for this project's tasks
    attachments = TaskAttachment.objects.filter(
        task__project=project
    ).select_related('task', 'uploaded_by').order_by('-uploaded_at')
    
    # Add file existence check to each attachment
    for attachment in attachments:
        attachment.exists = attachment.file_exists()
    
    # Filter options
    show_missing_only = request.GET.get('missing') == 'true'
    search_query = request.GET.get('search', '')
    
    if show_missing_only:
        attachments = [a for a in attachments if not a.exists]
    
    if search_query:
        attachments = [a for a in attachments if search_query.lower() in a.filename.lower()]
    
    # Count missing files
    missing_count = sum(1 for a in TaskAttachment.objects.filter(task__project=project) if not a.file_exists())
    
    context = {
        'project': project,
        'attachments': attachments,
        'user_role': user_role,
        'missing_count': missing_count,
        'show_missing_only': show_missing_only,
        'search_query': search_query,
    }
    
    return render(request, 'project_management/project_file_pool.html', context)
