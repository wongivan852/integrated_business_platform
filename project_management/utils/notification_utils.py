"""
Notification Utilities for Project Management
Provides notification creation and management functions
"""

from django.urls import reverse
from ..models import Notification, Task, Project
from django.utils import timezone
from datetime import timedelta


def create_notification(user, notification_type, title, message, project=None, task=None, action_url=''):
    """
    Create a notification for a user

    Args:
        user: User to notify
        notification_type: Type of notification (from NOTIFICATION_TYPES)
        title: Short title
        message: Detailed message
        project: Related project (optional)
        task: Related task (optional)
        action_url: URL to navigate to when clicked

    Returns:
        Notification object
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        project=project,
        task=task,
        action_url=action_url
    )
    return notification


def notify_task_assigned(task, assigned_by):
    """Notify user when task is assigned to them"""
    if task.assigned_to and task.assigned_to != assigned_by:
        action_url = reverse('project_management:task_detail', kwargs={
            'project_pk': task.project.id,
            'pk': task.id
        })

        create_notification(
            user=task.assigned_to,
            notification_type='task_assigned',
            title=f'New task assigned: {task.name}',
            message=f'{assigned_by.get_full_name() or assigned_by.username} assigned you a task in {task.project.name}',
            project=task.project,
            task=task,
            action_url=action_url
        )


def notify_task_completed(task):
    """Notify project owner when task is completed"""
    if task.status == 'done' and task.assigned_to:
        action_url = reverse('project_management:task_detail', kwargs={
            'project_pk': task.project.id,
            'pk': task.id
        })

        # Notify project owner
        create_notification(
            user=task.project.owner,
            notification_type='task_completed',
            title=f'Task completed: {task.name}',
            message=f'{task.assigned_to.get_full_name() or task.assigned_to.username} completed a task in {task.project.name}',
            project=task.project,
            task=task,
            action_url=action_url
        )


def notify_deadline_approaching(task, days_until):
    """Notify assigned user when deadline is approaching"""
    if task.assigned_to and task.due_date:
        action_url = reverse('project_management:task_detail', kwargs={
            'project_pk': task.project.id,
            'pk': task.id
        })

        create_notification(
            user=task.assigned_to,
            notification_type='deadline_approaching',
            title=f'Deadline approaching: {task.name}',
            message=f'Task due in {days_until} days',
            project=task.project,
            task=task,
            action_url=action_url
        )


def notify_task_overdue(task):
    """Notify assigned user and project owner when task is overdue"""
    action_url = reverse('project_management:task_detail', kwargs={
        'project_pk': task.project.id,
        'pk': task.id
    })

    # Notify assigned user
    if task.assigned_to:
        create_notification(
            user=task.assigned_to,
            notification_type='task_overdue',
            title=f'Task overdue: {task.name}',
            message=f'This task is past its due date ({task.due_date})',
            project=task.project,
            task=task,
            action_url=action_url
        )

    # Notify project owner
    if task.project.owner != task.assigned_to:
        create_notification(
            user=task.project.owner,
            notification_type='task_overdue',
            title=f'Task overdue: {task.name}',
            message=f'Task in {task.project.name} is overdue',
            project=task.project,
            task=task,
            action_url=action_url
        )


def notify_budget_alert(project, threshold_percent):
    """Notify project owner when budget threshold is exceeded"""
    if project.budget and project.owner:
        action_url = reverse('project_management:project_costs', kwargs={'pk': project.id})

        create_notification(
            user=project.owner,
            notification_type='budget_alert',
            title=f'Budget alert: {project.name}',
            message=f'Project has used {threshold_percent}% of budget',
            project=project,
            action_url=action_url
        )


def notify_project_status_changed(project, old_status, new_status, changed_by):
    """Notify team members when project status changes"""
    action_url = reverse('project_management:project_detail', kwargs={'pk': project.id})

    # Notify all team members except the one who made the change
    for member in project.team_members.exclude(id=changed_by.id):
        create_notification(
            user=member,
            notification_type='project_status_changed',
            title=f'Project status changed: {project.name}',
            message=f'{changed_by.get_full_name() or changed_by.username} changed status from {old_status} to {new_status}',
            project=project,
            action_url=action_url
        )


def notify_comment_added(comment, mentioned_users=None):
    """Notify relevant users when comment is added"""
    # This would require a Comment model (not yet implemented)
    # Placeholder for future implementation
    pass


def notify_mention(user, mentioned_by, context_object):
    """Notify user when mentioned in comment or description"""
    # Placeholder for @mention functionality
    pass


def notify_milestone_completed(project, milestone_name):
    """Notify team when milestone is completed"""
    action_url = reverse('project_management:project_detail', kwargs={'pk': project.id})

    for member in project.team_members.all():
        create_notification(
            user=member,
            notification_type='milestone_completed',
            title=f'Milestone completed: {milestone_name}',
            message=f'Milestone "{milestone_name}" completed in {project.name}',
            project=project,
            action_url=action_url
        )


def notify_resource_assigned(resource_assignment):
    """Notify resource when assigned to task"""
    # This would use ResourceAssignment model from Phase 4
    # Placeholder for future enhancement
    pass


def get_unread_count(user):
    """Get count of unread notifications for user"""
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).count()


def mark_all_as_read(user):
    """Mark all notifications as read for user"""
    Notification.objects.filter(
        user=user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )


def delete_old_notifications(days=30):
    """Delete notifications older than specified days"""
    cutoff_date = timezone.now() - timedelta(days=days)
    Notification.objects.filter(
        created_at__lt=cutoff_date,
        is_read=True
    ).delete()


def check_approaching_deadlines():
    """
    Check for tasks with approaching deadlines and create notifications
    This should be run as a daily scheduled task (cron/celery)
    """
    today = timezone.now().date()

    # Tasks due in 3 days
    tasks_due_soon = Task.objects.filter(
        due_date=today + timedelta(days=3),
        status__in=['todo', 'in_progress']
    )

    for task in tasks_due_soon:
        notify_deadline_approaching(task, days_until=3)

    # Tasks due in 1 day
    tasks_due_tomorrow = Task.objects.filter(
        due_date=today + timedelta(days=1),
        status__in=['todo', 'in_progress']
    )

    for task in tasks_due_tomorrow:
        notify_deadline_approaching(task, days_until=1)


def check_overdue_tasks():
    """
    Check for overdue tasks and create notifications
    This should be run as a daily scheduled task (cron/celery)
    """
    today = timezone.now().date()

    overdue_tasks = Task.objects.filter(
        due_date__lt=today,
        status__in=['todo', 'in_progress']
    )

    for task in overdue_tasks:
        # Check if notification already sent today
        existing_notification = Notification.objects.filter(
            task=task,
            notification_type='task_overdue',
            created_at__date=today
        ).exists()

        if not existing_notification:
            notify_task_overdue(task)


def check_budget_alerts():
    """
    Check for budget threshold violations and create notifications
    This should be run as a daily scheduled task (cron/celery)
    """
    projects = Project.objects.filter(
        status='active',
        budget__gt=0
    )

    for project in projects:
        utilization = (float(project.actual_cost) / float(project.budget)) * 100

        # Alert at 75%, 90%, and 100%
        thresholds = [75, 90, 100]

        for threshold in thresholds:
            if utilization >= threshold:
                # Check if already notified for this threshold today
                today = timezone.now().date()
                existing_notification = Notification.objects.filter(
                    project=project,
                    notification_type='budget_alert',
                    message__contains=f'{threshold}%',
                    created_at__date=today
                ).exists()

                if not existing_notification:
                    notify_budget_alert(project, int(utilization))
                    break  # Only send one alert per day
