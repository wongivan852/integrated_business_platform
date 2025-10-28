"""
Slack Integration Handler
Handles notifications and slash commands for Slack
"""

from .base import BaseIntegration, IntegrationError
import json


class SlackIntegration(BaseIntegration):
    """
    Slack integration for sending notifications and handling slash commands.
    """

    def authenticate(self):
        """Authenticate with Slack using OAuth token"""
        if not self.integration.access_token:
            return False

        try:
            response = self._make_request(
                'GET',
                'https://slack.com/api/auth.test'
            )

            data = response.json()
            if data.get('ok'):
                from ..models import IntegrationLog
                IntegrationLog.log_action(
                    'auth',
                    self.provider,
                    f"Slack authentication successful for team {data.get('team', 'unknown')}",
                    integration=self.integration,
                    status='success'
                )
                return True

        except IntegrationError:
            pass

        return False

    def sync_tasks(self):
        """Slack doesn't have tasks to sync"""
        return 0

    def send_notification(self, channel, message, **kwargs):
        """
        Send a notification to a Slack channel.

        Args:
            channel: Slack channel ID or name
            message: Message text
            **kwargs: Additional Slack message parameters (blocks, attachments, etc.)

        Returns:
            dict: Slack API response
        """
        try:
            payload = {
                'channel': channel,
                'text': message,
                **kwargs
            }

            response = self._make_request(
                'POST',
                'https://slack.com/api/chat.postMessage',
                json=payload
            )

            data = response.json()

            if not data.get('ok'):
                raise IntegrationError(f"Slack API error: {data.get('error', 'unknown')}")

            from ..models import IntegrationLog
            IntegrationLog.log_action(
                'export',
                self.provider,
                f'Sent notification to {channel}',
                integration=self.integration,
                status='success',
                details={'channel': channel, 'message_preview': message[:100]}
            )

            return data

        except Exception as e:
            raise IntegrationError(f'Failed to send Slack notification: {str(e)}')

    def send_task_notification(self, task, action='created', channel=None):
        """
        Send a task notification to Slack.

        Args:
            task: Task model instance
            action: Action performed (created, updated, completed, etc.)
            channel: Override default channel

        Returns:
            dict: Slack API response
        """
        if channel is None:
            channel = self.integration.settings.get('default_channel', '#general')

        # Format message with blocks for better presentation
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Task {action.capitalize()}: {task.title}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Project:*\n{self.project.name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{task.get_status_display()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority:*\n{task.get_priority_display()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Assignee:*\n{task.assignee.username if task.assignee else 'Unassigned'}"
                    }
                ]
            }
        ]

        if task.description:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{task.description[:200]}..."
                }
            })

        # Add task URL button
        task_url = f"{self.integration.settings.get('base_url', '')}/projects/tasks/{task.id}/"
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Task"
                    },
                    "url": task_url
                }
            ]
        })

        return self.send_notification(
            channel=channel,
            message=f"Task {action}: {task.title}",
            blocks=blocks
        )

    def process_webhook(self, payload, headers):
        """Process Slack webhook/slash command"""
        from ..models import IntegrationWebhook

        # Slack sends JSON in body for slash commands
        if isinstance(payload, dict):
            event_type = payload.get('type', 'slash_command')
        else:
            event_type = 'unknown'

        # Store webhook
        webhook = IntegrationWebhook.objects.create(
            integration=self.integration,
            provider=self.provider,
            event_type=event_type,
            payload=payload,
            headers=dict(headers)
        )

        # Process slash command
        if 'command' in payload:
            return self._process_slash_command(webhook, payload)

        # Process event
        if event_type == 'url_verification':
            # Slack URL verification
            return {'challenge': payload.get('challenge')}

        webhook.processed = True
        webhook.save()

        return {'status': 'ok'}

    def _process_slash_command(self, webhook, payload):
        """Process Slack slash command"""
        command = payload.get('command', '')
        text = payload.get('text', '').strip()
        user_name = payload.get('user_name', 'unknown')

        webhook.event_action = command
        webhook.processed = True

        # Example: /task list
        if command == '/task':
            if text == 'list':
                tasks = self.project.tasks.filter(status__in=['pending', 'in_progress'])[:5]

                response_text = f"*Recent Tasks for {self.project.name}:*\n\n"
                for task in tasks:
                    response_text += f"• {task.title} ({task.get_status_display()})\n"

                webhook.result = {'response': response_text}
                webhook.save()

                return {
                    'response_type': 'ephemeral',
                    'text': response_text
                }

        webhook.result = {'response': f'Unknown command: {command} {text}'}
        webhook.save()

        return {
            'response_type': 'ephemeral',
            'text': f'Command received: {command} {text}'
        }

    def _get_auth_headers(self):
        """Override to use Slack's Bearer token format"""
        headers = {}
        if self.integration.access_token:
            headers['Authorization'] = f'Bearer {self.integration.access_token}'
            headers['Content-Type'] = 'application/json; charset=utf-8'
        return headers
