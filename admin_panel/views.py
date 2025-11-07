"""
Admin Panel Views for User and App Access Management
Updated for current authentication system
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from authentication.models import CompanyUser, ApplicationConfig


def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard"""
    total_users = CompanyUser.objects.filter(is_active=True).count()
    total_apps = ApplicationConfig.objects.filter(is_active=True).count()

    # Count total access grants (users with non-empty apps_access)
    total_access_grants = sum(
        len(user.apps_access) for user in CompanyUser.objects.all() if user.apps_access
    )

    context = {
        'total_users': total_users,
        'total_apps': total_apps,
        'total_access_grants': total_access_grants,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def user_list(request):
    """List all users with filter and search"""
    users = CompanyUser.objects.all().order_by('-date_joined')

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            email__icontains=search_query
        ) | users.filter(
            first_name__icontains=search_query
        ) | users.filter(
            last_name__icontains=search_query
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    context = {
        'users': users,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/user_list.html', context)


@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    """View and edit user details and app access"""
    user = get_object_or_404(CompanyUser, id=user_id)

    # Get all apps
    all_apps = ApplicationConfig.objects.filter(is_active=True).order_by('display_name')

    # Combine with user access info
    apps_with_access = []
    for app in all_apps:
        has_access = app.name in user.apps_access
        apps_with_access.append({
            'key': app.name,
            'name': app.display_name,
            'description': app.description,
            'icon': app.icon,
            'color': app.color,
            'has_access': has_access,
        })

    context = {
        'user': user,
        'apps': apps_with_access,
    }
    return render(request, 'admin_panel/user_detail.html', context)


@login_required
@user_passes_test(is_admin)
def app_access_matrix(request):
    """
    Matrix view showing all users and their access to all apps.
    Grid format: rows = users, columns = apps
    """
    # Get all active users
    users = CompanyUser.objects.filter(is_active=True).order_by('last_name', 'first_name')

    # Get all active apps in alphabetical order
    apps = ApplicationConfig.objects.filter(is_active=True).order_by('display_name')

    # Build matrix data - create list of access status for each app in same order as apps list
    matrix_data = []
    for user in users:
        access_list = []
        for app in apps:
            access_list.append({
                'app_name': app.name,
                'has_access': app.name in user.apps_access
            })
        matrix_data.append({
            'user': user,
            'access_list': access_list
        })

    context = {
        'users': users,
        'apps': apps,
        'matrix_data': matrix_data,
    }
    return render(request, 'admin_panel/app_access_matrix.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def toggle_app_access(request, user_id, app_name):
    """
    Toggle user access to a specific app.
    AJAX endpoint for matrix interface.
    """
    try:
        user = get_object_or_404(CompanyUser, id=user_id)
        app = get_object_or_404(ApplicationConfig, name=app_name)

        if app.name in user.apps_access:
            # Remove access
            user.remove_app_access(app.name)
            has_access = False
            action = 'removed'
        else:
            # Grant access
            user.add_app_access(app.name)
            has_access = True
            action = 'granted'

        return JsonResponse({
            'success': True,
            'has_access': has_access,
            'action': action,
            'message': f'Access {action} successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def grant_all_apps_access(request, user_id):
    """Grant user access to all active apps"""
    try:
        user = get_object_or_404(CompanyUser, id=user_id)
        apps = ApplicationConfig.objects.filter(is_active=True)

        user.apps_access = [app.name for app in apps]
        user.save()

        messages.success(request, f'Granted {user.get_display_name()} access to all {apps.count()} apps')
        return redirect('admin_panel:user_detail', user_id=user_id)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:user_detail', user_id=user_id)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def revoke_all_apps_access(request, user_id):
    """Revoke user access from all apps"""
    try:
        user = get_object_or_404(CompanyUser, id=user_id)

        user.apps_access = []
        user.save()

        messages.success(request, f'Revoked all app access for {user.get_display_name()}')
        return redirect('admin_panel:user_detail', user_id=user_id)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:user_detail', user_id=user_id)
