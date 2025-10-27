"""
Analytics Utilities for Project Management
Provides metric calculation and data aggregation functions
"""

from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from ..models import Project, Task, ProjectMetrics, ProjectMember


def calculate_project_health_score(project):
    """
    Calculate overall project health score (0-100)
    Based on schedule, budget, progress, and quality metrics
    """
    score = 100

    # Schedule health (30 points)
    if project.end_date < timezone.now().date():
        days_overdue = (timezone.now().date() - project.end_date).days
        schedule_penalty = min(30, days_overdue * 3)
        score -= schedule_penalty

    # Budget health (30 points)
    if project.budget:
        budget_variance = float(project.budget) - float(project.actual_cost)
        if budget_variance < 0:  # Over budget
            over_percent = abs(budget_variance) / float(project.budget) * 100
            budget_penalty = min(30, over_percent)
            score -= budget_penalty

    # Progress health (20 points)
    expected_progress = calculate_expected_progress(project)
    progress_variance = project.progress_percentage - expected_progress
    if progress_variance < -10:  # More than 10% behind
        progress_penalty = min(20, abs(progress_variance + 10))
        score -= progress_penalty

    # Task completion health (20 points)
    tasks = project.tasks.all()
    if tasks.exists():
        overdue_tasks = tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=timezone.now().date()
        ).count()
        total_tasks = tasks.count()
        overdue_percent = (overdue_tasks / total_tasks) * 100
        task_penalty = min(20, overdue_percent)
        score -= task_penalty

    return max(0, min(100, int(score)))


def calculate_expected_progress(project):
    """
    Calculate expected progress percentage based on timeline
    """
    if not project.start_date or not project.end_date:
        return 0

    today = timezone.now().date()

    if today < project.start_date:
        return 0
    elif today > project.end_date:
        return 100

    total_days = (project.end_date - project.start_date).days
    days_passed = (today - project.start_date).days

    if total_days == 0:
        return 100

    return int((days_passed / total_days) * 100)


def calculate_velocity(project, weeks=4):
    """
    Calculate project velocity (tasks completed per week)
    """
    cutoff_date = timezone.now() - timedelta(weeks=weeks)

    completed_tasks = project.tasks.filter(
        status='done',
        updated_at__gte=cutoff_date
    ).count()

    return round(completed_tasks / weeks, 2)


def create_metrics_snapshot(project):
    """
    Create a daily metrics snapshot for a project
    """
    today = timezone.now().date()

    # Get all tasks
    tasks = project.tasks.all()
    tasks_total = tasks.count()
    tasks_completed = tasks.filter(status='done').count()
    tasks_in_progress = tasks.filter(status='in_progress').count()
    tasks_overdue = tasks.filter(
        status__in=['todo', 'in_progress'],
        due_date__lt=today
    ).count()

    # Calculate schedule variance
    days_remaining = (project.end_date - today).days
    expected_progress = calculate_expected_progress(project)
    progress_variance = project.progress_percentage - expected_progress
    schedule_variance_days = int(progress_variance / 100 * (project.end_date - project.start_date).days)

    # Cost metrics
    budget_allocated = project.budget or Decimal('0')
    actual_cost = project.actual_cost
    cost_variance = budget_allocated - actual_cost

    # Team metrics
    team_size = project.team_members.count()
    resource_utilization = calculate_resource_utilization(project)

    # Quality metrics (placeholder for now)
    issues_open = 0
    issues_resolved = 0

    # Velocity
    velocity = calculate_velocity(project)

    # Health score
    health_score = calculate_project_health_score(project)

    # Create or update snapshot
    snapshot, created = ProjectMetrics.objects.update_or_create(
        project=project,
        snapshot_date=today,
        defaults={
            'tasks_total': tasks_total,
            'tasks_completed': tasks_completed,
            'tasks_in_progress': tasks_in_progress,
            'tasks_overdue': tasks_overdue,
            'progress_percentage': Decimal(str(project.progress_percentage)),
            'days_remaining': days_remaining,
            'schedule_variance_days': schedule_variance_days,
            'budget_allocated': budget_allocated,
            'actual_cost': actual_cost,
            'cost_variance': cost_variance,
            'team_size': team_size,
            'resource_utilization': Decimal(str(resource_utilization)),
            'issues_open': issues_open,
            'issues_resolved': issues_resolved,
            'velocity': Decimal(str(velocity)),
            'health_score': health_score,
        }
    )

    return snapshot


def calculate_resource_utilization(project):
    """
    Calculate team resource utilization percentage
    """
    team_members = project.team_members.all()
    if not team_members.exists():
        return 0

    # Assume 40 hours per week capacity per person
    total_capacity = team_members.count() * 40

    # Sum assigned hours for current week
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    assigned_hours = project.tasks.filter(
        status='in_progress',
        start_date__lte=week_end,
        due_date__gte=week_start
    ).aggregate(
        total=Sum('estimated_hours')
    )['total'] or 0

    if total_capacity == 0:
        return 0

    return round((float(assigned_hours) / total_capacity) * 100, 2)


def get_project_trends(project, days=30):
    """
    Get trend data for a project over specified days
    """
    cutoff_date = timezone.now().date() - timedelta(days=days)

    snapshots = ProjectMetrics.objects.filter(
        project=project,
        snapshot_date__gte=cutoff_date
    ).order_by('snapshot_date')

    trends = {
        'dates': [],
        'progress': [],
        'cost': [],
        'velocity': [],
        'health_score': [],
        'tasks_completed': [],
    }

    for snapshot in snapshots:
        trends['dates'].append(snapshot.snapshot_date.strftime('%Y-%m-%d'))
        trends['progress'].append(float(snapshot.progress_percentage))
        trends['cost'].append(float(snapshot.actual_cost))
        trends['velocity'].append(float(snapshot.velocity))
        trends['health_score'].append(snapshot.health_score)
        trends['tasks_completed'].append(snapshot.tasks_completed)

    return trends


