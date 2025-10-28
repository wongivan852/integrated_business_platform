"""
WebSocket consumers for real-time collaboration features.
Handles live project updates, task changes, user presence, and real-time comments.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from asgiref.sync import sync_to_async

User = get_user_model()


class ProjectConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for project-level real-time updates.
    Handles live updates for project changes, member activities, and general notifications.
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.project_group_name = f'project_{self.project_id}'
        self.user = self.scope['user']

        # Reject if user is not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Check if user has access to this project
        has_access = await self.check_project_access()
        if not has_access:
            await self.close()
            return

        # Join project group
        await self.channel_layer.group_add(
            self.project_group_name,
            self.channel_name
        )

        # Accept connection
        await self.accept()

        # Update user presence
        await self.update_user_presence(True)

        # Send initial data
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to project updates',
            'project_id': self.project_id,
            'user_id': self.user.id
        }))

        # Broadcast user joined
        await self.channel_layer.group_send(
            self.project_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Update user presence
        await self.update_user_presence(False)

        # Broadcast user left
        if hasattr(self, 'project_group_name'):
            await self.channel_layer.group_send(
                self.project_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'timestamp': timezone.now().isoformat()
                }
            )

            # Leave project group
            await self.channel_layer.group_discard(
                self.project_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                # Respond to heartbeat
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'update_presence':
                # Update user's current page/activity
                page = data.get('page', '')
                await self.update_user_page(page)
            else:
                # Unknown message type
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    # Event handlers for group messages
    async def project_updated(self, event):
        """Send project update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'project_updated',
            'project': event['project'],
            'updated_by': event.get('updated_by'),
            'changes': event.get('changes', {}),
            'timestamp': event['timestamp']
        }))

    async def user_joined(self, event):
        """Send user joined notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def user_left(self, event):
        """Send user left notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def task_created(self, event):
        """Send task created notification"""
        await self.send(text_data=json.dumps({
            'type': 'task_created',
            'task': event['task'],
            'created_by': event['created_by'],
            'timestamp': event['timestamp']
        }))

    async def task_updated(self, event):
        """Send task updated notification"""
        await self.send(text_data=json.dumps({
            'type': 'task_updated',
            'task': event['task'],
            'updated_by': event['updated_by'],
            'changes': event.get('changes', {}),
            'timestamp': event['timestamp']
        }))

    # Database operations
    @database_sync_to_async
    def check_project_access(self):
        """Check if user has access to the project"""
        from .models import Project
        try:
            project = Project.objects.get(id=self.project_id)
            # Check if user is owner or member
            return (
                project.owner == self.user or
                self.user in project.team_members.all() or
                self.user.is_superuser
            )
        except Project.DoesNotExist:
            return False

    @database_sync_to_async
    def update_user_presence(self, is_online):
        """Update user presence status"""
        from .models import UserPresence
        UserPresence.objects.update_or_create(
            user=self.user,
            project_id=self.project_id,
            defaults={
                'is_online': is_online,
                'last_seen': timezone.now()
            }
        )

    @database_sync_to_async
    def update_user_page(self, page):
        """Update user's current page"""
        from .models import UserPresence
        UserPresence.objects.filter(
            user=self.user,
            project_id=self.project_id
        ).update(
            current_page=page,
            last_seen=timezone.now()
        )


class TaskConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for task-level real-time updates.
    Handles live updates for task changes, comments, and assignments.
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.task_group_name = f'task_{self.task_id}'
        self.user = self.scope['user']

        # Reject if user is not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Check if user has access to this task
        has_access = await self.check_task_access()
        if not has_access:
            await self.close()
            return

        # Join task group
        await self.channel_layer.group_add(
            self.task_group_name,
            self.channel_name
        )

        # Accept connection
        await self.accept()

        # Send initial data
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to task updates',
            'task_id': self.task_id,
            'user_id': self.user.id
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave task group
        if hasattr(self, 'task_group_name'):
            await self.channel_layer.group_discard(
                self.task_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'typing':
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.task_group_name,
                    {
                        'type': 'user_typing',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'is_typing': data.get('is_typing', True)
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    # Event handlers
    async def task_updated(self, event):
        """Send task update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'task_updated',
            'task': event['task'],
            'updated_by': event.get('updated_by'),
            'changes': event.get('changes', {}),
            'timestamp': event['timestamp']
        }))

    async def comment_added(self, event):
        """Send comment added notification"""
        await self.send(text_data=json.dumps({
            'type': 'comment_added',
            'comment': event['comment'],
            'user': event['user'],
            'timestamp': event['timestamp']
        }))

    async def user_typing(self, event):
        """Send typing indicator"""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    async def task_assigned(self, event):
        """Send task assignment notification"""
        await self.send(text_data=json.dumps({
            'type': 'task_assigned',
            'task_id': event['task_id'],
            'assigned_to': event['assigned_to'],
            'assigned_by': event['assigned_by'],
            'timestamp': event['timestamp']
        }))

    # Database operations
    @database_sync_to_async
    def check_task_access(self):
        """Check if user has access to the task"""
        from .models import Task
        try:
            task = Task.objects.select_related('project').get(id=self.task_id)
            project = task.project
            # Check if user is project owner or member
            return (
                project.owner == self.user or
                self.user in project.team_members.all() or
                self.user.is_superuser
            )
        except Task.DoesNotExist:
            return False


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for user-level notifications.
    Handles real-time notification delivery.
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope['user']

        # Reject if user is not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return

        # Create user-specific group
        self.user_group_name = f'user_{self.user.id}'

        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        # Accept connection
        await self.accept()

        # Send initial data
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notifications',
            'user_id': self.user.id
        }))

        # Send unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave user group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif message_type == 'mark_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    # Event handlers
    async def new_notification(self, event):
        """Send new notification to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification'],
            'timestamp': event['timestamp']
        }))

    async def notification_read(self, event):
        """Send notification read status update"""
        await self.send(text_data=json.dumps({
            'type': 'notification_read',
            'notification_id': event['notification_id'],
            'timestamp': event['timestamp']
        }))

    # Database operations
    @database_sync_to_async
    def get_unread_count(self):
        """Get count of unread notifications"""
        from .models import Notification
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        from .models import Notification
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False
