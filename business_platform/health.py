"""
Health Check Views for Integrated Business Platform

Provides health check endpoints for Docker, Kubernetes, and monitoring systems.
"""

import time
import redis
from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_GET
def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if the application is running.

    URL: /health/
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'integrated_business_platform',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
    })


@csrf_exempt
@require_GET
def health_db(request):
    """
    Database health check.
    Tests database connectivity.

    URL: /health/db/
    """
    try:
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        response_time = (time.time() - start_time) * 1000  # ms

        return JsonResponse({
            'status': 'healthy',
            'service': 'database',
            'engine': settings.DATABASES['default']['ENGINE'],
            'response_time_ms': round(response_time, 2),
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'database',
            'error': str(e),
        }, status=503)


@csrf_exempt
@require_GET
def health_redis(request):
    """
    Redis health check.
    Tests Redis connectivity.

    URL: /health/redis/
    """
    redis_url = getattr(settings, 'REDIS_URL', None)

    if not redis_url:
        # Check environment variable
        import os
        redis_url = os.environ.get('REDIS_URL')

    if not redis_url:
        return JsonResponse({
            'status': 'not_configured',
            'service': 'redis',
            'message': 'Redis is not configured',
        })

    try:
        start_time = time.time()
        r = redis.from_url(redis_url)
        r.ping()
        response_time = (time.time() - start_time) * 1000  # ms

        return JsonResponse({
            'status': 'healthy',
            'service': 'redis',
            'response_time_ms': round(response_time, 2),
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'service': 'redis',
            'error': str(e),
        }, status=503)


@csrf_exempt
@require_GET
def health_full(request):
    """
    Full health check endpoint.
    Checks all services and returns detailed status.

    URL: /health/full/
    """
    health_status = {
        'status': 'healthy',
        'service': 'integrated_business_platform',
        'version': getattr(settings, 'APP_VERSION', '1.0.0'),
        'checks': {}
    }

    all_healthy = True

    # Check database
    try:
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        response_time = (time.time() - start_time) * 1000

        health_status['checks']['database'] = {
            'status': 'healthy',
            'response_time_ms': round(response_time, 2),
        }
    except Exception as e:
        all_healthy = False
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e),
        }

    # Check Redis (optional)
    import os
    redis_url = os.environ.get('REDIS_URL')

    if redis_url:
        try:
            start_time = time.time()
            r = redis.from_url(redis_url)
            r.ping()
            response_time = (time.time() - start_time) * 1000

            health_status['checks']['redis'] = {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
            }
        except Exception as e:
            # Redis is optional, so don't fail the overall health check
            health_status['checks']['redis'] = {
                'status': 'unhealthy',
                'error': str(e),
            }
    else:
        health_status['checks']['redis'] = {
            'status': 'not_configured',
        }

    # Check disk space (basic check)
    try:
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_percent = (free / total) * 100

        health_status['checks']['disk'] = {
            'status': 'healthy' if free_percent > 10 else 'warning',
            'free_percent': round(free_percent, 2),
            'free_gb': round(free / (1024**3), 2),
        }
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'error': str(e),
        }

    # Overall status
    if not all_healthy:
        health_status['status'] = 'degraded'

    return JsonResponse(health_status, status=200 if all_healthy else 503)


@csrf_exempt
@require_GET
def health_ready(request):
    """
    Kubernetes readiness probe endpoint.
    Returns 200 only if the application is ready to serve traffic.

    URL: /health/ready/
    """
    try:
        # Check database is accessible
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()

        return JsonResponse({
            'status': 'ready',
            'service': 'integrated_business_platform',
        })
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e),
        }, status=503)


@csrf_exempt
@require_GET
def health_live(request):
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if the application process is alive.

    URL: /health/live/
    """
    return JsonResponse({
        'status': 'alive',
        'service': 'integrated_business_platform',
    })


@csrf_exempt
@require_GET
def health_apps(request):
    """
    Check status of all registered apps.

    URL: /health/apps/
    """
    from django.apps import apps

    installed_apps = []
    for app_config in apps.get_app_configs():
        if not app_config.name.startswith('django.') and not app_config.name.startswith('rest_framework'):
            installed_apps.append({
                'name': app_config.name,
                'label': app_config.label,
                'verbose_name': str(app_config.verbose_name),
            })

    return JsonResponse({
        'status': 'healthy',
        'total_apps': len(installed_apps),
        'apps': installed_apps,
    })
