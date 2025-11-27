"""
Dashboard views for the integrated business platform.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from authentication.models import ApplicationConfig, UserSession
from sso.utils import SSOTokenManager
from urllib.parse import urljoin


@login_required
def home(request):
    """
    Main dashboard home page showing available applications.
    """
    user = request.user

    # Get available applications for the user
    available_apps = ApplicationConfig.objects.filter(
        is_active=True
    ).order_by('display_name')

    # Filter apps based on user access
    if not user.is_superuser:
        available_apps = available_apps.filter(
            name__in=user.apps_access
        )

    # Get recent user sessions
    recent_sessions = UserSession.objects.filter(
        user=user
    ).order_by('-last_activity')[:5]

    context = {
        'page_title': _('Dashboard'),
        'available_apps': available_apps,
        'recent_sessions': recent_sessions,
        'user': user,
    }

    return render(request, 'dashboard/home.html', context)


@login_required
def sso_redirect(request, app_name):
    """
    Generate SSO token and redirect to external application.
    """
    try:
        # Get application configuration
        app_config = ApplicationConfig.objects.get(name=app_name, is_active=True)
        
        # Check if user has access
        if not request.user.is_superuser and app_name not in request.user.apps_access:
            return HttpResponse('Access denied', status=403)
        
        # Generate SSO token
        tokens = SSOTokenManager.generate_token(request.user, request)
        
        # Build redirect URL with token
        redirect_url = f"{app_config.url}?sso_token={tokens['access']}"
        
        return redirect(redirect_url)
        
    except ApplicationConfig.DoesNotExist:
        return HttpResponse('Application not found', status=404)
    except Exception as e:
        return HttpResponse(f'SSO Error: {str(e)}', status=500)
