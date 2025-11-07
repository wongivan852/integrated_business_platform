"""
Dashboard views for the integrated business platform.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from authentication.models import ApplicationConfig, UserSession


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
