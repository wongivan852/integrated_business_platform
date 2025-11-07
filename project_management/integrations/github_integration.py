"""
GitHub Integration Handler
Handles OAuth, webhooks, and issue synchronization with GitHub
"""

from .base import BaseIntegration, IntegrationError
from django.utils import timezone


class GitHubIntegration(BaseIntegration):
    """
    GitHub integration for syncing issues, pull requests, and commits.
    """

    def authenticate(self):
        """Authenticate with GitHub using OAuth token"""
        if not self.integration.access_token:
            return False

        try:
            # Verify token by getting user info
            response = self._make_request(
                'GET',
                'https://api.github.com/user'
            )

            if response.ok:
                from ..models import IntegrationLog
                IntegrationLog.log_action(
                    'auth',
                    self.provider,
                    'GitHub authentication successful',
                    integration=self.integration,
                    status='success'
                )
                return True

        except IntegrationError:
            pass

        return False

    def sync_tasks(self):
        """Sync issues from GitHub repository"""
        if not self.integration.external_id:
            raise IntegrationError('GitHub repository not configured')

        self.update_sync_status('syncing')

        try:
            # Get repository issues
            repo = self.integration.external_id
            response = self._make_request(
                'GET',
                f'https://api.github.com/repos/{repo}/issues',
                params={'state': 'all', 'per_page': 100}
            )

            issues = response.json()
            synced_count = 0

            for issue in issues:
                # Skip pull requests (they appear as issues in GitHub API)
                if 'pull_request' in issue:
                    continue

                self._sync_issue(issue)
                synced_count += 1

            self.update_sync_status('success')

            from ..models import IntegrationLog
            IntegrationLog.log_action(
                'sync',
                self.provider,
                f'Synced {synced_count} issues from GitHub',
                integration=self.integration,
                status='success',
                details={'synced_count': synced_count}
            )

            return synced_count

        except Exception as e:
            self.update_sync_status('error', str(e))
            raise IntegrationError(f'GitHub sync failed: {str(e)}')

    def _sync_issue(self, issue):
        """Sync a single GitHub issue to local task"""
        from ..models import Task, ExternalTaskMapping

        # Check if task already exists
        try:
            mapping = ExternalTaskMapping.objects.get(
                integration=self.integration,
                external_id=str(issue['id'])
            )
            task = mapping.task
        except ExternalTaskMapping.DoesNotExist:
            # Create new task
            task = Task(
                project=self.project,
                created_by=self.project.owner
            )

        # Update task fields
        task.title = issue['title']
        task.description = issue['body'] or ''
        task.status = 'completed' if issue['state'] == 'closed' else 'in_progress'

        # Map labels to priority
        labels = [label['name'].lower() for label in issue.get('labels', [])]
        if 'critical' in labels or 'urgent' in labels:
            task.priority = 'critical'
        elif 'high' in labels:
            task.priority = 'high'
        elif 'low' in labels:
            task.priority = 'low'
        else:
            task.priority = 'medium'

        task.save()

        # Create/update mapping
        self.create_external_task_mapping(
            task=task,
            external_id=str(issue['id']),
            external_key=f"#{issue['number']}",
            external_url=issue['html_url']
        )

        return task

    def process_webhook(self, payload, headers):
        """Process GitHub webhook"""
        from ..models import IntegrationWebhook

        # Verify signature
        signature = headers.get('X-Hub-Signature-256', '')
        if signature.startswith('sha256='):
            signature = signature[7:]

        if not self.verify_webhook_signature(payload, signature):
            raise IntegrationError('Invalid webhook signature')

        # Parse event
        event_type = headers.get('X-GitHub-Event', 'unknown')

        # Store webhook
        webhook = IntegrationWebhook.objects.create(
            integration=self.integration,
            provider=self.provider,
            event_type=event_type,
            payload=payload,
            headers=dict(headers)
        )

        # Process based on event type
        if event_type == 'issues':
            return self._process_issue_webhook(webhook)
        elif event_type == 'push':
            return self._process_push_webhook(webhook)

        webhook.processed = True
        webhook.save()

        return {'status': 'ignored', 'event': event_type}

    def _process_issue_webhook(self, webhook):
        """Process issue webhook event"""
        payload = webhook.payload
        action = payload.get('action', '')
        issue = payload.get('issue', {})

        webhook.event_action = action

        try:
            if action in ['opened', 'edited', 'reopened', 'closed']:
                task = self._sync_issue(issue)

                webhook.processed = True
                webhook.result = {
                    'task_id': task.id,
                    'task_title': task.title,
                    'action': action
                }
            else:
                webhook.processed = True
                webhook.result = {'status': 'ignored', 'action': action}

            webhook.processed_at = timezone.now()
            webhook.save()

            return webhook.result

        except Exception as e:
            webhook.processing_error = str(e)
            webhook.save()
            raise

    def _process_push_webhook(self, webhook):
        """Process push webhook event"""
        payload = webhook.payload

        # Extract commit information
        commits = payload.get('commits', [])
        ref = payload.get('ref', '')

        webhook.processed = True
        webhook.result = {
            'branch': ref.replace('refs/heads/', ''),
            'commit_count': len(commits),
            'pusher': payload.get('pusher', {}).get('name', 'unknown')
        }
        webhook.processed_at = timezone.now()
        webhook.save()

        return webhook.result
