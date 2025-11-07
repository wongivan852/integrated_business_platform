"""
Phase 4: Resource Management Views
Handles resource listing, capacity tracking, workload visualization, and resource allocation
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from datetime import datetime, timedelta
import json

from ..models import (
    Resource, ResourceAssignment, Skill,
    Project, Task, ProjectMember
)
from ..utils.permissions import check_project_access


# ============================================================================
# RESOURCE LIST & DIRECTORY
# ============================================================================

@login_required
def resource_list(request):
    """
    Display list of all resources with capacity overview

    Features:
    - Filter by department, skills, availability
    - Search by name, job title
    - Sort by utilization, hourly rate
    - Capacity indicators (available, busy, over-allocated)
    """
    # Base queryset
    resources = Resource.objects.filter(is_active=True).select_related('user')

    # Apply filters
    department = request.GET.get('department')
    if department:
        resources = resources.filter(department=department)

    skill_id = request.GET.get('skill')
    if skill_id:
        resources = resources.filter(skills__id=skill_id)

    availability = request.GET.get('availability')
    if availability == 'available':
        # Resources with <70% utilization
        resources = [r for r in resources if r.get_current_utilization() < 70]
    elif availability == 'busy':
        # Resources with 70-100% utilization
        resources = [r for r in resources if 70 <= r.get_current_utilization() <= 100]
    elif availability == 'overallocated':
        # Resources with >100% utilization
        resources = [r for r in resources if r.get_current_utilization() > 100]

    # Search
    search_query = request.GET.get('search')
    if search_query:
        resources = resources.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(job_title__icontains=search_query) |
            Q(department__icontains=search_query)
        )

    # Get all departments and skills for filters
    departments = Resource.objects.filter(is_active=True).values_list('department', flat=True).distinct()
    skills = Skill.objects.all()

    # Calculate utilization for each resource (current week)
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    resource_data = []
    for resource in resources:
        utilization = resource.get_utilization(week_start, week_end)
        resource_data.append({
            'resource': resource,
            'utilization': utilization,
            'workload': resource.get_workload(week_start, week_end)
        })

    # Sort
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'utilization':
        resource_data.sort(key=lambda x: x['utilization'], reverse=True)
    elif sort_by == 'rate':
        resource_data.sort(key=lambda x: x['resource'].hourly_rate, reverse=True)
    elif sort_by == 'department':
        resource_data.sort(key=lambda x: x['resource'].department)
    else:
        resource_data.sort(key=lambda x: x['resource'].user.get_full_name() or x['resource'].user.email)

    context = {
        'resource_data': resource_data,
        'departments': departments,
        'skills': skills,
        'filters': {
            'department': department,
            'skill': skill_id,
            'availability': availability,
            'search': search_query,
            'sort': sort_by
        }
    }

    return render(request, 'project_management/resource_list.html', context)


@login_required
def resource_detail(request, resource_id):
    """
    Display detailed resource profile with assignment history

    Shows:
    - Personal information (job title, department, skills)
    - Capacity settings (hours/day, availability %)
    - Current assignments
    - Utilization chart (past 12 weeks)
    - Assignment history
    """
    resource = get_object_or_404(Resource, pk=resource_id)

    # Get current assignments
    current_assignments = ResourceAssignment.objects.filter(
        resource=resource,
        end_date__gte=timezone.now().date()
    ).select_related('task', 'task__project').order_by('start_date')

    # Get past assignments (last 6 months)
    six_months_ago = timezone.now().date() - timedelta(days=180)
    past_assignments = ResourceAssignment.objects.filter(
        resource=resource,
        end_date__lt=timezone.now().date(),
        end_date__gte=six_months_ago
    ).select_related('task', 'task__project').order_by('-end_date')[:20]

    # Calculate utilization for last 12 weeks
    today = timezone.now().date()
    utilization_data = []
    for i in range(12):
        week_start = today - timedelta(weeks=i+1)
        week_end = week_start + timedelta(days=6)
        utilization = resource.get_utilization(week_start, week_end)
        utilization_data.insert(0, {
            'week': week_start.strftime('%b %d'),
            'utilization': round(utilization, 1)
        })

    # Current week utilization
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    current_utilization = resource.get_utilization(week_start, week_end)

    # Next 4 weeks forecast
    forecast_data = []
    for i in range(4):
        week_start = today + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        workload = resource.get_workload(week_start, week_end)
        available = resource.available_hours_per_day * 5  # 5 working days
        utilization = (workload / available * 100) if available > 0 else 0
        forecast_data.append({
            'week': week_start.strftime('%b %d'),
            'utilization': round(utilization, 1),
            'hours': round(workload, 1)
        })

    context = {
        'resource': resource,
        'current_assignments': current_assignments,
        'past_assignments': past_assignments,
        'utilization_data': json.dumps(utilization_data),
        'current_utilization': current_utilization,
        'forecast_data': forecast_data
    }

    return render(request, 'project_management/resource_detail.html', context)


# ============================================================================
# WORKLOAD & CAPACITY VIEWS
# ============================================================================

@login_required
def resource_workload(request):
    """
    Workload calendar view showing resource allocation over time

    Features:
    - Calendar timeline (day/week/month view)
    - Color-coded capacity indicators
    - Over-allocation warnings
    - Drag-and-drop to reschedule
    """
    # Get date range from request
    view_mode = request.GET.get('view', 'week')  # day, week, month
    date_str = request.GET.get('date')

    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    # Calculate date range based on view mode
    if view_mode == 'day':
        start_date = current_date
        end_date = current_date
        num_days = 1
    elif view_mode == 'month':
        start_date = current_date.replace(day=1)
        # Get last day of month
        if current_date.month == 12:
            end_date = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
        num_days = (end_date - start_date).days + 1
    else:  # week
        start_date = current_date - timedelta(days=current_date.weekday())
        end_date = start_date + timedelta(days=6)
        num_days = 7

    # Get all active resources
    resources = Resource.objects.filter(is_active=True).select_related('user').order_by('department', 'user__first_name')

    # Build workload data for each resource and each day
    workload_data = []
    for resource in resources:
        daily_workload = []
        for day_offset in range(num_days):
            day = start_date + timedelta(days=day_offset)

            # Get assignments for this day
            assignments = ResourceAssignment.objects.filter(
                resource=resource,
                start_date__lte=day,
                end_date__gte=day
            ).select_related('task', 'task__project')

            # Calculate hours for this day
            total_hours = sum([
                (a.assigned_hours / ((a.end_date - a.start_date).days + 1))
                for a in assignments
            ])

            # Calculate capacity for this day
            available_hours = resource.available_hours_per_day
            utilization = (total_hours / available_hours * 100) if available_hours > 0 else 0

            # Determine status
            if utilization <= 70:
                status = 'available'
            elif utilization <= 100:
                status = 'busy'
            else:
                status = 'overallocated'

            daily_workload.append({
                'date': day,
                'hours': round(total_hours, 1),
                'available': round(available_hours, 1),
                'utilization': round(utilization, 1),
                'status': status,
                'assignments': list(assignments)
            })

        workload_data.append({
            'resource': resource,
            'daily_workload': daily_workload
        })

    # Navigation dates
    if view_mode == 'day':
        prev_date = current_date - timedelta(days=1)
        next_date = current_date + timedelta(days=1)
    elif view_mode == 'month':
        if current_date.month == 1:
            prev_date = current_date.replace(year=current_date.year - 1, month=12, day=1)
        else:
            prev_date = current_date.replace(month=current_date.month - 1, day=1)

        if current_date.month == 12:
            next_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_date = current_date.replace(month=current_date.month + 1, day=1)
    else:  # week
        prev_date = start_date - timedelta(days=7)
        next_date = start_date + timedelta(days=7)

    context = {
        'workload_data': workload_data,
        'start_date': start_date,
        'end_date': end_date,
        'current_date': current_date,
        'view_mode': view_mode,
        'prev_date': prev_date.strftime('%Y-%m-%d'),
        'next_date': next_date.strftime('%Y-%m-%d'),
        'num_days': num_days
    }

    return render(request, 'project_management/resource_workload.html', context)


@login_required
def resource_capacity_report(request):
    """
    Team capacity utilization report

    Shows:
    - Overall team utilization percentage
    - Department breakdown
    - Available capacity hours
    - Over-allocated resources
    - Skill availability
    """
    # Date range
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            # Default to current week
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
    else:
        # Default to current week
        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

    # Get all active resources
    resources = Resource.objects.filter(is_active=True).select_related('user')

    # Calculate overall statistics
    total_available_hours = 0
    total_allocated_hours = 0
    overallocated_resources = []
    available_resources = []

    department_stats = {}

    for resource in resources:
        available_hours = resource.available_hours_per_day * ((end_date - start_date).days + 1)
        allocated_hours = resource.get_workload(start_date, end_date)
        utilization = resource.get_utilization(start_date, end_date)

        total_available_hours += available_hours
        total_allocated_hours += allocated_hours

        if utilization > 100:
            overallocated_resources.append({
                'resource': resource,
                'utilization': utilization,
                'allocated_hours': allocated_hours,
                'available_hours': available_hours,
                'overage': allocated_hours - available_hours
            })
        elif utilization < 70:
            available_resources.append({
                'resource': resource,
                'utilization': utilization,
                'available_capacity': available_hours - allocated_hours
            })

        # Department statistics
        if resource.department not in department_stats:
            department_stats[resource.department] = {
                'available': 0,
                'allocated': 0,
                'count': 0
            }
        department_stats[resource.department]['available'] += available_hours
        department_stats[resource.department]['allocated'] += allocated_hours
        department_stats[resource.department]['count'] += 1

    # Calculate department utilization
    for dept in department_stats:
        dept_data = department_stats[dept]
        dept_data['utilization'] = (dept_data['allocated'] / dept_data['available'] * 100) if dept_data['available'] > 0 else 0

    # Overall utilization
    overall_utilization = (total_allocated_hours / total_available_hours * 100) if total_available_hours > 0 else 0

    # Skill availability
    skills = Skill.objects.all()
    skill_stats = []
    for skill in skills:
        skill_resources = resources.filter(skills=skill)
        if skill_resources.exists():
            available_count = sum(1 for r in skill_resources if r.get_utilization(start_date, end_date) < 70)
            skill_stats.append({
                'skill': skill,
                'total_resources': skill_resources.count(),
                'available_resources': available_count
            })

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_available_hours': round(total_available_hours, 1),
        'total_allocated_hours': round(total_allocated_hours, 1),
        'overall_utilization': round(overall_utilization, 1),
        'overallocated_resources': overallocated_resources,
        'available_resources': available_resources,
        'department_stats': department_stats,
        'skill_stats': skill_stats,
        'total_resources': resources.count()
    }

    return render(request, 'project_management/resource_capacity_report.html', context)


# ============================================================================
# RESOURCE ALLOCATION
# ============================================================================

@login_required
def project_resource_allocation(request, pk):
    """
    Assign resources to project tasks

    Features:
    - View project tasks
    - See available resources
    - Drag-and-drop resource assignment
    - Set allocation percentage and hours
    - Check for conflicts/over-allocation
    """
    project = get_object_or_404(Project, pk=pk)
    has_access, user_role = check_project_access(request.user, project)

    if not has_access:
        messages.error(request, "You don't have permission to access this project.")
        return redirect('project_management:project_list')

    # Can only allocate if owner or manager
    if user_role not in ['owner', 'manager']:
        messages.error(request, "Only project owners and managers can allocate resources.")
        return redirect('project_management:project_detail', pk=project.pk)

    # Get project tasks
    tasks = Task.objects.filter(project=project).select_related('parent_task').prefetch_related('assigned_to')

    # Get all active resources
    all_resources = Resource.objects.filter(is_active=True).select_related('user').prefetch_related('skills')

    # Calculate current utilization for each resource
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    resource_availability = []
    for resource in all_resources:
        utilization = resource.get_utilization(week_start, week_end)
        available_capacity = max(0, 100 - utilization)

        resource_availability.append({
            'resource': resource,
            'utilization': round(utilization, 1),
            'available_capacity': round(available_capacity, 1),
            'status': 'available' if utilization < 70 else ('busy' if utilization <= 100 else 'overallocated')
        })

    # Sort by availability
    resource_availability.sort(key=lambda x: x['available_capacity'], reverse=True)

    # Get existing assignments for this project
    project_assignments = ResourceAssignment.objects.filter(
        task__project=project
    ).select_related('resource', 'resource__user', 'task')

    context = {
        'project': project,
        'tasks': tasks,
        'resource_availability': resource_availability,
        'project_assignments': project_assignments,
        'user_role': user_role
    }

    return render(request, 'project_management/project_resource_allocation.html', context)


# ============================================================================
# API ENDPOINTS FOR RESOURCE OPERATIONS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_assign_resource(request, project_pk, task_id):
    """
    API endpoint to assign a resource to a task
    """
    try:
        project = get_object_or_404(Project, pk=project_pk)
        has_access, user_role = check_project_access(request.user, project)

        if not has_access or user_role not in ['owner', 'manager']:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)

        task = get_object_or_404(Task, pk=task_id, project=project)
        data = json.loads(request.body)

        resource_id = data.get('resource_id')
        allocation_percentage = int(data.get('allocation_percentage', 100))
        assigned_hours = float(data.get('assigned_hours', 0))
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        # Validate
        if not resource_id or not start_date_str or not end_date_str:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)

        resource = get_object_or_404(Resource, pk=resource_id)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Check for conflicts
        conflicts = ResourceAssignment.objects.filter(
            resource=resource,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exclude(task=task)

        if conflicts.exists():
            return JsonResponse({
                'success': False,
                'error': f'Resource has {conflicts.count()} conflicting assignment(s) in this date range',
                'warning': True
            })

        # Create or update assignment
        assignment, created = ResourceAssignment.objects.update_or_create(
            task=task,
            resource=resource,
            defaults={
                'allocation_percentage': allocation_percentage,
                'assigned_hours': assigned_hours,
                'start_date': start_date,
                'end_date': end_date
            }
        )

        # Also add to task assigned_to
        if resource.user not in task.assigned_to.all():
            task.assigned_to.add(resource.user)

        return JsonResponse({
            'success': True,
            'created': created,
            'assignment_id': assignment.id,
            'message': f'Resource assigned successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_remove_resource_assignment(request, project_pk, assignment_id):
    """
    API endpoint to remove a resource assignment
    """
    try:
        project = get_object_or_404(Project, pk=project_pk)
        has_access, user_role = check_project_access(request.user, project)

        if not has_access or user_role not in ['owner', 'manager']:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)

        assignment = get_object_or_404(ResourceAssignment, pk=assignment_id, task__project=project)

        # Remove from task assigned_to if no other assignments
        other_assignments = ResourceAssignment.objects.filter(
            task=assignment.task,
            resource__user=assignment.resource.user
        ).exclude(pk=assignment.pk).exists()

        if not other_assignments:
            assignment.task.assigned_to.remove(assignment.resource.user)

        assignment.delete()

        return JsonResponse({
            'success': True,
            'message': 'Resource assignment removed'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_resource_availability(request):
    """
    API endpoint to check resource availability for a date range
    """
    try:
        resource_id = request.GET.get('resource_id')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if not all([resource_id, start_date_str, end_date_str]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            }, status=400)

        resource = get_object_or_404(Resource, pk=resource_id)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Calculate utilization
        utilization = resource.get_utilization(start_date, end_date)
        workload = resource.get_workload(start_date, end_date)
        available_hours = resource.available_hours_per_day * ((end_date - start_date).days + 1)

        # Get conflicting assignments
        assignments = ResourceAssignment.objects.filter(
            resource=resource,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).select_related('task', 'task__project')

        conflicts = [{
            'task_code': a.task.task_code,
            'task_title': a.task.title,
            'project_name': a.task.project.name,
            'start_date': a.start_date.strftime('%Y-%m-%d'),
            'end_date': a.end_date.strftime('%Y-%m-%d'),
            'assigned_hours': float(a.assigned_hours),
            'allocation_percentage': a.allocation_percentage
        } for a in assignments]

        return JsonResponse({
            'success': True,
            'resource_name': resource.user.get_full_name() or resource.user.email,
            'utilization': round(utilization, 1),
            'workload_hours': round(workload, 1),
            'available_hours': round(available_hours, 1),
            'remaining_capacity': round(available_hours - workload, 1),
            'is_available': utilization < 100,
            'is_overallocated': utilization > 100,
            'conflicts': conflicts
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
