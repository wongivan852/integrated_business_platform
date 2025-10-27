"""
Analytics Views for Project Management
Provides comprehensive analytics dashboards and reports
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
import json

from ..models import Project, Task, ProjectMetrics, DashboardWidget
from ..utils.analytics_utils import (
    calculate_project_health_score,
    create_metrics_snapshot,
    get_project_trends,
    get_portfolio_analytics,
    get_team_performance_metrics,
    predict_project_completion,
    get_burndown_data,
    get_cost_breakdown,
)
from ..utils.permissions import check_project_access


@login_required
def analytics_dashboard(request):
    """
    Main analytics dashboard with portfolio overview and key metrics
    """
    # Get user's projects
    user_projects = Project.objects.filter(
        Q(owner=request.user) | Q(team_members=request.user)
    ).distinct()

    # Get portfolio analytics
    portfolio_data = get_portfolio_analytics(request.user)

    # Get recent metrics snapshots for trending
    recent_snapshots = ProjectMetrics.objects.filter(
        project__in=user_projects
    ).order_by('-snapshot_date')[:10]

    # Get projects needing attention (health score < 60)
    at_risk_projects = []
    for project in user_projects.filter(status='active'):
        health_score = calculate_project_health_score(project)
        if health_score < 60:
            at_risk_projects.append({
                'project': project,
                'health_score': health_score,
            })

    # Sort by health score (worst first)
    at_risk_projects.sort(key=lambda x: x['health_score'])

    # Get user's dashboard widgets
    widgets = DashboardWidget.objects.filter(
        user=request.user,
        is_visible=True
    ).order_by('position')

    # Upcoming deadlines
    upcoming_deadlines = Task.objects.filter(
        project__in=user_projects,
        status__in=['todo', 'in_progress'],
        due_date__gte=timezone.now().date(),
        due_date__lte=timezone.now().date() + timedelta(days=7)
    ).select_related('project').order_by('due_date')[:10]

    # Recent activity (recently updated tasks)
    recent_activity = Task.objects.filter(
        project__in=user_projects
    ).select_related('project', 'assigned_to').order_by('-updated_at')[:10]

    context = {
        'portfolio_data': portfolio_data,
        'at_risk_projects': at_risk_projects[:5],  # Top 5 at-risk
        'widgets': widgets,
        'upcoming_deadlines': upcoming_deadlines,
        'recent_activity': recent_activity,
        'recent_snapshots': recent_snapshots,
    }

    return render(request, 'project_management/analytics/analytics_dashboard.html', context)


@login_required
def project_analytics(request, pk):
    """
    Detailed analytics for a specific project
    """
    project = get_object_or_404(Project, pk=pk)

    # Check access
    if not check_project_access(request.user, project):
        messages.error(request, "You don't have permission to view this project's analytics.")
        return redirect('project_management:project_list')

    # Create today's snapshot
    snapshot = create_metrics_snapshot(project)

    # Get trends for last 30 days
    trends = get_project_trends(project, days=30)

    # Get burndown data
    burndown = get_burndown_data(project)

    # Get cost breakdown
    cost_breakdown = get_cost_breakdown(project)

    # Calculate health score
    health_score = calculate_project_health_score(project)

    # Predict completion
    predicted_completion = predict_project_completion(project)

    # Task statistics
    tasks = project.tasks.all()
    task_stats = {
        'total': tasks.count(),
        'completed': tasks.filter(status='done').count(),
        'in_progress': tasks.filter(status='in_progress').count(),
        'todo': tasks.filter(status='todo').count(),
        'overdue': tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=timezone.now().date()
        ).count(),
    }

    # Team performance
    team_members = project.team_members.all()
    team_performance = []
    for member in team_members:
        member_tasks = tasks.filter(assigned_to=member)
        completed = member_tasks.filter(status='done').count()
        total = member_tasks.count()
        completion_rate = (completed / total * 100) if total > 0 else 0

        team_performance.append({
            'member': member,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round(completion_rate, 1),
        })

    # Status distribution for pie chart
    status_distribution = tasks.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    # Priority distribution
    priority_distribution = tasks.values('priority').annotate(
        count=Count('id')
    ).order_by('priority')

    context = {
        'project': project,
        'snapshot': snapshot,
        'trends': json.dumps(trends),
        'burndown': json.dumps(burndown),
        'cost_breakdown': cost_breakdown,
        'health_score': health_score,
        'predicted_completion': predicted_completion,
        'task_stats': task_stats,
        'team_performance': team_performance,
        'status_distribution': list(status_distribution),
        'priority_distribution': list(priority_distribution),
    }

    return render(request, 'project_management/analytics/project_analytics.html', context)


@login_required
def portfolio_analytics(request):
    """
    Portfolio-level analytics across all projects
    """
    # Get all user's projects
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(team_members=request.user)
    ).distinct()

    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        projects = projects.filter(status=status_filter)

    # Get portfolio analytics
    portfolio_data = get_portfolio_analytics(request.user, status_filter)

    # Project health scores
    project_health = []
    for project in projects:
        health_score = calculate_project_health_score(project)
        project_health.append({
            'project': project,
            'health_score': health_score,
        })

    # Sort by health score
    project_health.sort(key=lambda x: x['health_score'])

    # Budget utilization by project
    budget_data = []
    for project in projects:
        if project.budget:
            utilization = (float(project.actual_cost) / float(project.budget)) * 100
            budget_data.append({
                'project': project,
                'budget': project.budget,
                'actual_cost': project.actual_cost,
                'utilization': round(utilization, 1),
            })

    # Timeline overview (projects by end date)
    timeline_projects = projects.filter(
        end_date__gte=timezone.now().date()
    ).order_by('end_date')[:20]

    # Resource allocation across projects
    resource_summary = {}
    for project in projects.filter(status='active'):
        members = project.team_members.all()
        for member in members:
            if member.id not in resource_summary:
                resource_summary[member.id] = {
                    'member': member,
                    'projects': [],
                    'total_tasks': 0,
                }
            resource_summary[member.id]['projects'].append(project.name)
            resource_summary[member.id]['total_tasks'] += project.tasks.filter(
                assigned_to=member
            ).count()

    resource_allocation = list(resource_summary.values())

    context = {
        'portfolio_data': portfolio_data,
        'project_health': project_health,
        'budget_data': budget_data,
        'timeline_projects': timeline_projects,
        'resource_allocation': resource_allocation,
        'status_filter': status_filter,
        'status_choices': Project.STATUS_CHOICES,
    }

    return render(request, 'project_management/analytics/portfolio_analytics.html', context)


@login_required
def team_performance(request):
    """
    Team performance analytics and metrics
    """
    # Get team metrics
    team_metrics = get_team_performance_metrics(request.user)

    # Group by team member
    member_summary = {}
    for metric in team_metrics:
        member_id = metric['member'].id
        if member_id not in member_summary:
            member_summary[member_id] = {
                'member': metric['member'],
                'projects': [],
                'total_tasks': 0,
                'completed_tasks': 0,
                'overdue_tasks': 0,
            }

        member_summary[member_id]['projects'].append(metric['project'].name)
        member_summary[member_id]['total_tasks'] += metric['total_tasks']
        member_summary[member_id]['completed_tasks'] += metric['completed_tasks']
        member_summary[member_id]['overdue_tasks'] += metric['overdue_tasks']

    # Calculate completion rates
    for member_id, data in member_summary.items():
        total = data['total_tasks']
        completed = data['completed_tasks']
        data['completion_rate'] = round((completed / total * 100), 1) if total > 0 else 0

    # Sort by completion rate
    team_summary = sorted(
        member_summary.values(),
        key=lambda x: x['completion_rate'],
        reverse=True
    )

    # Top performers (completion rate >= 80%)
    top_performers = [m for m in team_summary if m['completion_rate'] >= 80]

    # Needs support (completion rate < 50% or high overdue)
    needs_support = [
        m for m in team_summary
        if m['completion_rate'] < 50 or m['overdue_tasks'] > 5
    ]

    context = {
        'team_summary': team_summary,
        'top_performers': top_performers,
        'needs_support': needs_support,
        'team_metrics': team_metrics,
    }

    return render(request, 'project_management/analytics/team_performance.html', context)


@login_required
def trend_analysis(request):
    """
    Historical trend analysis across projects
    """
    # Get user's projects
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(team_members=request.user)
    ).distinct()

    # Time period filter
    days = int(request.GET.get('days', 30))

    # Aggregate metrics over time
    cutoff_date = timezone.now().date() - timedelta(days=days)

    snapshots = ProjectMetrics.objects.filter(
        project__in=projects,
        snapshot_date__gte=cutoff_date
    ).order_by('snapshot_date')

    # Aggregate by date
    daily_aggregates = {}
    for snapshot in snapshots:
        date_str = snapshot.snapshot_date.strftime('%Y-%m-%d')
        if date_str not in daily_aggregates:
            daily_aggregates[date_str] = {
                'date': date_str,
                'total_tasks': 0,
                'completed_tasks': 0,
                'cost': 0,
                'health_score': [],
            }

        daily_aggregates[date_str]['total_tasks'] += snapshot.tasks_total
        daily_aggregates[date_str]['completed_tasks'] += snapshot.tasks_completed
        daily_aggregates[date_str]['cost'] += float(snapshot.actual_cost)
        daily_aggregates[date_str]['health_score'].append(snapshot.health_score)

    # Calculate averages
    trend_data = {
        'dates': [],
        'completion_rate': [],
        'avg_health_score': [],
        'total_cost': [],
    }

    for date_str in sorted(daily_aggregates.keys()):
        data = daily_aggregates[date_str]
        trend_data['dates'].append(date_str)

        # Completion rate
        total = data['total_tasks']
        completed = data['completed_tasks']
        completion_rate = (completed / total * 100) if total > 0 else 0
        trend_data['completion_rate'].append(round(completion_rate, 1))

        # Average health score
        health_scores = data['health_score']
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
        trend_data['avg_health_score'].append(round(avg_health, 1))

        # Total cost
        trend_data['total_cost'].append(round(data['cost'], 2))

    # Project-specific trends
    project_trends = {}
    for project in projects.filter(status='active')[:10]:  # Top 10 active projects
        project_trends[project.id] = {
            'project': project,
            'trends': get_project_trends(project, days=days),
        }

    context = {
        'trend_data': json.dumps(trend_data),
        'project_trends': project_trends,
        'days': days,
    }

    return render(request, 'project_management/analytics/trend_analysis.html', context)


@login_required
def predictive_analytics(request):
    """
    Predictive analytics and forecasting
    """
    # Get active projects
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(team_members=request.user),
        status='active'
    ).distinct()

    # Generate predictions for each project
    predictions = []
    for project in projects:
        predicted_completion = predict_project_completion(project)

        if predicted_completion:
            # Check if on track
            on_track = predicted_completion <= project.end_date

            # Calculate delay (if any)
            delay_days = (predicted_completion - project.end_date).days if not on_track else 0

            predictions.append({
                'project': project,
                'predicted_completion': predicted_completion,
                'planned_completion': project.end_date,
                'on_track': on_track,
                'delay_days': delay_days,
            })

    # Sort by delay (worst first)
    predictions.sort(key=lambda x: x.get('delay_days', 0), reverse=True)

    # Budget forecasts
    budget_forecasts = []
    for project in projects:
        if project.budget:
            # Simple linear projection based on current burn rate
            days_elapsed = (timezone.now().date() - project.start_date).days
            total_days = (project.end_date - project.start_date).days

            if days_elapsed > 0:
                daily_burn = float(project.actual_cost) / days_elapsed
                projected_cost = daily_burn * total_days

                budget_forecasts.append({
                    'project': project,
                    'current_cost': project.actual_cost,
                    'projected_cost': round(projected_cost, 2),
                    'budget': project.budget,
                    'over_budget': projected_cost > float(project.budget),
                    'variance': round(float(project.budget) - projected_cost, 2),
                })

    # Sort by variance (worst first)
    budget_forecasts.sort(key=lambda x: x['variance'])

    # Risk assessment
    risk_projects = []
    for project in projects:
        health_score = calculate_project_health_score(project)

        risk_factors = []
        if health_score < 50:
            risk_factors.append('Low health score')

        tasks = project.tasks.all()
        overdue_count = tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=timezone.now().date()
        ).count()
        if overdue_count > 5:
            risk_factors.append(f'{overdue_count} overdue tasks')

        if project.budget:
            budget_utilization = (float(project.actual_cost) / float(project.budget)) * 100
            if budget_utilization > 90:
                risk_factors.append('Budget nearly exhausted')

        if risk_factors:
            risk_projects.append({
                'project': project,
                'health_score': health_score,
                'risk_factors': risk_factors,
                'risk_level': 'High' if health_score < 40 else 'Medium',
            })

    context = {
        'predictions': predictions,
        'budget_forecasts': budget_forecasts,
        'risk_projects': risk_projects,
    }

    return render(request, 'project_management/analytics/predictive_analytics.html', context)
