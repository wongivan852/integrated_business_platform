"""
Notification Views for Project Management
Handles user notifications and alerts
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator

from ..models import Notification
from ..utils.notification_utils import get_unread_count, mark_all_as_read


@login_required
def notification_list(request):
    """
    Display list of user notifications with pagination
    """
    # Get filter parameters
    notification_type = request.GET.get('type')
    is_read = request.GET.get('is_read')

    # Base queryset
    notifications = Notification.objects.filter(user=request.user)

    # Apply filters
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)

    if is_read == 'true':
        notifications = notifications.filter(is_read=True)
    elif is_read == 'false':
        notifications = notifications.filter(is_read=False)

    # Pagination
    paginator = Paginator(notifications, 20)  # 20 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unread count
    unread_count = get_unread_count(request.user)

    # Get notification types for filter
    notification_types = Notification.NOTIFICATION_TYPES

    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
        'notification_types': notification_types,
        'current_type': notification_type,
        'current_is_read': is_read,
    }

    return render(request, 'project_management/notifications/notification_list.html', context)


@login_required
@require_http_methods(["POST"])
def api_mark_as_read(request, notification_id):
    """
    Mark a single notification as read (AJAX)
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    notification.mark_as_read()

    return JsonResponse({
        'success': True,
        'unread_count': get_unread_count(request.user)
    })


@login_required
@require_http_methods(["POST"])
def api_mark_all_as_read(request):
    """
    Mark all notifications as read for the current user (AJAX)
    """
    mark_all_as_read(request.user)

    return JsonResponse({
        'success': True,
        'message': 'All notifications marked as read',
        'unread_count': 0
    })


@login_required
@require_http_methods(["POST"])
def api_delete_notification(request, notification_id):
    """
    Delete a notification (AJAX)
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    notification.delete()

    return JsonResponse({
        'success': True,
        'message': 'Notification deleted',
        'unread_count': get_unread_count(request.user)
    })


@login_required
def api_get_unread_count(request):
    """
    Get unread notification count (AJAX)
    For polling or real-time updates
    """
    unread_count = get_unread_count(request.user)

    # Get recent notifications (last 5 unread)
    recent_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    )[:5]

    notifications_data = []
    for notification in recent_notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'action_url': notification.action_url,
            'created_at': notification.created_at.isoformat(),
        })

    return JsonResponse({
        'unread_count': unread_count,
        'recent_notifications': notifications_data
    })
