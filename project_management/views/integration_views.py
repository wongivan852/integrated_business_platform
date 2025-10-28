"""
Integration Views for Phase 6.4
Handles webhook endpoints and integration management UI
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
import json
import logging

from ..models import (
    Project,
    IntegrationProvider,
    ProjectIntegration,
    IntegrationWebhook,
    IntegrationLog,
)
from ..integrations import (
    GitHubIntegration,
    SlackIntegration,
    JiraIntegration,
    IntegrationError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Webhook Handlers (CSRF Exempt - External Services)
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def github_webhook(request, integration_id):
    """
    Handle incoming GitHub webhooks.

    Webhook URL format: /integrations/webhooks/github/<integration_id>/
    """
    try:
        integration = get_object_or_404(
            ProjectIntegration,
            id=integration_id,
            provider__provider_type='github',
            is_active=True
        )

        # Get payload and headers
        payload_str = request.body.decode('utf-8')
        payload = json.loads(payload_str)
        headers = {
            'X-GitHub-Event': request.META.get('HTTP_X_GITHUB_EVENT', ''),
            'X-Hub-Signature-256': request.META.get('HTTP_X_HUB_SIGNATURE_256', ''),
        }

        # Process webhook
        handler = GitHubIntegration(integration)
        result = handler.process_webhook(payload, headers)

        logger.info(f"GitHub webhook processed for integration {integration_id}: {result}")

        return JsonResponse({
            'status': 'success',
            'message': 'Webhook processed successfully',
            'result': result
        })

    except IntegrationError as e:
        logger.error(f"GitHub webhook error for integration {integration_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

    except Exception as e:
        logger.exception(f"Unexpected error processing GitHub webhook {integration_id}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def slack_webhook(request, integration_id):
    """
    Handle incoming Slack webhooks and slash commands.

    Webhook URL format: /integrations/webhooks/slack/<integration_id>/
    """
    try:
        integration = get_object_or_404(
            ProjectIntegration,
            id=integration_id,
            provider__provider_type='slack',
            is_active=True
        )

        # Parse payload (Slack sends form-encoded data for slash commands)
        content_type = request.META.get('CONTENT_TYPE', '')

        if 'application/json' in content_type:
            payload = json.loads(request.body.decode('utf-8'))
        else:
            # Form-encoded (slash commands)
            payload = {key: value for key, value in request.POST.items()}

        headers = {
            'X-Slack-Signature': request.META.get('HTTP_X_SLACK_SIGNATURE', ''),
            'X-Slack-Request-Timestamp': request.META.get('HTTP_X_SLACK_REQUEST_TIMESTAMP', ''),
        }

        # Process webhook
        handler = SlackIntegration(integration)
        result = handler.process_webhook(payload, headers)

        logger.info(f"Slack webhook processed for integration {integration_id}: {result}")

        # Slack expects specific response format for slash commands
        if payload.get('command'):
            return JsonResponse(result)

        return JsonResponse({
            'status': 'success',
            'message': 'Webhook processed successfully'
        })

    except IntegrationError as e:
        logger.error(f"Slack webhook error for integration {integration_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

    except Exception as e:
        logger.exception(f"Unexpected error processing Slack webhook {integration_id}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def jira_webhook(request, integration_id):
    """
    Handle incoming Jira webhooks.

    Webhook URL format: /integrations/webhooks/jira/<integration_id>/
    """
    try:
        integration = get_object_or_404(
            ProjectIntegration,
            id=integration_id,
            provider__provider_type='jira',
            is_active=True
        )

        # Get payload and headers
        payload = json.loads(request.body.decode('utf-8'))
        headers = {
            'X-Jira-Event-Type': request.META.get('HTTP_X_JIRA_EVENT_TYPE', ''),
        }

        # Process webhook
        handler = JiraIntegration(integration)
        result = handler.process_webhook(payload, headers)

        logger.info(f"Jira webhook processed for integration {integration_id}: {result}")

        return JsonResponse({
            'status': 'success',
            'message': 'Webhook processed successfully',
            'result': result
        })

    except IntegrationError as e:
        logger.error(f"Jira webhook error for integration {integration_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

    except Exception as e:
        logger.exception(f"Unexpected error processing Jira webhook {integration_id}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


# ============================================================================
# Integration Management Views (Authenticated)
# ============================================================================

@login_required
def integration_list(request, project_id):
    """
    List all integrations for a project.
    """
    project = get_object_or_404(Project, id=project_id)

    # Check permission
    if not (project.owner == request.user or request.user in project.team_members.all()):
        return HttpResponseForbidden("You don't have permission to view this project's integrations")

    integrations = project.integrations.select_related('provider').all()
    available_providers = IntegrationProvider.objects.filter(is_active=True)

    context = {
        'project': project,
        'integrations': integrations,
        'available_providers': available_providers,
    }

    return render(request, 'project_management/integrations/list.html', context)


@login_required
@require_http_methods(["POST"])
def integration_create(request, project_id):
    """
    Create a new integration for a project.
    """
    project = get_object_or_404(Project, id=project_id)

    # Check permission - only owner can create integrations
    if project.owner != request.user:
        return HttpResponseForbidden("Only project owner can create integrations")

    provider_id = request.POST.get('provider_id')
    provider = get_object_or_404(IntegrationProvider, id=provider_id)

    # Create integration
    integration = ProjectIntegration.objects.create(
        project=project,
        provider=provider,
        created_by=request.user
    )

    messages.success(request, f'{provider.name} integration created successfully')

    # Redirect to configuration page
    return redirect('project_management:integration_configure',
                    project_id=project_id,
                    integration_id=integration.id)


@login_required
def integration_configure(request, project_id, integration_id):
    """
    Configure an integration (set tokens, external IDs, etc.)
    """
    project = get_object_or_404(Project, id=project_id)
    integration = get_object_or_404(ProjectIntegration, id=integration_id, project=project)

    # Check permission
    if project.owner != request.user:
        return HttpResponseForbidden("Only project owner can configure integrations")

    if request.method == 'POST':
        # Update integration settings
        integration.access_token = request.POST.get('access_token', '')
        integration.external_id = request.POST.get('external_id', '')
        integration.sync_enabled = request.POST.get('sync_enabled') == 'on'
        integration.sync_interval = int(request.POST.get('sync_interval', 300))

        # Update settings JSON
        settings = {}
        if request.POST.get('channel'):
            settings['default_channel'] = request.POST.get('channel')
        if request.POST.get('email'):
            settings['email'] = request.POST.get('email')
        integration.settings = settings

        integration.save()

        # Test authentication
        try:
            if integration.provider.provider_type == 'github':
                handler = GitHubIntegration(integration)
            elif integration.provider.provider_type == 'slack':
                handler = SlackIntegration(integration)
            elif integration.provider.provider_type == 'jira':
                handler = JiraIntegration(integration)
            else:
                handler = None

            if handler and handler.authenticate():
                messages.success(request, 'Integration configured and authenticated successfully')
            else:
                messages.warning(request, 'Integration saved but authentication failed. Check your credentials.')

        except IntegrationError as e:
            messages.error(request, f'Authentication error: {str(e)}')

        return redirect('project_management:integration_list', project_id=project_id)

    # Generate webhook URL
    webhook_url = request.build_absolute_uri(
        f'/integrations/webhooks/{integration.provider.provider_type}/{integration.id}/'
    )

    context = {
        'project': project,
        'integration': integration,
        'webhook_url': webhook_url,
    }

    return render(request, 'project_management/integrations/configure.html', context)


@login_required
@require_http_methods(["POST"])
def integration_sync(request, project_id, integration_id):
    """
    Manually trigger synchronization for an integration.
    """
    project = get_object_or_404(Project, id=project_id)
    integration = get_object_or_404(ProjectIntegration, id=integration_id, project=project)

    # Check permission
    if not (project.owner == request.user or request.user in project.team_members.all()):
        return HttpResponseForbidden("You don't have permission to sync this integration")

    try:
        # Get appropriate handler
        if integration.provider.provider_type == 'github':
            handler = GitHubIntegration(integration)
        elif integration.provider.provider_type == 'jira':
            handler = JiraIntegration(integration)
        else:
            messages.error(request, 'Sync not supported for this integration type')
            return redirect('project_management:integration_list', project_id=project_id)

        # Run sync
        synced_count = handler.sync_tasks()
        messages.success(request, f'Successfully synced {synced_count} tasks')

    except IntegrationError as e:
        messages.error(request, f'Sync failed: {str(e)}')

    return redirect('project_management:integration_list', project_id=project_id)


@login_required
@require_http_methods(["POST"])
def integration_delete(request, project_id, integration_id):
    """
    Delete an integration.
    """
    project = get_object_or_404(Project, id=project_id)
    integration = get_object_or_404(ProjectIntegration, id=integration_id, project=project)

    # Check permission - only owner can delete
    if project.owner != request.user:
        return HttpResponseForbidden("Only project owner can delete integrations")

    provider_name = integration.provider.name
    integration.delete()

    messages.success(request, f'{provider_name} integration deleted successfully')
    return redirect('project_management:integration_list', project_id=project_id)


@login_required
def integration_logs(request, project_id, integration_id):
    """
    View integration logs for debugging.
    """
    project = get_object_or_404(Project, id=project_id)
    integration = get_object_or_404(ProjectIntegration, id=integration_id, project=project)

    # Check permission
    if not (project.owner == request.user or request.user in project.team_members.all()):
        return HttpResponseForbidden("You don't have permission to view these logs")

    logs = integration.logs.order_by('-timestamp')[:100]
    webhooks = integration.webhooks.order_by('-received_at')[:50]

    context = {
        'project': project,
        'integration': integration,
        'logs': logs,
        'webhooks': webhooks,
    }

    return render(request, 'project_management/integrations/logs.html', context)
