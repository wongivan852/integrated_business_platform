"""
Context processors for Project Management
Makes data available to all templates
"""

from .models import Notification


def notification_count(request):
    """
    Add unread notification count to template context
    Available as {{ notification_unread_count }} in all templates
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return {
            'notification_unread_count': unread_count
        }
    return {
        'notification_unread_count': 0
    }
