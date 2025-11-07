"""
URL Configuration for Phase 6.4 Third-Party Integrations
Includes webhook endpoints and integration management
"""

from django.urls import path
from ..views.integration_views import (
    # Webhook handlers (CSRF exempt)
    github_webhook,
    slack_webhook,
    jira_webhook,

    # Integration management
    integration_list,
    integration_create,
    integration_configure,
    integration_sync,
    integration_delete,
    integration_logs,
)

app_name = 'integrations'

urlpatterns = [
    # ========================================================================
    # Webhook Endpoints (CSRF Exempt - for external services)
    # ========================================================================

    # GitHub webhooks
    path(
        'webhooks/github/<int:integration_id>/',
        github_webhook,
        name='webhook_github'
    ),

    # Slack webhooks and slash commands
    path(
        'webhooks/slack/<int:integration_id>/',
        slack_webhook,
        name='webhook_slack'
    ),

    # Jira webhooks
    path(
        'webhooks/jira/<int:integration_id>/',
        jira_webhook,
        name='webhook_jira'
    ),

    # ========================================================================
    # Integration Management UI (Authenticated)
    # ========================================================================

    # List all integrations for a project
    path(
        'project/<int:project_id>/',
        integration_list,
        name='integration_list'
    ),

    # Create new integration
    path(
        'project/<int:project_id>/create/',
        integration_create,
        name='integration_create'
    ),

    # Configure integration
    path(
        'project/<int:project_id>/<int:integration_id>/configure/',
        integration_configure,
        name='integration_configure'
    ),

    # Manually trigger sync
    path(
        'project/<int:project_id>/<int:integration_id>/sync/',
        integration_sync,
        name='integration_sync'
    ),

    # Delete integration
    path(
        'project/<int:project_id>/<int:integration_id>/delete/',
        integration_delete,
        name='integration_delete'
    ),

    # View logs
    path(
        'project/<int:project_id>/<int:integration_id>/logs/',
        integration_logs,
        name='integration_logs'
    ),
]


"""
URL Pattern Documentation
=========================

Webhook Endpoints (External Services):
--------------------------------------
POST /integrations/webhooks/github/<integration_id>/
    - Receives GitHub webhooks (issues, PRs, push events)
    - CSRF exempt
    - Verifies signature with X-Hub-Signature-256

POST /integrations/webhooks/slack/<integration_id>/
    - Receives Slack events and slash commands
    - CSRF exempt
    - Verifies signature with X-Slack-Signature

POST /integrations/webhooks/jira/<integration_id>/
    - Receives Jira webhooks (issue events)
    - CSRF exempt
    - Verifies signature (optional)


Integration Management (Authenticated Users):
---------------------------------------------
GET  /integrations/project/<project_id>/
    - List all integrations for a project
    - Shows connection status, last sync time
    - Available to project members

POST /integrations/project/<project_id>/create/
    - Create new integration
    - Only available to project owner
    - Requires provider selection

GET  /integrations/project/<project_id>/<integration_id>/configure/
POST /integrations/project/<project_id>/<integration_id>/configure/
    - Configure integration settings
    - Set access tokens, external IDs, sync preferences
    - Only available to project owner
    - Shows webhook URL for setup

POST /integrations/project/<project_id>/<integration_id>/sync/
    - Manually trigger synchronization
    - Available to project members
    - Returns sync results (count of items synced)

POST /integrations/project/<project_id>/<integration_id>/delete/
    - Delete integration
    - Only available to project owner
    - Also deletes related webhooks and logs

GET  /integrations/project/<project_id>/<integration_id>/logs/
    - View integration logs and webhook history
    - Available to project members
    - Shows last 100 log entries and 50 webhooks


Setting Up Integrations:
-------------------------

GitHub:
1. Create GitHub OAuth App or Personal Access Token
2. Configure webhook in GitHub repo settings
3. Set webhook URL to: https://yourdomain.com/integrations/webhooks/github/<integration_id>/
4. Set content type to: application/json
5. Select events: Issues, Pull requests (optional)
6. Add webhook secret for signature verification

Slack:
1. Create Slack App at api.slack.com
2. Add Bot Token Scopes: chat:write, channels:read
3. Install app to workspace
4. Copy Bot User OAuth Token
5. Set up slash command (optional):
   - Command: /task
   - Request URL: https://yourdomain.com/integrations/webhooks/slack/<integration_id>/
6. Subscribe to events (optional): message.channels

Jira:
1. Generate API token at id.atlassian.com/manage-profile/security/api-tokens
2. Format credentials as: email:api_token
3. Configure webhook in Jira project settings
4. Set webhook URL to: https://yourdomain.com/integrations/webhooks/jira/<integration_id>/
5. Select events: Issue created, Issue updated
6. No signature verification by default (Jira doesn't provide it)


Example Usage:
--------------

# Create GitHub integration
1. Navigate to: /integrations/project/1/
2. Click "Add Integration" → Select "GitHub"
3. Configure:
   - Access Token: ghp_xxxxxxxxxxxxxxxxxxxx
   - External ID: owner/repository (e.g., "myorg/myrepo")
   - Sync Enabled: Yes
   - Sync Interval: 300 seconds
4. Copy webhook URL and add to GitHub repo settings
5. Click "Save & Test Connection"

# Manual sync
POST /integrations/project/1/5/sync/
Response: "Successfully synced 15 tasks"

# View logs
GET /integrations/project/1/5/logs/
Shows API calls, sync results, webhook events


Security Notes:
---------------
- Webhook endpoints are CSRF exempt (required for external services)
- All webhooks verify signatures when provided
- Integration management requires authentication
- Only project owners can create/delete/configure integrations
- Project members can trigger sync and view logs
- Access tokens should be stored encrypted in production
- Use HTTPS in production for webhook URLs
"""
