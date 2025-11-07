"""
Export views for generating downloadable reports
Supports PDF, Excel, and CSV formats
"""

from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Avg, Q

from ..models import Project, Task, Resource, ProjectMetrics
from ..utils.export_utils import (
    generate_csv_response,
    export_project_list_excel,
    export_project_analytics_pdf,
    export_tasks_excel,
    export_resource_allocation_excel,
    export_portfolio_analytics_excel
)


@login_required
def export_projects_csv(request):
    """
    Export project list as CSV

    URL: /project-management/export/projects/csv/
    Query Params:
        - status: Filter by status (optional)
        - priority: Filter by priority (optional)
    """
    # Get user's accessible projects
    if request.user.is_superuser:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(
            Q(owner=request.user) | Q(projectmember__user=request.user)
        ).distinct()

    # Apply filters
    status = request.GET.get('status')
    priority = request.GET.get('priority')

    if status:
        projects = projects.filter(status=status)
    if priority:
        projects = projects.filter(priority=priority)

    # Prepare data
    data = []
    for project in projects:
        data.append({
            'Project Code': project.project_code,
            'Name': project.name,
            'Status': project.get_status_display(),
            'Priority': project.get_priority_display(),
            'Owner': project.owner.get_full_name() or project.owner.email,
            'Start Date': project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
            'End Date': project.end_date.strftime('%Y-%m-%d') if project.end_date else '',
            'Progress %': project.progress_percentage,
            'Budget': float(project.budget) if project.budget else 0,
            'Actual Cost': float(project.actual_cost),
            'Team Size': project.team_members.count(),
            'Tasks Total': project.tasks.count(),
            'Tasks Completed': project.tasks.filter(status='completed').count()
        })

    return generate_csv_response(data, f'projects_{datetime.now().strftime("%Y%m%d")}')


@login_required
def export_projects_excel(request):
    """
    Export project list as Excel

    URL: /project-management/export/projects/excel/
    Query Params:
        - status: Filter by status (optional)
        - priority: Filter by priority (optional)
    """
    # Get user's accessible projects
    if request.user.is_superuser:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(
            Q(owner=request.user) | Q(projectmember__user=request.user)
        ).distinct()

    # Apply filters
    status = request.GET.get('status')
    priority = request.GET.get('priority')

    if status:
        projects = projects.filter(status=status)
    if priority:
        projects = projects.filter(priority=priority)

    return export_project_list_excel(projects)


@login_required
def export_project_analytics_pdf_view(request, pk):
    """
    Export project analytics as PDF report

    URL: /project-management/<pk>/export/analytics/pdf/
    """
    project = get_object_or_404(Project, pk=pk)

    # Check permissions
    if not (request.user.is_superuser or project.owner == request.user or
            project.team_members.filter(id=request.user.id).exists()):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You don't have permission to export this project's analytics.")

    # Gather metrics
    tasks = project.tasks.all()
    completed_tasks = tasks.filter(status='completed').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    overdue_tasks = tasks.filter(due_date__lt=datetime.now().date(), status__in=['todo', 'in_progress']).count()

    metrics = {
        'total_tasks': tasks.count(),
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': (completed_tasks / tasks.count() * 100) if tasks.count() > 0 else 0,
        'budget': float(project.budget) if project.budget else 0,
        'actual_cost': float(project.actual_cost),
        'cost_variance': float(project.budget or 0) - float(project.actual_cost),
        'health_score': 85  # Calculate actual health score based on your logic
    }

    return export_project_analytics_pdf(project, metrics)


