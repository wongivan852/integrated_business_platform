"""
Admin Panel Views for User and App Access Management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model

from core.models import UserAppAccess, AppAccessAuditLog
from apps.app_integrations.registry import INTEGRATED_APPS, get_all_apps

User = get_user_model()


def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard"""
    total_users = User.objects.filter(is_active=True).count()
    total_apps = len(INTEGRATED_APPS)
    total_access_grants = UserAppAccess.objects.filter(is_active=True).count()
    recent_audit_logs = AppAccessAuditLog.objects.all()[:10]

    context = {
        'total_users': total_users,
        'total_apps': total_apps,
        'total_access_grants': total_access_grants,
        'recent_audit_logs': recent_audit_logs,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def user_list(request):
    """List all users with filter and search"""
    users = User.objects.all().order_by('-date_joined')

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
    user = get_object_or_404(User, id=user_id)

    # Get all apps
    all_apps = get_all_apps()

    # Get user's current app access
    user_access = {}
    for access in UserAppAccess.objects.filter(user=user, is_active=True):
        user_access[access.app_code] = access.role

    # Combine with app info
    apps_with_access = []
    for app in all_apps:
        app_key = next((k for k, v in INTEGRATED_APPS.items() if v == app), None)
        if app_key:
            apps_with_access.append({
                'key': app_key,
                'name': app['name'],
                'description': app['description'],
                'icon': app['icon'],
                'color': app['color'],
                'role': user_access.get(app_key, 'none'),
            })

    # Get audit logs for this user
    audit_logs = AppAccessAuditLog.objects.filter(user=user).order_by('-created_at')[:20]

    context = {
        'user_obj': user,
        'apps_with_access': apps_with_access,
        'audit_logs': audit_logs,
    }
    return render(request, 'admin_panel/user_detail.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_user_app_access(request, user_id):
    """Update user's app access via AJAX"""
    user = get_object_or_404(User, id=user_id)
    app_code = request.POST.get('app_code')
    role = request.POST.get('role', 'none')

    if not app_code or app_code not in INTEGRATED_APPS:
        return JsonResponse({'success': False, 'error': 'Invalid app code'}, status=400)

    if role not in ['none', 'employee', 'manager', 'admin']:
        return JsonResponse({'success': False, 'error': 'Invalid role'}, status=400)

    try:
        with transaction.atomic():
            # Get or create UserAppAccess
            access, created = UserAppAccess.objects.get_or_create(
                user=user,
                app_code=app_code,
                defaults={
                    'role': role,
                    'is_active': role != 'none',
                    'granted_by': request.user,
                }
            )

            old_role = access.role if not created else 'none'

            if not created:
                # Update existing access
                access.role = role
                access.is_active = role != 'none'
                access.modified_by = request.user
                access.save()

            # Log the change
            AppAccessAuditLog.log_change(
                user=user,
                app_code=app_code,
                action='access_granted' if role != 'none' else 'access_revoked',
                old_value={'role': old_role},
                new_value={'role': role},
                modified_by=request.user,
                request=request
            )

        app_name = INTEGRATED_APPS[app_code]['name']
        if role != 'none':
            messages.success(request, f"Granted {role} access to {app_name} for {user.email}")
        else:
            messages.success(request, f"Revoked access to {app_name} for {user.email}")

        return JsonResponse({
            'success': True,
            'role': role,
            'app_name': app_name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
def app_access_matrix(request):
    """View app access matrix - all users and their access to all apps"""
    users = User.objects.filter(is_active=True).order_by('email')
    apps = get_all_apps()

    # Build matrix
    matrix = []
    for user in users:
        user_access = {}
        for access in UserAppAccess.objects.filter(user=user, is_active=True):
            user_access[access.app_code] = access.role

        user_row = {
            'user': user,
            'accesses': []
        }

        for app in apps:
            app_key = next((k for k, v in INTEGRATED_APPS.items() if v == app), None)
            if app_key:
                user_row['accesses'].append({
                    'app_key': app_key,
                    'app_name': app['name'],
                    'role': user_access.get(app_key, 'none'),
                })

        matrix.append(user_row)

    context = {
        'matrix': matrix,
        'apps': apps,
    }
    return render(request, 'admin_panel/app_access_matrix.html', context)


@login_required
@user_passes_test(is_admin)
def audit_logs(request):
    """View all audit logs with filtering"""
    logs = AppAccessAuditLog.objects.all().order_by('-created_at')

    # Filter by action
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)

    # Filter by app
    app_filter = request.GET.get('app', '')
    if app_filter:
        logs = logs.filter(app_code=app_filter)

    # Filter by user
    user_filter = request.GET.get('user', '')
    if user_filter:
        logs = logs.filter(user__email__icontains=user_filter)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'app_filter': app_filter,
        'user_filter': user_filter,
        'action_choices': AppAccessAuditLog.ACTION_CHOICES,
        'apps': INTEGRATED_APPS,
    }
    return render(request, 'admin_panel/audit_logs.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def bulk_grant_access(request):
    """Bulk grant access to multiple users"""
    user_ids = request.POST.getlist('user_ids[]')
    app_code = request.POST.get('app_code')
    role = request.POST.get('role', 'employee')

    if not user_ids or not app_code or app_code not in INTEGRATED_APPS:
        return JsonResponse({'success': False, 'error': 'Invalid parameters'}, status=400)

    try:
        with transaction.atomic():
            granted_count = 0
            for user_id in user_ids:
                user = User.objects.get(id=user_id)

                access, created = UserAppAccess.objects.get_or_create(
                    user=user,
                    app_code=app_code,
                    defaults={
                        'role': role,
                        'is_active': True,
                        'granted_by': request.user,
                    }
                )

                if not created:
                    access.role = role
                    access.is_active = True
                    access.modified_by = request.user
                    access.save()

                AppAccessAuditLog.log_change(
                    user=user,
                    app_code=app_code,
                    action='access_granted',
                    new_value={'role': role},
                    modified_by=request.user,
                    request=request
                )

                granted_count += 1

        app_name = INTEGRATED_APPS[app_code]['name']
        messages.success(request, f"Granted {role} access to {app_name} for {granted_count} users")

        return JsonResponse({
            'success': True,
            'granted_count': granted_count,
            'app_name': app_name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
