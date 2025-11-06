"""
Dashboard views for Integrated Business Platform
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.app_integrations.registry import get_active_apps


def home_view(request):
    """
    Main landing page showing platform overview
    """
    if request.user.is_authenticated:
        return redirect('dashboard:main')

    context = {
        'platform_name': 'Krystal Business Platform',
        'company_name': 'CG Global Entertainment Ltd',
    }
    return render(request, 'home.html', context)


@login_required
def dashboard_view(request):
    """
    Main dashboard showing available applications based on user permissions
    """
    from core.models import UserAppAccess
    from apps.app_integrations.registry import INTEGRATED_APPS
    from authentication.models import ApplicationConfig

    # Get all active apps
    all_apps = get_active_apps()

    # Get featured app names from ApplicationConfig
    featured_app_names = set(
        ApplicationConfig.objects.filter(
            is_active=True,
            is_featured=True
        ).values_list('name', flat=True)
    )

    # Filter apps based on user permissions
    if request.user.is_superuser:
        # Superuser can see all apps
        permitted_apps = all_apps
    else:
        # Get user's permitted app codes
        user_accesses = UserAppAccess.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(role='none').values_list('app_code', flat=True)

        permitted_app_codes = set(user_accesses)

        # Filter apps
        permitted_apps = []
        for app in all_apps:
            app_key = next((k for k, v in INTEGRATED_APPS.items() if v == app), None)
            if app_key and app_key in permitted_app_codes:
                permitted_apps.append(app)

    # Separate featured and regular apps
    featured_apps = []
    regular_apps = []
    for app in permitted_apps:
        # Check if app name is in featured list
        if app.get('name') in featured_app_names:
            featured_apps.append(app)
        else:
            regular_apps.append(app)

    context = {
        'user': request.user,
        'apps': permitted_apps,
        'featured_apps': featured_apps,
        'regular_apps': regular_apps,
        'total_apps': len(all_apps),
        'permitted_apps_count': len(permitted_apps),
        'platform_name': 'Krystal Business Platform',
        'company_name': 'CG Global Entertainment Ltd',
    }
    return render(request, 'dashboard/main.html', context)


@login_required
def app_launcher_view(request, app_key):
    """
    Launch an integrated app with SSO token
    """
    from apps.app_integrations.registry import get_app_by_key, INTEGRATED_APPS
    from core.models import UserAppAccess, AppAccessAuditLog
    from sso.utils import SSOTokenManager
    from django.contrib import messages

    app = get_app_by_key(app_key)
    if not app:
        messages.error(request, "Application not found")
        return redirect('dashboard:main')

    # Check user permission
    has_access = False
    user_role = 'none'

    if request.user.is_superuser:
        has_access = True
        user_role = 'admin'
    else:
        try:
            access = UserAppAccess.objects.get(
                user=request.user,
                app_code=app_key,
                is_active=True
            )
            if access.role != 'none':
                has_access = True
                user_role = access.role
        except UserAppAccess.DoesNotExist:
            pass

    if not has_access:
        # Log access denied
        AppAccessAuditLog.log_change(
            user=request.user,
            app_code=app_key,
            action='access_denied',
            request=request
        )
        messages.error(request, f"You don't have permission to access {app['name']}")
        return redirect('dashboard:main')

    # Generate SSO token
    tokens = SSOTokenManager.generate_token(request.user, request)

    # Log successful app access
    AppAccessAuditLog.log_change(
        user=request.user,
        app_code=app_key,
        action='permission_checked',
        new_value={'role': user_role, 'access_granted': True},
        request=request
    )

    context = {
        'app': app,
        'app_key': app_key,
        'user': request.user,
        'sso_token': tokens['access'],
        'user_role': user_role,
    }
    return render(request, 'dashboard/app_launcher.html', context)
