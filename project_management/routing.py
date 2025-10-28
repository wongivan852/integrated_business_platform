"""
WebSocket URL routing for real-time collaboration features.
Defines WebSocket endpoints for projects, tasks, and notifications.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Project-level WebSocket for real-time project updates
    re_path(
        r'ws/projects/(?P<project_id>\d+)/$',
        consumers.ProjectConsumer.as_asgi()
    ),

    # Task-level WebSocket for real-time task updates and comments
    re_path(
        r'ws/tasks/(?P<task_id>\d+)/$',
        consumers.TaskConsumer.as_asgi()
    ),

    # User-level WebSocket for personal notifications
    re_path(
        r'ws/notifications/$',
        consumers.NotificationConsumer.as_asgi()
    ),
]