@login_required
def export_tasks_csv(request, project_pk):
    """
    Export tasks for a project as CSV

    URL: /project-management/<project_pk>/export/tasks/csv/
    """
    project = get_object_or_404(Project, pk=project_pk)

    # Check permissions
    if not (request.user.is_superuser or project.owner == request.user or
            project.team_members.filter(id=request.user.id).exists()):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You don't have permission to export this project's tasks.")

    tasks = project.tasks.all()

    # Prepare data
    data = []
    for task in tasks:
        assigned_to = ', '.join([u.get_full_name() or u.email for u in task.assigned_to.all()])
        data.append({
            'Task Code': task.task_code,
            'Title': task.title,
            'Status': task.get_status_display(),
            'Priority': task.get_priority_display(),
            'Progress %': task.progress,
            'Start Date': task.start_date.strftime('%Y-%m-%d') if task.start_date else '',
            'End Date': task.end_date.strftime('%Y-%m-%d') if task.end_date else '',
            'Due Date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            'Assigned To': assigned_to,
            'Estimated Hours': float(task.estimated_hours) if task.estimated_hours else 0,
            'Actual Hours': float(task.actual_hours) if task.actual_hours else 0,
            'Is Milestone': 'Yes' if task.is_milestone else 'No'
        })

    return generate_csv_response(
        data,
        f'tasks_{project.name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}'
    )


@login_required
def export_tasks_excel_view(request, project_pk):
    """
    Export tasks for a project as Excel

    URL: /project-management/<project_pk>/export/tasks/excel/
    """
    project = get_object_or_404(Project, pk=project_pk)

    # Check permissions
    if not (request.user.is_superuser or project.owner == request.user or
            project.team_members.filter(id=request.user.id).exists()):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You don't have permission to export this project's tasks.")

    tasks = project.tasks.all()

    return export_tasks_excel(tasks, project.name)


@login_required
def export_resource_allocation_view(request):
    """
    Export resource allocation report as Excel

    URL: /project-management/export/resources/allocation/
    Query Params:
        - start_date: Start date (YYYY-MM-DD, default: 30 days ago)
        - end_date: End date (YYYY-MM-DD, default: today)
    """
    # Only admins can export resource allocation
    if not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Only administrators can export resource allocation reports.")

    # Parse dates
    try:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = (datetime.now() - timedelta(days=30)).date()

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = datetime.now().date()
    except ValueError:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("Invalid date format. Use YYYY-MM-DD.")

    # Get resources with their assignments
    resources = Resource.objects.filter(is_active=True).prefetch_related(
        'resourceassignment_set__task__project'
    )

    return export_resource_allocation_excel(resources, start_date, end_date)


@login_required
def export_portfolio_analytics_view(request):
    """
    Export portfolio analytics as Excel

    URL: /project-management/export/portfolio/analytics/
    Query Params:
        - status: Filter by status (optional, comma-separated)
    """
    # Get user's accessible projects
    if request.user.is_superuser:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(
            Q(owner=request.user) | Q(projectmember__user=request.user)
        ).distinct()

    # Apply status filter
    status_filter = request.GET.get('status')
    if status_filter:
        statuses = status_filter.split(',')
        projects = projects.filter(status__in=statuses)

    # Gather project data
    projects_data = []
    for project in projects:
        tasks = project.tasks.all()
        completed_tasks = tasks.filter(status='completed').count()
        overdue_tasks = tasks.filter(
            due_date__lt=datetime.now().date(),
            status__in=['todo', 'in_progress']
        ).count()

        # Calculate health score (simplified)
        health_score = 100
        if project.is_overdue:
            health_score -= 30
        if overdue_tasks > 0:
            health_score -= min(overdue_tasks * 5, 30)
        if project.budget_percentage_used > 100:
            health_score -= 20
        health_score = max(health_score, 0)

        projects_data.append({
            'project_code': project.project_code,
            'name': project.name,
            'status': project.get_status_display(),
            'health_score': health_score,
            'progress': project.progress_percentage,
            'budget': float(project.budget) if project.budget else 0,
            'actual_cost': float(project.actual_cost),
            'tasks_total': tasks.count(),
            'tasks_completed': completed_tasks,
            'tasks_overdue': overdue_tasks
        })

    return export_portfolio_analytics_excel(projects_data)
