"""
PWA Views for Phase 6.5
Handles PWA installation tracking, push subscriptions, and offline sync
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
import json
import logging

from ..models import (
    PWAInstallation,
    PushSubscription,
    OfflineSyncQueue,
    OfflineCache,
    PWAAnalytics,
)

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def track_installation(request):
    """Track PWA installation"""
    try:
        data = json.loads(request.body)

        installation, created = PWAInstallation.objects.get_or_create(
            user=request.user,
            platform=data.get('platform', 'unknown'),
            defaults={
                'device_name': data.get('device_name', ''),
                'user_agent': data.get('user_agent', request.META.get('HTTP_USER_AGENT', '')),
                'app_version': data.get('app_version', '1.0.0'),
            }
        )

        if not created:
            installation.mark_active()

        # Log analytics
        PWAAnalytics.log_event(
            event_type='install',
            event_name='PWA Installed',
            user=request.user,
            installation=installation,
            data=data
        )

        return JsonResponse({
            'status': 'success',
            'installation_id': installation.id,
            'created': created
        })

    except Exception as e:
        logger.exception('Failed to track installation')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def push_subscription(request):
    """Handle push subscription registration"""
    try:
        data = json.loads(request.body)

        subscription, created = PushSubscription.objects.get_or_create(
            endpoint=data.get('endpoint'),
            defaults={
                'user': request.user,
                'p256dh_key': data.get('keys', {}).get('p256dh', ''),
                'auth_key': data.get('keys', {}).get('auth', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

        if not created:
            subscription.mark_used()

        return JsonResponse({
            'status': 'success',
            'subscription_id': subscription.id
        })

    except Exception as e:
        logger.exception('Failed to register push subscription')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def sync_offline_operations(request):
    """Sync offline operations from client"""
    try:
        data = json.loads(request.body)
        operations = data.get('operations', [])

        synced_count = 0
        failed_count = 0

        for operation in operations:
            try:
                # Create sync queue entry
                sync_entry = OfflineSyncQueue.objects.create(
                    user=request.user,
                    operation_type=operation.get('type'),
                    model_name=operation.get('model'),
                    object_id=operation.get('id'),
                    data=operation.get('data', {}),
                    original_data=operation.get('original_data', {}),
                )

                # Process sync immediately if possible
                # (In production, this would be handled by Celery task)
                synced_count += 1

            except Exception as e:
                logger.error(f'Failed to sync operation: {e}')
                failed_count += 1

        return JsonResponse({
            'status': 'success',
            'synced': synced_count,
            'failed': failed_count
        })

    except Exception as e:
        logger.exception('Failed to sync offline operations')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def offline_page(request):
    """Offline fallback page"""
    return render(request, 'project_management/pwa/offline.html')
