"""
Phase 4: Earned Value Management (EVM) Views
Handles financial tracking, cost performance, and EVM calculations
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..models import (
    Project, ProjectCost, TaskCost, EVMSnapshot,
    Task, ProjectMember
)
from ..utils.permissions import check_project_access, user_can_edit_project


# ============================================================================
# EVM DASHBOARD
# ============================================================================

@login_required
def evm_dashboard(request, pk):
    """
    Main EVM dashboard showing all earned value metrics

    Displays:
    - S-Curve (PV, EV, AC over time)
    - Current performance indices (CPI, SPI)
    - Cost and schedule variances
    - Forecasts (EAC, ETC, VAC)
    - Trend analysis
    """
    project = get_object_or_404(Project, pk=pk)
    has_access, user_role = check_project_access(request.user, project)

    if not has_access:
        messages.error(request, "You don't have permission to access this project.")
        return redirect('project_management:project_list')

    # Get latest EVM snapshot
    latest_snapshot = EVMSnapshot.objects.filter(project=project).order_by('-snapshot_date').first()

    # Get all snapshots for trend
    snapshots = EVMSnapshot.objects.filter(project=project).order_by('snapshot_date')

    # Calculate current metrics if no snapshot exists yet
    if not latest_snapshot:
        latest_snapshot = calculate_current_evm(project)

    # Get cost breakdown
    cost_by_category = ProjectCost.objects.filter(project=project).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Get task-level costs
    task_costs = TaskCost.objects.filter(task__project=project).select_related('task')

    # Calculate totals
    total_planned_cost = task_costs.aggregate(Sum('planned_cost'))['planned_cost__sum'] or 0
    total_actual_cost = task_costs.aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0

    # Performance status
    performance_status = 'healthy'
    if latest_snapshot:
        if latest_snapshot.cost_performance_index < 0.9 or latest_snapshot.schedule_performance_index < 0.9:
            performance_status = 'at_risk'
        if latest_snapshot.cost_performance_index < 0.8 or latest_snapshot.schedule_performance_index < 0.8:
            performance_status = 'critical'

    # Format snapshot data for charts
    chart_data = {
        'dates': [s.snapshot_date.strftime('%Y-%m-%d') for s in snapshots],
        'pv': [float(s.planned_value) for s in snapshots],
        'ev': [float(s.earned_value) for s in snapshots],
        'ac': [float(s.actual_cost) for s in snapshots],
    }

    context = {
        'project': project,
        'latest_snapshot': latest_snapshot,
        'snapshots': snapshots,
        'cost_by_category': cost_by_category,
        'task_costs': task_costs,
        'total_planned_cost': total_planned_cost,
        'total_actual_cost': total_actual_cost,
        'performance_status': performance_status,
        'chart_data': json.dumps(chart_data),
        'user_role': user_role
    }

    return render(request, 'project_management/evm_dashboard.html', context)


def calculate_current_evm(project):
    """
    Calculate EVM metrics for current date

    Returns:
        Temporary EVMSnapshot object (not saved to database)
    """
    today = timezone.now().date()

    # Get project baseline data
    bac = project.budget or Decimal('0')
    planned_duration = (project.end_date - project.start_date).days if project.end_date and project.start_date else 0

    # Calculate Planned Value (PV)
    if planned_duration > 0 and project.start_date:
        days_elapsed = (today - project.start_date).days
        planned_progress = min(days_elapsed / planned_duration, 1.0) * 100
        pv = bac * Decimal(str(planned_progress / 100))
    else:
        planned_progress = 0
        pv = Decimal('0')

    # Calculate Earned Value (EV)
    # EV = BAC × Actual % Complete
    actual_progress = project.progress_percentage
    ev = bac * Decimal(str(actual_progress / 100))

    # Calculate Actual Cost (AC)
    ac = ProjectCost.objects.filter(project=project).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')

    # Calculate performance indices
    cpi = (ev / ac) if ac > 0 else Decimal('1.0')
    spi = (ev / pv) if pv > 0 else Decimal('1.0')

    # Calculate variances
    cv = ev - ac
    sv = ev - pv

    # Calculate forecasts
    eac = bac / cpi if cpi > 0 else bac
    etc = eac - ac
    vac = bac - eac

    # Create temporary snapshot
    snapshot = EVMSnapshot(
        project=project,
        snapshot_date=today,
        budget_at_completion=bac,
        planned_duration_days=planned_duration,
        planned_value=pv,
        earned_value=ev,
        actual_cost=ac,
        cost_performance_index=cpi,
        schedule_performance_index=spi,
        cost_variance=cv,
        schedule_variance=sv,
        estimate_at_completion=eac,
        estimate_to_complete=etc,
        variance_at_completion=vac
    )

    return snapshot


# ============================================================================
# COST TRACKING
# ============================================================================

@login_required
def project_costs(request, pk):
    """
    View and manage project costs

    Features:
    - Add new cost entries
    - View cost history
    - Cost breakdown by category
    - Budget tracking
    """
    project = get_object_or_404(Project, pk=pk)
    has_access, user_role = check_project_access(request.user, project)

    if not has_access:
        messages.error(request, "You don't have permission to access this project.")
        return redirect('project_management:project_list')

    # Get all costs
    costs = ProjectCost.objects.filter(project=project).order_by('-date')

    # Calculate totals by category
    cost_summary = ProjectCost.objects.filter(project=project).values('category').annotate(
        total=Sum('amount')
    ).order_by('category')

    # Calculate overall totals
    total_costs = costs.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    budget = project.budget or Decimal('0')
    budget_remaining = budget - total_costs
    budget_percentage = (total_costs / budget * 100) if budget > 0 else 0

    context = {
        'project': project,
        'costs': costs,
        'cost_summary': cost_summary,
        'total_costs': total_costs,
        'budget': budget,
        'budget_remaining': budget_remaining,
        'budget_percentage': budget_percentage,
        'user_role': user_role
    }

    return render(request, 'project_management/project_costs.html', context)


@login_required
def cost_entry_form(request, pk):
    """
    Form to add a new cost entry
    """
    project = get_object_or_404(Project, pk=pk)
    has_access, user_role = check_project_access(request.user, project)

    if not has_access or user_role not in ['owner', 'manager']:
        messages.error(request, "You don't have permission to add costs.")
        return redirect('project_management:project_costs', pk=project.pk)

    if request.method == 'POST':
        # Process form
        date_str = request.POST.get('date')
        category = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        vendor = request.POST.get('vendor', '')
        invoice_number = request.POST.get('invoice_number', '')

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            amount_decimal = Decimal(amount)

            ProjectCost.objects.create(
                project=project,
                date=date,
                category=category,
                amount=amount_decimal,
                description=description,
                vendor=vendor,
                invoice_number=invoice_number,
                created_by=request.user
            )

            messages.success(request, f'Cost entry of ${amount_decimal:,.2f} added successfully.')
            return redirect('project_management:project_costs', pk=project.pk)

        except Exception as e:
            messages.error(request, f'Error adding cost entry: {str(e)}')

    context = {
        'project': project,
        'user_role': user_role
    }

    return render(request, 'project_management/cost_entry_form.html', context)


# ============================================================================
# EVM SNAPSHOT MANAGEMENT
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_create_evm_snapshot(request, pk):
    """
    API endpoint to create a new EVM snapshot

    This captures the current EVM metrics for historical tracking
    """
    try:
        project = get_object_or_404(Project, pk=pk)
        has_access, user_role = check_project_access(request.user, project)

        if not has_access or user_role not in ['owner', 'manager']:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)

        # Calculate current EVM metrics
        snapshot = calculate_current_evm(project)

        # Save to database
        snapshot.save()

        return JsonResponse({
            'success': True,
            'snapshot_id': snapshot.id,
            'snapshot_date': snapshot.snapshot_date.strftime('%Y-%m-%d'),
            'cpi': float(snapshot.cost_performance_index),
            'spi': float(snapshot.schedule_performance_index),
            'message': 'EVM snapshot created successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def evm_report(request, pk):
    """
    Generate comprehensive EVM report

    Includes:
    - Executive summary
    - Detailed metrics
    - Trend analysis
    - Recommendations
    """
    project = get_object_or_404(Project, pk=pk)
    has_access, user_role = check_project_access(request.user, project)

    if not has_access:
        messages.error(request, "You don't have permission to access this project.")
        return redirect('project_management:project_list')

    # Get date range
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        # Default to project dates
        start_date = project.start_date or timezone.now().date()
        end_date = timezone.now().date()

    # Get snapshots in date range
    snapshots = EVMSnapshot.objects.filter(
        project=project,
        snapshot_date__gte=start_date,
        snapshot_date__lte=end_date
    ).order_by('snapshot_date')

    # Calculate trends
    if snapshots.count() >= 2:
        first_snapshot = snapshots.first()
        last_snapshot = snapshots.last()

        cpi_trend = last_snapshot.cost_performance_index - first_snapshot.cost_performance_index
        spi_trend = last_snapshot.schedule_performance_index - first_snapshot.schedule_performance_index

        cpi_improving = cpi_trend > 0
        spi_improving = spi_trend > 0
    else:
        cpi_trend = spi_trend = 0
        cpi_improving = spi_improving = None

    # Generate recommendations
    recommendations = []
    latest = snapshots.last() if snapshots.exists() else calculate_current_evm(project)

    if latest.cost_performance_index < 1.0:
        recommendations.append({
            'type': 'warning',
            'title': 'Cost Overrun',
            'message': f'Project is over budget. CPI is {latest.cost_performance_index:.2f}. Consider cost reduction measures.'
        })

    if latest.schedule_performance_index < 1.0:
        recommendations.append({
            'type': 'warning',
            'title': 'Schedule Delay',
            'message': f'Project is behind schedule. SPI is {latest.schedule_performance_index:.2f}. Review task dependencies and resource allocation.'
        })

    if latest.cost_performance_index > 1.1:
        recommendations.append({
            'type': 'success',
            'title': 'Under Budget',
            'message': f'Project is under budget. CPI is {latest.cost_performance_index:.2f}. Good cost control!'
        })

    if latest.schedule_performance_index > 1.1:
        recommendations.append({
            'type': 'success',
            'title': 'Ahead of Schedule',
            'message': f'Project is ahead of schedule. SPI is {latest.schedule_performance_index:.2f}. Excellent progress!'
        })

    # Cost breakdown
    costs = ProjectCost.objects.filter(
        project=project,
        date__gte=start_date,
        date__lte=end_date
    )

    cost_by_category = costs.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'project': project,
        'snapshots': snapshots,
        'latest_snapshot': latest,
        'start_date': start_date,
        'end_date': end_date,
        'cpi_trend': cpi_trend,
        'spi_trend': spi_trend,
        'cpi_improving': cpi_improving,
        'spi_improving': spi_improving,
        'recommendations': recommendations,
        'cost_by_category': cost_by_category,
        'user_role': user_role
    }

    return render(request, 'project_management/evm_report.html', context)


# ============================================================================
# TASK COST TRACKING
# ============================================================================

@login_required
def task_cost_tracking(request, pk):
    """
    View task-level cost breakdown

    Shows:
    - Planned vs actual costs per task
    - Cost variances
    - Task completion efficiency
    """
    project = get_object_or_404(Project, pk=pk)
    has_access, user_role = check_project_access(request.user, project)

    if not has_access:
        messages.error(request, "You don't have permission to access this project.")
        return redirect('project_management:project_list')

    # Get all tasks with costs
    task_costs = TaskCost.objects.filter(task__project=project).select_related('task').order_by('task__task_code')

    # Calculate totals
    totals = task_costs.aggregate(
        total_planned=Sum('planned_cost'),
        total_actual=Sum('actual_cost')
    )

    total_planned = totals['total_planned'] or Decimal('0')
    total_actual = totals['total_actual'] or Decimal('0')
    total_variance = total_actual - total_planned

    # Find highest variances
    tasks_over_budget = []
    tasks_under_budget = []

    for tc in task_costs:
        variance = tc.actual_cost - tc.planned_cost
        if variance > 0:
            tasks_over_budget.append({
                'task_cost': tc,
                'variance': variance
            })
        elif variance < 0:
            tasks_under_budget.append({
                'task_cost': tc,
                'variance': abs(variance)
            })

    # Sort by variance
    tasks_over_budget.sort(key=lambda x: x['variance'], reverse=True)
    tasks_under_budget.sort(key=lambda x: x['variance'], reverse=True)

    context = {
        'project': project,
        'task_costs': task_costs,
        'total_planned': total_planned,
        'total_actual': total_actual,
        'total_variance': total_variance,
        'tasks_over_budget': tasks_over_budget[:10],  # Top 10
        'tasks_under_budget': tasks_under_budget[:10],  # Top 10
        'user_role': user_role
    }

    return render(request, 'project_management/task_cost_tracking.html', context)


@login_required
@require_http_methods(["POST"])
def api_update_task_cost(request, pk, task_id):
    """
    API endpoint to update task cost information
    """
    try:
        project = get_object_or_404(Project, pk=pk)
        has_access, user_role = check_project_access(request.user, project)

        if not has_access or user_role not in ['owner', 'manager']:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)

        task = get_object_or_404(Task, pk=task_id, project=project)
        data = json.loads(request.body)

        cost_type = data.get('cost_type', 'total')
        planned_cost = Decimal(str(data.get('planned_cost', 0)))
        actual_cost = Decimal(str(data.get('actual_cost', 0)))

        # Create or update task cost
        task_cost, created = TaskCost.objects.update_or_create(
            task=task,
            cost_type=cost_type,
            defaults={
                'planned_cost': planned_cost,
                'actual_cost': actual_cost
            }
        )

        return JsonResponse({
            'success': True,
            'created': created,
            'task_cost_id': task_cost.id,
            'variance': float(actual_cost - planned_cost),
            'message': 'Task cost updated successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
