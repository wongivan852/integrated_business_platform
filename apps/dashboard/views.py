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
    Main dashboard showing all available applications
    """
    context = {
        'user': request.user,
        'apps': get_active_apps(),
        'platform_name': 'Krystal Business Platform',
        'company_name': 'CG Global Entertainment Ltd',
    }
    return render(request, 'dashboard/main.html', context)


@login_required
def app_launcher_view(request, app_key):
    """
    Launch an integrated app (opens in iframe or new tab)
    """
    from apps.app_integrations.registry import get_app_by_key

    app = get_app_by_key(app_key)
    if not app:
        return redirect('dashboard:main')

    context = {
        'app': app,
        'user': request.user,
    }
    return render(request, 'dashboard/app_launcher.html', context)
