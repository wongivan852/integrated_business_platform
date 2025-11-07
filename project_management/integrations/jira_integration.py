"""
Jira Integration Handler
Handles issue synchronization with Jira
"""

from .base import BaseIntegration, IntegrationError
from django.utils import timezone


class JiraIntegration(BaseIntegration):
    """
    Jira integration for bi-directional issue synchronization.
    """

    def authenticate(self):
        """Authenticate with Jira using API token"""
        if not self.integration.access_token:
            return False

        try:
            # Verify credentials by getting server info
            response = self._make_request(
                'GET',
                f'{self.provider.api_base_url}/rest/api/3/serverInfo'
            )

            if response.ok:
                from ..models import IntegrationLog
                IntegrationLog.log_action(
                    'auth',
                    self.provider,
                    'Jira authentication successful',
                    integration=self.integration,
                    status='success'
                )
                return True

        except IntegrationError:
            pass

        return False

    def sync_tasks(self):
        """Sync issues from Jira project"""
        if not self.integration.external_id:
            raise IntegrationError('Jira project key not configured')

        self.update_sync_status('syncing')

        try:
            # Get project issues
            project_key = self.integration.external_id
            jql = f'project = {project_key} ORDER BY updated DESC'

            response = self._make_request(
                'GET',
                f'{self.provider.api_base_url}/rest/api/3/search',
                params={
                    'jql': jql,
                    'maxResults': 100,
                    'fields': 'summary,description,status,priority,assignee,updated'
                }
            )

            data = response.json()
            issues = data.get('issues', [])
            synced_count = 0

            for issue in issues:
                self._sync_issue(issue)
                synced_count += 1

            self.update_sync_status('success')

            from ..models import IntegrationLog
            IntegrationLog.log_action(
                'sync',
                self.provider,
                f'Synced {synced_count} issues from Jira',
                integration=self.integration,
                status='success',
                details={'synced_count': synced_count}
            )

            return synced_count

        except Exception as e:
            self.update_sync_status('error', str(e))
            raise IntegrationError(f'Jira sync failed: {str(e)}')

    def _sync_issue(self, issue):
        """Sync a single Jira issue to local task"""
        from ..models import Task, ExternalTaskMapping

        issue_id = issue['id']
        issue_key = issue['key']
        fields = issue['fields']

        # Check if task already exists
        try:
            mapping = ExternalTaskMapping.objects.get(
                integration=self.integration,
                external_id=issue_id
            )
            task = mapping.task
        except ExternalTaskMapping.DoesNotExist:
            # Create new task
            task = Task(
                project=self.project,
                created_by=self.project.owner
            )

        # Update task fields
        task.title = fields.get('summary', 'Untitled')
        task.description = fields.get('description', '')

        # Map status
        status_name = fields.get('status', {}).get('name', '')
        task.status = self.map_status(status_name)

        # Map priority
        priority = fields.get('priority', {})
        if priority:
            priority_name = priority.get('name', 'Medium')
            task.priority = self.map_priority(priority_name)

        task.save()

        # Create/update mapping
        jira_url = f"{self.provider.api_base_url}/browse/{issue_key}"
        self.create_external_task_mapping(
            task=task,
            external_id=issue_id,
            external_key=issue_key,
            external_url=jira_url
        )

        return task

    def export_task(self, task):
        """
        Export local task to Jira as an issue.

        Args:
            task: Task model instance

        Returns:
            dict: Created Jira issue data
        """
        try:
            # Prepare issue data
            issue_data = {
                'fields': {
                    'project': {
                        'key': self.integration.external_id
                    },
                    'summary': task.title,
                    'description': {
                        'type': 'doc',
                        'version': 1,
                        'content': [
                            {
                                'type': 'paragraph',
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': task.description or 'No description'
                                    }
                                ]
                            }
                        ]
                    },
                    'issuetype': {
                        'name': 'Task'
                    },
                    'priority': {
                        'name': self._get_jira_priority(task.priority)
                    }
                }
            }

            response = self._make_request(
                'POST',
                f'{self.provider.api_base_url}/rest/api/3/issue',
                json=issue_data
            )

            jira_issue = response.json()

            # Create mapping
            issue_key = jira_issue['key']
            issue_id = jira_issue['id']
            jira_url = f"{self.provider.api_base_url}/browse/{issue_key}"

            self.create_external_task_mapping(
                task=task,
                external_id=issue_id,
                external_key=issue_key,
                external_url=jira_url
            )

            from ..models import IntegrationLog
            IntegrationLog.log_action(
                'export',
                self.provider,
                f'Exported task "{task.title}" to Jira as {issue_key}',
                integration=self.integration,
                status='success',
                details={'task_id': task.id, 'jira_key': issue_key}
            )

            return jira_issue

        except Exception as e:
            raise IntegrationError(f'Failed to export task to Jira: {str(e)}')

    def _get_jira_priority(self, internal_priority):
        """Map internal priority to Jira priority"""
        priority_map = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High',
            'critical': 'Highest'
        }
        return priority_map.get(internal_priority, 'Medium')

    def process_webhook(self, payload, headers):
        """Process Jira webhook"""
        from ..models import IntegrationWebhook

        event_type = payload.get('webhookEvent', 'unknown')

        # Store webhook
        webhook = IntegrationWebhook.objects.create(
            integration=self.integration,
            provider=self.provider,
            event_type=event_type,
            payload=payload,
            headers=dict(headers)
        )

        # Process based on event type
        if event_type.startswith('jira:issue_'):
            return self._process_issue_webhook(webhook)

        webhook.processed = True
        webhook.save()

        return {'status': 'ignored', 'event': event_type}

    def _process_issue_webhook(self, webhook):
        """Process Jira issue webhook"""
        payload = webhook.payload
        event_type = payload.get('webhookEvent', '')

        webhook.event_action = event_type.replace('jira:issue_', '')

        try:
            if event_type in ['jira:issue_created', 'jira:issue_updated']:
                issue = payload.get('issue', {})
                if issue:
                    task = self._sync_issue(issue)

                    webhook.processed = True
                    webhook.result = {
                        'task_id': task.id,
                        'task_title': task.title,
                        'event': event_type
                    }
                    webhook.processed_at = timezone.now()

            else:
                webhook.processed = True
                webhook.result = {'status': 'ignored', 'event': event_type}
                webhook.processed_at = timezone.now()

            webhook.save()
            return webhook.result

        except Exception as e:
            webhook.processing_error = str(e)
            webhook.save()
            raise

    def _get_auth_headers(self):
        """Override to use Jira's Basic Auth"""
        import base64
        headers = {}

        if self.integration.access_token:
            # Jira uses email:api_token format
            credentials = self.integration.access_token
            if ':' not in credentials:
                # If only token provided, use configured email
                email = self.integration.settings.get('email', 'user@example.com')
                credentials = f'{email}:{credentials}'

            # Encode credentials
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded}'
            headers['Content-Type'] = 'application/json'

        return headers