def get_portfolio_analytics(user, status_filter=None):
    """
    Get analytics across all projects for a user (portfolio view)
    """
    projects = Project.objects.filter(
        Q(owner=user) | Q(team_members=user)
    ).distinct()

    if status_filter:
        projects = projects.filter(status=status_filter)

    total_projects = projects.count()

    # Status breakdown
    status_breakdown = projects.values('status').annotate(
        count=Count('id')
    ).order_by('status')

    # Budget analytics
    budget_data = projects.aggregate(
        total_budget=Sum('budget'),
        total_cost=Sum('actual_cost')
    )

    # Health score distribution
    active_projects = projects.filter(status='active')
    health_scores = []
    for project in active_projects:
        health_scores.append(calculate_project_health_score(project))

    avg_health_score = sum(health_scores) / len(health_scores) if health_scores else 0

    # At-risk projects (health score < 50)
    at_risk_count = sum(1 for score in health_scores if score < 50)

    # Task completion rate
    all_tasks = Task.objects.filter(project__in=projects)
    total_tasks = all_tasks.count()
    completed_tasks = all_tasks.filter(status='done').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    return {
        'total_projects': total_projects,
        'status_breakdown': list(status_breakdown),
        'total_budget': budget_data['total_budget'] or 0,
        'total_cost': budget_data['total_cost'] or 0,
        'budget_variance': (budget_data['total_budget'] or 0) - (budget_data['total_cost'] or 0),
        'avg_health_score': round(avg_health_score, 1),
        'at_risk_count': at_risk_count,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': round(completion_rate, 1),
    }


def get_team_performance_metrics(user):
    """
    Get performance metrics for team members
    """
    # Get projects where user is owner or manager
    projects = Project.objects.filter(
        Q(owner=user) | Q(projectmember__user=user, projectmember__role='manager')
    ).distinct()

    team_metrics = []

    for project in projects:
        members = project.team_members.all()

        for member in members:
            # Tasks assigned to this member
            assigned_tasks = project.tasks.filter(assigned_to=member)
            completed_tasks = assigned_tasks.filter(status='done')
            overdue_tasks = assigned_tasks.filter(
                status__in=['todo', 'in_progress'],
                due_date__lt=timezone.now().date()
            )

            # Calculate completion rate
            total = assigned_tasks.count()
            completed = completed_tasks.count()
            completion_rate = (completed / total * 100) if total > 0 else 0

            team_metrics.append({
                'member': member,
                'project': project,
                'total_tasks': total,
                'completed_tasks': completed,
                'overdue_tasks': overdue_tasks.count(),
                'completion_rate': round(completion_rate, 1),
            })

    return team_metrics


def predict_project_completion(project):
    """
    Predict project completion date based on current velocity
    """
    # Get velocity from last 4 weeks
    velocity = calculate_velocity(project, weeks=4)

    if velocity == 0:
        return None  # Cannot predict

    # Remaining tasks
    remaining_tasks = project.tasks.exclude(status='done').count()

    # Weeks needed
    weeks_needed = remaining_tasks / velocity if velocity > 0 else 0

    # Predicted completion date
    predicted_date = timezone.now().date() + timedelta(weeks=weeks_needed)

    return predicted_date


def get_burndown_data(project):
    """
    Get burndown chart data for a project
    """
    start_date = project.start_date
    end_date = project.end_date
    today = timezone.now().date()

    # Total tasks
    total_tasks = project.tasks.count()

    # Get snapshots
    snapshots = ProjectMetrics.objects.filter(
        project=project,
        snapshot_date__gte=start_date,
        snapshot_date__lte=min(today, end_date)
    ).order_by('snapshot_date')

    # Ideal burndown line
    total_days = (end_date - start_date).days
    ideal_line = []
    actual_line = []
    dates = []

    for i in range(total_days + 1):
        current_date = start_date + timedelta(days=i)
        dates.append(current_date.strftime('%Y-%m-%d'))

        # Ideal: linear decrease
        ideal_remaining = total_tasks * (1 - i / total_days)
        ideal_line.append(round(ideal_remaining, 1))

        # Actual: from snapshots
        if current_date <= today:
            snapshot = snapshots.filter(snapshot_date=current_date).first()
            if snapshot:
                actual_remaining = snapshot.tasks_total - snapshot.tasks_completed
                actual_line.append(actual_remaining)
            else:
                actual_line.append(None)
        else:
            actual_line.append(None)

    return {
        'dates': dates,
        'ideal': ideal_line,
        'actual': actual_line,
        'total_tasks': total_tasks,
    }


def get_cost_breakdown(project):
    """
    Get detailed cost breakdown for a project
    """
    # Task-level costs
    tasks_with_costs = project.tasks.exclude(
        actual_cost__isnull=True
    ).values('status').annotate(
        total_cost=Sum('actual_cost'),
        count=Count('id')
    )

    breakdown = {
        'by_status': list(tasks_with_costs),
        'total_cost': project.actual_cost,
        'budget': project.budget or 0,
        'variance': (project.budget or 0) - project.actual_cost,
        'variance_percent': 0,
    }

    if project.budget and project.budget > 0:
        breakdown['variance_percent'] = round(
            (breakdown['variance'] / float(project.budget)) * 100,
            1
        )

    return breakdown
