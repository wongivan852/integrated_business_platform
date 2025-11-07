"""
Management command to initialize default integration providers
Usage: python manage.py init_integrations
"""

from django.core.management.base import BaseCommand
from project_management.models import IntegrationProvider


class Command(BaseCommand):
    help = 'Initialize default integration providers for third-party services'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Initializing integration providers...'))

        providers_data = [
            {
                'name': 'GitHub',
                'provider_type': 'github',
                'api_base_url': 'https://api.github.com',
                'oauth_authorize_url': 'https://github.com/login/oauth/authorize',
                'oauth_token_url': 'https://github.com/login/oauth/access_token',
                'description': 'Sync issues and pull requests with GitHub repositories',
                'config': {
                    'scopes': ['repo', 'read:org'],
                    'webhook_events': ['issues', 'pull_request', 'push'],
                }
            },
            {
                'name': 'Slack',
                'provider_type': 'slack',
                'api_base_url': 'https://slack.com/api',
                'oauth_authorize_url': 'https://slack.com/oauth/v2/authorize',
                'oauth_token_url': 'https://slack.com/api/oauth.v2.access',
                'description': 'Send notifications and receive commands via Slack',
                'config': {
                    'scopes': ['chat:write', 'channels:read', 'commands'],
                    'webhook_events': ['message.channels', 'app_mention'],
                }
            },
            {
                'name': 'Jira',
                'provider_type': 'jira',
                'api_base_url': 'https://your-domain.atlassian.net',
                'description': 'Bi-directional sync with Jira issues',
                'config': {
                    'auth_type': 'basic',
                    'api_version': 'v3',
                    'webhook_events': ['jira:issue_created', 'jira:issue_updated'],
                }
            },
            {
                'name': 'Google Calendar',
                'provider_type': 'google_calendar',
                'api_base_url': 'https://www.googleapis.com/calendar/v3',
                'oauth_authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'oauth_token_url': 'https://oauth2.googleapis.com/token',
                'description': 'Sync project milestones and deadlines with Google Calendar',
                'config': {
                    'scopes': ['https://www.googleapis.com/auth/calendar.events'],
                }
            },
            {
                'name': 'Outlook Calendar',
                'provider_type': 'outlook_calendar',
                'api_base_url': 'https://graph.microsoft.com/v1.0',
                'oauth_authorize_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'oauth_token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'description': 'Sync project milestones and deadlines with Outlook Calendar',
                'config': {
                    'scopes': ['Calendars.ReadWrite', 'offline_access'],
                }
            },
        ]

        created_count = 0
        updated_count = 0

        for provider_data in providers_data:
            provider, created = IntegrationProvider.objects.update_or_create(
                provider_type=provider_data['provider_type'],
                defaults={
                    'name': provider_data['name'],
                    'api_base_url': provider_data['api_base_url'],
                    'oauth_authorize_url': provider_data.get('oauth_authorize_url', ''),
                    'oauth_token_url': provider_data.get('oauth_token_url', ''),
                    'description': provider_data['description'],
                    'config': provider_data['config'],
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {provider.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  ↻ Updated: {provider.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Integration providers initialized successfully!'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f'   - Created: {created_count} providers')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   - Updated: {updated_count} providers')
        )

        # Display setup instructions
        self.stdout.write(
            self.style.NOTICE(
                '\n📝 Next Steps:\n'
                '   1. Configure OAuth credentials for each provider in the database\n'
                '   2. For GitHub: Create OAuth App at https://github.com/settings/developers\n'
                '   3. For Slack: Create App at https://api.slack.com/apps\n'
                '   4. For Jira: Generate API token at https://id.atlassian.com/manage-profile/security/api-tokens\n'
                '   5. For Google Calendar: Create OAuth Client at https://console.cloud.google.com/\n'
                '   6. For Outlook: Register app at https://portal.azure.com/\n'
            )
        )
